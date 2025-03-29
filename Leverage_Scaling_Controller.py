'''
Module: Leverage Scaling Controller
Version: 1.0.0
Last Updated: 2025-03-27
Purpose: Dynamically assign safe leverage levels per strategy based on stability + confidence.
Core Objectives:
  - Explicit profitability and risk targets alignment: Ensure leverage scaling maximizes profit and minimizes risk.
  - Explicit ESG compliance adherence: Ensure leverage scaling does not disproportionately impact ESG-compliant assets.
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
SIGNAL_EXPIRY = 60  # Signal expiry time in seconds
MAX_LEVERAGE = 3.0 # Maximum leverage
DEFAULT_LEVERAGE = 1.0 # Default leverage

# Prometheus metrics (example)
strategy_leverage = Gauge('strategy_leverage', 'Leverage level for each strategy', ['strategy', 'symbol'])
leverage_scaling_errors_total = Counter('leverage_scaling_errors_total', 'Total number of leverage scaling errors', ['error_type'])
leverage_scaling_latency_seconds = Histogram('leverage_scaling_seconds', 'Latency of leverage scaling')

async def fetch_data(strategy):
    '''Fetches stability score, confidence score, chaos state, and circuit status from Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        stability_score = await redis.get(f"titan:volatility:stability_score:{SYMBOL}")
        confidence_score = await redis.get(f"titan:prod::confidence:{strategy}:{SYMBOL}")
        chaos_state = await redis.get("titan:chaos:state")
        circuit_status = await redis.get("titan:circuit:status")

        if stability_score and confidence_score and chaos_state and circuit_status:
            return {"stability_score": float(stability_score), "confidence_score": float(confidence_score), "chaos_state": (chaos_state == "TRUE"), "circuit_status": (circuit_status == "TRIPPED")}
        else:
            logger.warning(json.dumps({"module": "Leverage Scaling Controller", "action": "Fetch Data", "status": "No Data", "strategy": strategy}))
            return None
    except Exception as e:
        logger.error(json.dumps({"module": "Leverage Scaling Controller", "action": "Fetch Data", "status": "Failed", "error": str(e)}))
        return None

async def calculate_leverage(data):
    '''Calculates the appropriate leverage level based on stability, confidence, and system health.'''
    if not data:
        return DEFAULT_LEVERAGE

    try:
        stability_score = data["stability_score"]
        confidence_score = data["confidence_score"]
        chaos_state = data["chaos_state"]
        circuit_status = data["circuit_status"]

        if chaos_state or circuit_status:
            leverage = 1.0  # or 0.5 in fallback
            logger.info(json.dumps({"module": "Leverage Scaling Controller", "action": "Calculate Leverage", "status": "Chaos/Circuit Breaker", "leverage": leverage}))
        elif stability_score >= 0.7 and confidence_score >= 0.85:
            leverage = 2.0 # or 3.0 (configurable)
            logger.info(json.dumps({"module": "Leverage Scaling Controller", "action": "Calculate Leverage", "status": "High Stability", "leverage": leverage}))
        elif stability_score >= 0.5 and confidence_score >= 0.7:
            leverage = 1.5
            logger.info(json.dumps({"module": "Leverage Scaling Controller", "action": "Calculate Leverage", "status": "Medium Stability", "leverage": leverage}))
        else:
            leverage = 1.0
            logger.info(json.dumps({"module": "Leverage Scaling Controller", "action": "Calculate Leverage", "status": "Low Stability", "leverage": leverage}))

        return min(leverage, MAX_LEVERAGE) # Never exceed 3.0x (configurable)
    except Exception as e:
        global leverage_scaling_errors_total
        leverage_scaling_errors_total.labels(error_type="Calculation").inc()
        logger.error(json.dumps({"module": "Leverage Scaling Controller", "action": "Calculate Leverage", "status": "Exception", "error": str(e)}))
        return DEFAULT_LEVERAGE

async def publish_leverage(strategy, symbol, leverage):
    '''Publishes the leverage level to Redis with a TTL.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        await redis.setex(f"titan:capital:leverage:{strategy}:{symbol}", SIGNAL_EXPIRY, str(leverage))  # TTL set to SIGNAL_EXPIRY
        strategy_leverage.labels(strategy=strategy, symbol=symbol).set(leverage)
        logger.info(json.dumps({"module": "Leverage Scaling Controller", "action": "Publish Leverage", "status": "Success", "strategy": strategy, "symbol": symbol, "leverage": leverage}))
    except Exception as e:
        global leverage_scaling_errors_total
        leverage_scaling_errors_total.labels(error_type="RedisUpdate").inc()
        logger.error(json.dumps({"module": "Leverage Scaling Controller", "action": "Publish Leverage", "status": "Exception", "error": str(e)}))

async def leverage_scaling_loop():
    '''Main loop for the leverage scaling controller module.'''
    try:
        # Simulate fetching data and calculating leverage
        data = {"stability_score": 0.8, "confidence_score": 0.9, "chaos_state": False, "circuit_status": False}
        leverage = await calculate_leverage(data)
        await publish_leverage("MomentumStrategy", SYMBOL, leverage)

        await asyncio.sleep(60)  # Check for new opportunities every 60 seconds
    except Exception as e:
        logger.error(json.dumps({"module": "Leverage Scaling Controller", "action": "Management Loop", "status": "Exception", "error": str(e)}))
        await asyncio.sleep(300)  # Wait before retrying

async def main():
    '''Main function to start the leverage scaling controller module.'''
    await leverage_scaling_loop()

if __name__ == "__main__":
    import aiohttp
    asyncio.run(main())