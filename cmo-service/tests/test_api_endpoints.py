from fastapi.testclient import TestClient
from cmo_service.main import app
import pytest

client = TestClient(app)

def test_job_submission_api():
    """Test CMO's job submission endpoint"""
    # This is CMO's responsibility
    response = client.post(
        "/api/v1/jobs",
        json={
            "required_memory": 32,
            "max_price": 2.5,
            "docker_image": "pytorch/pytorch:latest",
            "command": ["python", "train.py"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "status" in data

def test_gpu_summary_api():
    """Test CMO's GPU summary endpoint"""
    # This is CMO's responsibility
    response = client.get("/api/v1/gpus/summary")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_gpus" in data
    assert "providers" in data 