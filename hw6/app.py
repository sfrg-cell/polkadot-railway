import http.server
import datetime 
import time
import socketserver
import threading
import urllib.parse
from influxdb_client import InfluxDBClient
import os
import threading
from collector import fetch_and_store_dot_price
from dotenv import load_dotenv
from pathlib import Path

dotenv_path = Path('/home/anna/i_havryliuk/.env')
load_dotenv(dotenv_path=dotenv_path)

PORT = 5336
TOKEN = os.getenv("INFLUX_TOKEN")
ORG = os.getenv("INFLUX_ORG")
BUCKET = os.getenv("INFLUX_BUCKET")
URL = os.getenv("INFLUX_URL")

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
query_api = client.query_api()

class CryptoHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        if parsed_path.path == "/":
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

            hours_list = params.get("hours_ago")

            if not hours_list:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Error: Please provide number of hours.")
                return

            hours = hours_list[0]
            start_time = f"-{hours}h"

            flux_query = f'''
            from(bucket: "{BUCKET}")
                |> range(start: {start_time})
                |> filter(fn: (r) => r._measurement == "crypto_price" and r.coin == "DOT")
            '''
            
            results = query_api.query(org=ORG, query=flux_query)
            
            prices = []
            for table in results:
                for record in table.records:
                    prices.append(record.get_value())

            if not prices:
                response_text = "No data found for this period."
            else:
                avg_p = sum(prices) / len(prices)
                min_p = min(prices)
                max_p = max(prices)
                response_text = f"""
                <h3>Results for DOT:</h3>
                <p>Max Price: {max_p}</p>
                <p>Min Price: {min_p}</p>
                <p>Average Price: {avg_p:.2f}</p>
                <a href="/">Back</a>
                """

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(response_text.encode())

    def log_message(self, format, *args):
        return

def run_scraper():
    while True:
        fetch_and_store_dot_price()
        time.sleep(60)

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    print(f"Service started on port {PORT}")

    scraper_thread = threading.Thread(target=run_scraper, daemon=True)
    scraper_thread.start()
    
    with ReusableTCPServer(("", PORT), CryptoHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    main()