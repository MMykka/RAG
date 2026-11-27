import threading
import redis
from app.config import settings

KEY = "llm:active"
# Safety net: if the backend crashes mid-answer and never releases its slot, the counter
# disappears after this many seconds without any new question (same as Nginx's proxy_read_timeout).
KEY_TTL_SECONDS = 300
# real Redis in Docker; None on a PC without Redis (REDIS_URL = memory://)
_redis = redis.Redis.from_url(settings.redis_url) if settings.redis_url.startswith("redis") else None
_local_count = 0
_lock = threading.Lock()


def take_slot() -> bool:
    global _local_count
    if _redis:
        # Redis: one counter shared by every Gunicorn worker. INCR adds 1 and returns the new value
        # in one step, so two workers can never both get the last free slot.
        count = _redis.incr(KEY)
        _redis.expire(KEY, KEY_TTL_SECONDS)
        if count > settings.max_generations:
            _redis.decr(KEY)  # over the cap: give the slot back, or the counter would keep growing
            return False
        return True

    # No Redis: count in this process only (plain uvicorn, pytest).
    with _lock:
        if _local_count < settings.max_generations:
            _local_count += 1
            return True
        return False


def release_slot() -> None:
    global _local_count
    if _redis:
        # If the key had expired in the meantime, DECR would start again at -1; put it back to 0.
        if _redis.decr(KEY) < 0:
            _redis.set(KEY, 0, ex=KEY_TTL_SECONDS)
        return

    with _lock:
        if _local_count > 0:
            _local_count -= 1


def active_generations() -> int:
    # how many answers are being written right now (used by the tests)
    if _redis:
        return int(_redis.get(KEY) or 0)
    return _local_count
