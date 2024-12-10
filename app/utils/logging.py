import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

def setup_logging(log_dir):
    """Configure logging with both file and console handlers"""
    logger = logging.getLogger('dashboard')
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] '
        '[%(filename)s:%(lineno)d] '
        '%(message)s - '
        'Function: %(funcName)s'
    )
    
    # Daily rotating file handler for general logs
    daily_handler = TimedRotatingFileHandler(
        log_dir / 'dashboard.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    daily_handler.setFormatter(formatter)
    daily_handler.setLevel(logging.INFO)
    
    # Error log file handler
    error_handler = RotatingFileHandler(
        log_dir / 'error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    logger.handlers.clear()
    
    # Add all handlers
    logger.addHandler(daily_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger
