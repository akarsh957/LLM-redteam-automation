import json
import csv
import sys
import os

def export_telemetry(json_filepath: str = "final_attack_telemetry.json"):
    if not os.path.exists(json_filepath):
        print(f"[!] Error: File '{json_filepath}' not found.")
        sys.exit(1)

    with open(json_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("metadata", {})
    records = data.get("records", [])

    print("=" * 70)
    print("           RED TEAM ATTACK TELEMETRY SUMMARY")
    print("=" * 70)
    print(f"Target Model     : {meta.get('target_model')}")
    print(f"Total Probes     : {meta.get('total_probes')}")
    print(f"Successful Hits  : {meta.get('successful_hits')}")
    print(f"Attack Success % : {meta.get('overall_asr_percent')}%")
    print("=" * 70)

    # Strategy breakdown
    breakdown = {}
    for r in records:
        strat = r["strategy"]
        breakdown.setdefault(strat, {"total": 0, "hits": 0})
        breakdown[strat]["total"] += 1
        if r["score"] == 1:
            breakdown[strat]["hits"] += 1

    print("\n[+] Performance by Attack Vector:")
    print(f"{'Strategy':<22} | {'Probes':<10} | {'Hits':<8} | {'ASR (%)':<10}")
    print("-" * 55)
    for s, v in breakdown.items():
        asr = round((v["hits"] / v["total"]) * 100, 1) if v["total"] > 0 else 0
        print(f"{s:<22} | {v['total']:<10} | {v['hits']:<8} | {asr}%")

    # Export to CSV for Member 4
    csv_filename = json_filepath.replace(".json", ".csv")
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["test_id", "category", "strategy", "score", "verdict", "latency_sec", "final_prompt_sent", "model_response"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({k: r[k] for k in fieldnames})

    print(f"\n[+] Exported clean CSV for Member 4: '{csv_filename}'")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "final_attack_telemetry.json"
    export_telemetry(target_file)