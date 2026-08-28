# GGUF / llama.cpp Quantization — Reference
*Source skill: gguf-quantization (absorbed into llm-inference umbrella)*
*Source path: mlops/inference/gguf/SKILL.md*

## When to Use

- Deploying on **consumer hardware** (laptops, desktops)
- Running on **Apple Silicon** (M1/M2/M3) with Metal acceleration
- **CPU inference** without GPU requirements
- Wanting **flexible quantization** from Q2_K to Q8_0
- Using local AI tools: LM Studio, Ollama, text-generation-webui, koboldcpp

## Key Advantages

- **Universal hardware**: CPU, Apple Silicon, NVIDIA, AMD support
- **No Python runtime**: Pure C/C++ inference
- **Flexible quantization**: 2–8 bit with K-quants (Q2_K, Q3_K, Q4_K, Q5_K, Q6_K, Q8_0)
- **Ecosystem**: LM Studio, Ollama, koboldcpp, and more
- **imatrix**: Importance matrix for better low-bit quality

## When NOT to Use

- **AWQ/GPTQ**: Maximum accuracy with calibration on NVIDIA GPUs
- **HQQ**: Fast calibration-free quantization for HuggingFace
- **bitsandbytes**: Simple integration with transformers library
- **TensorRT-LLM**: Production NVIDIA deployment with maximum speed

## Quick Start

```bash
# Install llama.cpp Python bindings
pip install llama-cpp-python

# Or use quantization tools directly
python -m llama_cpp --quantize model.gguf --output model-q4_k_m.gguf Q4_K_M
```

## Key Concepts

**Quantization Levels:**
| Format | Size | Quality | Speed |
|--------|------|---------|-------|
| Q8_0 | ~70% of fp16 | Near-lossless | Fast |
| Q6_K | ~55% | Good | Medium |
| Q5_K_M | ~47% | Very Good | Medium |
| Q4_K_M | ~38% | Good | Fast |
| Q3_K_M | ~33% | Acceptable | Medium |
| Q2_K | ~25% | Low | Fastest |

**GGUF Metadata:** Header in quantized file containing tokenizer, architecture, and metadata — self-contained.
