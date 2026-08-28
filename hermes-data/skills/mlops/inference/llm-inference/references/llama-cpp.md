# llama.cpp + GGUF Reference

*Source: mlops/inference/llama-cpp (absorbed into llm-inference umbrella)*

## When to Use

Use llama.cpp when:
- Running on CPU, Apple Silicon, or consumer GPUs (no NVIDIA required)
- Need zero Python runtime overhead
- Deploying edge/embedded AI as a standalone binary
- Want flexible quantization from Q2 to Q8 without GPU constraints

## Model Discovery Workflow

1. Search: `https://huggingface.co/models?apps=llama.cpp&sort=trending`
2. Open: `https://huggingface.co/<repo>?local-app=llama.cpp`
3. Extract the exact `llama-server` or `llama-cli` command
4. Confirm via tree API: `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`

## Quick Start

```bash
# Run from HuggingFace Hub directly
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0

# Start OpenAI-compatible server
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q4_K_M \
    --host 0.0.0.0 --port 8080 -ngl 35 -c 4096
```

## Choosing a Quant

| Quant | Bits | Size (7B) | Quality | Notes |
|-------|------|-----------|---------|-------|
| Q4_K_M | 4.5 | ~4.1 GB | High | **Recommended default** |
| Q5_K_M | 5.5 | ~4.8 GB | Very High | Quality focused |
| Q6_K | 6.0 | ~5.5 GB | Excellent | Near-original |
| Q8_0 | 8.0 | ~7.2 GB | Best | Maximum quality |

## Python API

```python
from llama_cpp import Llama

llm = Llama(model_path="./model-q4_k_m.gguf", n_ctx=4096, n_gpu_layers=35, n_threads=8)

# Streaming
for chunk in llm("Explain quantum:", stream=True):
    print(chunk["choices"][0]["text"], end="", flush=True)
```

## Key Reference Files in Original Skill

- `references/hub-discovery.md` — URL-only HF workflows, search patterns, GGUF extraction
- `references/advanced-usage.md` — speculative decoding, batched inference, LoRA, multi-GPU
- `references/quantization.md` — K-quants explained, imatrix calibration
- `references/server.md` — server launch, OpenAI API, Docker, NGINX
- `references/troubleshooting.md` — install/convert/quantize issues
- `references/optimization.md` — CPU threading, BLAS, GPU offload, benchmarks
