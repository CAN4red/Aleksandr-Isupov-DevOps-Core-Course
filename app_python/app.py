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
from pythonjsonlogger import jsonlogger

# Initialize Flask application
app = Flask(__name__)

# Configuration from environment variables
load_dotenv('.env')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Application start time (in UTC)
START_TIME = datetime.now(timezone.utc)

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
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    logger.info("Processing main endpoint request", 
                extra={
                    'method': request.method,
                    'path': request.path,
                    'client_ip': client_ip,
                    'user_agent': user_agent
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
            'timezone': 'UTC'
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
            {'path': '/health', 'method': 'GET', 'description': 'Health check'}
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


@app.route('/health')
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
                    'start_time': START_TIME.isoformat()
                })

    app.run(host=HOST, port=PORT, debug=DEBUG)
