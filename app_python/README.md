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

### Local Development

```bash
# Default configuration
python app.py

# With custom port
PORT=8080 python app.py

# With custom host and port
HOST=127.0.0.1 PORT=3000 python app.py
```

### Docker Container

```bash
# Build the Docker image
docker build -t devops-info-service .

# Run the container
docker run -d -p 5000:5000 --name devops-info devops-info-service

# Run with custom port mapping
docker run -d -p 8080:5000 --name devops-info devops-info-service
```

### Pull from Docker Hub

```bash
# Pull the image
docker pull [your-dockerhub-username]/devops-info-service:latest

# Run the container
docker run -d -p 5000:5000 [your-dockerhub-username]/devops-info-service:latest
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
├── Dockerfile          # Docker container configuration
├── .dockerignore       # Files to exclude from Docker build
├── requirements.txt    # Dependencies
├── .gitignore         # Git ignore rules
├── README.md          # This file
├── tests/             # Unit tests (Lab 3)
│   └── __init__.py
└── docs/              # Lab documentation
    ├── LAB01.md       # Lab 1 submission
    ├── LAB02.md       # Lab 2 submission (Docker)
    └── screenshots/   # Proof screenshots
```

## Testing

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```
