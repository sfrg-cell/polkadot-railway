import pytest
import http.client
import threading
import time
import os
from app import main, LOG_FILE, PORT


@pytest.fixture
def server():

    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    server_thread = threading.Thread(target=main, daemon=True)
    server_thread.start()
    
    time.sleep(2)
    
    yield
    

def test_server_starts_and_logs(server):
    time.sleep(1)
    
    assert os.path.exists(LOG_FILE)
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
        assert f"Service started on port {PORT}" in content


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
        assert f"Service started on port {PORT}" in data
        
    finally:
        conn.close()


def test_heartbeat_writes_logs(server):
    time.sleep(3)
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
        assert f"Service started on port {PORT}" in content