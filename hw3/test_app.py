import pytest
import http.client
import threading
import time
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import app

TEST_LOG_FILE = os.path.join(os.path.dirname(__file__), "test_service.log")


@pytest.fixture(scope="module")
def server():
    app.LOG_FILE = TEST_LOG_FILE
    os.environ["LOG_FILE"] = TEST_LOG_FILE
    
    if os.path.exists(TEST_LOG_FILE):
        os.remove(TEST_LOG_FILE)
    
    server_thread = threading.Thread(target=app.main, daemon=True)
    server_thread.start()
    
    time.sleep(3)
    
    yield
    
    if os.path.exists(TEST_LOG_FILE):
        os.remove(TEST_LOG_FILE)


def test_server_starts_and_logs(server):
    assert os.path.exists(TEST_LOG_FILE), f"Log file should exist at {TEST_LOG_FILE}"
    
    with open(TEST_LOG_FILE, "r") as f:
        content = f.read()
        assert f"Service started on port {app.PORT}" in content


def test_index_endpoint_returns_logs(server):
    conn = http.client.HTTPConnection("localhost", app.PORT, timeout=10)
    
    try:
        conn.request("GET", "/")
        response = conn.getresponse()
        
        assert response.status == 200
        assert response.getheader("Content-type").startswith("text/html")
        
        data = response.read().decode("utf-8")
        assert "<html>" in data
        assert "Last 100 logs" in data
        
    finally:
        conn.close()


def test_log_file_created(server):
    assert os.path.exists(TEST_LOG_FILE), f"Log file should exist at {TEST_LOG_FILE}"
    assert os.path.getsize(TEST_LOG_FILE) > 0