# Local AI Inference Guide — llama.cpp & GGUF

This guide covers running local, offline AI inference for Back-Office AI Copilot using `llama.cpp` and GGUF quantized models.

---

## 1. Runtime Sizing & Requirements

| Specification | CPU Inference | GPU (NVIDIA CUDA) |
| :--- | :--- | :--- |
| **Model** | Qwen2.5-1.5B-Instruct | Qwen2.5-1.5B-Instruct |
| **Quantization** | Q4_K_M (~1.1 GB) | Q4_K_M (~1.1 GB) |
| **RAM Required** | >= 2.5 GB available | >= 2.0 GB system RAM |
| **VRAM Required** | N/A | >= 1.5 GB VRAM |
| **Tokens / Sec** | 15–35 tok/s | 60–120 tok/s |
| **Context Length**| 4,096–8,192 tokens | Up to 32,768 tokens |

---

## 2. Directory Layout

Place model files into `models/`:

```
models/
├── model_registry.json
├── base/
│   └── qwen2.5-1.5b-instruct/    # (Optional) Hugging Face base weights
├── adapters/
│   └── business-analyst-v1/       # LoRA adapter weights & config
└── gguf/
    └── Qwen2.5-1.5B-Instruct-Q4_K_M.gguf
```

---

## 3. Starting the llama.cpp Server

### Option A: Using the Installer Script
The project provides an automated installer and launcher script in `scripts/`:

```powershell
backend\.venv\Scripts\python.exe scripts/install_local_ai.py
```

### Option B: Direct CLI Execution
If you downloaded `llama-server.exe` (from [llama.cpp releases](https://github.com/ggerganov/llama.cpp/releases)):

```powershell
# Run with CPU
llama-server.exe -m models/gguf/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf -c 4096 --port 8080 --host 127.0.0.1

# Run with GPU offloading (CUDA)
llama-server.exe -m models/gguf/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf -c 8192 -ngl 99 --port 8080 --host 127.0.0.1
```

---

## 4. Backend Configuration (`.env`)

Configure the backend to communicate with the local server:

```ini
AI_ENABLED=true
AI_PROVIDER=local
LOCAL_AI_URL=http://127.0.0.1:8080
LOCAL_AI_MODEL=Qwen2.5-1.5B-Instruct
LOCAL_AI_MAX_TOKENS=1024
LOCAL_AI_TEMPERATURE=0.2
```

---

## 5. Deterministic Offline Fallback

Even if the local LLM server is **OFFLINE** or not yet installed:
- **Direct Metric Answering**: Headcounts, averages, sums, and percentages remain **100% operational** (< 1ms latency).
- **Dimension Rankings**: Top categories and distribution lookups continue to work seamlessly.
- **Unavailable Metric Warnings**: Guardrails prevent hallucinating non-existent fields.
- **Reports & Dashboard**: All visualizations and section tables generate deterministically from pandas aggregations.

---

## 6. Troubleshooting

### Issue: "Local AI model is currently offline"
- Ensure `llama-server.exe` is running on port `8080`.
- Verify the server health via `GET http://127.0.0.1:8080/health`.

### Issue: "Low available RAM" warning
- Close memory-intensive background apps (browsers, IDEs).
- Run Qwen 1.5B in Q4_K_M quantization, which requires only ~1.1 GB of RAM.

### Issue: Response is slow on CPU
- Reduce context window (`-c 2048` or `-c 4096`).
- Increase CPU thread count flag in llama-server (e.g. `-t 4` or `-t 6`).
