"""
DevOps Info Service - Lab 1 & Lab 18
A simple Flask API for demonstrating reproducible builds with Nix.
"""

from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def index():
    """Main endpoint with service information."""
    return jsonify({
        "service": "DevOps Info Service",
        "version": "1.0.0",
        "description": "A simple Flask API for DevOps Core Course",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


@app.route('/info')
def info():
    """Detailed service information."""
    return jsonify({
        "name": "DevOps Info Service",
        "version": "1.0.0",
        "author": "DevOps Core Course Student",
        "lab": "Lab 1 & Lab 18",
        "build_system": "Nix (reproducible)",
        "endpoints": ["/", "/health", "/info"]
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
