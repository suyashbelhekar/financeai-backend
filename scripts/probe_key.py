"""
probe_key.py — Diagnose a Gemini API key:
  1. Validate key is non-empty (opaque string, no format check)
  2. List available models
  3. Try generation on every chat-capable model until one works
  4. Report the working model — update .env automatically
"""
import sys, os, warnings, re
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from google import genai
from google.genai import types

KEY   = os.getenv("GEMINI_API_KEY", "").strip()
if not KEY:
    # Try loading from .env file in parent directory
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            if line.startswith("GEMINI_API_KEY="):
                KEY = line.split("=", 1)[1].strip()
                break
if not KEY:
    print("ERROR: Set GEMINI_API_KEY env var or add it to backend/.env")
    sys.exit(1)

# ── 1. Validate non-empty ──────────────────────────────────────────────────
key = KEY.strip()
if not key:
    print("ERROR: GEMINI_API_KEY is empty")
    sys.exit(1)
print(f"Key  : {'*' * 10}{key[-6:]}  (length={len(key)}, opaque — no format validation)")

# ── 2. List available models ───────────────────────────────────────────────
client = genai.Client(api_key=key)
print("\nAvailable models:")
all_models = []
try:
    for m in client.models.list():
        all_models.append(m.name)
        print(f"  {m.name}")
except Exception as e:
    print(f"  ERROR listing models: {e}")
    sys.exit(1)

# ── 3. Find working model ──────────────────────────────────────────────────
# Prefer flash models (fastest), exclude audio/image/tts/embedding/veo/lyria
candidates = [
    m for m in all_models
    if "flash" in m.lower()
    and not any(x in m.lower() for x in ["audio", "tts", "image", "transcribe",
                                          "live", "native", "embed", "veo", "lyria"])
]
# Sort: prefer lower version numbers (more stable)
candidates.sort()

print(f"\nTesting {len(candidates)} flash models...")
working_model = None
working_response = None

for model_path in candidates:
    model_name = model_path.replace("models/", "")
    try:
        r = client.models.generate_content(
            model=model_name,
            contents=PROBE,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=10,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        text = r.text if r.text else ""
        if text:
            print(f"  ✅  {model_name}  →  '{text.strip()[:40]}'")
            working_model    = model_name
            working_response = text.strip()
            break
        else:
            print(f"  ⚠   {model_name}  →  empty response (finish={r.candidates[0].finish_reason if r.candidates else 'none'})")
    except Exception as e:
        msg = str(e)
        # Redact key from error message
        msg = msg.replace(key, "[REDACTED]")
        short = msg[:100]
        print(f"  ❌  {model_name}  →  {short}")

# ── 4. Result ──────────────────────────────────────────────────────────────
print()
if not working_model:
    print("❌  No working model found for this key.")
    print("   The key may be restricted to the Interactions API (Live/streaming only).")
    print("   Contact Google AI Studio to enable generateContent access.")
    sys.exit(1)

print(f"✅  Working model: {working_model}")
print(f"   Response      : {working_response}")

# ── 5. Auto-update .env ────────────────────────────────────────────────────
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        content = f.read()
    content = re.sub(r"^GEMINI_MODEL=.*$", f"GEMINI_MODEL={working_model}", content, flags=re.MULTILINE)
    with open(env_path, "w") as f:
        f.write(content)
    print(f"   .env updated  : GEMINI_MODEL={working_model}")
else:
    print(f"   Set in .env   : GEMINI_MODEL={working_model}")

print()
print("Run the server and the API will use this model automatically.")
