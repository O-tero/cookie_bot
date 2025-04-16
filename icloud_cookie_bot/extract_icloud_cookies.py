#!/usr/bin/env python3
"""
iCloud Cookie Extractor

This script extracts iCloud authentication cookies from Chrome on macOS
and saves them to a JSON file for use with automation tools.

Usage:
    python extract_icloud_cookies.py [--output cookies.json]
"""

import os
import sys
import json
import sqlite3
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Optional, List

# iCloud cookie names we're looking for
REQUIRED_COOKIES = [
    "X-APPLE-WEBAUTH-HSA-TRUST",
    "X-APPLE-ID-SESSION-ID",
    "X-APPLE-WEBAUTH-USER",
    "dsid",
    "scnt",
    "X-APPLE-ID-TOKEN",
]


def get_chrome_cookie_path() -> Path:
    """Get the path to Chrome's Cookies database on macOS."""
    user_home = os.path.expanduser("~")
    return (
        Path(user_home)
        / "Library"
        / "Application Support"
        / "Google"
        / "Chrome"
        / "Default"
        / "Cookies"
    )


def get_chrome_profiles() -> List[Dict[str, str]]:
    """Get a list of available Chrome profiles."""
    user_home = os.path.expanduser("~")
    chrome_dir = (
        Path(user_home) / "Library" / "Application Support" / "Google" / "Chrome"
    )

    profiles = []

    # Check for the default profile
    default_path = chrome_dir / "Default"
    if default_path.exists() and (default_path / "Cookies").exists():
        profiles.append({"name": "Default", "path": str(default_path), "id": "default"})

    # Look for numbered profiles
    for item in chrome_dir.glob("Profile *"):
        if item.is_dir() and (item / "Cookies").exists():
            profile_id = item.name.lower().replace(" ", "_")
            profiles.append({"name": item.name, "path": str(item), "id": profile_id})

    return profiles


def decrypt_cookie_value(encrypted_value: bytes) -> Optional[str]:
    """
    Decrypt Chrome cookie value on macOS using the system keychain.

    This is a simplified version that works for many cookie types.
    For v10 cookies, would need more complex decryption using the Chrome Safe Storage key.
    """
    # For newer Chrome versions with v10 encryption
    if encrypted_value.startswith(b"v10"):
        try:
            # Get Chrome's encryption key from macOS keychain
            cmd = [
                "security",
                "find-generic-password",
                "-w",
                "-a",
                "Chrome",
                "-s",
                "Chrome Safe Storage",
            ]
            chrome_key = subprocess.check_output(cmd).strip()
            print(f"WARNING: v10 encrypted cookie found. Advanced decryption needed.")
            # Full v10 decryption would require PBKDF2 and AES operations
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error accessing macOS keychain: {e}")
            return None

    # For older/simpler cookie encryption
    try:
        # Try UTF-8 decoding first (sometimes works for older cookies)
        return encrypted_value.decode("utf-8")
    except UnicodeDecodeError:
        # Fall back to hex representation if decoding fails
        return encrypted_value.hex()


def extract_cookies(profile_path: str) -> Dict[str, str]:
    """Extract iCloud cookies from the specified Chrome profile."""
    cookies_path = Path(profile_path) / "Cookies"

    if not cookies_path.exists():
        print(f"Cookies database not found at: {cookies_path}")
        return {}

    # Create a temporary copy of the database (since Chrome might have it locked)
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "chrome_cookies.db")

    try:
        # Copy the database
        shutil.copy2(str(cookies_path), temp_db_path)

        # Connect to the copied database
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        cookies = {}
        for cookie_name in REQUIRED_COOKIES:
            # Query for cookies from apple.com domains
            cursor.execute(
                "SELECT name, value, host_key, encrypted_value FROM cookies "
                "WHERE name = ? AND host_key LIKE '%apple.com%'",
                (cookie_name,),
            )

            results = cursor.fetchall()
            if results:
                for row in results:
                    name, value, host_key, encrypted_value = row

                    # If we have a plaintext value, use it
                    if value:
                        cookies[name] = value
                        print(f"Found cookie: {name} (plaintext) from {host_key}")
                    # Otherwise try to decrypt the encrypted value
                    elif encrypted_value:
                        decrypted = decrypt_cookie_value(encrypted_value)
                        if decrypted:
                            cookies[name] = decrypted
                            print(f"Found cookie: {name} (encrypted) from {host_key}")
            else:
                print(f"Cookie not found: {cookie_name}")

        conn.close()
        return cookies

    except Exception as e:
        print(f"Error extracting cookies: {e}")
        return {}
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


def save_cookies(cookies: Dict[str, str], output_path: str):
    """Save extracted cookies to a JSON file."""
    try:
        with open(output_path, "w") as f:
            json.dump(
                {"cookies": cookies, "timestamp": __import__("time").time()},
                f,
                indent=2,
            )
        print(f"Cookies saved to: {output_path}")
    except Exception as e:
        print(f"Error saving cookies: {e}")


def main():
    parser = argparse.ArgumentParser(description="Extract iCloud cookies from Chrome")
    parser.add_argument(
        "--output", default="icloud_cookies.json", help="Output file path"
    )
    parser.add_argument(
        "--list-profiles", action="store_true", help="List available Chrome profiles"
    )
    parser.add_argument("--profile", default="Default", help="Chrome profile to use")
    args = parser.parse_args()

    # Get available profiles
    profiles = get_chrome_profiles()

    if not profiles:
        print("No Chrome profiles found. Is Chrome installed?")
        return 1

    # List profiles if requested
    if args.list_profiles:
        print("Available Chrome profiles:")
        for i, profile in enumerate(profiles):
            print(f"{i+1}. {profile['name']} ({profile['id']})")
        return 0

    # Find the requested profile
    selected_profile = None
    for profile in profiles:
        if profile["name"] == args.profile or profile["id"] == args.profile:
            selected_profile = profile
            break

    if not selected_profile:
        print(f"Profile '{args.profile}' not found. Available profiles:")
        for profile in profiles:
            print(f"- {profile['name']} ({profile['id']})")
        return 1

    print(f"Extracting iCloud cookies from profile: {selected_profile['name']}")
    cookies = extract_cookies(selected_profile["path"])

    if not cookies:
        print("No iCloud cookies found. Are you logged into iCloud in Chrome?")
        return 1

    print(f"Found {len(cookies)} out of {len(REQUIRED_COOKIES)} required cookies")

    # Check for missing cookies
    missing = [cookie for cookie in REQUIRED_COOKIES if cookie not in cookies]
    if missing:
        print(f"Missing cookies: {', '.join(missing)}")

    # Save the cookies
    save_cookies(cookies, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
