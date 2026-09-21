import urllib.request
import json
from app.core.config import settings

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {settings.llm_api_key}",
    "User-Agent": "AIBackOfficeCopilot/1.0",
}
for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Return the number 42."}],
        "max_tokens": 10,
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            print(f"Model {model}: SUCCESS -> {content.strip()}")
    except urllib.error.HTTPError as e:
        print(f"Model {model}: HTTP {e.code} -> {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Model {model}: ERROR -> {e}")
