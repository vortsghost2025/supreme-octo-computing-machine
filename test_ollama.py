import urllib.request
import json

url = "http://localhost:9001/v1/models"
try:
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode())
    print(f"Status: {response.status}")
    print(f"Models: {data}")
except Exception as e:
    print(f"Error: {e}")
