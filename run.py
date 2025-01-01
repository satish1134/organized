from flask import Flask
from app.routes.dashboard import bp as dashboard_bp
from app.routes.package import package_bp
from app.routes.trend import bp as trend_bp, layout, register_callbacks, index_string
from app.utils.cache import init_cache
import os
import logging
from logging.handlers import RotatingFileHandler
from config import MONITORED_PACKAGES
from dash import Dash

# Configure logging
def setup_logging(app):
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    # Set up file handler
    file_handler = RotatingFileHandler(
        'logs/package_monitor.log', 
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    # Configure app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Package Monitor startup')

def create_app():
    # Get absolute paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(current_dir, 'app', 'templates')
    static_dir = os.path.join(current_dir, 'app', 'static')
    
    # Create Flask app instance
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Initialize cache
    init_cache(app)
    
    # Set up logging
    setup_logging(app)
    
    # Log the registration of blueprints
    app.logger.info('Registering blueprints...')
    
    # Register blueprints
    app.register_blueprint(dashboard_bp)
    app.logger.info('Dashboard blueprint registered')
    
    app.register_blueprint(package_bp)
    app.logger.info('Package blueprint registered with prefix /package')

    app.register_blueprint(trend_bp)
    app.logger.info('Trend blueprint registered with prefix /trend')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize Dash app
    app.logger.info('Initializing Dash app...')
    dash_app = Dash(__name__, server=app, url_base_pathname='/trend/dash/')
    dash_app.layout = layout
    dash_app.index_string = index_string
    register_callbacks(dash_app)
    app.logger.info('Dash app initialized')
    
    # Log available routes
    app.logger.info('Registered routes:')
    for rule in app.url_map.iter_rules():
        app.logger.info(f'Route: {rule.rule} - Endpoint: {rule.endpoint} - Methods: {rule.methods}')
    
    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f'Page not found: {error}')
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        app.logger.error(f'Unhandled Exception: {error}')
        return {'error': 'An unexpected error occurred'}, 500

if __name__ == '__main__':
    app = create_app()
    
    # Get port from environment variable or use default
    port = 5000
    
    # Get debug mode from environment variable or use default
    debug = os.environ.get('FLASK_DEBUG', '0').lower() in ['1', 'true']
    
    # Log startup configuration
    app.logger.info(f'Starting server on port {port}')
    app.logger.info(f'Debug mode: {debug}')
    app.logger.info(f'Template directory: {app.template_folder}')
    app.logger.info(f'Static directory: {app.static_folder}')
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
