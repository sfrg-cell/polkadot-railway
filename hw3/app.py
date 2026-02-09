import http.server
import socketserver
import threading
import time
from datetime import datetime
import os


PORT = 5336
LOG_FILE = os.environ.get("LOG_FILE", "service.log")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def heartbeat():
    while True:
        log("heartbeat: service is alive")
        time.sleep(60)


def read_last_logs():
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            return lines[-100:]
    except FileNotFoundError:
        return []


class Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/kill":
            log("kill endpoint called, exiting process")

            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Service is being killed. It should restart.\n")

            self.wfile.flush()
            os._exit(1)

        else:
            logs = read_last_logs()

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html = "<html><head><title>Service Logs</title></head><body>"
            html += "<h1>Last 100 logs</h1><pre>"

            for line in logs:
                html += line

            html += "</pre></body></html>"

            self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    log(f"Service started on port {PORT}")

    t = threading.Thread(target=heartbeat, daemon=True)
    t.start()

    with ReusableTCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    main()
