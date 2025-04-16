# iCloud Hide My Email Generator Bot - Complete Setup Guide

This comprehensive guide will walk you through setting up and running the iCloud Hide My Email Generator Bot from scratch. Follow these detailed steps to automate extraction of iCloud session cookies from Chrome profiles and schedule automatic email generation.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Initial Configuration](#initial-configuration)
- [Running the Application](#running-the-application)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)
- [Maintaining the System](#maintaining-the-system)

## Prerequisites

Before starting, ensure you have:

- **Python 3.7+** installed on your system
- **Google Chrome** with active iCloud logins on multiple profiles
- **iCloud+ subscription** on each account (required for Hide My Email functionality)
- **Git** installed for cloning repositories
- Administrator/sudo privileges (required for Chrome cookie access)
- Windows, macOS, or Linux operating system

## Installation

### Step 1: Set up the project directory

```bash
# Create project directory
mkdir icloud-email-bot
cd icloud-email-bot

# Create required subdirectories
mkdir -p logs sessions profiles
```

### Step 2: Set up a virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Clone the repositories

```bash
# Clone the hidemyemail-generator repo
git clone https://github.com/username/hidemyemail-generator.git

# Create our project files
touch main.py extract_cookies.py scheduler.py generator_client.py config.json requirements.txt
```

### Step 4: Create the requirements.txt file

Copy the following content to the `requirements.txt` file:

```
requests==2.31.0
schedule==1.2.0
cryptography==41.0.3
pycryptodome==3.19.0
pywin32==306; sys_platform == 'win32'
colorama==0.4.6
rich==13.5.2
```

### Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Create the project files

Copy and paste the code for each of the following files from the provided implementation:

1. `extract_cookies.py` - Cookie extraction module
2. `generator_client.py` - Hide My Email generator integration
3. `scheduler.py` - Task scheduling system
4. `main.py` - Main console application
5. `config.json` - Configuration file (or let the application create it)

## Initial Configuration

### Step 1: Create a basic configuration

You can either manually create a `config.json` file with the following template or let the application auto-detect profiles:

```json
{
  "profiles": [
    {
      "name": "Profile 1",
      "path": "PATH_TO_CHROME_PROFILE_1",
      "id": "profile1"
    },
    {
      "name": "Profile 2",
      "path": "PATH_TO_CHROME_PROFILE_2",
      "id": "profile2"
    }
  ],
  "email_limit_per_hour": 5,
  "refresh_interval_minutes": 60
}
```

Replace `PATH_TO_CHROME_PROFILE_X` with the actual path to your Chrome profiles:

- **macOS**: `/Users/YourUsername/Library/Application Support/Google/Chrome/Profile X`

### Step 2: Verify Chrome profiles have active iCloud sessions

For each Chrome profile in your configuration:

1. Open Chrome with that specific profile
2. Navigate to `https://www.icloud.com/`
3. Ensure you are logged in to an iCloud account with iCloud+ subscription
4. Verify that Hide My Email is available in the account settings
5. Close Chrome completely before running the bot

## Running the Application

### Interactive Mode

Start the application in interactive mode to configure and test:

```bash
python main.py
```

#### First-time setup steps:

1. **Select option 5** to configure profiles
   - Choose option 4 to auto-detect Chrome profiles
   - Confirm the profiles that are detected

2. **Select option 3** to run jobs immediately
   - This will test cookie extraction and email generation
   - Review the output for any errors

3. **Select option 4** to view the status
   - Check that cookies were successfully extracted
   - Verify if any emails were generated

### Testing Cookie Extraction

To specifically test cookie extraction without starting the scheduler:

1. Ensure Chrome is completely closed
2. In the main menu, select option 3 to run jobs now
3. Check the logs directory for detailed logs:
   ```bash
   cat logs/bot.log | grep "cookie"
   ```

### Starting the Scheduler

Once you've confirmed everything works:

1. From the main menu, select option 1 to start the scheduler
2. The application will now run on the configured schedule
3. You can view the status at any time by selecting option 4

### Daemon Mode

For 24/7 operation without the interactive interface:

```bash
python main.py --daemon
```

Consider setting up a system service or using tools like `screen`, `tmux`, or `nohup` to keep the process running:

```bash
# Using nohup
nohup python main.py --daemon > daemon.log 2>&1 &

# Using screen
screen -S email-bot
python main.py --daemon
# Press Ctrl+A, then D to detach
```

## Advanced Configuration

### Customizing the Schedule

Edit `config.json` to change the refresh interval:

```json
{
  "refresh_interval_minutes": 30
}
```

### Adjusting Email Generation Limits

Configure how many emails to generate per profile per hour:

```json
{
  "email_limit_per_hour": 3
}
```

### Using a Custom Configuration File

Run the application with a custom configuration file:

```bash
python main.py --config custom_config.json
```

### Setting up for Multiple Systems

To deploy on multiple systems:

1. Copy the entire project directory
2. On each system, run the application with auto-detection:
   ```bash
   python main.py
   ```
3. Use option 5 → 4 to auto-detect the system's Chrome profiles
4. Configure the scheduler as needed

## Troubleshooting

### Cookie Extraction Issues

**Issue**: "Failed to extract cookies" error

**Solutions**:
1. Ensure Chrome is completely closed during extraction
   ```bash
   # On Windows
   taskkill /F /IM chrome.exe
   
   # On macOS
   killall "Google Chrome"
   
   # On Linux
   pkill -f chrome
   ```

2. Verify profile paths are correct
   ```bash
   # Check file existence on Windows
   dir "C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data\Profile 1\Cookies"
   
   # Check on macOS/Linux
   ls -la ~/Library/Application\ Support/Google/Chrome/Profile\ 1/Cookies
   ```

3. Check permissions
   ```bash
   # Run with elevated privileges on Windows
   # Run Command Prompt as Administrator and then run the script
   
   # On macOS/Linux
   sudo python main.py
   ```

### Decryption Issues

**Issue**: "Decryption failed" or "Could not decrypt cookie value"

**Solutions**:
1. Ensure you're using the same user account that created the cookies
2. On macOS, check keychain access:
   ```bash
   security find-generic-password -a Chrome
   ```
3. On Windows, verify the Local State file exists:
   ```bash
   dir "C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data\Local State"
   ```

### Email Generation Failures

**Issue**: "Failed to generate email" error

**Solutions**:
1. Verify cookies are valid by checking extraction logs
2. Ensure the hidemyemail-generator is properly configured:
   ```bash
   cd hidemyemail-generator
   python main.py --help
   ```
3. Check if the iCloud account has an active iCloud+ subscription
4. Verify Apple's services aren't down or rate-limiting your requests

## Maintaining the System

### Regular Tasks

1. **Update dependencies** periodically:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Backup your configuration**:
   ```bash
   cp config.json config.json.backup
   ```

3. **Clear old logs** to prevent disk space issues:
   ```bash
   # Delete logs older than 7 days
   find logs -type f -name "*.log" -mtime +7 -delete
   ```

4. **Periodic login refreshes**:
   - Every few weeks, log into each iCloud account in Chrome
   - This helps prevent session expirations

### Monitoring

1. **Check application logs**:
   ```bash
   tail -f logs/bot.log
   ```

2. **View generated emails** through the UI:
   ```bash
   python main.py
   # Select option 6
   ```

3. **Check process status** when running in daemon mode:
   ```bash
   ps aux | grep "python main.py --daemon"
   ```

### Security Best Practices

1. **Restrict access** to the project directory:
   ```bash
   # On macOS/Linux
   chmod 700 -R icloud-email-bot/
   ```

2. **Encrypt sensitive files** when not in use:
   ```bash
   # Example using GPG
   gpg -c sessions/profile1.json
   ```

3. **Run on a private network** to prevent unauthorized access

4. **Use a dedicated user account** for running the bot in production environments


By following this guide, you should have a fully functional iCloud Hide My Email generator bot running on your system. For any issues not covered in the troubleshooting section, check the logs for detailed error messages and consider filing an issue on the project repository.