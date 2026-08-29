import requests
import json

URL = "http://127.0.0.1:8000/generate"
HEADERS = {"Content-Type": "application/json"}

with open("test_payload.json", "r") as f:
    payload = json.load(f)

response = requests.post(URL, json=payload, headers=HEADERS)

print(f"Status Code: {response.status_code}")
print("Response Body:")
print(response.text)