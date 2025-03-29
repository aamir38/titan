'''
Module: Stability Scorer
Version: 1.0.0
Last Updated: 2025-03-27
Purpose: Assess real-time market stability for each symbol and publish a normalized score (0–1 scale).
Core Objectives:
  - Explicit profitability and risk targets alignment: Ensure stability scoring provides accurate information for profit and risk management.
  - Explicit ESG compliance adherence: Ensure stability scoring does not disproportionately impact ESG-compliant assets.
  - Explicit regulatory and compliance standards adherence: Ensure all trading activities comply with exchange regulations and UAE financial regulations.
  - Explicit 10/10 quality rating definition adherence: Code must meet all quality criteria, including modularity, error handling, metrics, logging, and testing.
Summary of Enhancements:
  - Initial version.
'''

import asyncio
import aioredis
import json
import logging
import os
from prometheus_client import Counter, Gauge, Histogram
import random  # For chaos testing
import time
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
SYMBOL = "BTCUSDT"  # Example symbol
STABILITY_SCORE_EXPIRY = 10 # Stability score expiry time in seconds

# Prometheus metrics (example)
stability_scores_generated_total = Counter('stability_scores_generated_total', 'Total number of stability scores generated')
stability_scorer_errors_total = Counter('stability_scorer_errors_total', 'Total number of stability scorer errors', ['error_type'])
stability_scoring_latency_seconds = Histogram('stability_scoring_latency_seconds', 'Latency of stability scoring')
titan_stability_score = Gauge('titan_stability_score', 'System stability score based on chaos testing', ['symbol'])

async def fetch_data():
    '''Fetches ATR values, order book wall consistency, spread width, slippage pressure, depth imbalance volatility, and API latency jitter from Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        atr_1m = await redis.get(f"titan:prod::atr_1m:{SYMBOL}")
        atr_5m = await redis.get(f"titan:prod::atr_5m:{SYMBOL}")
        atr_15m = await redis.get(f"titan:prod::atr_15m:{SYMBOL}")
        order_book_consistency = await redis.get(f"titan:prod::order_book_consistency:{SYMBOL}")
        spread_width = await redis.get(f"titan:prod::spread_width:{SYMBOL}")
        slippage_pressure = await redis.get(f"titan:prod::slippage_pressure:{SYMBOL}")
        depth_imbalance_volatility = await redis.get(f"titan:prod::depth_imbalance_volatility:{SYMBOL}")
        api_latency_jitter = await redis.get(f"titan:prod::api_latency_jitter:{SYMBOL}")

        if atr_1m and atr_5m and atr_15m and order_book_consistency and spread_width and slippage_pressure and depth_imbalance_volatility and api_latency_jitter:
            return {"atr_1m": float(atr_1m), "atr_5m": float(atr_5m), "atr_15m": float(atr_15m), "order_book_consistency": float(order_book_consistency), "spread_width": float(spread_width), "slippage_pressure": float(slippage_pressure), "depth_imbalance_volatility": float(depth_imbalance_volatility), "api_latency_jitter": float(api_latency_jitter)}
        else:
            logger.warning(json.dumps({"module": "Stability Scorer", "action": "Fetch Data", "status": "No Data"}))
            return None
    except Exception as e:
        logger.error(json.dumps({"module": "Stability Scorer", "action": "Fetch Data", "status": "Failed", "error": str(e)}))
        return None

async def calculate_stability_score(data):
    '''Calculates a stability score based on the fetched data.'''
    if not data:
        return None

    try:
        atr_volatility = (data["atr_1m"] + data["atr_5m"] + data["atr_15m"]) / 3
        tight_spreads = 1 - data["spread_width"] # Assuming spread_width is a ratio
        consistent_depth = data["order_book_consistency"]
        low_jitter = 1 - data["api_latency_jitter"]

        # Placeholder for stability score calculation logic (replace with actual logic)
        score = (1 - atr_volatility + tight_spreads + consistent_depth + low_jitter) / 4
        score = max(0.0, min(score, 1.0)) # Normalize between 0 and 1

        titan_stability_score.labels(symbol=SYMBOL).set(score)
        logger.info(json.dumps({"module": "Stability Scorer", "action": "Calculate Score", "status": "Success", "score": score}))
        return score
    except Exception as e:
        global stability_scorer_errors_total
        stability_scorer_errors_total.labels(error_type="Calculation").inc()
        logger.error(json.dumps({"module": "Stability Scorer", "action": "Calculate Score", "status": "Exception", "error": str(e)}))
        return None

async def publish_stability_score(score):
    '''Publishes the stability score to Redis with a TTL.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        await redis.setex(f"titan:volatility:stability_score:{SYMBOL}", STABILITY_SCORE_EXPIRY, str(score))  # TTL set to SIGNAL_EXPIRY
        logger.info(json.dumps({"module": "Stability Scorer", "action": "Publish Score", "status": "Success", "score": score}))
    except Exception as e:
        logger.error(json.dumps({"module": "Stability Scorer", "action": "Publish Score", "status": "Exception", "error": str(e)}))

async def stability_scorer_loop():
    '''Main loop for the stability scorer module.'''
    try:
        data = await fetch_data()
        if data:
            score = await calculate_stability_score(data)
            if score:
                await publish_stability_score(score)

        await asyncio.sleep(60)  # Check stability every 60 seconds
    except Exception as e:
        logger.error(json.dumps({"module": "Stability Scorer", "action": "Management Loop", "status": "Exception", "error": str(e)}))
        await asyncio.sleep(300)  # Wait before retrying

async def main():
    '''Main function to start the stability scorer module.'''
    await stability_scorer_loop()

if __name__ == "__main__":
    import aiohttp
    asyncio.run(main())