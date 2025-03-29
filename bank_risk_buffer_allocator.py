'''
Module: bank_risk_buffer_allocator
Version: 1.0.0
Last Updated: 2025-03-28
Purpose: Diverts 5–10% daily profit to reserve buffer before reinvestment to protect from compounding overexposure.
Core Objectives:
  - Explicit profitability and risk targets alignment: Ensure risk buffer allocation protects capital without compromising profitability or increasing risk.
  - Explicit ESG compliance adherence: Ensure risk buffer allocation does not disproportionately impact ESG-compliant assets.
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
MIN_BUFFER_ALLOCATION = 0.05 # Minimum buffer allocation (5%)
MAX_BUFFER_ALLOCATION = 0.1 # Maximum buffer allocation (10%)
PROFIT_POOL_KEY = "titan:capital:profit_pool"
RESERVE_BUFFER_KEY = "titan:capital:reserve_buffer"

# Prometheus metrics (example)
capital_allocated_to_buffer_total = Counter('capital_allocated_to_buffer_total', 'Total capital allocated to reserve buffer')
risk_buffer_allocator_errors_total = Counter('risk_buffer_allocator_errors_total', 'Total number of risk buffer allocator errors', ['error_type'])
buffer_allocation_latency_seconds = Histogram('buffer_allocation_latency_seconds', 'Latency of buffer allocation')
reserve_buffer_level = Gauge('reserve_buffer_level', 'Current level of the reserve buffer')

async def fetch_daily_profit():
    '''Fetches the daily profit from Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        daily_profit = await redis.get("titan:prod::trade_outcome_recorder:daily_profit") # Example key
        if daily_profit:
            return float(daily_profit)
        else:
            logger.warning(json.dumps({"module": "bank_risk_buffer_allocator", "action": "Get Daily Profit", "status": "No Data"}))
            return 0.0
    except Exception as e:
        logger.error(json.dumps({"module": "bank_risk_buffer_allocator", "action": "Get Daily Profit", "status": "Exception", "error": str(e)}))
        return 0.0

async def allocate_to_reserve_buffer(daily_profit):
    '''Diverts 5–10% daily profit to reserve buffer before reinvestment.'''
    if not daily_profit:
        return False

    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        buffer_allocation_percentage = random.uniform(MIN_BUFFER_ALLOCATION, MAX_BUFFER_ALLOCATION)
        buffer_allocation = daily_profit * buffer_allocation_percentage

        # Update profit pool and reserve buffer in Redis
        profit_pool = await redis.get(PROFIT_POOL_KEY) or 0.0
        new_profit_pool = float(profit_pool) - buffer_allocation
        await redis.set(PROFIT_POOL_KEY, new_profit_pool)

        reserve_buffer = await redis.get(RESERVE_BUFFER_KEY) or 0.0
        new_reserve_buffer = float(reserve_buffer) + buffer_allocation
        await redis.set(RESERVE_BUFFER_KEY, new_reserve_buffer)

        logger.info(json.dumps({"module": "bank_risk_buffer_allocator", "action": "Allocate to Buffer", "status": "Success", "buffer_allocation": buffer_allocation, "new_profit_pool": new_profit_pool, "new_reserve_buffer": new_reserve_buffer}))
        global capital_allocated_to_buffer_total
        capital_allocated_to_buffer_total.inc(buffer_allocation)
        global reserve_buffer_level
        reserve_buffer_level.set(new_reserve_buffer)
        return True
    except Exception as e:
        global risk_buffer_allocator_errors_total
        risk_buffer_allocator_errors_total.labels(error_type="Allocation").inc()
        logger.error(json.dumps({"module": "bank_risk_buffer_allocator", "action": "Allocate to Buffer", "status": "Exception", "error": str(e)}))
        return False

async def bank_risk_buffer_allocator_loop():
    '''Main loop for the bank risk buffer allocator module.'''
    try:
        daily_profit = await fetch_daily_profit()
        if daily_profit > 0:
            await allocate_to_reserve_buffer(daily_profit)

        await asyncio.sleep(86400)  # Re-evaluate buffer allocation daily
    except Exception as e:
        logger.error(json.dumps({"module": "bank_risk_buffer_allocator", "action": "Management Loop", "status": "Exception", "error": str(e)}))
        await asyncio.sleep(300)  # Wait before retrying

async def main():
    '''Main function to start the bank risk buffer allocator module.'''
    await bank_risk_buffer_allocator_loop()

if __name__ == "__main__":
    import aiohttp
    asyncio.run(main())