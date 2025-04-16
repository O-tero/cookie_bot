# scheduler.py
import time
import json
import logging
import schedule
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable

# Import our modules
from extract_cookies import CookieExtractor
from generator_client import HideMyEmailGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduler")

class TaskScheduler:
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the task scheduler.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.cookie_extractor = CookieExtractor(config_path)
        self.generator = HideMyEmailGenerator()
        
        # Keep track of the running state
        self.running = False
        self.scheduler_thread = None
        
        # Stats for UI display
        self.last_extraction = None
        self.next_scheduled = None
        self.stats = {
            "emails_generated": {},
            "extraction_counts": {}
        }
        
        # Initialize stats for each profile
        for profile in self.config.get("profiles", []):
            profile_id = profile.get("id")
            if profile_id:
                self.stats["emails_generated"][profile_id] = 0
                self.stats["extraction_counts"][profile_id] = 0
                
    def _load_config(self) -> dict:
        """Load the configuration from the specified path."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {
                "profiles": [],
                "email_limit_per_hour": 5,
                "refresh_interval_minutes": 60
            }
            
    def extract_cookies_job(self):
        """Job to extract cookies from all profiles."""
        logger.info("Running scheduled cookie extraction job")
        self.last_extraction = datetime.now()
        
        try:
            # Extract cookies from all profiles
            cookies = self.cookie_extractor.extract_all_profiles_cookies()
            
            # Update stats
            for profile_id in cookies:
                if profile_id in self.stats["extraction_counts"]:
                    self.stats["extraction_counts"][profile_id] += 1
                    
            logger.info(f"Successfully extracted cookies for {len(cookies)} profiles")
            return cookies
        except Exception as e:
            logger.error(f"Error in cookie extraction job: {e}")
            return {}
            
    def generate_emails_job(self):
        """Job to generate emails using extracted cookies."""
        logger.info("Running scheduled email generation job")
        
        try:
            # Get the email limit from config
            email_limit = self.config.get("email_limit_per_hour", 5)
            
            # Get all profile IDs
            profile_ids = [p.get("id") for p in self.config.get("profiles", []) if p.get("id")]
            
            # Generate emails
            results = self.generator.generate_batch(profile_ids, email_limit)
            
            # Update stats
            for profile_id, emails in results.items():
                if profile_id in self.stats["emails_generated"]:
                    self.stats["emails_generated"][profile_id] += len(emails)
                    
            logger.info(f"Successfully generated {sum(len(emails) for emails in results.values())} emails")
            
            # Log the results
            for profile_id, emails in results.items():
                logger.info(f"Profile {profile_id}: Generated {len(emails)} emails")
                for email in emails:
                    logger.info(f"  - {email}")
                    
            return results
        except Exception as e:
            logger.error(f"Error in email generation job: {e}")
            return {}
            
    def schedule_jobs(self):
        """Schedule jobs based on the configuration."""
        # Get the refresh interval
        refresh_interval = self.config.get("refresh_interval_minutes", 60)
        
        # Schedule the cookie extraction job
        schedule.every(refresh_interval).minutes.do(self.extract_cookies_job)
        
        # Schedule the email generation job (right after cookie extraction)
        schedule.every(refresh_interval).minutes.do(self.generate_emails_job)
        
        # Set the next scheduled time
        self.next_scheduled = datetime.now().timestamp() + (refresh_interval * 60)
        
        logger.info(f"Jobs scheduled to run every {refresh_interval} minutes")
        
    def run_scheduler(self):
        """Run the scheduler in a separate thread."""
        self.running = True
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
            
    def start(self):
        """Start the scheduler."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Scheduler is already running")
            return False
            
        # Schedule jobs
        self.schedule_jobs()
        
        # Run an initial extraction
        self.extract_cookies_job()
        
        # Start the scheduler thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Scheduler started")
        return True
        
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return False
            
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            
        logger.info("Scheduler stopped")
        return True
        
    def get_status(self) -> dict:
        """Get the current status of the scheduler."""
        return {
            "running": self.running,
            "last_extraction": self.last_extraction.isoformat() if self.last_extraction else None,
            "next_scheduled": datetime.fromtimestamp(self.next_scheduled).isoformat() if self.next_scheduled else None,
            "time_until_next": int(self.next_scheduled - time.time()) if self.next_scheduled else None,
            "stats": self.stats
        }
        
    def run_now(self) -> Dict:
        """Run the extraction and generation jobs immediately."""
        logger.info("Running jobs now")
        
        # Run the extraction job
        cookies = self.extract_cookies_job()
        
        # Run the generation job
        emails = self.generate_emails_job()
        
        # Update the next scheduled time
        refresh_interval = self.config.get("refresh_interval_minutes", 60)
        self.next_scheduled = datetime.now().timestamp() + (refresh_interval * 60)
        
        return {
            "cookies_extracted": bool(cookies),
            "emails_generated": emails
        }

if __name__ == "__main__":
    # Create a simple CLI for testing the scheduler
    scheduler = TaskScheduler()
    
    # Run the jobs once
    print("Running jobs now...")
    result = scheduler.run_now()
    
    print(f"Cookies extracted: {result['cookies_extracted']}")
    print(f"Emails generated: {result['emails_generated']}")