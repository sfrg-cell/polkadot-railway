import pytest
import http.client
import threading
import time
import os
import app

@pytest.fixture(scope="module", autouse=True)
def setup_env():
    os.environ["INFLUX_URL"] = "http://localhost:8086"
    os.environ["INFLUX_TOKEN"] = "test-token"
    os.environ["INFLUX_ORG"] = "test-org"
    os.environ["INFLUX_BUCKET"] = "test-bucket"
    os.environ["PORT"] = "5336"

@pytest.fixture(scope="module")
def server():
    server_thread = threading.Thread(target=app.main, daemon=True)
    server_thread.start()
    time.sleep(2)
    yield

def test_index_page_returns_200(server):
    conn = http.client.HTTPConnection("localhost", 5336)
    try:
        conn.request("GET", "/")
        response = conn.getresponse()
        assert response.status == 200
        data = response.read().decode("utf-8")
        assert "<h1>Polkadot Analytics</h1>" in data
        assert "<form" in data
    finally:
        conn.close()

def test_calculate_endpoint_structure(server):
    conn = http.client.HTTPConnection("localhost", 5336)
    try:
        conn.request("GET", "/calculate?hours_ago=1")
        response = conn.getresponse()
        assert response.status == 200
        data = response.read().decode("utf-8")
        assert "Results:" in data
    finally:
        conn.close()