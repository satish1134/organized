from flask import Flask
from config import Config
from app.utils.cache import cache, init_cache
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize cache
    init_cache(app)
    
    # Configure logging
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        # Set up file handler
        file_handler = RotatingFileHandler(
            'logs/organized.log', 
            maxBytes=10240, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # Set up app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Organized startup')
        
        # Set up package logger
        package_logger = logging.getLogger('package')
        package_logger.setLevel(logging.INFO)
        package_logger.addHandler(file_handler)
    
    # Register blueprints
    from app.routes import dashboard, package
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(package.bp, url_prefix='/package')

    return app
