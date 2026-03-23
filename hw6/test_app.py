import pytest
import http.client
import threading
import time
import os
import app

@pytest.fixture(scope="module", autouse=True)
def setup_env():
    os.environ["INFLUX_URL"] = "http://localhost:8086"
    os.environ["INFLUX_TOKEN"] = "test"
    os.environ["INFLUX_ORG"] = "test"
    os.environ["INFLUX_BUCKET"] = "test"

@pytest.fixture(scope="module")
def server():
    server_thread = threading.Thread(target=app.main, daemon=True)
    server_thread.start()
    time.sleep(2)
    yield

def test_index_page(server):
    conn = http.client.HTTPConnection("localhost", app.PORT)
    conn.request("GET", "/")
    response = conn.getresponse()
    assert response.status == 200
    data = response.read().decode("utf-8")
    assert "Polkadot Analytics" in data
    assert "form" in data

def test_calculate_no_params(server):
    conn = http.client.HTTPConnection("localhost", app.PORT)
    conn.request("GET", "/calculate")
    response = conn.getresponse()
    assert response.status == 400

def test_calculate_with_params(server):
    conn = http.client.HTTPConnection("localhost", app.PORT)
    conn.request("GET", "/calculate?hours_ago=1")
    response = conn.getresponse()
    assert response.status == 200
    data = response.read().decode("utf-8")
    assert "No data found" in data or "Results for DOT" in data