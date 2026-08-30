import time
import json
import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
import httpx

# Import your defense modules
from guards.regex_filter import RegexGuard
from guards.entropy_scanner import EntropyScanner
from guards.llama_guard import LlamaGuardScanner
from guards.output_sanitizer import OutputSanitizer

from contextlib import asynccontextmanager

# Global Async HTTPX Client for Connection Pooling
http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(
        timeout=60.0,
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=200)
    )
    yield
    await http_client.aclose()

app = FastAPI(title="LLM Defense Proxy", version="2.0", lifespan=lifespan)

# Initialize Guard Modules
regex_guard = RegexGuard()
entropy_guard = EntropyScanner()
llama_guard = LlamaGuardScanner()
output_sanitizer = OutputSanitizer()

# Ollama target endpoint for Member 3 integration
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Configure file logging for text audit trails
logging.basicConfig(
    filename="proxy_security.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Persistent block counters and analytics tracking in memory
blocked_stats = {
    "total_blocked": 0,
    "breakdown": {}
}

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    ui_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>LLM Defense Proxy API Running</h1><p>Visit <a href='/docs'>/docs</a> for Swagger UI.</p>"

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "LLM Defense Middleware Proxy",
        "total_attacks_blocked": blocked_stats["total_blocked"],
        "breakdown": blocked_stats["breakdown"]
    }


def refusal_response(category_name: str, details: str = "", latency_ms: float = 0.0) -> JSONResponse:
    """Return the capstone-member-safe refusal payload for blocked prompts."""
    response_text = f"Refused: Content flagged under Safety Policy [{category_name}]."
    logging.warning(f"BLOCKED: [{category_name}] - Details: {details}")
    return JSONResponse(
        status_code=200, 
        content={
            "response": response_text,
            "latency_metrics": {"total_ms": round(latency_ms, 3)}
        }
    )


def log_and_block(attack_name: str, details: str, latency: float):
    """Helper to log security incidents, maintain a structured JSON log file, and return a clean JSON block response."""
    blocked_stats["total_blocked"] += 1
    blocked_stats["breakdown"][attack_name] = blocked_stats["breakdown"].get(attack_name, 0) + 1

    incident_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "blocked",
        "attack_name": attack_name,
        "total_attacks_blocked": blocked_stats["total_blocked"],
        "details": details,
        "latency_ms": round(latency, 3)
    }

    logging.warning(f"BLOCKED: [{attack_name}] - Details: {details} (Latency: {latency:.3f}ms)")

    json_log_path = "proxy_security.json"
    logs = []
    if os.path.exists(json_log_path):
        try:
            with open(json_log_path, "r") as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []

    logs.append(incident_data)
    with open(json_log_path, "w") as f:
        json.dump(logs, f, indent=4)

    return refusal_response(attack_name if attack_name else "Safety Policy", details, latency)


@app.post("/generate")
async def proxy_generate(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    model = body.get("model", "qwen2.5:0.5b")
    user_prompt = body.get("prompt", "")
    stream = body.get("stream", False)

    input_guard_start = time.time()

    # LAYER 1: Regex Guard
    is_regex_safe, regex_reason = regex_guard.check(user_prompt)
    if not is_regex_safe:
        return log_and_block("Prompt Injection", regex_reason, (time.time() - input_guard_start) * 1000)

    # LAYER 2: Entropy / Base64 Scanner
    is_entropy_safe, entropy_reason, _ = entropy_guard.check(user_prompt)
    if not is_entropy_safe:
        return log_and_block("Obfuscation / Base64", entropy_reason, (time.time() - input_guard_start) * 1000)

    # LAYER 3: Llama Guard Safety Intent Classifier
    intent_result = llama_guard.scan_prompt(user_prompt)
    if not intent_result.get("passed", False):
        violated_cats = intent_result.get("violated_categories", [])
        category_name = violated_cats[0] if violated_cats else "Safety Policy"
        return log_and_block(category_name, intent_result.get("reason", "Safety policy violation detected"), (time.time() - input_guard_start) * 1000)

    input_guard_time_ms = (time.time() - input_guard_start) * 1000

    # Forward benign payload to upstream Ollama
    client = http_client if http_client is not None else httpx.AsyncClient()
    try:
        upstream_response = await client.post(
            OLLAMA_API_URL,
            json={
                "model": model,
                "prompt": user_prompt,
                "stream": stream,
            },
            timeout=60.0,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama upstream failure: {str(exc)}")

    if upstream_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Ollama upstream failure",
                "details": upstream_response.text,
            },
        )

    # LAYER 4: Output Sanitizer
    output_guard_start = time.time()
    ollama_data = upstream_response.json()
    raw_response_text = str(ollama_data.get("response", "")).strip()
    clean_response_text, _ = output_sanitizer.sanitize(raw_response_text)
    output_guard_time_ms = (time.time() - output_guard_start) * 1000

    total_guardrail_overhead_ms = input_guard_time_ms + output_guard_time_ms

    return JSONResponse(
        status_code=200, 
        content={
            "response": clean_response_text,
            "latency_metrics": {
                "total_ms": round(total_guardrail_overhead_ms, 3),
                "guardrail_overhead_ms": round(total_guardrail_overhead_ms, 3)
            }
        }
    )


# Backward-compatible alias: keep the legacy route but point it to the new behavior.
@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request):
    return await proxy_generate(request)