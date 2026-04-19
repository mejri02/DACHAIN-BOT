# 🤖 DACHAIN-BOT

Automation bot for the [DaChain Inception](https://inception.dachain.io/?ref=DAC5189311) testnet platform. Supports multi-wallet automation, proxy rotation, staking, burning, crate opening, faucet claiming, and badge farming.

---

## ✨ Features

- 🪙 **Faucet Claiming** — Auto-claims testnet DAC with cooldown detection
- 📦 **Daily Crate Opening** — Opens up to 5 crates/day within the 1000 QE cap
- 🔥 **Burn for QE** — Burns DAC to earn QE points on-chain
- 📈 **Staking** — Stakes DAC into the QE pool contract
- 💸 **Fee Claiming** — Automatically claims pending staking rewards
- 🏅 **Badge Farming** — Claims rank and holding badges based on QE/DACC balance
- 📤 **Send Transactions** — Sends DAC to random addresses for activity farming
- 🔄 **Multi-Wallet** — Runs all accounts in sequence, cycle after cycle
- 🌐 **Proxy Support** — Rotates proxies per account from `proxy.txt`
- 🔃 **Auto Cycle** — Repeats every 8 hours automatically

---

## 📋 Requirements

- Python 3.8+
- pip packages:

```
web3
eth-account
requests
colorama
pytz
```

Install with:

```bash
pip install web3 eth-account requests colorama pytz
```

---

## 🚀 Getting Started

### 1. Create an Account

1. Visit [https://inception.dachain.io/?ref=DAC5189311](https://inception.dachain.io/?ref=DAC5189311)
2. Connect your EVM wallet (MetaMask or similar)
3. Sign in — your wallet address is your identity

### 2. Link Your Socials

Inside the DaChain Inception dashboard:
- Connect your **Discord** account for bonus tasks
- Connect your **Twitter/X** account if prompted
- Complete any available social tasks to earn extra QE

> Linking socials unlocks additional badge tasks that the bot can auto-claim.

### 3. Get Testnet DAC

Use the in-app faucet or let the bot claim it automatically on first run.

---

## ⚙️ Configuration

### `accounts.txt`

Add one private key per line:

```
0xYOUR_PRIVATE_KEY_1
0xYOUR_PRIVATE_KEY_2
```

> ⚠️ Never share your private keys. Use testnet wallets only.

### `proxy.txt` *(optional)*

Add one proxy per line in the format `http://user:pass@host:port` or `http://host:port`:

```
http://127.0.0.1:8080
http://user:pass@proxy.example.com:3128
```

Leave the file empty or skip if running without proxy.

---

## ▶️ Usage

```bash
python bot.py
```

On startup:
1. Choose proxy mode (1 = with proxy, 2 = without)
2. Enter number of send transactions per account (0 to skip)
3. Enter DAC amount to stake per account (0 to skip)
4. Enter DAC amount to burn for QE per account (0 to skip)

The bot will then loop through all accounts and repeat every **8 hours**.

---

## 📊 Runtime Stats

After each cycle the bot prints a summary:

```
Crates | QE Earned | Stakes | Burns | Txs Sent | Fees Claimed | Faucet Claims
```

---

## 🔗 Links

| Resource | Link |
|----------|------|
| 🌐 DaChain Inception | [inception.dachain.io](https://inception.dachain.io/?ref=DAC5189311) |
| 💬 Telegram Community | [t.me/AirDropXDevs](https://t.me/AirDropXDevs) |
| 🐙 GitHub | [github.com/mejri02](https://github.com/mejri02) |

---

## ⚠️ Disclaimer

This bot is built for **testnet use only**. Use at your own risk. The author is not responsible for any loss of funds. Always use dedicated wallets for automation.

---

<p align="center">Made by <a href="https://github.com/mejri02">mejri02</a> • <a href="https://t.me/AirDropXDevs">AirDropXDevs</a></p>
