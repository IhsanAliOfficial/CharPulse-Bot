🪙 CharPulse-Bot — Automated CharCoin Swap Keeper

A fully automated Solana-based micro-swap bot that keeps your CharCoin wallet alive and active — quietly, efficiently, and reliably.

🚀 Overview

CharPulse-Bot is a lightweight yet production-ready Solana micro-trading bot built to automatically perform periodic USDT → CHAR swaps using the Jupiter Lite API.
It runs on a schedule (e.g. every 6 hours) to ensure your CharCoin wallet remains active, liquid, and on-chain, even during idle periods.

⚙️ Core Features

💱 Automated Micro-Buys — Executes tiny swaps (e.g. $0.01–$0.10) to maintain wallet activity.

🔒 Real Wallet Integration — Uses Solana’s solders library for secure signing and transaction dispatch.

🌐 Jupiter Aggregator API — Fetches best swap routes via Jupiter Lite (/quote & /swap endpoints).

🔔 Webhook Notifications — Sends trade results and alerts directly to your Discord or Telegram.

🧪 Dry-Run Mode — Safe simulation for testing without using real funds.

⏰ Dynamic Scheduling — Randomized sleep intervals prevent predictable transaction patterns.

🧰 Detailed Logging — Local logs/bot.log plus console logs with emoji-rich real-time status.

🔧 Tech Stack

Language: Python 3.10+

Blockchain: Solana (via solders + solana.rpc.api)

APIs: Jupiter Lite Swap & Quote endpoints

Env Handling: python-dotenv

Notifications: Webhooks (Discord/Telegram compatible)

Logging: File + Console with emoji-friendly output
