# DevOps Info Service

A web application providing system information and health status.

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
# Clone the project
git clone git@github.com:CAN4red/Aleksandr-Isupov-DevOps-Core-Course.git

# Navigate to the root
cd Aleksandr-Isupov-DevOps-Core-Course/app_python

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
# Default configuration
python app.py

# With custom port
PORT=8080 python app.py

# With custom host and port
HOST=127.0.0.1 PORT=3000 python app.py
```

## API Endpoints

### `GET /`

Returns service and system information.

**Response:**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Linux",
    "platform_version": "Ubuntu 24.04",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-07T14:30:00.000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    { "path": "/", "method": "GET", "description": "Service information" },
    { "path": "/health", "method": "GET", "description": "Health check" }
  ]
}
```

### `GET /health`

Health check for monitoring.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

## Configuration

| Variable | Default   | Description                  |
| -------- | --------- | ---------------------------- |
| `HOST`   | `0.0.0.0` | Network interface to bind to |
| `PORT`   | `5000`    | Port to listen on            |
| `DEBUG`  | `false`   | Enable debug mode            |

## Project Structure

```
app_python/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── .gitignore         # Git ignore rules
├── README.md          # This file
├── tests/             # Unit tests (Lab 3)
│   └── __init__.py
└── docs/              # Lab documentation
    ├── LAB01.md       # Lab submission
    └── screenshots/   # Proof screenshots
```

## Testing

```bash
# Test endpoints
curl http://localhost:5000/
curl http://localhost:5000/health
```

```

**Note:** The "Running the Application" section was already present in the previous version, but I've kept it in this minimal version to ensure it's included as required. The README now contains all the essential sections mentioned in the spec: Overview (implied), Prerequisites, Installation, Running the Application, API Endpoints, Configuration, Project Structure, and Testing.
```
