'''
Module: commander_signal_override.py
Version: 1.0.0
Last Updated: 2025-03-28
Purpose: Allows manual override of trading signals.
'''

import asyncio
import aioredis
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration from file
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
    logger.error(f"Error loading configuration: {e}. Using default values.")
    config = {}

REDIS_HOST = config.get("REDIS_HOST", "localhost")
REDIS_PORT = config.get("REDIS_PORT", 6379)

async def override_signal(original_signal, override_action):
    '''Overrides a trading signal in Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        channel = "titan:prod:commander_signal_override:signal_override"

        override_signal = original_signal.copy()
        override_signal["side"] = override_action  # "buy" or "sell"

        message = json.dumps(override_signal)
        await redis.publish(channel, message)
        logger.info(json.dumps({"module": "commander_signal_override", "action": "override_signal", "status": "success", "original_signal": original_signal, "override_action": override_action, "override_signal": override_signal}))
        return True
    except Exception as e:
        logger.error(json.dumps({"module": "commander_signal_override", "action": "override_signal", "status": "error", "original_signal": original_signal, "override_action": override_action, "error": str(e)}))
        return False

async def commander_signal_override_loop():
    '''Main loop for the commander_signal_override module.'''
    try:
        # Example: Overriding a signal
        original_signal = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "confidence": 0.8,
            "strategy": "momentum_module",
            "ttl": 60
        }
        await override_signal(original_signal, "sell")

        await asyncio.sleep(60)  # Run every 60 seconds
    except Exception as e:
        logger.error(json.dumps({"module": "commander_signal_override", "action": "commander_signal_override_loop", "status": "exception", "error": str(e)}))
        await asyncio.sleep(300)  # Wait before retrying

async def main():
    '''Main function to start the commander_signal_override module.'''
    try:
        await commander_signal_override_loop()
    except Exception as e:
        logger.error(json.dumps({"module": "commander_signal_override", "action": "main", "status": "exception", "error": str(e)}))

if __name__ == "__main__":
    import os
    os.environ["SYMBOL"] = "BTCUSDT"
    asyncio.run(main())

# === Titan Module Footnotes ===
# ✅ Implemented Features: redis-pub, async safety, signal override
# 🔄 Deferred Features: UI integration, permission control, signal validation
# ❌ Excluded Features: direct trade execution
# 🎯 Quality Rating: 7/10 reviewed by Roo on 2025-03-28