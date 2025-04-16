# main.py
import os
import sys
import json
import time
import logging
import argparse
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union

# Import our modules
from extract_cookies import CookieExtractor
from generator_client import HideMyEmailGenerator
from scheduler import TaskScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

# ASCII art for the console header
HEADER = """
╔═════════════════════════════════════════════════════════════╗
║                iCloud HideMyEmail Generator                 ║
║                   24/7 Console Edition                      ║
╚═════════════════════════════════════════════════════════════╝
"""

class ConsoleUI:
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the console UI.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.scheduler = TaskScheduler(config_path)
        self.extractor = CookieExtractor(config_path)
        self.generator = HideMyEmailGenerator()
        
        # Ensure directories exist
        Path("logs").mkdir(exist_ok=True)
        Path("sessions").mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # UI state
        self.running = False
        self.ui_thread = None
        
    def _load_config(self) -> dict:
        """Load the configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}")
            return self._create_default_config()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file: {self.config_path}")
            return self._create_default_config()
            
    def _create_default_config(self) -> dict:
        """Create a default configuration."""
        config = {
            "profiles": [],
            "email_limit_per_hour": 5,
            "refresh_interval_minutes": 60
        }
        
        # Try to auto-detect Chrome profiles
        profiles = self._detect_chrome_profiles()
        if profiles:
            config["profiles"] = profiles
            
        # Save the default configuration
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        return config
        
    def _detect_chrome_profiles(self) -> List[Dict[str, str]]:
        """Try to auto-detect Chrome profiles on macOS."""
        profiles = []
        
        # macOS Chrome profiles path
        base_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Google", "Chrome")
            
        if not os.path.exists(base_path):
            return []
            
        # Look for profile directories
        try:
            for item in os.listdir(base_path):
                profile_path = os.path.join(base_path, item)
                
                # Check if it's a directory and contains a Cookies file
                if (os.path.isdir(profile_path) and 
                    (item.startswith("Profile ") or item == "Default") and
                    os.path.exists(os.path.join(profile_path, "Cookies"))):
                    
                    profile_id = item.lower().replace(" ", "_")
                    profiles.append({
                        "name": item,
                        "path": profile_path,
                        "id": profile_id
                    })
                    
            return profiles
        except Exception as e:
            logger.error(f"Error detecting Chrome profiles: {e}")
            return []
            
    def display_menu(self):
        """Display the main menu."""
        print(HEADER)
        print("\nMain Menu:")
        print("1. Start scheduler")
        print("2. Stop scheduler")
        print("3. Run jobs now")
        print("4. View status")
        print("5. Configure profiles")
        print("6. View generated emails")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ")
        return choice
        
    def display_status(self):
        """Display the current status."""
        status = self.scheduler.get_status()
        
        print("\nCurrent Status:")
        print(f"Running: {'Yes' if status['running'] else 'No'}")
        
        if status['last_extraction']:
            print(f"Last extraction: {status['last_extraction']}")
            
        if status['next_scheduled']:
            print(f"Next scheduled: {status['next_scheduled']}")
            
            # Show countdown
            time_until = status['time_until_next']
            if time_until:
                minutes, seconds = divmod(time_until, 60)
                print(f"Time until next job: {int(minutes)}m {int(seconds)}s")
                
        # Show profile stats
        print("\nProfile Statistics:")
        for profile in self.config.get("profiles", []):
            profile_id = profile.get("id")
            
            if profile_id in status['stats']['emails_generated']:
                emails = status['stats']['emails_generated'][profile_id]
                extractions = status['stats']['extraction_counts'][profile_id]
                
                print(f"Profile {profile['name']}:")
                print(f"  - Emails generated: {emails}")
                print(f"  - Cookies extracted: {extractions}")
                
        input("\nPress Enter to continue...")
        
    def configure_profiles(self):
        """Configure the profiles."""
        print("\nProfile Configuration:")
        
        # Show existing profiles
        profiles = self.config.get("profiles", [])
        
        if not profiles:
            print("No profiles configured.")
        else:
            print("Existing profiles:")
            for i, profile in enumerate(profiles):
                print(f"{i+1}. {profile.get('name')} (ID: {profile.get('id')})")
                
        print("\nOptions:")
        print("1. Add a new profile")
        print("2. Edit an existing profile")
        print("3. Remove a profile")
        print("4. Auto-detect profiles")
        print("5. Return to main menu")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            # Add a new profile
            name = input("Enter profile name: ")
            path = input("Enter profile path: ")
            profile_id = name.lower().replace(" ", "_")
            
            profiles.append({
                "name": name,
                "path": path,
                "id": profile_id
            })
            
            self._save_config()
            print(f"Profile '{name}' added.")
            
        elif choice == "2":
            # Edit an existing profile
            if not profiles:
                print("No profiles to edit.")
                return
                
            idx = input("Enter the number of the profile to edit: ")
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(profiles):
                    profile = profiles[idx]
                    
                    name = input(f"Enter new name [{profile.get('name')}]: ")
                    path = input(f"Enter new path [{profile.get('path')}]: ")
                    
                    if name:
                        profile["name"] = name
                    if path:
                        profile["path"] = path
                        
                    self._save_config()
                    print("Profile updated.")
                else:
                    print("Invalid profile number.")
            except ValueError:
                print("Invalid input.")
                
        elif choice == "3":
            # Remove a profile
            if not profiles:
                print("No profiles to remove.")
                return
                
            idx = input("Enter the number of the profile to remove: ")
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(profiles):
                    removed = profiles.pop(idx)
                    self._save_config()
                    print(f"Profile '{removed.get('name')}' removed.")
                else:
                    print("Invalid profile number.")
            except ValueError:
                print("Invalid input.")
                
        elif choice == "4":
            # Auto-detect profiles
            detected = self._detect_chrome_profiles()
            
            if not detected:
                print("No Chrome profiles detected.")
                return
                
            print(f"Detected {len(detected)} Chrome profiles:")
            for i, profile in enumerate(detected):
                print(f"{i+1}. {profile.get('name')} (Path: {profile.get('path')})")
                
            confirm = input("\nReplace existing profiles with these? (y/n): ")
            if confirm.lower() == "y":
                self.config["profiles"] = detected
                self._save_config()
                print("Profiles updated.")
                
        input("\nPress Enter to continue...")
        
    def _save_config(self):
        """Save the configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved.")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            
    def view_generated_emails(self):
        """View the generated emails."""
        print("\nGenerated Emails:")
        
        # Get all session files
        sessions_dir = Path("sessions")
        session_files = list(sessions_dir.glob("*.json"))
        
        if not session_files:
            print("No sessions found.")
            input("\nPress Enter to continue...")
            return
            
        # Load and display sessions
        for session_file in session_files:
            profile_id = session_file.stem
            
            try:
                with open(session_file, 'r') as f:
                    session = json.load(f)
                    
                # Find the profile name
                profile_name = profile_id
                for profile in self.config.get("profiles", []):
                    if profile.get("id") == profile_id:
                        profile_name = profile.get("name")
                        break
                        
                print(f"\nProfile: {profile_name}")
                print(f"Last updated: {datetime.fromtimestamp(session.get('timestamp', 0))}")
                
                # Get emails for this profile from the email log
                # In a real implementation, we would store generated emails
                status = self.scheduler.get_status()
                count = status['stats']['emails_generated'].get(profile_id, 0)
                print(f"Total emails generated: {count}")
                
            except Exception as e:
                logger.error(f"Error reading session file {session_file}: {e}")
                
        input("\nPress Enter to continue...")
        
    def run_cli(self):
        """Run the command-line interface."""
        self.running = True
        
        while self.running:
            os.system('clear')  # macOS uses 'clear'
            choice = self.display_menu()
            
            if choice == "1":
                # Start scheduler
                if self.scheduler.start():
                    print("Scheduler started.")
                else:
                    print("Failed to start scheduler.")
                    
                input("\nPress Enter to continue...")
                
            elif choice == "2":
                # Stop scheduler
                if self.scheduler.stop():
                    print("Scheduler stopped.")
                else:
                    print("Scheduler is not running.")
                    
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                # Run jobs now
                print("Running jobs now...")
                result = self.scheduler.run_now()
                
                if result['cookies_extracted']:
                    print("Cookies extracted successfully.")
                else:
                    print("Failed to extract cookies.")
                    
                emails = result['emails_generated']
                if emails:
                    print(f"Generated {sum(len(emails) for emails in emails.values())} emails.")
                else:
                    print("No emails generated.")
                    
                input("\nPress Enter to continue...")
                
            elif choice == "4":
                # View status
                self.display_status()
                
            elif choice == "5":
                # Configure profiles
                self.configure_profiles()
                
            elif choice == "6":
                # View generated emails
                self.view_generated_emails()
                
            elif choice == "7":
                # Exit
                self.running = False
                
                # Stop the scheduler if it's running
                if self.scheduler.running:
                    self.scheduler.stop()
                    
                print("Exiting...")
                
            else:
                print("Invalid choice. Please try again.")
                input("\nPress Enter to continue...")
                
    def run_daemon(self):
        """Run as a daemon process without UI."""
        print(HEADER)
        print("\nStarting in daemon mode...")
        
        # Start the scheduler
        self.scheduler.start()
        
        try:
            # Keep running until interrupted
            while True:
                status = self.scheduler.get_status()
                time_until = status.get('time_until_next', 0)
                
                if time_until:
                    minutes, seconds = divmod(time_until, 60)
                    sys.stdout.write(f"\rNext job in: {int(minutes)}m {int(seconds)}s" + " " * 10)
                    sys.stdout.flush()
                    
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.scheduler.stop()
            print("Goodbye!")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="iCloud HideMyEmail Generator")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode without UI")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    args = parser.parse_args()
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Create the console UI
    ui = ConsoleUI(args.config)
    
    if args.daemon:
        # Run in daemon mode
        ui.run_daemon()
    else:
        # Run the interactive CLI
        ui.run_cli()

if __name__ == "__main__":
    main()