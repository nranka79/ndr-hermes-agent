import sys
import json
import os
from pathlib import Path

MODEL_MAPPINGS = {
    "minimax":  {"provider": "MiniMax",      "model": "Minimax-M2.7"},
    "nematron": {"provider": "OpenRouter",   "model": "nvidia/nemotron-3-super-120b-a12b:free"},
    "gemini2":   {"provider": "OpenRouter",   "model": "google/gemini-2.5-flash-lite"},
    "gemini3":   {"provider": "OpenRouter",   "model": "google/gemini-3-flash-preview"},
    "qwen":   {"provider": "OpenRouter",   "model": "qwen/qwen3.6-plus:free"}
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/main.py -- <model_keyword>")
        print(f"Available keywords: {', '.join(MODEL_MAPPINGS.keys())}")
        sys.exit(1)

    # argv[0]=script, argv[1]='--', argv[2]=keyword  (or argv[1]=keyword directly)
    keyword = (sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--" else sys.argv[1]).lower()

    if keyword not in MODEL_MAPPINGS:
        print(f"Error: Unknown model keyword '{keyword}'")
        print(f"Available keywords: {', '.join(MODEL_MAPPINGS.keys())}")
        sys.exit(1)

    cfg = MODEL_MAPPINGS[keyword]

    # Write model switch request to ~/.hermes/model_switch_request.json
    # This signals the agent loop to switch models before the next API call
    hermes_home = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
    hermes_home.mkdir(parents=True, exist_ok=True)

    request_file = hermes_home / "model_switch_request.json"
    request_data = {
        "model": cfg["model"],
        "provider": cfg["provider"],
        "keyword": keyword.capitalize(),
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }

    try:
        with open(request_file, "w") as f:
            json.dump(request_data, f)
        print(f"✅ Model switched to {cfg['provider']} ({cfg['model']})")
        print(f"📋 Starting from your next message, all LLM calls will use the new model.")
        return 0
    except Exception as e:
        print(f"❌ Error writing model switch request: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
