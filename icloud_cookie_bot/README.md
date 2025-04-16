# iCloud Hide My Email Generator Bot

A Python-based console application that automates the extraction of iCloud session cookies from multiple Chrome profiles and generates Hide My Email addresses on a scheduled basis.

## 🌟 Features

- **Automated Cookie Extraction**: Extracts essential iCloud session cookies from multiple Chrome user profiles
- **Multi-Profile Support**: Handle multiple Chrome profiles, each with a different iCloud account
- **Cookie Decryption**: Automatically decrypts Chrome's encrypted cookies
- **Scheduler**: Runs extraction and generation tasks on a configurable schedule
- **Console UI**: User-friendly command-line interface for monitoring and configuration
- **Daemon Mode**: Run headless for 24/7 operation

## 📋 Prerequisites

- Python 3.7+
- Google Chrome with active iCloud logins
- iCloud+ subscription (required for Hide My Email feature)
- A cloned version of the hidemyemail-generator repository

## 🔧 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/icloud-hidemyemail-bot.git
   cd icloud-hidemyemail-bot
   ```

2. Clone the hidemyemail-generator repository:
   ```bash
   git clone https://github.com/username/hidemyemail-generator.git
   ```

3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

The application uses a `config.json` file to store configuration:

```json
{
  "profiles": [
    {
      "name": "Profile 1",
      "path": "C:/Users/YourUser/AppData/Local/Google/Chrome/User Data/Profile 1",
      "id": "profile1"
    },
    {
      "name": "Profile 2",
      "path": "C:/Users/YourUser/AppData/Local/Google/Chrome/User Data/Profile 2",
      "id": "profile2"
    }
  ],
  "email_limit_per_hour": 5,
  "refresh_interval_minutes": 60
}
```

- **profiles**: List of Chrome profiles to extract cookies from
  - **name**: Display name for the profile
  - **path**: Path to the Chrome profile directory
  - **id**: Unique identifier for the profile
- **email_limit_per_hour**: Maximum number of emails to generate per profile per hour
- **refresh_interval_minutes**: Interval between cookie extraction and email generation

## 🚀 Usage

### Interactive Mode

Run the application with the interactive UI:

```bash
python main.py
```

This opens a console interface with the following options:
1. Start scheduler
2. Stop scheduler
3. Run jobs now
4. View status
5. Configure profiles
6. View generated emails
7. Exit

### Daemon Mode

Run the application as a background service:

```bash
python main.py --daemon
```

This starts the scheduler and runs in the background, displaying only minimal status information.

### Custom Configuration

Specify a custom configuration file:

```bash
python main.py --config myconfiguration.json
```

## 🧠 How It Works

### Cookie Extraction

1. The application identifies Chrome's cookie database for each configured profile
2. It extracts the following cookies:
   - X-APPLE-WEBAUTH-HSA-TRUST
   - X-APPLE-ID-SESSION-ID
   - X-APPLE-WEBAUTH-USER
   - dsid
   - scnt
   - X-APPLE-ID-TOKEN

### Cookie Decryption

- On **macOS**: Uses the Keychain to decrypt cookies

### Session Management

- Extracted cookies are stored in session files in the `sessions` directory
- Each profile has its own session file (`profile_id.json`)
- Sessions are validated before use and refreshed as needed

### Email Generation

- The application integrates with the hidemyemail-generator tool
- It passes the extracted cookies to authenticate with iCloud
- Respects Apple's limit of 5 emails per hour per account

## 📚 Project Structure

```
icloud_cookie_bot/
├── profiles/
│   └── profile1/
│   └── profile2/
├── sessions/
│   └── profile1.json
│   └── profile2.json
├── logs/
│   └── bot.log
├── main.py
├── extract_cookies.py
├── scheduler.py
├── generator_client.py
├── config.json
└── README.md
```

## ⚠️ Important Notes

- **Security**: This application handles sensitive data (cookies). Use it only on secure machines.
- **Terms of Service**: Ensure your use complies with Apple's terms of service.
- **Rate Limiting**: Apple may rate-limit or detect automated activity.
- **Cookie Expiration**: iCloud cookies can expire or be invalidated by Apple.

## 🔨 Troubleshooting

### Common Issues

1. **"Failed to extract cookies"**
   - Ensure Chrome is not running when extracting cookies
   - Check that the profile paths are correct
   - Verify that the profiles are logged into iCloud

2. **"Failed to generate email"**
   - Check if the cookies are valid
   - Ensure the hidemyemail-generator tool is properly configured
   - Verify the iCloud account has an iCloud+ subscription

3. **"Decryption failed"**
   - On macOS: Check that the Keychain is accessible

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- hidemyemail-generator for the email generation functionality
- browser-cookie3 for cookie extraction inspirations