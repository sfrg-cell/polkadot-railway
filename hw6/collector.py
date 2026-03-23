import requests
import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from dotenv import load_dotenv
from pathlib import Path 

dotenv_path = Path('/home/anna/i_havryliuk/.env')
load_dotenv(dotenv_path=dotenv_path)

token = os.getenv("INFLUX_TOKEN")
org = os.getenv("INFLUX_ORG")
bucket = os.getenv("INFLUX_BUCKET")
url = os.getenv("INFLUX_URL")

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

def fetch_and_store_dot_price():
    api_url = "https://api.coingecko.com/api/v3/simple/price?ids=polkadot&vs_currencies=usd"
    try:
        response = requests.get(api_url)
        data = response.json()
        price = data['polkadot']['usd']
        
        point = Point("crypto_price") \
            .tag("coin", "DOT") \
            .field("price", float(price)) \
            .time(time.time_ns(), WritePrecision.NS)
        
        write_api.write(bucket, org, point)
        print(f"Stored DOT price: {price}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_store_dot_price()