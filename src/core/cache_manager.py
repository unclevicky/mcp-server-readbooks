from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, max_size=100, ttl=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl)
        
    def get(self, key: str):
        entry = self.cache.get(key)
        if entry and datetime.now() - entry['timestamp'] < self.ttl:
            return entry['data']
        return None
        
    def set(self, key: str, data: str):
        if len(self.cache) >= self.max_size:
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }