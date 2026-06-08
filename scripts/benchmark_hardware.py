import os
import sys
import json
import time
import urllib.request
import urllib.error

def is_docker():
    """Detect if running inside a Docker container."""
    if os.path.exists('/.dockerenv'):
        return True
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            return 'docker' in f.read() or 'containerd' in f.read()
    except Exception:
        return False

def get_ollama_endpoints():
    """Get candidate Ollama endpoints to check."""
    env_host = os.getenv("OLLAMA_HOST")
    candidates = []
    if env_host:
        candidates.append(env_host.rstrip('/'))
    
    if is_docker():
        candidates.extend([
            "http://host.docker.internal:11434",
            "http://localhost:11434",
            "http://ollama:11434"
        ])
    else:
        candidates.extend([
            "http://localhost:11434",
            "http://127.0.0.1:11434"
        ])
    return list(dict.fromkeys(candidates)) # Remove duplicates

def test_generation(endpoint, model):
    """Run a test generation on Ollama and measure performance metrics."""
    url = f"{endpoint}/api/generate"
    payload = {
        "model": model,
        "prompt": "Explain in one sentence what a prime number is.",
        "stream": False,
        "options": {
            "num_predict": 30
        }
    }
    
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            latency = time.time() - start_time
            res_body = json.loads(response.read().decode('utf-8'))
            
            # Extract Ollama's detailed metrics
            eval_count = res_body.get("eval_count", 0)
            eval_duration = res_body.get("eval_duration", 0) # in nanoseconds
            prompt_eval_duration = res_body.get("prompt_eval_duration", 0) # in nanoseconds
            load_duration = res_body.get("load_duration", 0) # in nanoseconds
            
            # Calculate metrics
            tokens_per_sec = 0.0
            if eval_duration > 0 and eval_count > 0:
                tokens_per_sec = eval_count / (eval_duration * 1e-9)
                
            ttft = prompt_eval_duration * 1e-9 # Time To First Token in seconds
            load_time = load_duration * 1e-9 # Load time in seconds
            
            return {
                "available": True,
                "latency_sec": latency,
                "load_time_sec": load_time,
                "ttft_sec": ttft,
                "tokens_per_sec": tokens_per_sec,
                "tokens_generated": eval_count,
                "error": None
            }
    except Exception as e:
        return {
            "available": False,
            "latency_sec": 0.0,
            "load_time_sec": 0.0,
            "ttft_sec": 0.0,
            "tokens_per_sec": 0.0,
            "tokens_generated": 0,
            "error": str(e)
        }

def run_benchmarks():
    print("🚀 [Hardware Benchmark] Starting capability evaluation...")
    env_docker = is_docker()
    print(f"📦 Environment: {'Docker Container' if env_docker else 'Host Machine'}")
    
    endpoints = get_ollama_endpoints()
    active_endpoint = None
    available_models = []
    
    # 1. Discover active Ollama endpoint
    for ep in endpoints:
        try:
            req = urllib.request.Request(f"{ep}/api/tags", method='GET')
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    active_endpoint = ep
                    tags_data = json.loads(resp.read().decode('utf-8'))
                    available_models = [m["name"] for m in tags_data.get("models", [])]
                    print(f"✅ Discovered active Ollama endpoint: {ep}")
                    break
        except Exception:
            continue
            
    # 2. Run benchmarks for models
    test_models = ["qwen2.5:0.5b", "gemma3:1b", "gemma3:4b"]
    model_benchmarks = {}
    
    # Default fallback matrix if Ollama is not running
    fallback_matrix = {
        "qwen2.5:0.5b": {"available": False, "tokens_per_sec": 12.0, "load_time_sec": 0.2, "ttft_sec": 0.05, "note": "Estimated CPU Fallback"},
        "gemma3:1b": {"available": False, "tokens_per_sec": 6.5, "load_time_sec": 0.5, "ttft_sec": 0.08, "note": "Estimated CPU Fallback"},
        "gemma3:4b": {"available": False, "tokens_per_sec": 1.8, "load_time_sec": 2.5, "ttft_sec": 0.35, "note": "Estimated CPU Fallback"}
    }
    
    if not active_endpoint:
        print("⚠️  Ollama service not detected. Generating estimated fallback capability matrix.")
        model_benchmarks = fallback_matrix
    else:
        print(f"📋 Available models in Ollama: {available_models}")
        for model in test_models:
            # Check if model exists, if not we mark as unavailable but estimate
            matched_name = next((m for m in available_models if m.startswith(model)), None)
            if not matched_name:
                print(f"⚠️  Model '{model}' is not pulled in Ollama. (Run 'ollama pull {model}')")
                model_benchmarks[model] = {
                    "available": False,
                    "tokens_per_sec": fallback_matrix[model]["tokens_per_sec"],
                    "load_time_sec": fallback_matrix[model]["load_time_sec"],
                    "ttft_sec": fallback_matrix[model]["ttft_sec"],
                    "note": f"Model not pulled. Run 'ollama pull {model}' to measure."
                }
            else:
                print(f"⏳ Benchmarking model '{matched_name}'...")
                # Run twice: first might trigger load, second is warm cache
                test_generation(active_endpoint, matched_name) # Warm up
                stats = test_generation(active_endpoint, matched_name)
                model_benchmarks[model] = stats
                if stats["available"]:
                    print(f"   📊 Speed: {stats['tokens_per_sec']:.2f} tokens/s | TTFT: {stats['ttft_sec']:.3f}s | Load Time: {stats['load_time_sec']:.3f}s")
                else:
                    print(f"   ❌ Benchmark failed: {stats['error']}")
                    
    # 3. Save capabilities matrix report
    datetime_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report = {
        "timestamp": datetime_str,
        "is_docker": env_docker,
        "endpoint_used": active_endpoint,
        "hardware_acceleration": "GPU/Metal (Native)" if active_endpoint and not env_docker else "CPU (Fallback/Container)",
        "models": model_benchmarks
    }
    
    output_dir = "./.twin/diagnostics"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "hardware_capability_matrix.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print(f"📄 Hardware capability matrix written to: {output_path}")
    print("🏁 Benchmark complete.")

if __name__ == "__main__":
    run_benchmarks()
