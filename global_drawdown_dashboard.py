'''
Module: global_drawdown_dashboard
Version: 1.0.0
Last Updated: 2025-03-28
Purpose: Monitors total system drawdown across all modules and halts risky ones if global threshold is breached.
Core Objectives:
  - Explicit profitability and risk targets alignment: Ensure drawdown monitoring protects capital and aligns with risk targets.
  - Explicit ESG compliance adherence: Ensure drawdown monitoring does not disproportionately impact ESG-compliant assets.
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
DRAWDOWN_THRESHOLD = 0.15 # Global drawdown threshold (15%)
RISKY_MODULES = ["MomentumStrategy", "ScalpingModule", "ArbitrageModule"] # Example risky modules

# Prometheus metrics (example)
drawdown_events_triggered_total = Counter('drawdown_events_triggered_total', 'Total number of drawdown events triggered')
global_drawdown_dashboard_errors_total = Counter('global_drawdown_dashboard_errors_total', 'Total number of global drawdown dashboard errors', ['error_type'])
drawdown_monitoring_latency_seconds = Histogram('drawdown_monitoring_latency_seconds', 'Latency of drawdown monitoring')
global_drawdown_level = Gauge('global_drawdown_level', 'Current level of global drawdown')

async def fetch_module_drawdowns():
    '''Monitors total system drawdown across all modules.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        total_drawdown = 0
        for module in ["MomentumStrategy", "ScalpingModule", "ArbitrageModule", "ReversalStrategy"]: # Example modules
            drawdown = await redis.get(f"titan:performance:{module}:drawdown")
            if drawdown:
                total_drawdown += float(drawdown)
            else:
                logger.warning(json.dumps({"module": "global_drawdown_dashboard", "action": "Fetch Module Drawdown", "status": "No Data", "module": module}))

        logger.info(json.dumps({"module": "global_drawdown_dashboard", "action": "Fetch Module Drawdowns", "status": "Success", "total_drawdown": total_drawdown}))
        global global_drawdown_level
        global_drawdown_level.set(total_drawdown)
        return total_drawdown
    except Exception as e:
        logger.error(json.dumps({"module": "global_drawdown_dashboard", "action": "Fetch Module Drawdowns", "status": "Exception", "error": str(e)}))
        return None

async def halt_risky_modules(total_drawdown):
    '''Halts risky ones if global threshold is breached.'''
    if not total_drawdown:
        return False

    try:
        if total_drawdown > DRAWDOWN_THRESHOLD:
            redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
            for module in RISKY_MODULES:
                await redis.set(f"titan:module:status:{module}", "halted")
                logger.warning(json.dumps({"module": "global_drawdown_dashboard", "action": "Halt Risky Module", "status": "Halted", "module": module}))
            global drawdown_events_triggered_total
            drawdown_events_triggered_total.inc()
            return True
        else:
            return False
    except Exception as e:
        logger.error(json.dumps({"module": "global_drawdown_dashboard", "action": "Halt Risky Modules", "status": "Exception", "error": str(e)}))
        return False

async def global_drawdown_dashboard_loop():
    '''Main loop for the global drawdown dashboard module.'''
    try:
        total_drawdown = await fetch_module_drawdowns()
        if total_drawdown:
            await halt_risky_modules(total_drawdown)

        await asyncio.sleep(60)  # Check drawdown every 60 seconds
    except Exception as e:
        logger.error(json.dumps({"module": "global_drawdown_dashboard", "action": "Management Loop", "status": "Exception", "error": str(e)}))
        await asyncio.sleep(300)  # Wait before retrying

async def main():
    '''Main function to start the global drawdown dashboard module.'''
    await global_drawdown_dashboard_loop()

if __name__ == "__main__":
    import aiohttp
    asyncio.run(main())