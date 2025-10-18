# bot.py
import os
import sys
import time
import base64
import logging
import requests
import random
from datetime import datetime, timezone
from dotenv import load_dotenv

# Ensure console can print emojis on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    # older Pythons or environments may not support reconfigure; ignore
    pass

# === optional blockchain libs (only used in real mode) ===
try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.transaction import VersionedTransaction
    from solders.message import to_bytes_versioned
    from solders.presigner import Presigner
    from solana.rpc.api import Client
    from base58 import b58decode
except Exception:
    # In DRY_RUN this is fine. We'll check later for real mode.
    pass

# -----------------------------
# Load .env
# -----------------------------
load_dotenv()

RPC_URL = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
PUBLIC_KEY = os.getenv("PUBLIC_KEY", "").strip()
WALLET_SECRET_B58 = os.getenv("WALLET_SECRET_B58", "").strip()
CHAR_MINT = os.getenv("CHAR_MINT", "charyAhpBstVjf5VnszNiY8UUVDbvA167dQJqpBY2hw")
INPUT_MINT = os.getenv("INPUT_MINT", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB")
MICRO_BUY_USD = float(os.getenv("MICRO_BUY_USD", "0.01"))
FALLBACK_BUY_USD = float(os.getenv("FALLBACK_BUY_USD", "0.10"))
SLIPPAGE_BPS = int(os.getenv("SLIPPAGE_BPS", "500"))
SCHEDULE_HOURS = float(os.getenv("SCHEDULE_HOURS", "6"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")

# -----------------------------
# Logging (file + console)
# -----------------------------
os.makedirs("logs", exist_ok=True)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler("logs/bot.log", mode="a", encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
root_logger.addHandler(fh)

# Stream handler (force stdout so encoding change applies)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
root_logger.addHandler(sh)

logger = logging.getLogger("charcoin-bot")

# Jupiter Lite APIs
QUOTE_API = "https://lite-api.jup.ag/swap/v1/quote"
SWAP_API = "https://lite-api.jup.ag/swap/v1/swap"
headers = {"Content-Type": "application/json"}

# -----------------------------
# Helpers
# -----------------------------
def get_usdt_amount(usd: float) -> int:
    """Convert USD -> USDT smallest unit (6 decimals)."""
    return int(usd * 1_000_000)

def get_quote(amount_usdt: int):
    params = {
        "inputMint": INPUT_MINT,
        "outputMint": CHAR_MINT,
        "amount": str(amount_usdt),
        "slippageBps": str(SLIPPAGE_BPS),
        "onlyDirectRoutes": "true",
        "restrictIntermediateTokens": "true",
    }
    r = requests.get(QUOTE_API, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()

def notify_webhook(msg: str):
    if not WEBHOOK_URL:
        return
    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=8)
    except Exception as e:
        logger.debug(f"Webhook send failed (ignored): {e}")

# -----------------------------
# Execute swap (real or dry-run)
# -----------------------------
def execute_swap(quote):
    swap_req = {
        "quoteResponse": quote,
        "userPublicKey": PUBLIC_KEY,
        "dynamicComputeUnitLimit": True,
        "dynamicSlippage": True,
        "wrapAndUnwrapSol": True,
    }

    if DRY_RUN:
        fake_sig = f"TEST_TX_{int(time.time())}"
        logger.info(f"🧪 [DRY-RUN] Simulated Swap: https://solscan.io/tx/{fake_sig}")
        notify_webhook(f"🧪 [DRY-RUN] Simulated Swap Triggered ✅ Tx: {fake_sig}")
        return fake_sig

    # Real mode: make swap request, sign and send transaction
    r = requests.post(SWAP_API, json=swap_req, headers=headers, timeout=20)
    r.raise_for_status()
    tx_b64 = r.json().get("swapTransaction")
    if not tx_b64:
        raise RuntimeError("Swap transaction missing in swap response")

    # ensure we have required libs and wallet
    try:
        client = Client(RPC_URL)
        kp = Keypair.from_bytes(b58decode(WALLET_SECRET_B58))
    except Exception as e:
        raise RuntimeError(f"Failed to prepare wallet/client for real swap: {e}")

    raw_tx = base64.b64decode(tx_b64)
    tx = VersionedTransaction.from_bytes(raw_tx)
    msg_bytes = to_bytes_versioned(tx.message)
    sig = kp.sign_message(msg_bytes)
    signed_tx = VersionedTransaction(tx.message, [Presigner(kp.pubkey(), sig)])
    resp = client.send_raw_transaction(bytes(signed_tx))
    sig_str = getattr(resp, "value", None) or resp.get("result")
    if not sig_str:
        raise RuntimeError(f"Transaction send failed: {resp}")
    logger.info(f"✅ Swap successful: https://solscan.io/tx/{sig_str}")
    notify_webhook(f"✅ Successful Swap! Tx: https://solscan.io/tx/{sig_str}")
    return sig_str

# -----------------------------
# Wallet / environment checks
# -----------------------------
def ensure_wallet():
    if DRY_RUN:
        logger.info("🧪 Running in DRY_RUN mode — no real wallet required.")
        # show a fake balance for testing display
        fake_balance = 0.0
        logger.info(f"💰 Wallet (DRY-RUN) balance: {fake_balance:.6f} SOL")
        return

    # Real mode: ensure keys present and valid
    if not PUBLIC_KEY:
        raise SystemExit("❌ PUBLIC_KEY missing in .env (required in real mode).")
    if not WALLET_SECRET_B58:
        raise SystemExit("❌ WALLET_SECRET_B58 missing in .env (required in real mode).")

    # Validate public key format (Base58) using solders Pubkey if available
    try:
        pk = Pubkey.from_string(PUBLIC_KEY)
    except Exception as e:
        raise SystemExit(f"❌ PUBLIC_KEY invalid Base58 Solana address: {e}")

    # Check RPC connectivity & balance
    try:
        client = Client(RPC_URL)
        bal_resp = client.get_balance(pk)
        # client.get_balance returns dict-like depending on lib version
        sol_lamports = getattr(bal_resp, "value", None) or bal_resp.get("result", {}).get("value")
        if sol_lamports is None:
            # try older style
            sol_lamports = bal_resp.get("result", {}).get("value")
        if sol_lamports is None:
            logger.warning("⚠️ Could not read balance from RPC response; continuing.")
            bal = 0.0
        else:
            bal = float(sol_lamports) / 1_000_000_000
        logger.info(f"💰 Wallet {PUBLIC_KEY} balance: {bal:.6f} SOL")
    except Exception as e:
        logger.warning(f"⚠️ RPC balance check failed: {e}")

# -----------------------------
# Main bot loop
# -----------------------------
def run_bot():
    logger.info("🚀 CharCoin Auto-Swap Bot Started")
    ensure_wallet()
    retry_delay_sec = 5

    while True:
        try:
            logger.info(f"🕐 Scheduled Buy Triggered: ${MICRO_BUY_USD:.2f} USDT → CHAR")
            amt = get_usdt_amount(MICRO_BUY_USD)
            quote = get_quote(amt)
            execute_swap(quote)
            retry_delay_sec = 5  # reset

        except Exception as e:
            logger.error(f"❌ Buy failed: {e}")
            notify_webhook(f"⚠️ Buy failed: {e}")

            # try fallback buy
            try:
                logger.info(f"🔁 Retrying with fallback amount: ${FALLBACK_BUY_USD:.2f}")
                amt = get_usdt_amount(FALLBACK_BUY_USD)
                quote = get_quote(amt)
                execute_swap(quote)
            except Exception as e2:
                logger.error(f"❌ Fallback failed: {e2}")
                notify_webhook(f"⚠️ Fallback failed: {e2}")

        # Randomize sleep a bit to avoid strict schedule fingerprinting (±15%)
        sleep_hrs = random.uniform(SCHEDULE_HOURS * 0.85, SCHEDULE_HOURS * 1.15)
        logger.info(f"⏳ Sleeping for {sleep_hrs:.2f} hours...\n")
        time.sleep(max(1, sleep_hrs * 3600))  # ensure non-negative

if __name__ == "__main__":
    run_bot()
