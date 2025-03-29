# 📌 Name: module_changelog_logger.py
# 🧠 Purpose: Logs code or config changes per module including timestamps, diff hash, affected params, and initiator (manual or automated). Keeps audit trail for rollback or forensic recovery.
# ⚙️ Inputs: Module name, change details
# 📤 Outputs: Logs, Redis updates
# 🔄 Must interface with: Redis, Advanced_Logging_Engine.py, commander_override_ledger.py
import redis
import json
import logging
import os
import hashlib
import time

# Initialize Redis connection
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_namespace = os.getenv("REDIS_NAMESPACE", "titan:prod")
r = redis.Redis(host=redis_host, port=redis_port)

# Initialize logging
logging_level = os.getenv("LOGGING_LEVEL", "INFO").upper()
logging.basicConfig(level=logging_level)

class ModuleChangelogLogger:
    def __init__(self):
        pass

    def log_change(self, module_name, change_type, details, initiator):
        """Logs a code or config change for a module."""
        timestamp = time.time()
        change_id = hashlib.sha256(
            (module_name + str(timestamp) + json.dumps(details)).encode('utf-8')
        ).hexdigest()

        log_entry = {
            "module": module_name,
            "change_type": change_type,  # "code", "config"
            "timestamp": timestamp,
            "change_id": change_id,
            "details": details,
            "initiator": initiator  # "manual", "automated"
        }

        log_key = f"{redis_namespace}:changelog:{module_name}:{change_id}"
        r.set(log_key, json.dumps(log_entry))
        r.expire(log_key, 3600 * 24 * 7)  # Keep logs for 7 days

        logging.info(f"Logged {change_type} change for {module_name}: {change_id}")

    def get_module_changes(self, module_name, limit=10):
        """Retrieves recent changes for a module from Redis."""
        # In a real system, you might use a sorted set for more efficient retrieval
        keys = r.keys(f"{redis_namespace}:changelog:{module_name}:*")
        changes = []
        for key in keys:
            try:
                change_data = r.get(key)
                if change_data:
                    changes.append(json.loads(change_data.decode('utf-8')))
            except Exception as e:
                logging.error(f"Error retrieving changelog entry: {e}")
        return changes[:limit]

if __name__ == "__main__":
    logger = ModuleChangelogLogger()

    # Example usage
    module_name = os.getenv("MODULE_NAME", "Scalping_Strategy_Module")
    details = {
        "param": "leverage",
        "old_value": 1.0,
        "new_value": 1.2
    }
    logger.log_change(module_name, "config", details, "manual")

    changes = logger.get_module_changes(module_name)
    logging.info(f"Recent changes for {module_name}: {json.dumps(changes)}")

# === Titan Module Footnotes ===
# ✅ Implemented Features: Logging changes to Redis, retrieving change history
# 🔄 Deferred Features: Integration with a config management system for automated change tracking
# ❌ Excluded Features: Complex diffing logic