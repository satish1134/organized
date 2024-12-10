import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    # Server configurations
    HOST = os.environ.get('HOST', '0.0.0.0')
    try:
        PORT = int(os.environ.get('PORT', 5000))
    except ValueError:
        PORT = 5000
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    
    # Database configurations
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', 5433)),
        'user': os.environ.get('DB_USER', 'default_user'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'database': os.environ.get('DB_NAME', 'default_db'),
        'tlsmode': os.environ.get('DB_TLS_MODE', 'disable')
    }
    
    # Package monitoring configuration (new addition)
    MONITORED_PACKAGES = [
        "pandas", "pydantic", "numpy", "requests", "flask",
        "sqlalchemy", "pytest", "django", "tensorflow",
        "pytorch", "scikit-learn", "matplotlib", "seaborn",
        "beautifulsoup4", "fastapi", "celery", "redis",
        "psycopg2-binary", "boto3", "pillow", "opencv-python"
    ]
    
    # Cache settings
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))
    CACHE_THRESHOLD = int(os.environ.get('CACHE_THRESHOLD', 1000))
    CACHE_KEY_PREFIX = "dashboard_"
    
    # Memory management
    CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', 300))  # 5 minutes
    MEMORY_THRESHOLD = int(os.environ.get('MEMORY_THRESHOLD', 500))  # MB
    
    # Path configurations
    BASE_DIR = Path(__file__).parent
    LOG_DIR = BASE_DIR / 'logs'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Package monitoring settings (new addition)
    PYPI_API_URL = "https://pypi.org/pypi/{package}/json"
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 30))  # seconds
    API_RETRY_ATTEMPTS = int(os.environ.get('API_RETRY_ATTEMPTS', 3))
    
    # Session configurations
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('SESSION_LIFETIME', 3600))  # 1 hour
    
    @classmethod
    def init_app(cls, app):
        """Initialize application configuration"""
        # Create logs directory if it doesn't exist
        cls.LOG_DIR.mkdir(exist_ok=True)
        
        # Validate critical configurations
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-key-please-change':
            if cls.DEBUG:
                print("Warning: Using default SECRET_KEY. This is insecure in production.")
            else:
                raise ValueError("No SECRET_KEY set in environment variables")
        
        # Validate database configuration
        if not cls.DB_CONFIG['password'] and not cls.DEBUG:
            raise ValueError("No database password set in production environment")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    # Use separate test database
    DB_CONFIG = Config.DB_CONFIG.copy()
    DB_CONFIG['database'] = os.environ.get('TEST_DB_NAME', 'test_db')

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Add production-specific initialization here
        assert not cls.DEBUG, 'DEBUG must be False in production'
        assert cls.SECRET_KEY != 'dev-key-please-change', 'Change SECRET_KEY in production'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Create a separate variable for direct access to MONITORED_PACKAGES
MONITORED_PACKAGES = Config.MONITORED_PACKAGES
