import vertica_python
import os
import logging
import time
import traceback
from cryptography.fernet import Fernet
from flask_caching import Cache
import psutil  # Add this import for memory usage monitoring

logger = logging.getLogger('dashboard')

def get_memory_usage():
    """Get current memory usage of the application"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert to MB

def load_key():
    """Load the secret key from file"""
    try:
        logger.debug("Attempting to load secret key")
        with open("secret.key", "rb") as key_file:
            key = key_file.read()
        logger.debug("Secret key loaded successfully")
        return key
    except Exception as e:
        logger.error("Error loading secret key: %s", str(e), exc_info=True)
        raise

def decrypt_env():
    """Decrypt environment variables using the secret key"""
    try:
        start_time = time.time()
        logger.debug("Starting environment decryption")
        
        key = load_key()
        f = Fernet(key)
        
        config = {}
        with open('.env', 'r') as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                try:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key_name, encrypted_value = parts
                        key_name = key_name.strip()
                        encrypted_value = encrypted_value.strip()
                        if key_name and encrypted_value:
                            decrypted_value = f.decrypt(encrypted_value.encode()).decode()
                            config[key_name] = decrypted_value
                except Exception as e:
                    logger.error(f"Error processing line '{line}': {e}")
                    continue
        
        duration = time.time() - start_time
        logger.debug("Environment decryption completed in %.3f seconds", duration)
        return config
    except Exception as e:
        logger.error(f"Error in decrypt_env: {str(e)}", exc_info=True)
        raise

# Get decrypted database configuration
DB_CONFIG = decrypt_env()

def get_db_connection():
    """Create a Vertica database connection."""
    start_time = time.time()
    try:
        logger.debug("Attempting database connection to %s:%s", 
                    DB_CONFIG['HOST'], DB_CONFIG['PORT'])
        
        conn_info = {
            'host': DB_CONFIG['HOST'],
            'port': int(DB_CONFIG['PORT']),
            'user': DB_CONFIG['USER'],
            'password': DB_CONFIG['PASSWORD'],
            'database': DB_CONFIG['DATABASE'],
            'tlsmode': 'disable'
        }
        
        conn = vertica_python.connect(**conn_info)
        duration = time.time() - start_time
        logger.info("Database connection established in %.2f seconds", duration)
        return conn
    except Exception as e:
        logger.error("Database connection error: %s\n%s", 
                    str(e), traceback.format_exc())
        raise

def get_grouped_data():
    """Get grouped DAG data from database."""
    start_time = time.time()
    query_start_time = None
    try:
        logger.debug("Starting get_grouped_data function")
        
        with get_db_connection() as conn:
            cur = conn.cursor('dict')
            
            # First, let's check if the table exists and has data
            check_query = """
                SELECT COUNT(*) as count 
                FROM public.dag_data
            """
            
            logger.debug("Checking if table has data")
            cur.execute(check_query)
            count = cur.fetchone()['count']
            logger.debug(f"Total records in table: {count}")

            query = """
                SELECT 
                    SUBJECT_AREA,
                    DAG_NAME,
                    STATUS,
                    MODIFIED_TS,
                    DAG_START_TIME,
                    DAG_END_TIME,
                    ELAPSED_TIME
                FROM public.dag_data
                ORDER BY 
                    SUBJECT_AREA,
                    CASE 
                        WHEN MODIFIED_TS IS NULL THEN 1 
                        ELSE 0 
                    END,
                    MODIFIED_TS DESC
            """
            
            logger.debug("Executing main query")
            query_start_time = time.time()
            cur.execute(query)
            query_duration = time.time() - query_start_time
            
            results = cur.fetchall()
            logger.info("Retrieved %d records in %.2f seconds", 
                       len(results), query_duration)
            
            # Group results by subject area
            grouped_data = {}
            for row in results:
                subject_area = row['SUBJECT_AREA']
                if subject_area not in grouped_data:
                    grouped_data[subject_area] = []
                grouped_data[subject_area].append({
                    'subject_area': row['SUBJECT_AREA'],
                    'dag_name': row['DAG_NAME'],
                    'status': row['STATUS'].lower() if row['STATUS'] else 'yet_to_start',
                    'modified_ts': row['MODIFIED_TS'],
                    'dag_start_time': row['DAG_START_TIME'],
                    'dag_end_time': row['DAG_END_TIME'],
                    'elapsed_time': row['ELAPSED_TIME']
                })
            
            duration = time.time() - start_time
            logger.debug("get_grouped_data completed in %.2f seconds", duration)
            # Remove or comment out this line to prevent logging the entire dataset
            # logger.debug("Grouped data: %s", grouped_data)  
            return grouped_data
            
    except Exception as e:
        logger.error("Error in get_grouped_data:\nError: %s\nTraceback: %s\nQuery duration: %.2f seconds", 
                    str(e), traceback.format_exc(),
                    time.time() - query_start_time if query_start_time else 0)
        return {}




