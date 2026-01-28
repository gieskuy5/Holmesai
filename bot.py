import json
import random
import time
import uuid
import os
import requests
from pathlib import Path
from typing import Optional, Dict, List
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_account.hdaccount import generate_mnemonic

# Enable eth_account to generate accounts
Account.enable_unaudited_hdwallet_features()

class Config:
    """Configuration settings"""
    SCRIPT_DIR = Path(__file__).parent
    PROXY_FILE = SCRIPT_DIR / "proxy.txt"
    DATA_FILE = SCRIPT_DIR / "wallets_full.json"
    CONFIG_FILE = SCRIPT_DIR / "config.json"
    
    # Load config from JSON file
    @staticmethod
    def load_config():
        """Load configuration from config.json file"""
        config_path = Path(__file__).parent / "config.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: config.json not found at {config_path}")
            print("Please create config.json with required captcha keys.")
            exit(1)
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in config.json")
            exit(1)
    
    # Load configuration
    _config = load_config.__func__()
    
    # Configuration values from config.json
    REFERRAL_CODE = _config.get("referral_code", "aS2sSqBp")
    TURNSTILE_SITEKEY = _config.get("turnstile_sitekey", "0x4AAAAAACHUNmLd4bE8xwKK")
    CAPTCHA_API_KEY_1 = _config.get("captcha", {}).get("api_key_1", "")
    CAPTCHA_API_KEY_2 = _config.get("captcha", {}).get("api_key_2", "")
    
    # API Endpoints
    BASE_URL = "https://www.holmesai.xyz"
    API_URL = "https://api.holmesai.xyz/api"
    AGENT_SERVICE_URL = "https://api.holmesai.xyz/agent-service"
    AGENT_SERVICE_PUBLIC_URL = "https://api.holmesai.xyz/agent-service-public"

# Persona options for randomization
PERSONA_OPTIONS = {
    "business": ["Real Estate", "Consulting", "Healthcare", "Marketing", "Media", "Entertainment", "Technology", "Finance"],
    "niche": ["Cloud Computing", "Web Development", "Blockchain", "Cybersecurity", "Content Creation", "DePIN", "AI/ML"],
    "tone": ["Calm", "Witty", "Formal", "Informative", "Friendly", "Professional"],
    "level": ["Entry Level", "Intermediate", "Advanced", "Expert"],
    "names": ["Riley", "Avery", "Morgan", "Casey", "Jordan", "Taylor", "Quinn", "Alex"]
}

# Knowledge base content templates for persona files
KNOWLEDGE_TEMPLATES = [
    """As a {business} professional specializing in {niche}, I bring extensive expertise and a {tone} communication style.

Key Areas of Expertise:
- Strategic planning and execution in {business}
- Technical knowledge in {niche}
- Client relationship management
- Industry best practices and trends

Professional Background:
With {level} experience, I have developed a deep understanding of the {business} sector.
My focus on {niche} allows me to provide cutting-edge solutions and insights.

Communication Approach:
I maintain a {tone} demeanor in all interactions, ensuring clear and effective communication.
My goal is to deliver value through expertise and professionalism.""",
    
    """Professional Profile: {niche} Specialist

Industry Focus: {business}
Experience Level: {level}
Communication Style: {tone}

Core Competencies:
1. Deep expertise in {niche} technologies and methodologies
2. Strong background in {business} industry practices
3. Proven track record of delivering results
4. Excellent analytical and problem-solving skills

About Me:
I am dedicated to helping clients navigate the complexities of {business} with specialized knowledge in {niche}.
My {tone} approach ensures productive and meaningful interactions.""",
    
    """Welcome! I'm your {niche} expert with a focus on {business}.

What I Offer:
- Comprehensive {niche} solutions
- {business} industry insights
- {level} expertise and guidance
- {tone} and approachable communication

My Mission:
To provide exceptional support and knowledge in {niche} while maintaining the highest standards of professionalism in the {business} sector.

Let's work together to achieve your goals!"""
]

class PersonaFileManager:
    """Manages temporary .txt files for persona creation"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Config.SCRIPT_DIR
        self.temp_files: List[Path] = []
    
    def generate_content(self, name: str, business: str, niche: str, tone: str, level: str) -> str:
        """Generate unique content for persona knowledge base file"""
        template = random.choice(KNOWLEDGE_TEMPLATES)
        content = template.format(
            business=business,
            niche=niche,
            tone=tone.lower(),
            level=level.lower()
        )
        
        # Add unique identifier and timestamp
        unique_section = f"\n\n---\nPersona: {name}\nID: {uuid.uuid4().hex[:12]}\nGenerated: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return content + unique_section
    
    def create_file(self, name: str, business: str, niche: str, tone: str, level: str) -> Path:
        """Create a unique .txt file with generated content"""
        # Generate unique filename
        filename = f"persona_{name}_{uuid.uuid4().hex[:8]}.txt"
        filepath = self.base_dir / filename
        
        # Generate content
        content = self.generate_content(name, business, niche, tone, level)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.temp_files.append(filepath)
        return filepath
    
    def delete_file(self, filepath: Path) -> bool:
        """Delete a specific file"""
        try:
            if filepath.exists():
                os.remove(filepath)
                if filepath in self.temp_files:
                    self.temp_files.remove(filepath)
                return True
        except Exception as e:
            print(f"  Warning: Could not delete temp file: {e}")
        return False
    
    def cleanup_all(self):
        """Clean up all temporary files created by this manager"""
        for filepath in self.temp_files.copy():
            self.delete_file(filepath)

class WalletGenerator:
    @staticmethod
    def generate() -> Dict:
        mnemonic = generate_mnemonic(num_words=12, lang="english")
        account = Account.from_mnemonic(mnemonic)
        return {
            "address": account.address,
            "private_key": account.key.hex(),
            "mnemonic": mnemonic,
            "account": account
        }

class TurnstileSolver:
    """
    2Captcha-only Turnstile Captcha Solver
    
    This class EXCLUSIVELY uses 2Captcha API (https://2captcha.com) to solve
    Cloudflare Turnstile captchas. No other captcha solving services are supported.
    
    API Documentation: https://2captcha.com/api-docs/turnstile
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.2captcha.com"

    def solve(self, website_url: str, website_key: str) -> Optional[str]:
        try:
            # Submit captcha task to 2Captcha
            submit_url = f"{self.base_url}/createTask"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "TurnstileTaskProxyless",
                    "websiteURL": website_url,
                    "websiteKey": website_key
                }
            }
            
            resp = requests.post(submit_url, json=payload, headers=headers, timeout=30)
            result = resp.json()
            
            if result.get("errorId") != 0:
                error_desc = result.get("errorDescription", "Unknown error")
                print(f"  Captcha submission failed: {error_desc}")
                return None
            
            task_id = result.get("taskId")
            print(f"  Captcha ID: {task_id}", end="", flush=True)
            
            # Poll for solution
            result_url = f"{self.base_url}/getTaskResult"
            for _ in range(60):
                time.sleep(5)
                print(".", end="", flush=True)
                
                result_payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id
                }
                
                resp = requests.post(result_url, json=result_payload, headers=headers, timeout=30)
                result = resp.json()
                
                if result.get("status") == "ready":
                    print(" ✓")
                    solution = result.get("solution", {})
                    return solution.get("token")
                elif result.get("errorId") != 0 or result.get("status") == "failed":
                    error_desc = result.get("errorDescription", "Unknown error")
                    print(f" ✗ Error: {error_desc}")
                    return None
            
            print(" ✗ TIMEOUT")
            return None
        except Exception as e:
            print(f" ✗ ERROR: {e}")
            return None

class ProxyManager:
    @staticmethod
    def load() -> List[str]:
        try:
            proxy_file = Path(Config.PROXY_FILE)
            if proxy_file.exists():
                with open(proxy_file, 'r') as f:
                    return [l.strip() for l in f if l.strip() and not l.startswith('#')]
        except:
            pass
        return []

    @staticmethod
    def parse(proxy_string: str) -> Optional[Dict]:
        try:
            proxy_string = proxy_string.strip()
            # If already a full URL (http:// or https://), use as-is
            if proxy_string.startswith('http://') or proxy_string.startswith('https://'):
                return {"http": proxy_string, "https": proxy_string}
            
            # Otherwise, parse host:port or host:port:user:pass format
            parts = proxy_string.split(':')
            if len(parts) == 2:
                url = f"http://{parts[0]}:{parts[1]}"
            elif len(parts) == 4:
                url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            else:
                return None
            return {"http": url, "https": url}
        except:
            return None

class AccountManager:
    @staticmethod
    def load() -> List[Dict]:
        """Load all accounts from wallets_full.json"""
        data_file = Path(Config.DATA_FILE)
        try:
            if data_file.exists():
                with open(data_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    @staticmethod
    def save(account_data: Dict):
        """Append a new account to wallets_full.json"""
        accounts = AccountManager.load()
        accounts.append(account_data)
        
        with open(Config.DATA_FILE, 'w') as f:
            json.dump(accounts, f, indent=2)
    
    @staticmethod
    def save_all(accounts: List[Dict]):
        """Save all accounts to wallets_full.json"""
        with open(Config.DATA_FILE, 'w') as f:
            json.dump(accounts, f, indent=2)
    
    @staticmethod
    def update(address: str, updates: Dict):
        """Update a specific account by address"""
        accounts = AccountManager.load()
        for acc in accounts:
            if acc.get("address") == address:
                acc.update(updates)
                break
        AccountManager.save_all(accounts)

class HolmesAIClient:
    def __init__(self, proxy: Optional[Dict] = None):
        self.session = requests.Session()
        self.idempotency_key = None
        
        self.session.headers.update({
            "accept": "*/*",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "referer": Config.BASE_URL + "/"
        })
        
        if proxy:
            self.session.proxies = proxy
            self.session.verify = False
    
    def _post(self, url: str, payload: Dict) -> Optional[Dict]:
        for attempt in range(3):
            try:
                resp = self.session.post(url, json=payload, timeout=30)
                result = resp.json()
                if result.get("RetCode") == 0:
                    return result
                return result
            except:
                if attempt < 2:
                    time.sleep(2)
        return None
    
    def submit_turnstile(self, token: str) -> tuple:
        """Returns (success, error_message)"""
        for attempt in range(3):
            try:
                resp = self.session.post(Config.AGENT_SERVICE_PUBLIC_URL, json={
                    "Action": "CloudFlareTurnStile",
                    "Token": token
                }, timeout=30)
                result = resp.json()
                if result.get("RetCode") == 0:
                    self.idempotency_key = result.get("idempotencyKey")
                    return True, None
                error_msg = result.get("Message", result.get("RetCode", "Unknown"))
                if attempt < 2:
                    time.sleep(2)
                    continue
                return False, error_msg
            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                    continue
                return False, str(e)
        return False, "Max retries reached"
    
    def get_login_message(self, address: str) -> Optional[str]:
        result = self._post(Config.API_URL, {
            "Action": "Web3LoginGetMessage",
            "Address": address
        })
        if result and result.get("RetCode") == 0:
            return result.get("Message")
        return None
    
    def verify_signature(self, message: str, signature: str) -> bool:
        result = self._post(Config.API_URL, {
            "Action": "Web3LoginVerifySign",
            "Signature": signature,
            "Message": message
        })
        return result and result.get("RetCode") == 0
    
    def get_user(self, invite_code: str = "") -> Optional[Dict]:
        payload = {"Action": "GetUser", "InviteCode": invite_code}
        if self.idempotency_key:
            payload["IdempotencyKey"] = self.idempotency_key
        return self._post(Config.AGENT_SERVICE_URL, payload)
    
    def upload_knowledge_file(self, user_id: str, filepath: Path) -> Optional[int]:
        """Upload a .txt file to create a knowledge base and return its ID"""
        try:
            # Read file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to create knowledge base with file content
            # Note: This is a simplified approach - the actual API might use multipart upload
            result = self._post(Config.AGENT_SERVICE_URL, {
                "Action": "CreateKnowledgeBase",
                "UserId": user_id,
                "Name": filepath.stem,
                "Content": content,
                "Type": "text"
            })
            
            if result and result.get("RetCode") == 0:
                return result.get("KnowledgeBaseID", result.get("ID", 0))
            
            # If API doesn't support this, return 0 to proceed without knowledge base
            return 0
        except Exception as e:
            # If upload fails, proceed without knowledge base
            return 0
    
    def create_persona(self, user_id: str, name: str, business: str, niche: str, tone: str, level: str, knowledge_base_id: int = 0) -> Optional[Dict]:
        return self._post(Config.AGENT_SERVICE_URL, {
            "Action": "CreatePersona",
            "UserId": user_id,
            "PersonaName": name,
            "Niche": niche,
            "Business": business,
            "Tone": tone,
            "Level": level,
            "Prompt": "AI Assistant",
            "IsMarket": 0,
            "KnowledgeBaseID": knowledge_base_id
        })
    
    def check_in(self, user_id: str) -> bool:
        result = self._post(Config.AGENT_SERVICE_URL, {
            "Action": "CheckIn",
            "UserId": user_id
        })
        return result and result.get("RetCode") == 0
    
    def update_user_bind(self, user_id: str, bind_type: str, bind_value: str) -> bool:
        """Update user profile binding (x, discord, telegram)"""
        result = self._post(Config.AGENT_SERVICE_URL, {
            "Action": "UpdateUserBind",
            "UserId": user_id,
            "BindType": bind_type,
            "BindValue": bind_value
        })
        return result and result.get("RetCode") == 0
    
    def claim_profile_reward(self, address: str) -> Optional[Dict]:
        """Claim profile completion reward"""
        return self._post(Config.AGENT_SERVICE_URL, {
            "Action": "ClaimProfileReward",
            "Address": address
        })

def sign_message(account, message: str) -> str:
    message_hash = encode_defunct(text=message)
    signed = account.sign_message(message_hash)
    return "0x" + signed.signature.hex()

def register_account(captcha_solver: TurnstileSolver, referral_code: str, proxy: Optional[str] = None, num: int = 1, file_manager: PersonaFileManager = None) -> bool:
    wallet = WalletGenerator.generate()
    proxy_config = ProxyManager.parse(proxy) if proxy else None
    client = HolmesAIClient(proxy_config)
    
    # Initialize file manager if not provided
    if file_manager is None:
        file_manager = PersonaFileManager()
    
    persona_file = None
    
    print(f"\n[{num}] {wallet['address']}")
    
    try:
        # Solve captcha
        print("  Solving captcha...", end=" ", flush=True)
        token = captcha_solver.solve(Config.BASE_URL, Config.TURNSTILE_SITEKEY)
        if not token:
            raise Exception("Captcha failed")
        
        success, error = client.submit_turnstile(token)
        if not success:
            raise Exception(f"Turnstile failed: {error}")
        
        # Login flow
        print("  Login...", end=" ", flush=True)
        message = client.get_login_message(wallet['address'])
        if not message:
            raise Exception("Get message failed")
        
        signature = sign_message(wallet['account'], message)
        if not client.verify_signature(message, signature):
            raise Exception("Signature invalid")
        print("OK")
        
        # Register
        print("  Register...", end=" ", flush=True)
        user_info = client.get_user(referral_code)
        if not user_info or user_info.get("RetCode") != 0:
            raise Exception("Registration failed")
        print("OK")
        
        user_id = user_info.get("UserID")
        invite_code = user_info.get("InviteCode", "")
        tier = user_info.get("Tier", "trial")
        points = user_info.get("Points", 0)
        
        # Generate random persona attributes
        persona_name = f"{random.choice(PERSONA_OPTIONS['names'])}_{random.randint(1000, 9999)}"
        business = random.choice(PERSONA_OPTIONS['business'])
        niche = random.choice(PERSONA_OPTIONS['niche'])
        tone = random.choice(PERSONA_OPTIONS['tone'])
        level = random.choice(PERSONA_OPTIONS['level'])
        
        # Create unique .txt file for this persona
        print("  Creating persona file...", end=" ", flush=True)
        persona_file = file_manager.create_file(persona_name, business, niche, tone, level)
        print(f"OK ({persona_file.name})")
        
        # Upload knowledge file to get knowledge base ID
        print("  Uploading knowledge...", end=" ", flush=True)
        knowledge_base_id = client.upload_knowledge_file(user_id, persona_file)
        print(f"OK (ID: {knowledge_base_id})" if knowledge_base_id else "SKIP (ID: 0)")
        
        # Create persona with knowledge base
        print("  Create persona...", end=" ", flush=True)
        persona_result = client.create_persona(user_id, persona_name, business, niche, tone, level, knowledge_base_id)
        persona_created = persona_result and persona_result.get("RetCode") == 0
        print("OK" if persona_created else "SKIP")
        
        # Delete the persona file after creation (cleanup)
        if persona_file:
            print("  Cleaning up file...", end=" ", flush=True)
            file_manager.delete_file(persona_file)
            print("OK")
            persona_file = None
        
        # Check-in
        print("  Check-in...", end=" ", flush=True)
        checkin_ok = client.check_in(user_id)
        print("OK" if checkin_ok else "SKIP")
        
        # Auto-add profile data (X, Discord, Telegram bindings)
        print("  Adding profile data...", end=" ", flush=True)
        
        # Generate random usernames for social media bindings
        random_username = f"@{persona_name.lower()}{random.randint(100, 999)}"
        
        # Update X/Twitter binding
        x_bind_success = client.update_user_bind(user_id, "x", random_username)
        
        # Update Discord binding
        discord_bind_success = client.update_user_bind(user_id, "discord", random_username)
        
        # Update Telegram binding
        telegram_bind_success = client.update_user_bind(user_id, "telegram", random_username)
        
        all_binds_success = x_bind_success and discord_bind_success and telegram_bind_success
        print("OK" if all_binds_success else "PARTIAL")
        
        # Claim profile reward
        print("  Claiming profile reward...", end=" ", flush=True)
        reward_result = client.claim_profile_reward(wallet['address'])
        reward_claimed = reward_result and reward_result.get("RetCode") == 0
        
        if reward_claimed:
            reward_points = reward_result.get("Points", 0)
            reward_granted = reward_result.get("RewardGranted", False)
            print(f"OK (+{reward_points} points)" if reward_granted else "SKIP")
        else:
            print("SKIP")
        
        
        # Save in wallets_full.json format
        account_data = {
            "address": wallet['address'],
            "private_key": wallet['private_key'],
            "user_id": user_id,
            "invite_code": invite_code,
            "tier": tier,
            "points": points,
            "persona_created": persona_created,
            "persona_name": persona_name,
            "persona_business": business,
            "persona_niche": niche,
            "persona_tone": tone,
            "persona_level": level,
            "knowledge_base_id": knowledge_base_id,
            "profile_bindings": {
                "x": random_username,
                "discord": random_username,
                "telegram": random_username
            },
            "profile_reward_claimed": reward_claimed,
            "profile_points": reward_points if reward_claimed else 0
        }
        
        AccountManager.save(account_data)
        print(f"  ✓ Saved | Invite: {invite_code}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    finally:
        # Ensure cleanup of persona file even on error
        if persona_file and persona_file.exists():
            file_manager.delete_file(persona_file)

def checkin_account(account: Dict, captcha_solver: TurnstileSolver, proxy: Optional[str] = None, num: int = 1) -> bool:
    """Perform check-in for an existing account"""
    proxy_config = ProxyManager.parse(proxy) if proxy else None
    client = HolmesAIClient(proxy_config)
    
    address = account.get("address", "Unknown")
    user_id = account.get("user_id")
    private_key = account.get("private_key")
    
    print(f"\n[{num}] {address}")
    
    if not user_id or not private_key:
        print("  ✗ Error: Missing user_id or private_key")
        return False
    
    try:
        # Recreate account from private key for signing
        wallet_account = Account.from_key(private_key)
        
        # Solve captcha
        print("  Solving captcha...", end=" ", flush=True)
        token = captcha_solver.solve(Config.BASE_URL, Config.TURNSTILE_SITEKEY)
        if not token:
            raise Exception("Captcha failed")
        
        success, error = client.submit_turnstile(token)
        if not success:
            raise Exception(f"Turnstile failed: {error}")
        
        # Login flow
        print("  Login...", end=" ", flush=True)
        message = client.get_login_message(address)
        if not message:
            raise Exception("Get message failed")
        
        signature = sign_message(wallet_account, message)
        if not client.verify_signature(message, signature):
            raise Exception("Signature invalid")
        print("OK")
        
        # Check-in
        print("  Check-in...", end=" ", flush=True)
        checkin_ok = client.check_in(user_id)
        if checkin_ok:
            print("OK")
            # Update last check-in time
            AccountManager.update(address, {
                "last_checkin": time.strftime('%Y-%m-%d %H:%M:%S')
            })
            print(f"  ✓ Check-in successful")
            return True
        else:
            print("FAILED")
            print(f"  ✗ Check-in failed")
            return False
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def format_time(seconds: int) -> str:
    """Format seconds into HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def auto_register():
    """Auto Register feature"""
    print("\n" + "="*50)
    print("  HolmesAI Auto-Register")
    print("="*50)
    
    # Get number of accounts
    while True:
        try:
            num_input = input("  How many accounts? ").strip()
            num_accounts = int(num_input)
            if num_accounts > 0:
                break
            print("  Please enter a positive number.")
        except ValueError:
            print("  Please enter a valid number.")
    
    # Get referral code from user
    default_ref = Config.REFERRAL_CODE
    ref_input = input(f"  Referral code [{default_ref}]: ").strip()
    referral_code = ref_input if ref_input else default_ref
    
    print(f"  Accounts: {num_accounts} | Referral: {referral_code}")
    
    use_proxy = input("  Use proxies? (y/n): ").strip().lower() == 'y'
    proxies = ProxyManager.load() if use_proxy else []
    print(f"  Proxies: {len(proxies)}")
    
    # Select captcha API key
    print(f"\n  Select Captcha API Key:")
    print(f"  [1] API Key 1: {Config.CAPTCHA_API_KEY_1[:20]}...")
    print(f"  [2] API Key 2: {Config.CAPTCHA_API_KEY_2[:20]}...")
    while True:
        key_choice = input("  Select (1 or 2): ").strip()
        if key_choice == '1':
            captcha_api_key = Config.CAPTCHA_API_KEY_1
            break
        elif key_choice == '2':
            captcha_api_key = Config.CAPTCHA_API_KEY_2
            break
        else:
            print("  Please enter 1 or 2.")
    
    captcha_solver = TurnstileSolver(captcha_api_key)
    file_manager = PersonaFileManager()
    success = 0
    
    try:
        for i in range(num_accounts):
            proxy = proxies[i % len(proxies)] if proxies else None
            if register_account(captcha_solver, referral_code, proxy, i + 1, file_manager):
                success += 1
            
            if i < num_accounts - 1:
                delay = 5 + random.random() * 3
                time.sleep(delay)
    finally:
        file_manager.cleanup_all()
    
    print("\n" + "="*50)
    print(f"  Done: {success}/{num_accounts} | Saved: {Config.DATA_FILE}")
    print("="*50 + "\n")

def auto_daily_checkin():
    """Auto Daily Check-in feature - runs in 24-hour loop"""
    print("\n" + "="*50)
    print("  HolmesAI Auto Daily Check-in")
    print("="*50)
    
    # Load accounts
    accounts = AccountManager.load()
    if not accounts:
        print("  No accounts found in wallets_full.json")
        print("  Please run Auto Register first.")
        input("\n  Press Enter to return to menu...")
        return
    
    print(f"  Accounts loaded: {len(accounts)}")
    
    use_proxy = input("  Use proxies? (y/n): ").strip().lower() == 'y'
    proxies = ProxyManager.load() if use_proxy else []
    print(f"  Proxies: {len(proxies)}")
    
    # Select captcha API key
    print(f"\n  Select Captcha API Key:")
    print(f"  [1] API Key 1: {Config.CAPTCHA_API_KEY_1[:20]}...")
    print(f"  [2] API Key 2: {Config.CAPTCHA_API_KEY_2[:20]}...")
    while True:
        key_choice = input("  Select (1 or 2): ").strip()
        if key_choice == '1':
            captcha_api_key = Config.CAPTCHA_API_KEY_1
            break
        elif key_choice == '2':
            captcha_api_key = Config.CAPTCHA_API_KEY_2
            break
        else:
            print("  Please enter 1 or 2.")
    
    print("\n  Starting auto check-in loop (24-hour cycle)...")
    print("  Press Ctrl+C to stop\n")
    
    captcha_solver = TurnstileSolver(captcha_api_key)
    cycle = 1
    
    try:
        while True:
            print("\n" + "="*50)
            print(f"  Cycle #{cycle} | {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*50)
            
            success = 0
            failed = 0
            
            for i, account in enumerate(accounts):
                proxy = proxies[i % len(proxies)] if proxies else None
                if checkin_account(account, captcha_solver, proxy, i + 1):
                    success += 1
                else:
                    failed += 1
                
                # Small delay between accounts
                if i < len(accounts) - 1:
                    delay = 3 + random.random() * 2
                    time.sleep(delay)
            
            print("\n" + "-"*50)
            print(f"  Cycle #{cycle} Complete")
            print(f"  Success: {success} | Failed: {failed}")
            print("-"*50)
            
            # Wait 24 hours (86400 seconds)
            wait_seconds = 24 * 60 * 60  # 24 hours
            print(f"\n  Next check-in in 24 hours...")
            print(f"  Next run at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + wait_seconds))}")
            print("  Press Ctrl+C to stop\n")
            
            # Countdown display (update every minute)
            remaining = wait_seconds
            while remaining > 0:
                print(f"\r  Time remaining: {format_time(remaining)}    ", end="", flush=True)
                sleep_time = min(60, remaining)  # Update every minute or less
                time.sleep(sleep_time)
                remaining -= sleep_time
            
            print()  # New line after countdown
            cycle += 1
            
    except KeyboardInterrupt:
        print("\n\n  Stopped by user.")
        print("="*50)

def show_menu():
    """Display main menu and get user choice"""
    # Import colorama for colored output
    try:
        from colorama import init, Fore, Style
        init()
        colors_available = True
    except:
        colors_available = False
    
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print()
    if colors_available:
        print(f"{Fore.YELLOW} __ __   ___   _      ___ ___    ___  _____  ____  ____ {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}|  |  | /   \\ | |    |   |   |  /  _]/ ___/ /    ||    |{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}|  |  ||     || |    | _   _ | /  [_(   \\_ |  o  | |  | {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}|  _  ||  O  || |___ |  \\_/  ||    _]\\__  ||     | |  | {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}|  |  ||     ||     ||   |   ||   [_ /  \\ ||  _  | |  | {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}|  |  ||     ||     ||   |   ||     |\\    ||  |  | |  | {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}|__|__| \\___/ |_____||___|___||_____| \\___||__|__||____|{Style.RESET_ALL}")
        print()
        print(f"{Fore.GREEN}               https://t.me/MDFKOfficial              {Style.RESET_ALL}")
    else:
        print(" __ __   ___   _      ___ ___    ___  _____  ____  ____ ")
        print("|  |  | /   \\ | |    |   |   |  /  _]/ ___/ /    ||    |")
        print("|  |  ||     || |    | _   _ | /  [_(   \\_ |  o  | |  | ")
        print("|  _  ||  O  || |___ |  \\_/  ||    _]\\__  ||     | |  | ")
        print("|  |  ||     ||     ||   |   ||   [_ /  \\ ||  _  | |  | ")
        print("|  |  ||     ||     ||   |   ||     |\\    ||  |  | |  | ")
        print("|__|__| \\___/ |_____||___|___||_____| \\___||__|__||____|")
        print()
        print("          https://t.me/MDFKOfficial         ")
    
    print()
    print("  [1] Auto Register")
    print("  [2] Auto Daily Check-in")
    print("  [0] Exit")
    print()
    
    while True:
        choice = input("  Select option: ").strip()
        if choice in ['0', '1', '2']:
            return choice
        print("  Invalid option. Please enter 0, 1, or 2.")

def main():
    import sys
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    while True:
        choice = show_menu()
        
        if choice == '0':
            print("\n  Goodbye!\n")
            break
        elif choice == '1':
            auto_register()
            input("\n  Press Enter to return to menu...")
        elif choice == '2':
            auto_daily_checkin()
            input("\n  Press Enter to return to menu...")

if __name__ == "__main__":
    main()
