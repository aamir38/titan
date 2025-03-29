import redis
import logging

# Initialize logging
logger = logging.getLogger(__name__)

class RedisConnectionManager:
    def __init__(self, host="localhost", port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.redis_client = None

    def connect(self):
        """
        Establishes a connection to the Redis server.
        """
        try:
            self.redis_client = redis.Redis(host=self.host, port=self.port, db=self.db)
            self.redis_client.ping()  # Check the connection
            logger.info(f"Connected to Redis server at {self.host}:{self.port}, db={self.db}")
            return True
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Redis server at {self.host}:{self.port}, db={self.db}: {e}")
            self.redis_client = None
            return False

    def get_client(self):
        """
        Returns the Redis client instance.  Connects if not already connected.
        """
        if self.redis_client is None:
            if not self.connect():
                return None
        return self.redis_client

    def health_check(self):
        """
        Performs a health check on the Redis connection.
        """
        try:
            if self.redis_client:
                self.redis_client.ping()
                logger.info("Redis connection is healthy.")
                return True
            else:
                logger.warning("Redis client is not connected.")
                return False
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection health check failed: {e}")
            return False

    def close(self):
        """
        Closes the Redis connection.
        """
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed.")
            except Exception as e:
                logger.exception(f"Error closing Redis connection: {e}")
            finally:
                self.redis_client = None

# Example usage:
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    redis_manager = RedisConnectionManager()

    if redis_manager.connect():
        client = redis_manager.get_client()
        client.set("test_key", "test_value")
        value = client.get("test_key")
        logger.info(f"Retrieved value: {value}")
        redis_manager.close()
    else:
        logger.error("Failed to connect to Redis.  Check your Redis server settings.")

# Module Footer
# Implemented Features:
# - Connection management (connect, get_client, close)
# - Health check

# Deferred Features:
# - Connection pooling
# - Asynchronous connection support

# Excluded Features:
# - [List any explicitly excluded features]

# Quality Rating: [Placeholder for quality rating]