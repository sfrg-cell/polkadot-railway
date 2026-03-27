import http.server
import socketserver
import urllib.parse
import os
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv
from collector import fetch_and_store_dot_price
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter

load_dotenv()

PORT = int(os.getenv("PORT", 5336))
TOKEN = os.getenv("INFLUX_TOKEN")
ORG = os.getenv("INFLUX_ORG")
BUCKET = os.getenv("INFLUX_BUCKET")
URL = os.getenv("INFLUX_URL")

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
query_api = client.query_api()

VIEW_COUNT = Counter('index_page_views_total', 'Total number of views on the index page')

class CryptoHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        if parsed_path.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
            return

        elif parsed_path.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html><body>
                <h1>Polkadot Analytics</h1>
                <p>Specify the period in hours for the calculation (for example, 1 or 24):</p>
                <form action="/calculate" method="get">
                    Last: <input type="number" name="hours_ago" value="1" min="1"> hour(s)<br><br>
                    <input type="submit" value="Calculate Metrics">
                </form>
            </body></html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif parsed_path.path == "/calculate":
            VIEW_COUNT.inc()
            fetch_and_store_dot_price()
            hours_list = params.get("hours_ago")
            hours = hours_list[0] if hours_list else "1"
            start_time = f"-{hours}h"

            flux_query = f'from(bucket: "{BUCKET}") |> range(start: {start_time}) |> filter(fn: (r) => r._measurement == "crypto_price")'
            
            try:
                results = query_api.query(org=ORG, query=flux_query)
                prices = [record.get_value() for table in results for record in table.records]
                
                if not prices:
                    res_body = "<p>No data found.</p>"
                else:
                    res_body = f"<p>Max: {max(prices)}</p><p>Min: {min(prices)}</p><p>Avg: {sum(prices)/len(prices):.2f}</p>"
            except Exception as e:
                res_body = f"<p>Error: {e}</p>"

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            response = f"<html><body><h3>Results:</h3>{res_body}<br><a href='/'>Back</a></body></html>"
            self.wfile.write(response.encode("utf-8"))

    def log_message(self, format, *args):
        return

def main():
    print(f"Function node starting on port {PORT}")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CryptoHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    main()
