"""
Unit tests for DevOps Info Service
"""

import pytest
from datetime import datetime, timezone
from app import app, get_uptime, get_system_info

# Create a test client for the app
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestMainEndpoint:
    """Tests for the main endpoint (GET /)"""
    
    def test_endpoint_exists(self, client):
        """Test that main endpoint returns 200 OK"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_response_is_json(self, client):
        """Test that response is valid JSON"""
        response = client.get('/')
        assert response.content_type == 'application/json'
    
    def test_service_info_structure(self, client):
        """Test that service info contains required fields"""
        response = client.get('/')
        data = response.get_json()
        
        # Check service section
        assert 'service' in data
        service = data['service']
        assert service['name'] == 'devops-info-service'
        assert service['version'] == '1.0.0'
        assert service['description'] == 'DevOps course info service'
        assert service['framework'] == 'Flask'
    
    def test_system_info_structure(self, client):
        """Test that system info contains required fields"""
        response = client.get('/')
        data = response.get_json()
        
        # Check system section
        assert 'system' in data
        system = data['system']
        assert 'hostname' in system
        assert 'platform' in system
        assert 'platform_version' in system
        assert 'architecture' in system
        assert 'cpu_count' in system
        assert 'python_version' in system
    
    def test_runtime_info_structure(self, client):
        """Test that runtime info contains required fields"""
        response = client.get('/')
        data = response.get_json()
        
        # Check runtime section
        assert 'runtime' in data
        runtime = data['runtime']
        assert 'uptime_seconds' in runtime
        assert 'uptime_human' in runtime
        assert 'current_time' in runtime
        assert 'timezone' in runtime
        assert runtime['timezone'] == 'UTC'
        
        # Verify timestamp is ISO format
        import re
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3,6}\+\d{2}:\d{2}$'
        assert re.match(iso_pattern, runtime['current_time']) is not None
    
    def test_request_info_structure(self, client):
        """Test that request info is captured"""
        response = client.get('/')
        data = response.get_json()
        
        # Check request section
        assert 'request' in data
        request = data['request']
        assert 'client_ip' in request
        assert 'user_agent' in request
        assert 'method' in request
        assert 'path' in request
        assert request['method'] == 'GET'
        assert request['path'] == '/'
    
    def test_endpoints_list(self, client):
        """Test that endpoints list is returned"""
        response = client.get('/')
        data = response.get_json()
        
        # Check endpoints section
        assert 'endpoints' in data
        endpoints = data['endpoints']
        assert len(endpoints) == 2
        
        # Verify both endpoints are listed
        endpoint_paths = [e['path'] for e in endpoints]
        assert '/' in endpoint_paths
        assert '/health' in endpoint_paths

class TestHealthEndpoint:
    """Tests for the health endpoint (GET /health)"""
    
    def test_endpoint_exists(self, client):
        """Test that health endpoint returns 200 OK"""
        response = client.get('/health')
        assert response.status_code == 200
    
    def test_health_response_structure(self, client):
        """Test that health endpoint returns correct structure"""
        response = client.get('/health')
        data = response.get_json()
        
        assert 'status' in data
        assert 'timestamp' in data
        assert 'uptime_seconds' in data
        assert data['status'] == 'healthy'
    
    def test_health_timestamp_format(self, client):
        """Test that health timestamp is ISO format"""
        response = client.get('/health')
        data = response.get_json()
        
        import re
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3,6}\+\d{2}:\d{2}$'
        assert re.match(iso_pattern, data['timestamp']) is not None
    
    def test_uptime_is_positive(self, client):
        """Test that uptime is a positive number"""
        response = client.get('/health')
        data = response.get_json()
        
        assert isinstance(data['uptime_seconds'], int)
        assert data['uptime_seconds'] >= 0

class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_error(self, client):
        """Test that non-existent endpoint returns 404 with JSON"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert 'error' in data
        assert 'Not Found' in data['error']
        assert 'available_endpoints' in data

class TestHelperFunctions:
    """Tests for helper functions"""
    
    def test_get_system_info_structure(self):
        """Test that get_system_info returns correct structure"""
        system_info = get_system_info()
        
        assert isinstance(system_info, dict)
        assert 'hostname' in system_info
        assert 'platform' in system_info
        assert 'platform_version' in system_info
        assert 'architecture' in system_info
        assert 'cpu_count' in system_info
        assert 'python_version' in system_info
        
        # Check types
        assert isinstance(system_info['hostname'], str)
        assert isinstance(system_info['platform'], str)
        assert isinstance(system_info['cpu_count'], int)
        assert isinstance(system_info['python_version'], str)
    
    def test_get_uptime_structure(self):
        """Test that get_uptime returns correct structure"""
        uptime = get_uptime()
        
        assert isinstance(uptime, dict)
        assert 'seconds' in uptime
        assert 'human' in uptime
        
        # Check types
        assert isinstance(uptime['seconds'], int)
        assert isinstance(uptime['human'], str)
        
        # Verify human format contains "hours" and "minutes"
        assert "hour" in uptime['human'] or "hours" in uptime['human']
        assert "minute" in uptime['human'] or "minutes" in uptime['human']