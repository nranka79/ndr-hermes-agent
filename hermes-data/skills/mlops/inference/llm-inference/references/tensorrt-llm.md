# TensorRT-LLM Reference

*Source skill: `mlops/inference/tensorrt-llm` (absorbed into llm-inference umbrella)*

## When to Use

Use TensorRT-LLM when:
- Deploying on NVIDIA A100/H100/GB200
- Need absolute maximum throughput (10-100x vs PyTorch)
- Working with quantized models (FP8/INT4)
- Multi-GPU scaling with tensor parallelism
- Key advantage: compiled kernels + in-flight batching = extreme throughput

## Quick Start

```bash
# Docker (recommended)
docker pull nvidia/tensorrt_llm:latest

# Start server with automatic model download and compilation
trtllm-serve meta-llama/Meta-Llama-3-8B \
    --tp_size 4 \
    --max_batch_size 256 \
    --max_num_tokens 4096

# Query
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"meta-llama/Meta-Llama-3-8B","messages":[{"role":"user","content":"Hello"}]}'
```

## FP8 Quantization (2× Faster, 50% Memory)

```python
from tensorrt_llm import LLM

llm = LLM(
    model="meta-llama/Meta-Llama-3-70B",
    dtype="fp8",
    max_num_tokens=8192
)

outputs = llm.generate(["Explain quantum computing"])
```

## Multi-GPU Deployment

```python
from tensorrt_llm import LLM

# Tensor parallelism across 8 GPUs
llm = LLM(
    model="meta-llama/Meta-Llama-3-405B",
    tensor_parallel_size=8,
    dtype="fp8"
)
```

## Key Reference Files in Original Skill

- `references/serving.md` — production deployment, monitoring, autoscaling
- `references/multi-gpu.md` — tensor/pipeline parallelism, multi-node
- `references/optimization.md` — quantization, batching, KV cache tuning
