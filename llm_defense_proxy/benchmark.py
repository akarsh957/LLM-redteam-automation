import requests
import time

url = "http://127.0.0.1:8000/generate"
headers = {"Content-Type": "application/json"}
payload = {
    "model": "qwen2.5:0.5b",
    "prompt": "Explain the concept of public key cryptography.",
    "stream": False
}

latencies = []

print("Starting latency benchmark (10 requests)...")
for i in range(10):
    start = time.time()
    response = requests.post(url, json=payload, headers=headers)
    end = time.time()

    if response.status_code == 200:
        # Extract the total overhead calculated by your proxy
        proxy_latency = response.json()["latency_metrics"]["total_ms"]
        latencies.append(proxy_latency)
        print(f"Request {i+1}: {proxy_latency} ms")
    else:
        print(f"Request {i+1} Failed: {response.status_code}")

if latencies:
    avg_latency = sum(latencies) / len(latencies)
    print(f"\n=== Benchmark Complete ===")
    print(f"Average Guardrail Overhead: {avg_latency:.2f} ms")