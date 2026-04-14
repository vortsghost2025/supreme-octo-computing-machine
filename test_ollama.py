import urllib.request
import json

url = "http://187.77.3.56:11434/v1/models"
try:
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode())
    print(f"Status: {response.status}")
    print(f"Models: {data}")
except Exception as e:
    print(f"Error: {e}")
