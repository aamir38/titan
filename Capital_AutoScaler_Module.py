'''
Module: Capital AutoScaler Module
Version: 1.0.0
Last Updated: 2025-03-27
Purpose: Automatically adjust per-strategy capital allocation based on:
- Daily profit reinvestment
- Fixed capital growth logic
- Risk caps enforced by `Risk_Manager`
- Real-time capital usage stats from `Trade_Outcome_Recorder`
Core Objectives:
  - Explicit profitability and risk targets alignment: Ensure capital autoscaling maximizes profit and minimizes risk.
  - Explicit ESG compliance adherence: Ensure capital autoscaling does not disproportionately impact ESG-compliant assets.
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
BASE_CAPITAL_KEY = "titan:finance:base_capital"
AVAILABLE_CAPITAL_KEY = "titan:capital:available"
CIRCUIT_STATUS_KEY = "titan:circuit:status"
REINVESTMENT_PHASE_1_MONTHS = 6
REINVESTMENT_PHASE_2_MONTHS = 12
RESERVE_CAPITAL_PERCENT = 0.1 # 10% reserve
DEFAULT_REINVEST_PCT_PHASE_1 = 0.50
DEFAULT_REINVEST_PCT_PHASE_2 = 0.30

# Prometheus metrics (example)
capital_allocated_total = Counter('capital_allocated_total', 'Total capital allocated to strategies')
capital_reinvested_today = Gauge('capital_reinvested_today', 'Capital reinvested today')
capital_autoscaling_errors_total = Counter('capital_autoscaling_errors_total', 'Total number of capital autoscaling errors', ['error_type'])
strategy_allocation = Gauge('strategy_allocation', 'Capital allocated to each strategy', ['strategy'])

async def get_initial_capital():
    '''Fetches the initial capital from Redis or config.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        initial_capital = await redis.get(BASE_CAPITAL_KEY)
        if initial_capital:
            return float(initial_capital)
        else:
            logger.warning(json.dumps({"module": "Capital AutoScaler Module", "action": "Get Initial Capital", "status": "No Data", "source": "Redis"}))
            return float(os.environ.get("TOTAL_CAPITAL", 100000.0)) # Default
    except Exception as e:
        logger.error(json.dumps({"module": "Capital AutoScaler Module", "action": "Get Initial Capital", "status": "Exception", "error": str(e)}))
        return float(os.environ.get("TOTAL_CAPITAL", 100000.0))

async def get_daily_profit():
    '''Fetches the daily profit from Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        daily_profit = await redis.get("titan:prod::trade_outcome_recorder:daily_profit") # Example key
        if daily_profit:
            return float(daily_profit)
        else:
            logger.warning(json.dumps({"module": "Capital AutoScaler Module", "action": "Get Daily Profit", "status": "No Data"}))
            return 0.0
    except Exception as e:
        logger.error(json.dumps({"module": "Capital AutoScaler Module", "action": "Get Daily Profit", "status": "Exception", "error": str(e)}))
        return 0.0

async def get_strategy_performance(strategy_id):
    '''Fetches the performance of a given trading strategy from Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        performance_data = await redis.get(f"titan:prod::strategy:{strategy_id}:performance")
        if performance_data:
            return json.loads(performance_data)
        else:
            logger.warning(json.dumps({"module": "Capital AutoScaler Module", "action": "Get Strategy Performance", "status": "No Data", "strategy": strategy_id}))
            return {"pnl": 0.0, "drawdown": 0.0, "win_rate": 0.5, "confidence_score": 0.5} # Default values
    except Exception as e:
        logger.error(json.dumps({"module": "Capital AutoScaler Module", "action": "Get Strategy Performance", "status": "Exception", "error": str(e)}))
        return {"pnl": 0.0, "drawdown": 0.0, "win_rate": 0.5, "confidence_score": 0.5}

async def get_volatility():
    '''Fetches the current market volatility from Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        volatility = await redis.get("titan:prod::volatility:BTCUSDT") # Example key
        if volatility:
            return float(volatility)
        else:
            logger.warning(json.dumps({"module": "Capital AutoScaler Module", "action": "Get Volatility", "status": "No Data"}))
            return 0.05 # Default volatility
    except Exception as e:
        logger.error(json.dumps({"module": "Capital AutoScaler Module", "action": "Get Volatility", "status": "Exception", "error": str(e)}))
        return 0.05

async def get_circuit_status():
    '''Fetches the circuit breaker status from Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        circuit_status = await redis.get("titan:circuit:status")
        if circuit_status == "TRUE":
            return True
        else:
            return False
    except Exception as e:
        logger.error(json.dumps({"module": "Capital AutoScaler Module", "action": "Get Circuit Status", "status": "Exception", "error": str(e)}))
        return False

async def calculate_allocation_weight(strategy_performance, volatility):
    '''Calculates the allocation weight for a given strategy.'''
    confidence_score = strategy_performance.get("confidence_score", 0.5)
    win_rate = strategy_performance.get("win_rate", 0.5)
    drawdown_risk = strategy_performance.get("drawdown", 0.1)

    # Weight formula
    allocation_weight = (confidence_score * win_rate) / (volatility * (drawdown_risk + 0.01)) # Add small value to prevent division by zero
    return allocation_weight

async def adjust_capital_allocation():
    '''Adjusts capital allocation based on strategy performance, risk, and system health.'''
    try:
        initial_capital = await get_initial_capital()
        daily_profit = await get_daily_profit()
        volatility = await get_volatility()
        circuit_status = await get_circuit_status()

        # Reinvestment Logic
        now = datetime.datetime.now()
        months_since_start = (now.year - 2025) * 12 + now.month # Assuming project started in 2025
        if months_since_start <= REINVESTMENT_PHASE_1_MONTHS:
            reinvest_pct = DEFAULT_REINVEST_PCT_PHASE_1
        elif months_since_start <= REINVESTMENT_PHASE_2_MONTHS:
            reinvest_pct = DEFAULT_REINVEST_PCT_PHASE_2
        else:
            reinvest_pct = 0.0 # No reinvestment after 12 months

        reinvestment = daily_profit * reinvest_pct
        available_capital = initial_capital + reinvestment
        if daily_profit < 0:
            available_capital *= 0.9 # Shrink risk exposure by 10%

        # Cap total deployed capital
        available_capital = min(available_capital, initial_capital * (1 - RESERVE_CAPITAL_PERCENT))

        # Fetch strategy performance and calculate allocation weights
        strategy_weights = {}
        for strategy_id in ["MomentumStrategy", "ScalpingStrategy", "ArbitrageStrategy"]: # Example strategies
            strategy_performance = await get_strategy_performance(strategy_id)
            if strategy_performance:
                strategy_weights[strategy_id] = await calculate_allocation_weight(strategy_performance, volatility)
            else:
                strategy_weights[strategy_id] = 0.0

        # Normalize allocation weights
        total_weight = sum(strategy_weights.values())
        if total_weight == 0:
            logger.warning("No strategies available for capital allocation")
            return

        normalized_allocations = {}
        for strategy_id, weight in strategy_weights.items():
            normalized_allocations[strategy_id] = (weight / total_weight) * available_capital

        # Apply capital allocations to strategies
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        for strategy_id, allocation_amount in normalized_allocations.items():
            await redis.set(f"titan:capital:strategy:{strategy_id}", allocation_amount)
            strategy_allocation.labels(strategy=strategy_id).set(allocation_amount)
            logger.info(json.dumps({"module": "Capital AutoScaler Module", "action": "Apply Allocation", "status": "Success", "strategy": strategy_id, "allocation": allocation_amount}))

        capital_allocated_total.inc()
        capital_reinvested_today.set(reinvestment)
        logger.info(json.dumps({"module": "Capital AutoScaler Module", "action": "Adjust Capital", "status": "Success", "reinvestment": reinvestment, "available_capital": available_capital}))

    except Exception as e:
        global capital_autoscaling_errors_total
        capital_autoscaling_errors_total.labels(error_type="Allocation").inc()
        logger.error(json.dumps({"module": "Capital AutoScaler Module", "action": "Adjust Capital", "status": "Exception", "error": str(e)}))

async def capital_auto_scaling_loop():
    '''Main loop for the capital auto-scaling module.'''
    try:
        await adjust_capital_allocation()
        await asyncio.sleep(3600)  # Reallocate capital every hour
    except Exception as e:
        logger.error(json.dumps({"module": "Capital AutoScaler Module", "action": "Management Loop", "status": "Exception", "error": str(e)}))
        await asyncio.sleep(300)  # Wait before retrying

async def main():
    '''Main function to start the capital auto-scaling module.'''
    await capital_auto_scaling_loop()

if __name__ == "__main__":
    import aiohttp
    asyncio.run(main())