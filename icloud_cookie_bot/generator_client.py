# generator_client.py
import os
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("generator_client")

class HideMyEmailGenerator:
    def __init__(self, generator_path: str = "hidemyemail-generator"):
        """
        Initialize the Hide My Email generator client.
        
        Args:
            generator_path: Path to the hidemyemail-generator repository
        """
        self.generator_path = Path(generator_path)
        self.sessions_dir = Path("sessions")
        
        # Ensure the generator exists
        if not self.generator_path.exists():
            logger.error(f"Generator path not found: {self.generator_path}")
            raise FileNotFoundError(f"Generator path not found: {self.generator_path}")
        
        # Ensure the generator's main script exists
        self.main_script = self.generator_path / "main.py"
        if not self.main_script.exists():
            logger.error(f"Generator main script not found: {self.main_script}")
            raise FileNotFoundError(f"Generator main script not found: {self.main_script}")
    
    def load_session(self, profile_id: str) -> Optional[Dict]:
        """Load a session from the sessions directory."""
        session_path = self.sessions_dir / f"{profile_id}.json"
        
        if not session_path.exists():
            logger.error(f"Session file not found for profile {profile_id}")
            return None
            
        try:
            with open(session_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load session for profile {profile_id}: {e}")
            return None
    
    def generate_email(self, profile_id: str, label: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Generate a new Hide My Email address using the specified profile.
        
        Args:
            profile_id: ID of the profile to use
            label: Optional label for the generated email
        
        Returns:
            Tuple containing success status and generated email (if successful)
        """
        session = self.load_session(profile_id)
        if not session:
            return False, None
        
        cookies = session.get("cookies", {})
        if not cookies:
            logger.error(f"No cookies found in session for profile {profile_id}")
            return False, None
            
        # Create a temporary cookie file for the generator
        cookie_file = Path(f"temp_{profile_id}_cookies.json")
        try:
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f)
                
            # Build the command
            cmd = [
                "python", 
                str(self.main_script),
                "--cookie-file", str(cookie_file)
            ]
            
            if label:
                cmd.extend(["--label", label])
                
            # Execute the generator
            logger.info(f"Executing generator for profile {profile_id}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.generator_path)
            )
            
            # Process the output
            if result.returncode == 0:
                # Parse the output to extract the generated email
                output = result.stdout.strip()
                generated_email = self._parse_email_from_output(output)
                
                if generated_email:
                    logger.info(f"Successfully generated email for profile {profile_id}: {generated_email}")
                    return True, generated_email
                else:
                    logger.error(f"Failed to parse generated email from output: {output}")
                    return False, None
            else:
                logger.error(f"Generator failed with code {result.returncode}: {result.stderr}")
                return False, None
                
        except Exception as e:
            logger.error(f"Error generating email for profile {profile_id}: {e}")
            return False, None
        finally:
            # Clean up the temporary cookie file
            if cookie_file.exists():
                cookie_file.unlink()
    
    def _parse_email_from_output(self, output: str) -> Optional[str]:
        """Parse the generated email address from the generator output."""
        # Example implementation - adjust based on actual output format
        lines = output.splitlines()
        for line in lines:
            if "@" in line and "." in line and "Generated email:" in line:
                return line.split("Generated email:")[1].strip()
            elif "@" in line and "." in line:
                # If there's only an email in the output
                parts = line.split()
                for part in parts:
                    if "@" in part and "." in part:
                        return part.strip()
        return None
        
    def generate_batch(self, profile_ids: List[str], count_per_profile: int = 1, 
                     label_prefix: str = "Auto_") -> Dict[str, List[str]]:
        """
        Generate multiple email addresses across multiple profiles.
        
        Args:
            profile_ids: List of profile IDs to use
            count_per_profile: Number of emails to generate per profile
            label_prefix: Prefix for the email labels
            
        Returns:
            Dictionary mapping profile IDs to lists of generated emails
        """
        results = {}
        
        for profile_id in profile_ids:
            results[profile_id] = []
            
            for i in range(count_per_profile):
                label = f"{label_prefix}{int(time.time())}_{i}"
                success, email = self.generate_email(profile_id, label)
                
                if success and email:
                    results[profile_id].append(email)
                    
                # Sleep to avoid rate limiting
                if i < count_per_profile - 1:
                    time.sleep(2)  # 2-second delay between generations
        
        return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generator_client.py <profile_id> [label]")
        sys.exit(1)
        
    profile_id = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else None
    
    generator = HideMyEmailGenerator()
    success, email = generator.generate_email(profile_id, label)
    
    if success:
        print(f"Generated email: {email}")
    else:
        print("Failed to generate email")
        sys.exit(1)