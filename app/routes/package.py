from flask import Blueprint, render_template, jsonify
import requests
from datetime import datetime
import pytz
import traceback
import logging
from config import MONITORED_PACKAGES

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

package_bp = Blueprint('package', __name__)

@package_bp.route('/')
@package_bp.route('/package-parser')
def package_parser():
    """Route to render the package parser page"""
    try:
        packages = []
        notifications = []
        errors = []
        
        logger.info(f"Starting package version check for {len(MONITORED_PACKAGES)} packages")
        logger.debug(f"Packages to check: {MONITORED_PACKAGES}")
        
        if not MONITORED_PACKAGES:
            logger.warning("No packages configured in MONITORED_PACKAGES")
            return render_template(
                'package_parser.html',
                packages=[],
                notifications=[],
                total_packages=0,
                successful_packages=0,
                failed_packages=0
            )
        
        for package_name in MONITORED_PACKAGES:
            try:
                logger.info(f"Processing package: {package_name}")
                package_info = get_package_info(package_name)
                
                if package_info:
                    # Store the actual datetime object for sorting
                    packages.append(package_info)
                    logger.info(f"Successfully processed {package_name}")
                    
                    # Add notification if package has an update
                    if package_info.get('has_update'):
                        notifications.append({
                            'type': 'info',
                            'message': f"Update available for {package_name}: {package_info['version']}",
                            'package_name': package_name,
                            'timestamp': datetime.now(pytz.UTC).isoformat()
                        })
                else:
                    error_msg = f"Failed to fetch information for {package_name}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error processing {package_name}: {str(e)}"
                logger.error(f"{error_msg}\n{traceback.format_exc()}")
                errors.append(error_msg)
                continue
        
        # Sort packages by last update time (newest first)
        packages.sort(key=lambda x: datetime.strptime(x['last_update'].replace(' EST', ''), '%Y-%m-%d %H:%M:%S'), reverse=True)
        
        logger.info(f"Successfully processed {len(packages)} packages")
        logger.debug(f"Package data: {packages}")
        
        if errors:
            notifications.extend([{
                'type': 'error', 
                'message': error,
                'package_name': 'System',
                'timestamp': datetime.now(pytz.UTC).isoformat()
            } for error in errors])
        
        return render_template(
            'package_parser.html',
            packages=packages,
            notifications=notifications,
            total_packages=len(MONITORED_PACKAGES),
            successful_packages=len(packages),
            failed_packages=len(errors)
        )
                             
    except Exception as e:
        error_msg = f"Critical error in package parser: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return render_template(
            'package_parser.html',
            packages=[],
            notifications=[{
                'type': 'error', 
                'message': error_msg,
                'package_name': 'System',
                'timestamp': datetime.now(pytz.UTC).isoformat()
            }],
            total_packages=0,
            successful_packages=0,
            failed_packages=1
        )

def get_package_info(package_name):
    """Get package information from PyPI"""
    logger.info(f"Fetching info for package: {package_name}")
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        logger.debug(f"Making request to: {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        info = data['info']
        releases = data['releases']
        
        # Get latest version info
        latest_version = info['version']
        latest_release = releases.get(latest_version, [{}])[0]
        
        logger.info(f"Latest version for {package_name}: {latest_version}")
        
        # Convert upload time to EST
        upload_time = latest_release.get('upload_time', '')
        if upload_time:
            # Parse the upload time
            upload_time = datetime.strptime(upload_time, '%Y-%m-%dT%H:%M:%S')
            # Convert to EST timezone
            est = pytz.timezone('America/New_York')
            upload_time = pytz.utc.localize(upload_time).astimezone(est)
            # Format in desired format with EST
            formatted_time = f"{upload_time.strftime('%Y-%m-%d %H:%M:%S')} EST"
        else:
            upload_time = datetime.now(pytz.UTC)
            est = pytz.timezone('America/New_York')
            upload_time = upload_time.astimezone(est)
            formatted_time = f"{upload_time.strftime('%Y-%m-%d %H:%M:%S')} EST"
            logger.warning(f"No upload time found for {package_name}, using current time")
        
        package_info = {
            'name': package_name,
            'version': latest_version,
            'last_update': formatted_time,
            'status': get_package_status(upload_time),
            'has_update': False,
            'link': f"https://pypi.org/project/{package_name}/",
            'description': info.get('summary', 'No description available'),
            'author': info.get('author', 'Unknown'),
            'license': info.get('license', 'Not specified'),
            'home_page': info.get('home_page', ''),
            'requires_python': info.get('requires_python', 'Not specified')
        }
        
        logger.debug(f"Package info for {package_name}: {package_info}")
        return package_info
        
    except requests.RequestException as e:
        logger.error(f"Request error for {package_name}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error processing {package_name}: {str(e)}\n{traceback.format_exc()}")
        return None

def get_package_status(update_time):
    """Determine package status based on last update time"""
    try:
        now = datetime.now(pytz.UTC)
        if not update_time.tzinfo:
            update_time = pytz.UTC.localize(update_time)
            
        days_since_update = (now - update_time).days
        
        if days_since_update < 1:
            return 'Recent'
        elif days_since_update < 30:
            return 'Active'
        elif days_since_update < 180:
            return 'Stable'
        else:
            return 'Inactive'
    except Exception as e:
        logger.error(f"Error determining package status: {str(e)}")
        return 'Unknown'

@package_bp.route('/api/check_package_versions', methods=['GET'])
def check_package_versions():
    """API endpoint for checking package versions"""
    try:
        packages = []
        for package_name in MONITORED_PACKAGES:
            package_info = get_package_info(package_name)
            if package_info:
                packages.append(package_info)
        return jsonify({'packages': packages})
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@package_bp.route('/api/notifications', methods=['GET'])
def get_notifications():
    """API endpoint for notifications"""
    try:
        notifications = []
        for package_name in MONITORED_PACKAGES:
            package_info = get_package_info(package_name)
            if package_info and package_info.get('has_update'):
                notifications.append({
                    'type': 'info',
                    'message': f"Update available for {package_name}: {package_info['version']}",
                    'package_name': package_name,
                    'timestamp': datetime.now(pytz.UTC).isoformat()
                })
        return jsonify({'notifications': notifications})
    except Exception as e:
        logger.error(f"Notifications API error: {str(e)}")
        return jsonify({'error': str(e)}), 500
