import sys

MODEL_MAPPINGS = {
    "minimax":  {"provider": "MiniMax",      "model": "Minimax-M2.7"},
    "nematron": {"provider": "OpenRouter",   "model": "nvidia/nemotron-3-super-120b-a12b:free"},
    "gemini":   {"provider": "OpenRouter",   "model": "google/gemini-2.5-flash-lite"},
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
    cmd = f"hermes chat --model '{cfg['model']}' --provider '{cfg['provider']}'"

    print(f"To start a new session with {cfg['provider']} ({cfg['model']}), run:")
    print(cmd)


if __name__ == "__main__":
    main()
