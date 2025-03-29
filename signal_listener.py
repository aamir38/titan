"""
signal_listener.py
Listens to Redis channel and routes signals to the execution engine
"""

import redis
import json

class SignalListener:
    def __init__(self, redis_url='redis://localhost:6379'):
        self.r = redis.StrictRedis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe("titan:signal")

    def listen(self, callback):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    callback(data)
                except:
                    continue
