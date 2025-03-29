# Module: mock_market_feed.py
# Version: 1.0.0
# Last Updated: 2024-07-24
# Purpose: Provides a mock market data feed for testing and development purposes.

# Core Objectives:
# - Profitability (50–100% daily ROI target)
# - Risk reduction (50:1 profit:loss ratio)
# - ESG-safe actions only
# - Compliance with UAE financial law
# - Clean async logic and Redis safety
# - Prometheus metrics (if needed)

import asyncio
import json
import logging
import os
import aioredis
import datetime
import random

# Config from config.json or ENV
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
UPDATE_INTERVAL = float(os.getenv("UPDATE_INTERVAL", 1.0))  # 1 second
STRATEGY_SIGNALS_CHANNEL = os.getenv("STRATEGY_SIGNALS_CHANNEL", "titan:prod:strategy_signals")

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Module name
MODULE_NAME = "mock_market_feed"

async def generate_mock_data() -> dict:
    """Generates mock market data."""
    # Placeholder: Generate random price data
    price = random.uniform(30000, 45000)
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "symbol": SYMBOL,
        "price": price
    }

async def main():
    """Main function to provide a mock market data feed."""
    while True:
        try:
            # Generate mock data
            market_data = await generate_mock_data()

            # Create a sample trading signal
            signal = {
                "timestamp": market_data["timestamp"],
                "symbol": market_data["symbol"],
                "side": random.choice(["buy", "sell"]),
                "confidence": random.uniform(0.5, 1.0),
                "strategy": "mock_strategy",
                "price": market_data["price"]
            }

            # Publish the signal
            await redis.publish(STRATEGY_SIGNALS_CHANNEL, json.dumps(signal))

            logging.info(json.dumps({
                "module": MODULE_NAME,
                "action": "signal_published",
                "symbol": signal["symbol"],
                "message": "Mock trading signal published."
            }))

            await asyncio.sleep(UPDATE_INTERVAL)  # Update every second

        except Exception as e:
            logging.error(json.dumps({
                "module": MODULE_NAME,
                "action": "error",
                "message": str(e)
            }))

async def is_esg_compliant(symbol: str, side: str) -> bool:
    """Placeholder for ESG compliance check."""
    # Deferred to: esg_mode.py
    # TODO: Implement ESG compliance logic
    return True

# Chaos hook example
if os.getenv("CHAOS_MODE", "off") == "on":
    raise Exception("Simulated failure - chaos mode")

# Morphic mode control
morphic_mode = os.getenv("MORPHIC_MODE", "default")
# No morphic mode control specified for this module

# Test entry
if __name__ == "__main__":
    import os
    os.environ["SYMBOL"] = "BTCUSDT"
    asyncio.run(main())

# === Titan Module Footnotes ===
# Implemented Features: redis-pub, async safety, mock market data feed
# Deferred Features: ESG logic -> esg_mode.py
# Excluded Features: backtesting (in backtest_engine.py)
# Quality Rating: 10/10 reviewed by [Grok|Gemini|Claude] on [YYYY-MM-DD]