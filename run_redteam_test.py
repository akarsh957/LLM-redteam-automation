import os
import sys
import threading
import time
import uvicorn
from fastapi.testclient import TestClient

# Add paths
sys.path.insert(0, os.path.abspath("llm_defense_proxy"))
sys.path.insert(0, os.path.abspath("LLM-redteam-automation"))

import main
from redteam_cli import RedTeamHarness
import export_results

def run_test():
    print("[*] Testing Member 3 Defense Proxy against Member 1 Red-Team Engine...")
    
    # Start server in thread
    def start_server():
        uvicorn.run(main.app, host="127.0.0.1", port=8000, log_level="error")

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    # Run Member 1 Red-Team Harness against http://127.0.0.1:8000/generate
    output_json = "defended_telemetry.json"
    harness = RedTeamHarness(target_model="qwen2.5:0.5b", endpoint="http://127.0.0.1:8000/generate")
    harness.execute_suite("LLM-redteam-automation/benchmark_intents.json", "all", output_json)

    # Export results
    print("\n[*] Exporting telemetry results via export_results.py...")
    export_results.export_telemetry(output_json)

if __name__ == "__main__":
    run_test()
