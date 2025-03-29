'''
Module: config_sync_guard
Version: 1.0.0
Last Updated: 2025-03-28
Purpose: Guards against config drift.
Core Objectives:
  - Explicit profitability and risk targets alignment: Ensure config integrity prevents errors and reduces risk.
  - Explicit ESG compliance adherence: Ensure config integrity does not disproportionately impact ESG-compliant assets.
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
import hashlib
import yaml
from prometheus_client import Counter, Gauge, Histogram

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
CONFIG_FILE = "titan_config.yaml" # Path to the YAML configuration file
CONFIG_HASH_KEY = "titan:infra:config_hash" # Redis key to store the config hash

# Prometheus metrics (example)
config_mismatches_detected_total = Counter('config_mismatches_detected_total', 'Total number of config mismatches detected')
config_sync_guard_errors_total = Counter('config_sync_guard_errors_total', 'Total number of config sync guard errors', ['error_type'])
config_sync_latency_seconds = Histogram('config_sync_latency_seconds', 'Latency of config sync check')
config_hash_value = Gauge('config_hash_value', 'Hash value of the current configuration')

async def calculate_config_hash():
    '''Calculates the hash of the YAML configuration file.'''
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = f.read()
        hash_object = hashlib.sha256(config_data.encode('utf-8'))
        config_hash = hash_object.hexdigest()
        logger.info(json.dumps({"module": "config_sync_guard", "action": "Calculate Config Hash", "status": "Success", "config_hash": config_hash}))
        return config_hash
    except Exception as e:
        logger.error(json.dumps({"module": "config_sync_guard", "action": "Calculate Config Hash", "status": "Exception", "error": str(e)}))
        return None

async def fetch_stored_config_hash():
    '''Fetches the stored config hash from Redis.'''
    try:
        redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
        stored_hash = await redis.get("titan:infra:config_hash")
        if stored_hash:
            return stored_hash
        else:
            logger.warning(json.dumps({"module": "config_sync_guard", "action": "Fetch Stored Config Hash", "status": "No Data"}))
            return None
    except Exception as e:
        logger.error(json.dumps({"module": "config_sync_guard", "action": "Fetch Stored Config Hash", "status": "Exception", "error": str(e)}))
        return None

async def compare_config_hashes(config_hash, stored_hash):
    '''Compares live Redis config vs YAML baseline.'''
    if not config_hash or not stored_hash:
        return False

    try:
        if config_hash != stored_hash:
            logger.warning(json.dumps({"module": "config_sync_guard", "action": "Config Mismatch Detected", "status": "Mismatch", "config_hash": config_hash, "stored_hash": stored_hash}))
            global config_mismatches_detected_total
            config_mismatches_detected_total.inc()
            return True
        else:
            logger.info(json.dumps({"module": "config_sync_guard", "action": "Config Sync Validated", "status": "Match"}))
            return False
    except Exception as e:
        logger.error(json.dumps({"module": "config_sync_guard", "action": "Compare Config Hashes", "status": "Exception", "error": str(e)}))
        return False

async def config_sync_guard_loop():
    '''Main loop for the config sync guard module.'''
    try:
        config_hash = await calculate_config_hash()
        stored_hash = await fetch_stored_config_hash()

        if config_hash and stored_hash:
            await compare_config_hashes(config_hash, stored_hash)

        await asyncio.sleep(3600)  # Re-evaluate config sync every hour
    except Exception as e:
        global config_sync_guard_errors_total
        config_sync_guard_errors_total.labels(error_type="Management").inc()
        logger.error(json.dumps({"module": "config_sync_guard", "action": "Management Loop", "status": "Exception", "error": str(e)}))
        await asyncio.sleep(300)  # Wait before retrying

async def main():
    '''Main function to start the config sync guard module.'''
    await config_sync_guard_loop()

if __name__ == "__main__":
    import aiohttp
    asyncio.run(main())