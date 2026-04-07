import requests
import json

url = "http://localhost:8000/llm"
payload = {"prompt": "hello"}
headers = {"Content-Type": "application/json"}

try:
    r = requests.post(url, json=payload, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
