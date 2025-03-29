# ai_entropy_discriminator.py
# Version: 1.0
# Last Updated: 2025-03-28

"""
Titan AI Entropy Discriminator Module

Purpose:
- Filters out high-entropy (unreliable) AI-generated signals
- Ensures only low-entropy, high-confidence signals reach execution pipeline
- Enhances win-rate and capital efficiency during high-noise environments

Inputs:
- AI-generated signal stream (dict): {symbol, timestamp, confidence, entropy, fingerprint}
- Redis stream: titan:signal:raw:<symbol>

Outputs:
- titan:signal:entropy_clean:<symbol>
- titan:entropy:block:<id> if filtered

Dependencies:
- Redis (async)
- Logging

"""

import asyncio
import aioredis
import json
import logging
import time

# Configurable thresholds
ENTROPY_THRESHOLD = 0.38  # Above this = too much noise
CONFIDENCE_MINIMUM = 0.74  # Below this = unreliable
REDIS_URL = "redis://localhost"

logger = logging.getLogger("AIEntropyDiscriminator")
logger.setLevel(logging.INFO)

async def filter_signal(redis, signal):
    try:
        entropy = float(signal.get("entropy", 1.0))
        confidence = float(signal.get("confidence", 0.0))
        signal_id = signal.get("id", f"sig_{int(time.time())}")
        symbol = signal.get("symbol")

        if entropy > ENTROPY_THRESHOLD or confidence < CONFIDENCE_MINIMUM:
            logger.info(f"Signal {signal_id} blocked: entropy={entropy}, confidence={confidence}")
            await redis.setex(f"titan:entropy:block:{signal_id}", 1800, json.dumps(signal))
            return False

        await redis.setex(f"titan:signal:entropy_clean:{symbol}:{signal_id}", 900, json.dumps(signal))
        logger.info(f"Signal {signal_id} passed entropy screen → forwarded to clean stream")
        return True

    except Exception as e:
        logger.error(f"Error filtering signal: {e}")
        return False

async def entropy_discriminator_loop():
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.psubscribe("titan:signal:raw:*")
    logger.info("🧠 AI Entropy Discriminator active. Listening for raw signals...")

    async for msg in pubsub.listen():
        if msg['type'] != 'pmessage':
            continue

        try:
            data = json.loads(msg['data'])
            await filter_signal(redis, data)
        except Exception as e:
            logger.warning(f"Failed to parse or filter signal: {e}")

if __name__ == "__main__":
    asyncio.run(entropy_discriminator_loop())
