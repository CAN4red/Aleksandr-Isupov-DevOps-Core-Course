"""
DevOps Info Service
A web application providing system information and health status.
"""

import os
import socket
import platform
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Initialize Flask application
app = Flask(__name__)

# Configuration from environment variables
load_dotenv('.env')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time (in UTC)
START_TIME = datetime.now(timezone.utc)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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

    human_readable = f"""{hours} hour{'s' if hours != 1 else ''}
    ,{minutes} minute{'s' if minutes != 1 else ''}"""

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
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count(),
        'python_version': platform.python_version()
    }


@app.route('/')
def index():
    """
    Main endpoint - returns comprehensive service and system information.
    """
    logger.info(f"GET / from {request.remote_addr}")

    # Get current time in ISO format with timezone
    current_time = datetime.now(timezone.utc)

    # Get client IP address
    client_ip = request.remote_addr

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
            'timezone': 'UTC'
        },
        'request': {
            'client_ip': client_ip,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'method': request.method,
            'path': request.path
        },
        'endpoints': [
            {
                'path': '/',
                'method': 'GET',
                'description': 'Service information'
            },
            {'path': '/health', 'method': 'GET', 'description': 'Health check'}
        ]
    }

    return jsonify(response)


@app.route('/health')
def health():
    """
    Health check endpoint for monitoring.
    """
    logger.debug(f"GET /health from {request.remote_addr}")

    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': get_uptime()['seconds']
    }

    return jsonify(health_status), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({
        'error': 'Not Found',
        'message': f'The requested endpoint {request.path} does not exist',
        'available_endpoints': [
            {
                'path': '/',
                'method': 'GET',
                'description': 'Service information'
            },
            {'path': '/health', 'method': 'GET', 'description': 'Health check'}
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    logger.error(f"500 Internal Server Error: {str(error)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred. Please try again later.'
    }), 500


if __name__ == '__main__':
    logger.info(f"Starting DevOps Info Service on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG}")
    logger.info(f"Application started at {START_TIME.isoformat()}")

    app.run(host=HOST, port=PORT, debug=DEBUG)
