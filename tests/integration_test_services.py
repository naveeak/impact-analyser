"""
Integration Tests - Service-to-Service Communication
"""
import pytest
import asyncio
import httpx
from datetime import datetime

# These tests require services to be running
BASE_URL = "http://localhost:3000/api/v1"
REPO_SCANNER_URL = "http://localhost:8001"
IMPACT_ANALYZER_URL = "http://localhost:8003"
AI_ORCHESTRATOR_URL = "http://localhost:8002"


@pytest.fixture
async def http_client():
    """Create HTTP client for API calls"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.mark.asyncio
async def test_repository_scanner_health(http_client):
    """Test repository scanner health endpoint"""
    response = await http_client.get(f"{REPO_SCANNER_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'repository-scanner'


@pytest.mark.asyncio
async def test_impact_analyzer_health(http_client):
    """Test impact analyzer health endpoint"""
    response = await http_client.get(f"{IMPACT_ANALYZER_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'


@pytest.mark.asyncio
async def test_ai_orchestrator_health(http_client):
    """Test AI orchestrator health endpoint"""
    response = await http_client.get(f"{AI_ORCHESTRATOR_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'


@pytest.mark.asyncio
async def test_impact_analysis_workflow(http_client):
    """Test complete impact analysis workflow"""
    payload = {
        "change_description": "Modified payment processing logic in checkout module",
        "affected_files": [
            "src/payment/processor.py",
            "src/api/checkout.py"
        ],
        "repo_id": "test_repo_123",
        "branch": "main"
    }
    
    response = await http_client.post(
        f"{AI_ORCHESTRATOR_URL}/api/v1/analyze",
        json=payload
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['status'] in ['completed', 'processing']
    assert 'analysis_id' in data
    assert 'impact_analysis' in data
    assert 'criticality_scores' in data
    assert 'test_plan' in data


@pytest.mark.asyncio
async def test_graph_analysis_endpoint(http_client):
    """Test graph analysis endpoint"""
    # Create a simple graph
    graph_data = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "file_a"},
            {"id": "file_b"},
            {"id": "file_c"}
        ],
        "links": [
            {"source": "file_a", "target": "file_b"},
            {"source": "file_b", "target": "file_c"}
        ]
    }
    
    payload = {
        "changed_files": ["file_a"],
        "graph_data": graph_data
    }
    
    response = await http_client.post(
        f"{IMPACT_ANALYZER_URL}/api/v1/analyze/impact",
        json=payload
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'impacted_components' in data
    assert 'risk_level' in data
    assert 'recommendations' in data


@pytest.mark.asyncio
async def test_error_handling_invalid_input(http_client):
    """Test error handling with invalid input"""
    payload = {
        "change_description": "",  # Empty description
        "affected_files": [],
        "repo_id": "test_repo",
        "branch": "main"
    }
    
    response = await http_client.post(
        f"{AI_ORCHESTRATOR_URL}/api/v1/analyze",
        json=payload
    )
    
    # Should reject empty change_description
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_concurrent_requests(http_client):
    """Test handling of concurrent requests"""
    payload = {
        "change_description": "Test concurrent requests",
        "affected_files": ["test.py"],
        "repo_id": "test_repo",
        "branch": "main"
    }
    
    # Create multiple concurrent requests
    tasks = [
        http_client.post(
            f"{AI_ORCHESTRATOR_URL}/api/v1/analyze",
            json=payload
        )
        for _ in range(3)
    ]
    
    responses = await asyncio.gather(*tasks)
    
    # All should succeed
    for response in responses:
        assert response.status_code in [200, 202]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
