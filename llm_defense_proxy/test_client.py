import os
import requests
import json

URL = "http://127.0.0.1:8000/generate"
HEADERS = {"Content-Type": "application/json"}

def main_client():
    payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
    if os.path.exists(payload_path):
        with open(payload_path, "r") as f:
            payload = json.load(f)
    else:
        payload = {"model": "qwen2.5:0.5b", "prompt": "Hello", "stream": False}

    response = requests.post(URL, json=payload, headers=HEADERS)

    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)


if __name__ == "__main__":
    main_client()