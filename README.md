
# CharCoin Keep-Alive Bot

This bot keeps **CharCoin (CHAR)** visible on [Dexscreener](https://dexscreener.com) by ensuring at least one trade happens every 24 hours.  
If no activity is detected within 24h, the bot automatically performs a **tiny buy ($0.10–$1.00)** via Jupiter on Solana.  


# 🚀 CharCoin Keep-Alive Bot

An advanced automated trading bot built for the **Solana blockchain**, designed to perform **micro-buy transactions** from **USDT → CharCoin** at scheduled intervals.

### ✨ Features
- 🧠 **Auto Scheduler** – Buys CHAR every few hours automatically.  
- 🧪 **Dry-Run Mode** – Test everything safely without using a real wallet.  
- 🔁 **Smart Retry System** – Falls back to secondary buy amount if swap fails.  
- 🌐 **Jupiter Aggregator API** – Real quotes & swap routing.  
- ⚙️ **Environment Driven** – Configure RPCs, mints, and wallet in `.env`.  
- 🧾 **Detailed Logging** – All events stored in logs for easy debugging.
- Checks Dexscreener API for CHAR trades in the past 24h  
- If no trades → executes a micro-buy using your Solana wallet  
- Configurable buy amount, slippage, and check interval  
- Uses **Dexscreener free API** + **Jupiter swap API** (no extra cost)  
- Prevents graphs & data in the DAPP from collapsing 
---






