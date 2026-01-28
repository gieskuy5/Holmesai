# HolmesAI Bot

Automated bot for HolmesAI platform registration and daily check-in management.

## Features

- **Auto Register**: Automatically register multiple accounts on HolmesAI platform
  - Generate Ethereum wallets with mnemonic phrases
  - Solve Cloudflare Turnstile captcha automatically
  - Create randomized AI personas with unique knowledge bases
  - Auto-bind social media profiles (X/Twitter, Discord, Telegram)
  - Claim profile completion rewards
  - Support for proxy rotation
  
- **Auto Daily Check-in**: Automated 24-hour check-in loop
  - Load existing accounts from wallets_full.json
  - Automatic daily check-in for all accounts
  - Track check-in streaks and points
  - Support for proxy rotation

## Requirements

- Python 3.7+
- Required packages:
  ```
  eth-account
  requests
  pathlib
  ```

## Installation

1. Install required dependencies:
   ```bash
   pip install eth-account requests
   ```

2. Configure your captcha API keys in `config.json` (see Configuration section)

3. (Optional) Add proxies to `proxy.txt` (one proxy per line)

## Configuration

### config.json

The bot uses a `config.json` file to store configuration settings. Create this file in the same directory as `main.py`:

```json
{
  "captcha": {
    "api_key_1": "your_first_2captcha_api_key",
    "api_key_2": "your_second_2captcha_api_key"
  },
  "referral_code": "aS2sSqBp",
  "turnstile_sitekey": "0x4AAAAAACHUNmLd4bE8xwKK"
}
```

**Configuration Fields:**
- `captcha.api_key_1`: First 2Captcha API key (get from https://2captcha.com)
- `captcha.api_key_2`: Second 2Captcha API key (optional, for load balancing)
- `referral_code`: HolmesAI referral code (default: aS2sSqBp)
- `turnstile_sitekey`: Cloudflare Turnstile site key (usually doesn't need to be changed)

**Why Two Captcha Keys?**
- Load balancing across multiple API keys
- Avoid hitting rate limits on a single key
- Increase registration speed when processing many accounts
- Redundancy if one key runs out of balance

### proxy.txt

Add your proxies (one per line) in the following formats:
```
host:port
host:port:username:password
http://host:port
http://username:password@host:port
```

## Usage

Run the bot:
```bash
python main.py
```

### Menu Options:

1. **Auto Register** - Register new accounts
   - Enter the number of accounts to create
   - Optionally modify the referral code
   - Choose whether to use proxies
   - Select which captcha API key to use (1 or 2)
   - The bot will automatically:
     - Generate wallets
     - Solve captchas
     - Register accounts
     - Create personas
     - Bind social profiles
     - Save results to `wallets_full.json`

2. **Auto Daily Check-in** - Run 24-hour check-in loop
   - Choose whether to use proxies
   - Select which captcha API key to use (1 or 2)
   - The bot will:
     - Load accounts from `wallets_full.json`
     - Perform check-ins for all accounts
     - Wait 24 hours
     - Repeat automatically
   - Press Ctrl+C to stop

## Output Files

- **wallets_full.json** - Stores all account information including:
  - Wallet address and private key
  - User ID and invite code
  - Persona details
  - Points and tier information
  - Profile bindings

## Captcha Service

> **IMPORTANT**: This bot **EXCLUSIVELY** uses [2Captcha](https://2captcha.com) to solve Cloudflare Turnstile captchas. No other captcha solving services are supported or integrated.

**Setup Steps:**
1. Create an account at https://2captcha.com
2. Add funds to your account
3. Get your API key from the dashboard
4. Add the API key(s) to `config.json`

**Why 2Captcha Only?**
- Proven reliability for Cloudflare Turnstile challenges
- Fast solving times (usually 10-30 seconds)
- Competitive pricing
- Official API with good documentation
- No need for multiple service integrations

**Tip:** Using two API keys allows you to distribute the captcha solving load and avoid rate limits.

## Proxy Support

The bot supports using proxies for each account to avoid IP restrictions:
- Add proxies to `proxy.txt` (one per line)
- Proxies will be rotated automatically for each account
- Supports HTTP/HTTPS proxies with or without authentication

## Security Notes

- Keep your `config.json` and `wallets_full.json` files secure
- Never share your private keys or wallet files
- Store your mnemonic phrases safely
- Don't commit sensitive files to version control

## Troubleshooting

**Captcha fails:**
- Check if your 2Captcha API key has sufficient balance
- Try switching to the other API key
- Verify the API key is correctly set in `config.json`

**"config.json not found" error:**
- Create the `config.json` file in the same directory as `main.py`
- Use the format shown in the Configuration section

**Registration fails:**
- Check your internet connection
- Verify proxy settings if using proxies
- Ensure 2Captcha service is working

**Check-in fails:**
- Verify accounts exist in `wallets_full.json`
- Check if the accounts have valid user_id and private_key fields

## Telegram

For support and updates: https://t.me/MDFKOfficial

## Disclaimer

This bot is for educational purposes only. Use at your own risk. Make sure you comply with HolmesAI's terms of service.
