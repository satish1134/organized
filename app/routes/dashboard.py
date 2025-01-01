from flask import Blueprint, jsonify, request, render_template, current_app
from app.utils.db import get_grouped_data
from app import cache
import logging
import time
import traceback
import os
from functools import wraps

logger = logging.getLogger('dashboard')
bp = Blueprint('dashboard', __name__)

def monitor_cache(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"Cache request for {f.__name__} took {duration:.2f} seconds")
        return result
    return decorated_function

@bp.route('/')
def index():
    try:
        # Get grouped data
        grouped_data = get_grouped_data()
        if not grouped_data:
            return render_template('error.html', 
                                error_title='No Data Available',
                                error='No dashboard data found')
        
        # Get list of subjects
        subjects = list(grouped_data.keys())
        
        return render_template('index.html', 
                             grouped_data=grouped_data,
                             subjects=subjects)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}", exc_info=True)
        return render_template('error.html', 
                             error_title='Dashboard Error',
                             error='Failed to load dashboard'), 500

@bp.route('/dag_status')
@monitor_cache
@cache.cached(timeout=30, query_string=True)
def dag_status():
    try:
        start_time = time.time()
        logger.debug("Processing dag_status route request")
        
        subject_area = request.args.get('subject_area')
        status = request.args.get('status', '').lower()
        
        logger.debug("Request parameters - Subject Area: %s, Status: %s",
                    subject_area, status)
        
        if not subject_area or not status:
            logger.warning("Missing parameters in dag_status request")
            return jsonify({'error': 'Missing required parameters'}), 400

        grouped_data = get_grouped_data()
        
        if subject_area not in grouped_data:
            logger.info("No data found for subject area: %s", subject_area)
            return jsonify([])

        filtered_data = [
            {
                'dag_name': item['dag_name'],
                'status': item['status'],
                'dag_start_time': item['dag_start_time'],
                'dag_end_time': item['dag_end_time'],
                'modified_ts': item['modified_ts'],
                'elapsed_time': item['elapsed_time']
            }
            for item in grouped_data[subject_area]
            if item['status'].lower() == status
        ]

        duration = time.time() - start_time
        logger.info("Retrieved %d records for status request in %.2f seconds",
                   len(filtered_data), duration)
        return jsonify(filtered_data)

    except Exception as e:
        logger.error(
            "Error processing status request:\n"
            "Error: %s\n"
            "Traceback: %s",
            str(e),
            traceback.format_exc()
        )
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/package-parser')
def package_parser():
    try:
        return render_template('package_parser.html')
    except Exception as e:
        logger.error(f"Error loading package parser: {str(e)}", exc_info=True)
        return render_template('error.html',
                             error_title='Package Parser Error',
                             error='Failed to load package parser'), 500

@bp.route('/trend-analysis', endpoint='trend')
def trend():
    try:
        current_app.logger.info('Rendering trend.html...')
        return render_template('trend.html')
    except Exception as e:
        current_app.logger.error(f"Error loading trend analysis: {str(e)}", exc_info=True)
        return render_template('error.html',
                             error_title='Trend Analysis Error',
                             error='Failed to load trend analysis'), 500


# Error handlers
@bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return render_template('error.html',
                         error_title='Internal Server Error',
                         error='An unexpected error occurred'), 500

# Add this new route for testing modal functionality
@bp.route('/test-modal')
def test_modal():
    try:
        # Simulate some test data
        test_data = {
            'dag_name': 'test_dag',
            'status': 'success',
            'dag_start_time': '2024-01-01 00:00:00',
            'dag_end_time': '2024-01-01 00:01:00',
            'elapsed_time': '60 seconds'
        }
        return jsonify([test_data])
    except Exception as e:
        logger.error(f"Error in test modal: {str(e)}", exc_info=True)
        return jsonify({'error': 'Test modal error'}), 500

# Add a route to check cache status
@bp.route('/cache-status')
def cache_status():
    try:
        cache_stats = {
            'cache_type': current_app.config.get('CACHE_TYPE', 'unknown'),
            'cache_timeout': current_app.config.get('CACHE_DEFAULT_TIMEOUT', 'unknown'),
            'cache_enabled': cache.cache is not None
        }
        return jsonify(cache_stats)
    except Exception as e:
        logger.error(f"Error checking cache status: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to check cache status'}), 500

# Add a route to clear cache
@bp.route('/clear-cache')
def clear_cache():
    try:
        cache.clear()
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to clear cache'}), 500
