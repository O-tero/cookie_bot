# extract_cookies.py
import os
import json
import logging
import sqlite3
import shutil
import tempfile
from pathlib import Path
import subprocess
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("cookie_extractor")

# iCloud cookie names we need to extract
REQUIRED_COOKIES = [
    'X-APPLE-WEBAUTH-HSA-TRUST',
    'X-APPLE-ID-SESSION-ID', 
    'X-APPLE-WEBAUTH-USER',
    'dsid',
    'scnt',
    'X-APPLE-ID-TOKEN'
]

class CookieExtractor:
    def __init__(self, config_path="config.json"):
        """Initialize the cookie extractor with the specified configuration."""
        self.config = self._load_config(config_path)
        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)
        
    def _load_config(self, config_path: str) -> dict:
        """Load the configuration from a JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {"profiles": []}
            
    def get_chrome_profiles(self) -> List[dict]:
        """Return the list of configured Chrome profiles."""
        return self.config.get("profiles", [])
    
    def get_chrome_cookies_path(self, profile_path: str) -> Path:
        """Get the path to the Cookies file for the specified Chrome profile."""
        return Path(profile_path) / "Cookies"
    
    def extract_cookies_from_profile(self, profile: dict) -> Dict[str, str]:
        """Extract the required cookies from the specified Chrome profile."""
        profile_id = profile.get("id")
        profile_path = profile.get("path")
        
        if not profile_path:
            logger.error(f"No path specified for profile {profile_id}")
            return {}
            
        cookies_path = self.get_chrome_cookies_path(profile_path)
        
        if not cookies_path.exists():
            logger.error(f"Cookies file not found at {cookies_path}")
            return {}
            
        try:
            # SQLite database might be locked, so we'll make a copy
            temp_dir = tempfile.mkdtemp()
            temp_cookies_path = os.path.join(temp_dir, "Cookies")
            shutil.copy2(cookies_path, temp_cookies_path)
            
            # Connect to the database
            conn = sqlite3.connect(temp_cookies_path)
            cursor = conn.cursor()
            
            # Query for the cookies we need
            cookies = {}
            for cookie_name in REQUIRED_COOKIES:
                cursor.execute(
                    "SELECT name, value, host_key, encrypted_value FROM cookies WHERE name = ? AND host_key LIKE '%apple.com%'", 
                    (cookie_name,)
                )
                results = cursor.fetchall()
                
                for result in results:
                    name, value, host, encrypted_value = result
                    
                    # If the cookie value is encrypted, decrypt it
                    if not value and encrypted_value:
                        decrypted_value = self._decrypt_cookie_value(encrypted_value)
                        if decrypted_value:
                            cookies[name] = decrypted_value
                    elif value:
                        cookies[name] = value
            
            conn.close()
            shutil.rmtree(temp_dir)
            
            # Check if we got all required cookies
            missing_cookies = [cookie for cookie in REQUIRED_COOKIES if cookie not in cookies]
            if missing_cookies:
                logger.warning(f"Missing cookies for profile {profile_id}: {missing_cookies}")
            
            return cookies
        except Exception as e:
            logger.error(f"Error extracting cookies from profile {profile_id}: {e}")
            return {}
    
    def _decrypt_cookie_value(self, encrypted_value: bytes) -> Optional[str]:
        """Decrypt an encrypted cookie value on macOS."""
        try:
            if encrypted_value.startswith(b'v10'):
                # v10 cookies need a different approach with the macOS keychain
                cmd = ['security', 'find-generic-password', '-w', '-a', 'Chrome']
                try:
                    chrome_key = subprocess.check_output(cmd).strip()
                    # Further decryption would be needed here with the chrome_key
                    # This is a complex process requiring PBKDF2 and AES decryption
                    logger.warning("v10 cookie decryption not fully implemented")
                    return None
                except subprocess.CalledProcessError:
                    logger.error("Failed to get Chrome encryption key from keychain")
                    return None
            else:
                # Older cookies might be simpler to decrypt
                try:
                    return encrypted_value.decode('utf-8')
                except:
                    return None
        except Exception as e:
            logger.error(f"macOS decryption error: {e}")
            return None
    
    def extract_all_profiles_cookies(self) -> Dict[str, Dict[str, str]]:
        """Extract cookies from all configured Chrome profiles."""
        all_cookies = {}
        
        for profile in self.get_chrome_profiles():
            profile_id = profile.get("id")
            if not profile_id:
                logger.warning("Profile without ID found in config, skipping")
                continue
                
            logger.info(f"Extracting cookies for profile: {profile_id}")
            cookies = self.extract_cookies_from_profile(profile)
            
            if cookies:
                all_cookies[profile_id] = cookies
                # Save to individual session file
                self.save_session(profile_id, cookies)
            else:
                logger.warning(f"No cookies extracted for profile {profile_id}")
        
        return all_cookies
    
    def save_session(self, profile_id: str, cookies: Dict[str, str]) -> bool:
        """Save the extracted cookies to a session file."""
        try:
            session_path = self.sessions_dir / f"{profile_id}.json"
            with open(session_path, 'w') as f:
                json.dump({
                    "cookies": cookies,
                    "profile_id": profile_id,
                    "timestamp": import_time()
                }, f, indent=2)
            logger.info(f"Session saved for profile {profile_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session for profile {profile_id}: {e}")
            return False
            
    def validate_cookies(self, cookies: Dict[str, str]) -> bool:
        """Validate if the extracted cookies are still valid for Apple's services."""
        # This would make a simple request to an Apple service to check if cookies are valid
        # Implementation would depend on specific endpoints available
        logger.info("Cookie validation not implemented yet")
        return True

def import_time():
    """Import time module and return current timestamp."""
    import time
    return int(time.time())

if __name__ == "__main__":
    extractor = CookieExtractor()
    profiles_cookies = extractor.extract_all_profiles_cookies()
    print(f"Extracted cookies for {len(profiles_cookies)} profiles")