"""
DevOps Info Service
A web application providing system information and health status.
"""

import os
import socket
import platform
import logging
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import functools

# Initialize Flask application
app = Flask(__name__)

# Configuration from environment variables
load_dotenv('.env')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time (in UTC)
START_TIME = datetime.now(timezone.utc)

# Visit counter file path
VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')
VISITS_COUNT = 0

# Configure JSON logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

# Set up JSON logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)

# Create console handler and set formatter
console_handler = logging.StreamHandler()
formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Remove default handlers to avoid duplicate logs
logger.propagate = False

# =============================================================================
# Visit Counter Implementation
# =============================================================================

def load_visits():
    """Load visit count from file."""
    global VISITS_COUNT
    try:
        if os.path.exists(VISITS_FILE):
            with open(VISITS_FILE, 'r') as f:
                VISITS_COUNT = int(f.read().strip())
                logger.info(f"Loaded visits count: {VISITS_COUNT}")
        else:
            VISITS_COUNT = 0
            logger.info("No visits file found, starting from 0")
    except (ValueError, IOError) as e:
        logger.error(f"Error loading visits: {e}")
        VISITS_COUNT = 0
    return VISITS_COUNT

def save_visits():
    """Save visit count to file."""
    global VISITS_COUNT
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
        # Atomic write: write to temp file then rename
        temp_file = VISITS_FILE + '.tmp'
        with open(temp_file, 'w') as f:
            f.write(str(VISITS_COUNT))
        os.replace(temp_file, VISITS_FILE)
        logger.info(f"Saved visits count: {VISITS_COUNT}")
    except IOError as e:
        logger.error(f"Error saving visits: {e}")

def increment_visits():
    """Increment and return the visit count."""
    global VISITS_COUNT
    VISITS_COUNT += 1
    save_visits()
    return VISITS_COUNT

# Load visits on startup
load_visits()

# =============================================================================
# Prometheus Metrics - RED Method Implementation
# =============================================================================

# Counter: Total HTTP requests (R - Rate, E - Errors)
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Histogram: Request duration (D - Duration)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Gauge: Active requests currently being processed
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed'
)

# Counter: Application-specific metrics
devops_info_endpoint_calls = Counter(
    'devops_info_endpoint_calls',
    'DevOps Info Service endpoint calls',
    ['endpoint']
)

# Histogram: System info collection time
devops_info_system_collection_seconds = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system information',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1)
)

# Gauge: Application uptime in seconds
app_uptime_seconds = Gauge(
    'app_uptime_seconds',
    'Application uptime in seconds'
)

# Gauge: Total visits
total_visits = Gauge(
    'total_visits',
    'Total visits to the service'
)


def track_metrics(f):
    """Decorator to track HTTP request metrics."""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        # Track active requests
        http_requests_in_progress.inc()
        
        # Track start time for duration
        start_time = time.time()
        
        # Get endpoint from request
        endpoint = request.path
        method = request.method
        
        try:
            # Execute the actual function
            response = f(*args, **kwargs)
            
            # Get status code from response
            if isinstance(response, tuple):
                status_code = response[1] if len(response) > 1 else 200
            else:
                status_code = 200
            
            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            
            # Track endpoint-specific calls
            devops_info_endpoint_calls.labels(endpoint=endpoint).inc()
            
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status='500'
            ).inc()
            
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            raise
            
        finally:
            # Decrement active requests
            http_requests_in_progress.dec()
    
    return wrapped


def update_uptime():
    """Update the uptime gauge."""
    app_uptime_seconds.set(get_uptime()['seconds'])
    total_visits.set(VISITS_COUNT)


@app.route('/metrics')
def metrics():
    """
    Prometheus metrics endpoint.
    Returns all metrics in Prometheus exposition format.
    """
    # Update dynamic metrics before exposing
    update_uptime()
    
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


def get_uptime():
    """
    Calculate application uptime.

    Returns:
        dict: Uptime in seconds and human-readable format
    """
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())

    # Calculate human-readable format
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    human_readable = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"

    return {
        'seconds': seconds,
        'human': human_readable
    }


def get_system_info():
    """
    Collect comprehensive system information.

    Returns:
        dict: System information
    """
    start_time = time.time()
    
    result = {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }
    
    # Track system info collection time
    devops_info_system_collection_seconds.observe(time.time() - start_time)
    
    return result


@app.route('/')
@track_metrics
def index():
    """
    Main endpoint - returns comprehensive service and system information.
    Increments visit counter on each request.
    """
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    # Increment visit counter
    visits = increment_visits()
    
    logger.info("Processing main endpoint request", 
                extra={
                    'method': request.method,
                    'path': request.path,
                    'client_ip': client_ip,
                    'user_agent': user_agent,
                    'visits': visits
                })

    # Get current time in ISO format with timezone
    current_time = datetime.now(timezone.utc)

    response = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': get_uptime()['seconds'],
            'uptime_human': get_uptime()['human'],
            'current_time': current_time.isoformat(),
            'timezone': 'UTC',
            'visits': visits
        },
        'request': {
            'client_ip': client_ip,
            'user_agent': user_agent,
            'method': request.method,
            'path': request.path
        },
        'endpoints': [
            {
                'path': '/',
                'method': 'GET',
                'description': 'Service information'
            },
            {'path': '/health', 'method': 'GET', 'description': 'Health check'},
            {'path': '/visits', 'method': 'GET', 'description': 'Visit counter'}
        ]
    }

    logger.info("Main endpoint request processed successfully",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': 200,
                    'client_ip': client_ip
                })

    return jsonify(response)


@app.route('/visits')
@track_metrics
def visits():
    """
    Visit counter endpoint - returns current visit count.
    """
    client_ip = request.remote_addr
    
    logger.info("Processing visits endpoint request",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'client_ip': client_ip
                })
    
    visits_count = increment_visits()
    
    response = {
        'visits': visits_count,
        'message': 'Total visits to this service',
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Main endpoint'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check'},
            {'path': '/visits', 'method': 'GET', 'description': 'Visit counter'}
        ]
    }
    
    logger.info("Visits endpoint request processed successfully",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': 200,
                    'client_ip': client_ip,
                    'visits': visits_count
                })
    
    return jsonify(response)


@app.route('/health')
@track_metrics
def health():
    """
    Health check endpoint for monitoring.
    """
    client_ip = request.remote_addr
    
    logger.debug("Processing health check request",
                 extra={
                     'method': request.method,
                     'path': request.path,
                     'client_ip': client_ip
                 })

    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }

    logger.debug("Health check request processed successfully",
                 extra={
                     'method': request.method,
                     'path': request.path,
                     'status_code': 200,
                     'client_ip': client_ip
                 })

    return jsonify(health_status), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    client_ip = request.remote_addr
    
    logger.warning("404 Not Found",
                   extra={
                       'method': request.method,
                       'path': request.path,
                       'client_ip': client_ip,
                       'status_code': 404
                   })
    
    # Track 404 errors
    http_requests_total.labels(
        method=request.method,
        endpoint=request.path,
        status='404'
    ).inc()
    
    return jsonify({
        'error': 'Not Found',
        'message': f'The requested endpoint {request.path} does not exist',
        'available_endpoints': [
            {
                'path': '/',
                'method': 'GET',
                'description': 'Service information'
            },
            {'path': '/health', 'method': 'GET', 'description': 'Health check'},
            {'path': '/visits', 'method': 'GET', 'description': 'Visit counter'}
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    logger.error("500 Internal Server Error",
                 extra={
                     'error_message': str(error),
                     'status_code': 500
                 })
    
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred. Please try again later.'
    }), 500


if __name__ == '__main__':
    logger.info("Starting DevOps Info Service",
                extra={
                    'host': HOST,
                    'port': PORT,
                    'debug': DEBUG,
                    'start_time': START_TIME.isoformat(),
                    'visits_file': VISITS_FILE
                })

    app.run(host=HOST, port=PORT, debug=DEBUG)
