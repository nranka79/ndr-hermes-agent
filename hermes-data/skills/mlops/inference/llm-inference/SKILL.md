---
name: llm-inference
description: LLM inference serving — choose the right engine for your hardware (llama.cpp/GGUF for local/CPU, vLLM for high-throughput, TensorRT-LLM for NVIDIA峰值性能). Covers OpenAI-compatible endpoints, quantization, and deployment patterns.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Inference, LLM Serving, llama.cpp, vLLM, TensorRT-LLM, GGUF, Quantization, OpenAI API, Production]
---

# LLM Inference — Choosing and Using the Right Engine

This is the umbrella entry point. Select the right tool for your scenario, then use the detailed sub-skill references for deep-dive implementation.

## Decision Tree

```
What is your deployment target?
├── CPU or Apple Silicon or edge device
│   └── → llama.cpp + GGUF (see references/llama-cpp.md)
├── NVIDIA GPU (A100/H100) + maximum throughput
│   └── → TensorRT-LLM (see references/tensorrt-llm.md)
├── NVIDIA GPU + simpler setup + good performance
│   └── → vLLM (see references/vllm.md)
└── Multiple GPUs + auto-scaling + managed
    └── → vLLM (see references/vllm.md)
```

## When to Use Each Engine

| Engine | Hardware | Throughput | Latency | Setup | Best For |
|--------|----------|------------|---------|-------|---------|
| **llama.cpp + GGUF** | CPU, Apple Silicon, any GPU | Medium | Medium | Simple | Local, edge, consumer GPUs, Apple Silicon |
| **vLLM** | NVIDIA GPU | High (24k tok/s) | Low | Medium | Production API, OpenAI-compatible, multi-user |
| **TensorRT-LLM** | NVIDIA A100/H100/GB200 | Extreme (100x PyTorch) | Lowest | Complex | Maximum performance, production NVIDIA-only |

## Quick Selection Guide

### Use llama.cpp + GGUF when:
- Running on CPU, Apple Silicon, or consumer GPUs (RTX 4090)
- Need zero Python runtime overhead
- Deploying edge/inference as a binary
- Want flexible quantization (Q2–Q8) without GPU requirements
- Key reference: `references/llama-cpp.md`

### Use vLLM when:
- Deploying production LLM APIs (100+ req/sec)
- Serving OpenAI-compatible endpoints
- Need auto-scaling and managed experience
- Multi-user applications (chatbots, assistants)
- Key reference: `references/vllm.md`

### Use TensorRT-LLM when:
- Deploying on NVIDIA A100/H100/GB200
- Need absolute maximum throughput (10-100x vs PyTorch)
- Working with quantized models (FP8/INT4)
- Multi-GPU scaling with tensor parallelism
- Key reference: `references/tensorrt-llm.md`

## Common Workflows

### Workflow 1: Local Inference (llama.cpp + GGUF)

```bash
# Install llama.cpp
brew install llama.cpp  # macOS/Linux
# or: winget install llama.cpp  # Windows

# Run directly from Hugging Face Hub
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0

# Start OpenAI-compatible server
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q4_K_M \
    --host 0.0.0.0 --port 8080 -ngl 35 -c 4096

# Query
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

**Key decision: choosing a quant**

| Quant | Bits | Size (7B) | Quality | Use Case |
|-------|------|-----------|---------|----------|
| Q4_K_M | 4.5 | ~4.1 GB | High | **Recommended default** |
| Q5_K_M | 5.5 | ~4.8 GB | Very High | Quality focused |
| Q6_K | 6.0 | ~5.5 GB | Excellent | Near-original |
| Q8_0 | 8.0 | ~7.2 GB | Best | Maximum quality |

**For Apple Silicon**: use `-ngl 99` for Metal GPU offload.
**For NVIDIA**: use `-ngl 35` (or `GGML_CUDA=1` build).

See: `references/llama-cpp.md`, `references/gguf.md`

### Workflow 2: Production API (vLLM)

```bash
# Install
pip install vllm

# Start server
vllm serve meta-llama/Llama-3-8B-Instruct \
    --gpu-memory-utilization 0.9 \
    --max-model-len 8192 \
    --port 8000

# Or with Docker
docker run --gpus all -p 8000:8000 \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-3-8B-Instruct
```

```python
# Python client
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8000/v1', api_key='EMPTY')
print(client.chat.completions.create(
    model='meta-llama/Llama-3-8B-Instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}]
).choices[0].message.content)
```

**Quantized serving (AWQ/GPTQ) for 70B models**:
```bash
vllm serve TheBloke/Llama-2-70B-AWQ \
    --quantization awq \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.95
```

See: `references/vllm.md`

### Workflow 3: Maximum Performance (TensorRT-LLM)

```bash
# Docker (recommended)
docker pull nvidia/tensorrt_llm:latest

# Start server with automatic compilation
trtllm-serve meta-llama/Meta-Llama-3-8B \
    --tp_size 4 \
    --max_batch_size 256 \
    --max_num_tokens 4096

# Query
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"meta-llama/Meta-Llama-3-8B","messages":[{"role":"user","content":"Hello"}]}'
```

**FP8 quantization (2× faster, 50% memory)**:
```python
from tensorrt_llm import LLM
llm = LLM(model="meta-llama/Meta-Llama-3-70B", dtype="fp8")
```

See: `references/tensorrt-llm.md`

## Quantization Fundamentals

### Quantization Methods by Engine

| Method | Engines | Bits | Accuracy | Speed | Notes |
|--------|---------|------|----------|-------|-------|
| **GGUF K-quants** | llama.cpp | 2–8 | High | Medium | Q4_K_M recommended |
| **AWQ** | vLLM, TensorRT-LLM | 4 | High | Fast | Best for 70B |
| **GPTQ** | vLLM, TensorRT-LLM | 4 | High | Fast | Wide support |
| **FP8** | TensorRT-LLM | 8 | Highest | Fastest | H100 only |
| **INT4** | llama.cpp | 4 | Medium | Very Fast | Extreme compression |

### When to Quantize
- Model too large for available VRAM → use AWQ/GPTQ (4-bit) or GGUF Q4
- Need maximum quality → use FP16 or FP8
- CPU inference → use GGUF Q4/Q5 with CPU offload
- Edge deployment → use GGUF Q2/Q3

## OpenAI-Compatible API Pattern

All three engines expose the same OpenAI Chat Completions API:

```bash
# llama.cpp
llama-server -hf model:Q4_K_M --port 8080

# vLLM
vllm serve model --port 8000

# TensorRT-LLM
trtllm-serve model --port 8000
```

```python
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8000/v1', api_key='EMPTY')

response = client.chat.completions.create(
    model='model-name',
    messages=[
        {'role': 'system', 'content': 'You are helpful.'},
        {'role': 'user', 'content': 'What is 2+2?'}
    ],
    max_tokens=256,
    temperature=0.7
)
print(response.choices[0].message.content)
```

## Performance Comparison

| Engine | 7B Throughput | 70B Throughput | Setup Complexity |
|--------|--------------|----------------|-----------------|
| llama.cpp | ~30 tok/s (GPU) | ~15 tok/s (GPU) | Low |
| vLLM | ~6,000 tok/s (A100) | ~2,000 tok/s (8×A100) | Medium |
| TensorRT-LLM | ~60,000 tok/s (H100) | ~20,000 tok/s (8×H100) | High |

*llama.cpp numbers are for single-request inference; vLLM/TensorRT-LLM numbers are for batched serving.*

## Architecture Decision Framework

```
1. What hardware do you have?
   └── CPU/Apple Silicon → llama.cpp (GGUF)
   └── NVIDIA GPU
       ├── A100/H100/GB200 → TensorRT-LLM (maximum performance)
       └── Other NVIDIA → vLLM (good performance, easier setup)

2. What is your scale?
   └── <10 req/sec, single user → llama.cpp (simplest)
   └── 100+ req/sec, multi-user → vLLM (auto-batching)
   └── Maximum throughput → TensorRT-LLM

3. What is your priority?
   └── Simplicity → llama.cpp
   └── Balance of simplicity/performance → vLLM
   └── Absolute performance → TensorRT-LLM
```

## Reference Skills (Detailed Content)

- **references/llama-cpp.md** — llama.cpp CLI/CLI, GGUF format, Hub discovery, quant selection, server mode, hardware optimization
- **references/gguf.md** — GGUF conversion, K-quants explained, importance matrix, imatrix calibration, multi-quant workflow
- **references/vllm.md** — vLLM serving, PagedAttention, continuous batching, OpenAI API, quantization (AWQ/GPTQ), multi-GPU, deployment
- **references/tensorrt-llm.md** — TensorRT-LLM, FP8/INT4 quantization, in-flight batching, multi-GPU/tensor parallelism, speculative decoding

### Structured Output

For guaranteed structured output from LLMs, use `structured-output` (separate skill) which covers:
- `references/instructor.md` — Pydantic validation + retry (complex schemas, production APIs)
- `references/outlines.md** — Constrained decoding + JSON Schema (vLLM, local models, speed)
- `references/guidance.md` — Regex + grammar + templating (multi-step workflows, format enforcement)

**obliteratus** (abliteration) is a separate domain — modifies model weights, not output structure. See the `obliteratus` skill.
