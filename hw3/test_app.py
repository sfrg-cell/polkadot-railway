import pytest
import http.client
import threading
import time
import os
import sys
import app

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


@pytest.fixture
def server():

    os.environ["LOG_FILE"] = "test_service.log"


    if os.path.exists("test_service.log"):
        os.remove("test_service.log")
    
    server_thread = threading.Thread(target=app.main, daemon=True)
    server_thread.start()
    
    time.sleep(2)
    
    yield

    if os.path.exists("test_service.log"):
        os.remove("test_service.log")
    

def test_server_starts_and_logs(server):
    log_file = "test_service.log"

    
    assert os.path.exists(log_file)
    
    with open(log_file, "r") as f:
        content = f.read()
        assert f"Service started on port {app.PORT}" in content


def test_index_endpoint_returns_logs(server):
    conn = http.client.HTTPConnection("localhost", PORT)
    
    try:
        conn.request("GET", "/")
        response = conn.getresponse()
        
        assert response.status == 200
        assert response.getheader("Content-type").startswith("text/html")
        
        data = response.read().decode("utf-8")
        assert "<html>" in data
        assert "Last 100 logs" in data
        assert f"Service started on port {app.PORT}" in data
        
    finally:
        conn.close()


def test_log_file_created(server):
    log_file = "test_service.log"
    assert os.path.exists(log_file)
    assert os.path.getsize(log_file) > 0