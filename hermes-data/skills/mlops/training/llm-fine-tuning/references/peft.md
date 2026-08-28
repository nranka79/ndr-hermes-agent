# PEFT (LoRA/QLoRA) — Reference
*Source skill: peft-fine-tuning (absorbed into llm-fine-tuning umbrella)*
*Source path: mlops/training/peft/SKILL.md*

## When to Use

- Fine-tuning 7B–70B models on limited GPU memory
- Training <1% of parameters with minimal accuracy loss
- Multi-adapter serving (serve multiple task adapters on one base model)
- Domain adaptation with LoRA/DoRA adapters
- Need 25+ PEFT methods (LoRA, AdaLoRA, AdaLoRA+, DoRA, IA³, etc.)

## Key LoRA Concepts

```python
from peft import LoraConfig, get_peft_model, TaskType

config = LoraConfig(
    r=8,                          # Rank (higher = more params, more accuracy)
    lora_alpha=16,                # Scaling factor
    target_modules=["q_proj", "v_proj"],  # Which layers to adapt
    lora_dropout=0.05,
    bias="none",                  # or "all" or "lora_only"
    task_type=TaskType.CAUSAL_LM,
)
model = get_peft_model(base_model, config)
```

## Common Ranks

| Rank | Params | Quality | Use Case |
|------|--------|---------|---------|
| 4 | Very low | Acceptable | Tests, tiny models |
| 8 | Low | Good | Consumer GPUs |
| 16 | Medium | Very Good | 3090/4090 |
| 32 | High | Near-full | A100 |
| 64 | Very High | Near-full | Research |

## Target Modules by Architecture

- **Llama/Mistral**: `q_proj`, `v_proj`, `k_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
- **Embedding layers**: Add `embed_in` or `token_embedding` if using `modules_to_save`
- **Vision models**: Target `qkv_proj` for attention layers

## QLoRA (Quantized + LoRA)

```python
from peft import get_peft_model, LoraConfig
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)
# Load quantized base model, then apply LoRA
model = get_peft_model(quantized_model, lora_config)
```

## Merging Adapters

```python
# Merge and unload (weights become part of base model)
merged_model = model.merge_and_unload()

# Merge into a new file
merged_model.save_pretrained("merged-model")
```
