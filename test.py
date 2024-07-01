import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

print(redis_client.ping())
redis_client.set("name", "John")