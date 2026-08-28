# vLLM Reference

*Source skill: `mlops/inference/vllm` (absorbed into llm-inference umbrella)*

## When to Use

Use vLLM when:
- Deploying production LLM APIs (100+ req/sec)
- Serving OpenAI-compatible endpoints
- Need auto-scaling with managed experience
- Multi-user applications (chatbots, assistants)
- Key advantage: PagedAttention + continuous batching = 24x higher throughput than standard transformers

## Quick Start

```bash
# Install
pip install vllm

# Start server
vllm serve meta-llama/Llama-3-8B-Instruct \
    --gpu-memory-utilization 0.9 \
    --max-model-len 8192 \
    --port 8000
```

```python
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8000/v1', api_key='EMPTY')
print(client.chat.completions.create(
    model='meta-llama/Llama-3-8B-Instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}]
).choices[0].message.content)
```

## Offline Batch Inference

```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="meta-llama/Llama-3-8B-Instruct",
    tensor_parallel_size=2,  # Use 2 GPUs
    gpu_memory_utilization=0.9,
    max_model_len=4096
)

sampling = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=512)
outputs = llm.generate(prompts, sampling)
```

## Quantized Model Serving (AWQ/GPTQ)

```bash
# 70B model in ~40GB VRAM with AWQ
vllm serve TheBloke/Llama-2-70B-AWQ \
    --quantization awq \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.95
```

## Key Reference Files in Original Skill

- `references/quantization.md` — AWQ/GPTQ setup, accuracy comparisons
- `references/server-deployment.md` — Docker, Kubernetes, load balancing
- `references/troubleshooting.md` — OOM, slow TTFT, low throughput issues
- `references/optimization.md` — PagedAttention tuning, batching details
