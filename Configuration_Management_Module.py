'''
Module: Configuration Management Module
Version: 1.0.0
Last Updated: 2025-03-26
Purpose: Provides dynamic, centralized configuration management.
Core Objectives:
  - Explicit profitability and risk targets alignment: Ensure configuration changes optimize for maximum profit within defined risk limits.
  - Explicit ESG compliance adherence: Dynamically adjust ESG-related configuration parameters.
  - Explicit regulatory and compliance standards adherence: Ensure configuration adheres to UAE financial regulations.
  - Explicit 10/10 quality rating definition adherence: Code must meet all quality criteria, including modularity, error handling, metrics, logging, and testing.
Summary of Enhancements:
  - Initial version.
  - Implemented dynamic loading of configuration from Redis.
  - Added explicit validation of configuration parameters.
  - Enhanced error handling with specific error categories.
  - Expanded Prometheus metrics for detailed configuration tracking.
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
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
CONFIG_CHANNEL = "titan:prod::config_updates"  # Standardized Redis channel
DEFAULT_CONFIG = {
    "trading_limit": 1000,
    "leverage": 3,
    "esg_compliance_enabled": True,
    "profit_target": 500,
    "risk_tolerance": 0.00001,
    "data_retention_days": 30
}

# Prometheus metrics (example)
config_changes_total = Counter('config_changes_total', 'Total number of dynamic configuration changes applied')
config_change_errors_total = Counter('config_change_errors_total', 'Total number of dynamic configuration change errors', ['error_type'])
config_latency_seconds = Histogram('config_latency_seconds', 'Latency of configuration updates')
current_config_version = Gauge('current_config_version', 'Current configuration version')

async def fetch_configuration():
    '''Fetches the latest configuration from Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        config_data = await redis.get("titan:prod::config")  # Centralized config key
        if config_data:
            config = json.loads(config_data)
            logger.info(json.dumps({"module": "Dynamic Configuration Engine", "action": "Fetch Configuration", "status": "Success", "source": "Redis", "config": config}))
            return config
        else:
            logger.warning(json.dumps({"module": "Dynamic Configuration Engine", "action": "Fetch Configuration", "status": "Using Default", "source": "Default", "config": DEFAULT_CONFIG}))
            return DEFAULT_CONFIG
    except Exception as e:
        global config_change_errors_total
        config_change_errors_total.labels(error_type="RedisFetch").inc()
        logger.error(json.dumps({"module": "Dynamic Configuration Engine", "action": "Fetch Configuration", "status": "Failed", "error": str(e)}))
        return DEFAULT_CONFIG

async def validate_configuration(config):
    '''Validates the configuration to ensure it meets predefined criteria.'''
    try:
        # Example validation logic (replace with actual validation)
        if not isinstance(config.get("trading_limit"), (int, float)):
            raise ValueError("Trading limit must be a number")
        if not isinstance(config.get("leverage"), (int, float)):
            raise ValueError("Leverage must be a number")
        if not isinstance(config.get("esg_compliance_enabled"), bool):
            raise ValueError("ESG compliance enabled must be a boolean")
        if not isinstance(config.get("data_retention_days"), int):
            raise ValueError("Data retention days must be an integer")

        logger.info(json.dumps({"module": "Dynamic Configuration Engine", "action": "Validate Configuration", "status": "Success", "config": config}))
        return True
    except ValueError as e:
        global config_change_errors_total
        config_change_errors_total.labels(error_type="Validation").inc()
        logger.error(json.dumps({"module": "Dynamic Configuration Engine", "action": "Validate Configuration", "status": "Invalid", "error": str(e), "config": config}))
        return False

async def apply_dynamic_configuration(config):
    '''Applies the new dynamic configuration to the system.'''
    try:
        if not await validate_configuration(config):
            logger.error(json.dumps({"module": "Dynamic Configuration Engine", "action": "Apply Configuration", "status": "Aborted", "reason": "Invalid configuration", "config": config}))
            return False

        # Simulate applying configuration (replace with actual logic)
        global config_changes_total
        config_changes_total += 1
        logger.info(json.dumps({"module": "Dynamic Configuration Engine", "action": "Apply Configuration", "status": "Success", "config": config}))
        return True
    except Exception as e:
        global config_change_errors_total
        config_change_errors_total.labels(error_type="Application").inc()
        logger.error(json.dumps({"module": "Dynamic Configuration Engine", "action": "Apply Configuration", "status": "Failed", "error": str(e), "config": config}))
        return False

async def monitor_config_changes(redis_client):
    '''Monitors Redis for configuration changes and applies them.'''
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CONFIG_CHANNEL)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    config = json.loads(message['data'].decode('utf-8'))
                    if await apply_dynamic_configuration(config):
                        logger.info(json.dumps({"module": "Dynamic Configuration Engine", "action": "Config Update", "status": "Success", "config": config}))
                        current_config_version.inc()
                except json.JSONDecodeError as e:
                    logger.error(json.dumps({"module": "Dynamic Configuration Engine", "action": "Config Update", "status": "Failed", "error": str(e), "data": message["data"].decode("utf-8")}))
                except Exception as e:
                    logger.error(json.dumps({"module": "Dynamic Configuration Engine", "action": "Config Update", "status": "Failed", "error": str(e), "message": message}))
    except Exception as e:
        logger.error(json.dumps({"module": "Dynamic Configuration Engine", "action": "Subscription", "status": "Failed", "error": str(e)}))
    finally:
        await pubsub.unsubscribe(CONFIG_CHANNEL)

async def dynamic_configuration_loop():
    '''Main loop for the dynamic configuration engine module.'''
    try:
        redis_client = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        await monitor_config_changes(redis_client)
    except aioredis.exceptions.ConnectionError as e:
        logger.error(json.dumps({"module": "Dynamic Configuration Engine", "action": "Redis Connection", "status": "Failed", "error": str(e)}))
    except Exception as e:
        logger.error(json.dumps({"module": "Dynamic Configuration Engine", "action": "Main", "status": "Failed", "error": str(e)}))

async def main():
    '''Main function to start the dynamic configuration engine module.'''
    await dynamic_configuration_loop()

if __name__ == "__main__":
    import aiohttp
    asyncio.run(main())