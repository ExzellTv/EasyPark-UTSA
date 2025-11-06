# tests/test_parking.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test that the root endpoint returns the dashboard."""
    response = client.get("/")
    assert response.status_code == 200

def test_parking_spots_endpoint():
    """Test that the parking spots endpoint returns valid JSON."""
    response = client.get("/parking/spots")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "spots" in data
    assert "total" in data["summary"]
    assert "occupied" in data["summary"]
    assert "available" in data["summary"]

def test_parking_spots_debug_endpoint():
    """Test that the debug endpoint returns additional metrics."""
    response = client.get("/parking/spots?debug=true")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "spots" in data

def test_video_feed_endpoint():
    """Test that the video feed endpoint returns a stream."""
    response = client.get("/parking/video_feed")
    assert response.status_code == 200
    assert response.headers["content-type"] == "multipart/x-mixed-replace; boundary=frame"
