import os
import sys
import time
import random
import json
import warnings
import requests
from eth_account import Account
from web3 import Web3
from datetime import datetime, timedelta
import pytz
from colorama import init, Fore, Style
from itertools import cycle

warnings.filterwarnings('ignore')
init(autoreset=True)

Account.enable_unaudited_hdwallet_features()

CONFIG = {
    "RPC_URL": "https://rpctest.dachain.tech",
    "CHAIN_ID": 21894,
    "QE_POOL_ADDRESS": "0x3691A78bE270dB1f3b1a86177A8f23F89A8Cef24",
    "RANK_BADGE_ADDRESS": "0xB36ab4c2Bd6aCfC36e9D6c53F39F4301901Bd647",
    "REFERRAL_CODE": "DAC5189311",
    "MIN_DACC_FOR_HOLDING": [5, 10, 25, 50, 75, 100],
    "MIN_QE_FOR_RANK": [0, 1000, 2000, 5000, 10000, 25000, 50000, 100000, 200000, 300000, 400000, 500000, 750000],
    "RANK_NAMES": ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster", "Legend", "Mythic", "Hero", "Champion", "Titan", "Godly"],
    "DAILY_CRATE_LIMIT": 5,
    "DAILY_QE_CAP": 1000,
    "FAUCET_COOLDOWN_SECONDS": 8 * 3600,
    "STAKE_AMOUNT": 0.1,
    "BURN_AMOUNT": 0.05,
    "SEND_AMOUNT": 0.0001,
    "SWAP_SLIPPAGE": 0.5,
    "USER_AGENTS": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ],
    "QE_POOL_ABI": [
        {"type": "function", "name": "burnForQE", "stateMutability": "payable", "inputs": [], "outputs": []},
        {"type": "function", "name": "stake", "stateMutability": "payable", "inputs": [], "outputs": []},
        {"type": "function", "name": "unstake", "stateMutability": "nonpayable", "inputs": [{"name": "amount", "type": "uint256"}], "outputs": []},
        {"type": "function", "name": "claimFees", "stateMutability": "nonpayable", "inputs": [], "outputs": []},
        {"type": "function", "name": "lps", "stateMutability": "view", "inputs": [{"name": "user", "type": "address"}], "outputs": [{"name": "staked", "type": "uint256"}, {"name": "rewardDebt", "type": "uint256"}]},
        {"type": "function", "name": "pendingFees", "stateMutability": "view", "inputs": [{"name": "user", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}]}
    ],
    "TOKEN_ABI": [
        {"type": "function", "name": "approve", "stateMutability": "nonpayable", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}]},
        {"type": "function", "name": "allowance", "stateMutability": "view", "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}]},
        {"type": "function", "name": "balanceOf", "stateMutability": "view", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}]}
    ],
    "SWAP_ROUTER": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "DAC_TOKEN": "0x3691A78bE270dB1f3b1a86177A8f23F89A8Cef24"
}

class State:
    def __init__(self):
        self.w3 = None
        self.account = None
        self.session = None
        self.csrf_token = None
        self.profile = None
        self.proxy_pool = None
        self.use_proxy = False
        self.blockchain = None
        self.dac_client = None
        self.stats = {
            "faucet_claims": 0,
            "transactions_sent": 0,
            "badges_claimed": [],
            "crates_opened": 0,
            "qe_earned": 0,
            "stakes": 0,
            "burns": 0,
            "swaps": 0,
            "fees_claimed": 0,
            "unstakes": 0,
            "current_rank": 0,
            "current_holding_badge": 0
        }

state = State()

def get_wib_time():
    wib = pytz.timezone('Asia/Jakarta')
    return datetime.now(wib).strftime('%H:%M:%S')

def log(message, level="INFO"):
    colors = {
        "INFO": Fore.CYAN,
        "SUCCESS": Fore.GREEN,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW,
        "CYCLE": Fore.MAGENTA
    }
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "CYCLE": "🔄"
    }
    time_str = get_wib_time()
    print(f"{colors.get(level, Fore.CYAN)}[{time_str}] {symbols.get(level, '')} {message}{Style.RESET_ALL}")

def random_delay(min_sec=1, max_sec=5):
    delay = random.randint(min_sec, max_sec)
    time.sleep(delay)

def jitter():
    time.sleep(random.uniform(0.3, 1.2))

def load_file(filename):
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return lines
    except FileNotFoundError:
        return []

def get_random_user_agent():
    return random.choice(CONFIG["USER_AGENTS"])

def print_banner():
    os.system('clear')
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║                         DACHAIN BOT v1.0                                 ║
║                         By: Mejri02                                       ║
╚══════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def countdown(seconds):
    for i in range(seconds, 0, -1):
        hours = i // 3600
        minutes = (i % 3600) // 60
        secs = i % 60
        print(f"\r⏰ Next cycle: {hours:02d}:{minutes:02d}:{secs:02d} ", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 60 + "\r", end="", flush=True)

def show_menu():
    print(f"{Fore.CYAN}══════════════════════════════════════════════════════════════════════{Style.RESET_ALL}")
    print(f"{Fore.GREEN}1. Run with proxy{Style.RESET_ALL}")
    print(f"{Fore.GREEN}2. Run without proxy{Style.RESET_ALL}")
    print(f"{Fore.CYAN}══════════════════════════════════════════════════════════════════════{Style.RESET_ALL}")
    while True:
        try:
            choice = input(f"{Fore.YELLOW}Enter your choice (1/2): {Style.RESET_ALL}").strip()
            if choice in ['1', '2']:
                return choice
            else:
                print(f"{Fore.RED}Invalid choice! Please enter 1 or 2.{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Program terminated.{Style.RESET_ALL}")
            exit(0)

class APIClient:
    def __init__(self):
        self.base_url = "https://inception.dachain.io"
        self.session = None
        self.csrf_token = None
        self.proxy = None

    def init_session(self, proxy=None):
        self.session = requests.Session()
        user_agent = get_random_user_agent()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        if proxy:
            self.proxy = proxy
            self.session.proxies = {'http': proxy, 'https': proxy}

    def get_csrf_token(self):
        try:
            response = self.session.get(f"{self.base_url}/csrf/", timeout=30)
            cookies = response.cookies.get_dict()
            if 'csrftoken' in cookies:
                self.csrf_token = cookies['csrftoken']
                return self.csrf_token
        except Exception:
            pass
        return None

    def request(self, method, endpoint, data=None, retry=2):
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Referer': self.base_url
        }
        if self.csrf_token:
            headers['X-CSRFToken'] = self.csrf_token
        
        for attempt in range(retry + 1):
            try:
                if method == "GET":
                    response = self.session.get(url, headers=headers, timeout=45)
                else:
                    response = self.session.post(url, headers=headers, json=data, timeout=45)
                
                if response.status_code == 403 and "CSRF" in response.text and self.csrf_token:
                    self.get_csrf_token()
                    if self.csrf_token:
                        headers['X-CSRFToken'] = self.csrf_token
                        if method == "GET":
                            response = self.session.get(url, headers=headers, timeout=45)
                        else:
                            response = self.session.post(url, headers=headers, json=data, timeout=45)
                
                return response.json()
            except requests.exceptions.Timeout:
                if attempt < retry:
                    log(f"Request timeout, retrying ({attempt+1}/{retry})...", "WARNING")
                    time.sleep(3)
                    continue
                raise Exception("Request timeout after retries")
            except Exception as e:
                if attempt < retry:
                    log(f"Request failed, retrying ({attempt+1}/{retry})...", "WARNING")
                    time.sleep(3)
                    continue
                raise Exception(f"Request failed: {e}")
        
        raise Exception("Request failed")

    def get(self, endpoint):
        return self.request("GET", endpoint)

    def post(self, endpoint, data=None):
        return self.request("POST", endpoint, data)

class BlockchainClient:
    def __init__(self, private_key):
        self.w3 = Web3(Web3.HTTPProvider(CONFIG["RPC_URL"], request_kwargs={'timeout': 30}))
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.qe_pool = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONFIG["QE_POOL_ADDRESS"]),
            abi=CONFIG["QE_POOL_ABI"]
        )
        self.token = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONFIG["DAC_TOKEN"]),
            abi=CONFIG["TOKEN_ABI"]
        )

    def get_nonce(self):
        return self.w3.eth.get_transaction_count(self.address, 'pending')

    def get_balance(self):
        try:
            balance_wei = self.w3.eth.get_balance(self.address)
            return self.w3.from_wei(balance_wei, 'ether')
        except:
            return 0

    def get_token_balance(self):
        try:
            balance = self.token.functions.balanceOf(self.address).call()
            return self.w3.from_wei(balance, 'ether')
        except:
            return 0

    def get_allowance(self, spender):
        try:
            allowance = self.token.functions.allowance(self.address, spender).call()
            return self.w3.from_wei(allowance, 'ether')
        except:
            return 0

    def approve_token(self, spender, amount_eth):
        amount_wei = self.w3.to_wei(amount_eth, 'ether')
        nonce = self.get_nonce()
        tx = self.token.functions.approve(spender, amount_wei).build_transaction({
            'from': self.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CONFIG["CHAIN_ID"]
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def send_transaction(self, to, amount_eth):
        amount_wei = self.w3.to_wei(amount_eth, 'ether')
        nonce = self.get_nonce()
        tx = {
            'nonce': nonce,
            'to': to,
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': CONFIG["CHAIN_ID"]
        }
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def stake(self, amount_eth):
        amount_wei = self.w3.to_wei(amount_eth, 'ether')
        nonce = self.get_nonce()
        tx = self.qe_pool.functions.stake().build_transaction({
            'from': self.address,
            'value': amount_wei,
            'gas': 150000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CONFIG["CHAIN_ID"]
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def unstake(self, amount_eth):
        amount_wei = self.w3.to_wei(amount_eth, 'ether')
        nonce = self.get_nonce()
        tx = self.qe_pool.functions.unstake(amount_wei).build_transaction({
            'from': self.address,
            'gas': 150000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CONFIG["CHAIN_ID"]
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def burn_for_qe(self, amount_eth):
        amount_wei = self.w3.to_wei(amount_eth, 'ether')
        nonce = self.get_nonce()
        tx = self.qe_pool.functions.burnForQE().build_transaction({
            'from': self.address,
            'value': amount_wei,
            'gas': 150000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CONFIG["CHAIN_ID"]
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def claim_fees(self):
        nonce = self.get_nonce()
        tx = self.qe_pool.functions.claimFees().build_transaction({
            'from': self.address,
            'gas': 150000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
            'chainId': CONFIG["CHAIN_ID"]
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def get_staked_amount(self):
        try:
            result = self.qe_pool.functions.lps(self.address).call()
            return self.w3.from_wei(result[0], 'ether')
        except:
            return 0

    def get_pending_fees(self):
        try:
            fees = self.qe_pool.functions.pendingFees(self.address).call()
            return self.w3.from_wei(fees, 'ether')
        except:
            return 0

class DACClient:
    def __init__(self, api_client):
        self.api = api_client
        self.profile = {}

    def login(self, wallet_address):
        if not self.api.csrf_token:
            self.api.get_csrf_token()
        try:
            result = self.api.post('/api/auth/wallet/', {
                'wallet_address': wallet_address.lower()
            })
            if result.get('success'):
                log(f"Logged in as {wallet_address[:10]}...", "SUCCESS")
                self.get_profile()
                return True
            else:
                self.profile = {}
                return True
        except Exception as e:
            log(f"Login failed: {e}", "ERROR")
            self.profile = {}
            return False

    def get_profile(self):
        try:
            self.profile = self.api.get('/api/inception/profile/')
            return self.profile
        except Exception as e:
            self.profile = {}
            return {}

    def visit_faucet(self):
        try:
            result = self.api.post('/api/inception/visit/faucet/')
            if result and result.get('success'):
                log(f"Faucet visit tracked", "INFO")
                return True
        except Exception:
            pass
        return False

    def get_faucet_history(self):
        try:
            result = self.api.get('/api/inception/faucet-history/')
            if result and result.get('history'):
                last_claim = result['history'][0] if result['history'] else None
                if last_claim:
                    return last_claim
            return None
        except Exception:
            return None

    def claim_faucet(self):
        last_claim = self.get_faucet_history()
        if last_claim:
            try:
                last_claim_time = datetime.fromisoformat(last_claim.get('created_at', '').replace('Z', '+00:00'))
                time_since_claim = (datetime.now(pytz.UTC) - last_claim_time).total_seconds()
                if time_since_claim < CONFIG["FAUCET_COOLDOWN_SECONDS"]:
                    hours_left = (CONFIG["FAUCET_COOLDOWN_SECONDS"] - time_since_claim) / 3600
                    log(f"Faucet already claimed - {hours_left:.1f} hours until next claim", "WARNING")
                    return None
            except Exception:
                pass
        
        try:
            self.visit_faucet()
            time.sleep(1)
            result = self.api.post('/api/inception/faucet/')
            if result and result.get('success'):
                amount = result.get('amount', 'Unknown')
                log(f"Faucet claimed! +{amount} DAC", "SUCCESS")
                state.stats['faucet_claims'] += 1
                return result
            elif result and result.get('error'):
                error_msg = result.get('error', '')
                if 'cooldown' in error_msg.lower():
                    log(f"Faucet on cooldown (8 hours)", "WARNING")
                else:
                    log(f"Faucet error: {error_msg}", "WARNING")
        except Exception as e:
            if '429' in str(e):
                log(f"Faucet rate limited - on cooldown", "WARNING")
            else:
                log(f"Faucet claim failed: {e}", "WARNING")
        return None

    def get_crate_history(self):
        try:
            return self.api.get('/api/inception/crate/history/')
        except:
            return {'history': [], 'opens_today': 0, 'qe_today': 0}

    def open_crate(self):
        try:
            result = self.api.post('/api/inception/crate/open/')
            if result.get('success'):
                reward = result.get('reward_label', 'Unknown')
                qe_earned = result.get('qe_earned', 0)
                log(f"Crate opened! Reward: {reward} (+{qe_earned} QE)", "SUCCESS")
                state.stats['crates_opened'] += 1
                state.stats['qe_earned'] += qe_earned
                return result
        except Exception as e:
            log(f"Failed to open crate: {e}", "WARNING")
        return None

    def claim_badge(self, badge_key):
        try:
            result = self.api.post('/api/inception/task/', {'task': badge_key})
            if result.get('success'):
                log(f"Badge '{badge_key}' claimed!", "SUCCESS")
                if badge_key not in state.stats['badges_claimed']:
                    state.stats['badges_claimed'].append(badge_key)
                return result
        except Exception as e:
            if 'already' in str(e).lower() or 'claimed' in str(e).lower():
                pass
            else:
                log(f"Failed to claim badge: {e}", "WARNING")
        return None

    def sync_chain(self):
        try:
            self.api.post('/api/inception/sync/')
            self.get_profile()
        except Exception:
            pass

    def apply_referral(self, wallet_address):
        try:
            result = self.api.post('/api/inception/referral/', {
                'code': CONFIG["REFERRAL_CODE"],
                'wallet': wallet_address
            })
            if result.get('success'):
                log(f"Referral code applied!", "SUCCESS")
                return True
        except Exception:
            pass
        return False

    def get_available_badges(self):
        try:
            result = self.api.get('/api/inception/tasks/')
            return result.get('available', [])
        except:
            return []

    def get_network_info(self):
        try:
            result = self.api.get('/api/inception/network/')
            return result
        except Exception:
            return {}

    def get_discord_status(self):
        try:
            result = self.api.get('/api/inception/discord/status/')
            if result.get('is_connected'):
                log(f"Discord connected: {result.get('username', 'Unknown')}", "INFO")
            return result
        except Exception:
            return {}

    def get_leaderboard(self, limit=10):
        try:
            result = self.api.get(f'/api/inception/leaderboard/?limit={limit}')
            entries = result.get('entries', [])
            if entries:
                log(f"Leaderboard fetched - Top {len(entries)} users", "INFO")
                for idx, entry in enumerate(entries[:5], 1):
                    log(f"  #{idx}: {entry.get('username', 'Unknown')} - {entry.get('qe_balance', 0)} QE", "INFO")
            return entries
        except Exception:
            return []

    def get_user_rank_position(self):
        try:
            leaderboard = self.get_leaderboard(100)
            if not leaderboard or not self.profile:
                return None
            username = self.profile.get('username')
            for idx, entry in enumerate(leaderboard, 1):
                if entry.get('username') == username:
                    log(f"Your rank: #{idx} with {entry.get('qe_balance', 0)} QE", "SUCCESS")
                    return idx
        except Exception:
            pass
        return None

def check_and_claim_rank_badge(current_qe):
    if isinstance(current_qe, str):
        current_qe = float(current_qe) if current_qe else 0
    rank = 0
    for i, threshold in enumerate(CONFIG["MIN_QE_FOR_RANK"]):
        if current_qe >= threshold:
            rank = i
    if rank > state.stats['current_rank']:
        badge_key = f"rank_{CONFIG['RANK_NAMES'][rank].lower()}"
        result = state.dac_client.claim_badge(badge_key)
        if result:
            log(f"Achieved {CONFIG['RANK_NAMES'][rank]} rank! ({current_qe} QE)", "SUCCESS")
            state.stats['current_rank'] = rank
    return rank

def check_and_claim_holding_badge(current_dacc):
    if isinstance(current_dacc, str):
        current_dacc = float(current_dacc) if current_dacc else 0
    earned = []
    for threshold in CONFIG["MIN_DACC_FOR_HOLDING"]:
        if current_dacc >= threshold and threshold > state.stats['current_holding_badge']:
            badge_key = f"holding_{threshold}"
            result = state.dac_client.claim_badge(badge_key)
            if result:
                log(f"Holding badge earned: {threshold} DACC", "SUCCESS")
                earned.append(threshold)
    if earned:
        state.stats['current_holding_badge'] = max(earned + [state.stats['current_holding_badge']])
    return earned

def open_daily_crates():
    history = state.dac_client.get_crate_history()
    opens_today = history.get('opens_today', 0)
    qe_today = history.get('qe_today', 0)
    
    remaining_opens = CONFIG["DAILY_CRATE_LIMIT"] - opens_today
    remaining_qe = CONFIG["DAILY_QE_CAP"] - qe_today
    
    if remaining_opens <= 0:
        log(f"Daily crate limit reached ({opens_today}/{CONFIG['DAILY_CRATE_LIMIT']})", "WARNING")
        return
    
    log(f"Crates available: {remaining_opens} (QE cap: {remaining_qe} left)", "INFO")
    
    for i in range(remaining_opens):
        if qe_today >= CONFIG["DAILY_QE_CAP"]:
            log(f"Daily QE cap reached ({qe_today}/{CONFIG['DAILY_QE_CAP']})", "WARNING")
            break
        
        result = state.dac_client.open_crate()
        if result:
            qe_today += result.get('qe_earned', 0)
            random_delay(2, 4)
        else:
            break

def claim_all_available_badges():
    badges = state.dac_client.get_available_badges()
    if not badges:
        return
    
    for badge in badges:
        if badge not in state.stats['badges_claimed']:
            state.dac_client.claim_badge(badge)
            jitter()

def claim_pending_staking_fees():
    pending = state.blockchain.get_pending_fees()
    if pending > 0:
        log(f"Pending fees: {pending:.6f} DAC", "INFO")
        if pending > 0.001:
            try:
                tx_hash = state.blockchain.claim_fees()
                log(f"Fees claimed! Tx: https://exptest.dachain.tech/tx/{tx_hash}", "SUCCESS")
                state.stats['fees_claimed'] += 1
                return True
            except Exception as e:
                log(f"Failed to claim fees: {e}", "ERROR")
    return False

def check_and_claim_all_rewards():
    qe_balance = state.dac_client.profile.get('qe_balance', 0) if state.dac_client.profile else 0
    dacc_balance = state.dac_client.profile.get('dacc_balance', 0) if state.dac_client.profile else 0
    
    if isinstance(qe_balance, str):
        qe_balance = float(qe_balance) if qe_balance else 0
    if isinstance(dacc_balance, str):
        dacc_balance = float(dacc_balance) if dacc_balance else 0
    
    check_and_claim_rank_badge(qe_balance)
    check_and_claim_holding_badge(dacc_balance)
    claim_all_available_badges()
    claim_pending_staking_fees()
    open_daily_crates()

def perform_swap_if_needed():
    dac_balance = state.blockchain.get_token_balance()
    if dac_balance < 0.5:
        return
    
    log(f"DAC balance: {dac_balance:.6f}", "INFO")
    
    allowance = state.blockchain.get_allowance(CONFIG["SWAP_ROUTER"])
    if allowance < dac_balance:
        log(f"Approving swap router...", "INFO")
        try:
            tx_hash = state.blockchain.approve_token(CONFIG["SWAP_ROUTER"], dac_balance)
            log(f"Approval sent: https://exptest.dachain.tech/tx/{tx_hash}", "INFO")
            time.sleep(3)
        except Exception as e:
            log(f"Approval failed: {e}", "ERROR")

def sync_and_update_profile():
    state.dac_client.sync_chain()
    state.dac_client.get_profile()
    if state.dac_client.profile:
        qe = state.dac_client.profile.get('qe_balance', 0)
        if isinstance(qe, str):
            qe = float(qe) if qe else 0
        log(f"Profile synced - QE: {qe}", "INFO")

def process_account(pk, proxy=None):
    try:
        state.blockchain = BlockchainClient(pk)
        wallet_address = state.blockchain.address
        log(f"Wallet: {wallet_address}", "INFO")
        
        api_client = APIClient()
        if proxy:
            api_client.init_session(proxy)
        else:
            api_client.init_session()
        
        state.dac_client = DACClient(api_client)
        
        api_client.get_csrf_token()
        
        if not state.dac_client.login(wallet_address):
            log(f"Login failed", "ERROR")
            return False
        
        state.dac_client.apply_referral(wallet_address)
        
        if state.dac_client.profile:
            qe_bal = state.dac_client.profile.get('qe_balance', 0)
            dacc_bal = state.dac_client.profile.get('dacc_balance', 0)
            if isinstance(qe_bal, str):
                qe_bal = float(qe_bal) if qe_bal else 0
            if isinstance(dacc_bal, str):
                dacc_bal = float(dacc_bal) if dacc_bal else 0
            log(f"Username: {state.dac_client.profile.get('username', 'Unknown')}", "INFO")
            log(f"QE Balance: {qe_bal}", "INFO")
            log(f"DACC Balance: {dacc_bal}", "INFO")
        
        state.dac_client.claim_faucet()
        
        state.dac_client.get_network_info()
        state.dac_client.get_discord_status()
        state.dac_client.get_leaderboard(10)
        state.dac_client.get_user_rank_position()
        
        if state.blockchain.w3.is_connected():
            balance = state.blockchain.get_balance()
            log(f"Chain balance: {balance:.6f} DAC", "INFO")
            
            if balance > 0.01:
                check_and_claim_all_rewards()
                
                if CONFIG["STAKE_AMOUNT"] > 0 and balance >= CONFIG["STAKE_AMOUNT"]:
                    try:
                        tx_hash = state.blockchain.stake(CONFIG["STAKE_AMOUNT"])
                        log(f"Staked {CONFIG['STAKE_AMOUNT']} DAC! Tx: https://exptest.dachain.tech/tx/{tx_hash}", "SUCCESS")
                        state.stats['stakes'] += 1
                        time.sleep(2)
                    except Exception as e:
                        log(f"Stake failed: {e}", "ERROR")
                
                if CONFIG["BURN_AMOUNT"] > 0 and balance >= CONFIG["BURN_AMOUNT"]:
                    try:
                        tx_hash = state.blockchain.burn_for_qe(CONFIG["BURN_AMOUNT"])
                        log(f"Burned {CONFIG['BURN_AMOUNT']} DAC for QE! Tx: https://exptest.dachain.tech/tx/{tx_hash}", "SUCCESS")
                        state.stats['burns'] += 1
                        time.sleep(2)
                    except Exception as e:
                        log(f"Burn failed: {e}", "ERROR")
                
                for i in range(CONFIG.get("SEND_COUNT", 0)):
                    random_address = Account.create().address
                    try:
                        tx_hash = state.blockchain.send_transaction(random_address, CONFIG["SEND_AMOUNT"])
                        log(f"Sent {CONFIG['SEND_AMOUNT']} DAC [{i+1}/{CONFIG.get('SEND_COUNT', 0)}]! Tx: https://exptest.dachain.tech/tx/{tx_hash}", "SUCCESS")
                        state.stats['transactions_sent'] += 1
                        time.sleep(1)
                    except Exception as e:
                        log(f"Send failed: {e}", "ERROR")
                
                perform_swap_if_needed()
        
        sync_and_update_profile()
        
        return True
        
    except Exception as e:
        log(f"Account error: {e}", "ERROR")
        return False

def run():
    print_banner()
    
    choice = show_menu()
    
    try:
        send_input = input(f"{Fore.GREEN}How many send transactions per account? (0 to skip): {Style.RESET_ALL}")
        CONFIG["SEND_COUNT"] = int(float(send_input)) if int(float(send_input)) > 0 else 0
    except ValueError:
        CONFIG["SEND_COUNT"] = 0
        
    try:
        stake_input = input(f"{Fore.GREEN}How much DAC to STAKE per account? (0 to skip): {Style.RESET_ALL}")
        CONFIG["STAKE_AMOUNT"] = float(stake_input) if float(stake_input) > 0 else 0
    except ValueError:
        CONFIG["STAKE_AMOUNT"] = 0

    try:
        burn_input = input(f"{Fore.GREEN}How much DAC to BURN for QE per account? (0 to skip): {Style.RESET_ALL}")
        CONFIG["BURN_AMOUNT"] = float(burn_input) if float(burn_input) > 0 else 0
    except ValueError:
        CONFIG["BURN_AMOUNT"] = 0

    if choice == '1':
        log("Running with proxy", "INFO")
        proxies_list = load_file('proxy.txt')
        proxy_pool = cycle(proxies_list) if proxies_list else None
        if not proxies_list:
            log("No proxies found, running without proxy", "WARNING")
            proxy_pool = None
    else:
        log("Running without proxy", "INFO")
        proxy_pool = None
        
    private_keys = load_file('accounts.txt')
    if not private_keys:
        log("No private keys found in accounts.txt", "ERROR")
        return
        
    log(f"Loaded {len(private_keys)} accounts", "INFO")
    
    cycle_count = 1
    while True:
        log(f"Cycle #{cycle_count} Started", "CYCLE")
        
        success_count = 0
        
        for index, pk in enumerate(private_keys, start=1):
            log(f"Account #{index}/{len(private_keys)}", "INFO")
            
            proxy = None
            if proxy_pool:
                proxy = next(proxy_pool)
                log(f"Proxy: {proxy}", "INFO")
            
            if process_account(pk, proxy):
                success_count += 1
            
            if index < len(private_keys):
                random_delay(3, 7)
        
        log(f"Cycle #{cycle_count} Complete | Success: {success_count}/{len(private_keys)}", "CYCLE")
        log(f"Stats - Crates: {state.stats['crates_opened']} | QE: {state.stats['qe_earned']} | Stakes: {state.stats['stakes']} | Burns: {state.stats['burns']} | Txs: {state.stats['transactions_sent']} | Fees: {state.stats['fees_claimed']} | Faucet: {state.stats['faucet_claims']}", "INFO")
        
        cycle_count += 1
        countdown(28800)

if __name__ == "__main__":
    run()
