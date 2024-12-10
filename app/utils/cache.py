from functools import wraps
import time
import psutil
import gc
from flask import current_app
import logging
from flask_caching import Cache

# Initialize logging
logger = logging.getLogger('dashboard')

# Initialize cache with configuration
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Cache management variables
last_cleanup_time = time.time()

def init_cache(app):
    """Initialize cache with app"""
    try:
        cache.init_app(app)
        logger.info("Cache initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize cache: {str(e)}")
        raise

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def monitor_cache(f):
    """Decorator to monitor and manage cache memory usage"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global last_cleanup_time
        try:
            current_time = time.time()
            if current_time - last_cleanup_time > 300:  # 5 minutes
                memory_usage = get_memory_usage()
                if memory_usage > 500:  # 500MB threshold
                    gc.collect()
                    cache.clear()
                    last_cleanup_time = current_time
                    logger.info(
                        "Cache cleanup performed. Memory usage: %.2f MB",
                        get_memory_usage()
                    )
        except Exception as e:
            logger.error(f"Error in cache monitoring: {str(e)}")
        return f(*args, **kwargs)
    return decorated_function
