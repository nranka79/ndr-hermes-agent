---
name: mlops-infrastructure
description: "MLOps infrastructure umbrella — GPU cloud providers, HuggingFace Hub CLI, fast tokenizers, and vector databases for RAG. Covers model hosting, dataset management, cloud GPU compute, and embedding stores."
umbrella: mlops-infrastructure
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [MLOps, Infrastructure, HuggingFace, GPU Cloud, Modal, Lambda Labs, Tokenizers, Vector Databases, RAG, Model Hosting]
---

# MLOps Infrastructure — Umbrella

Covers the infrastructure layer for ML: model/dataset management, GPU cloud compute, fast tokenizers, and vector stores for RAG.

## Decision Tree

```
What MLOps infrastructure do you need?
├── Cloud GPU compute (serverless or reserved)
│   └── → GPU Cloud Providers (references/gpu-cloud.md)
│         Modal (serverless) or Lambda Labs (reserved A100/H100).
├── Upload/download models and datasets to HF Hub
│   └── → HuggingFace Hub CLI (references/huggingface-hub.md)
│         hf download/upload/sync/repos.
├── Fast tokenization for research or production
│   └── → HuggingFace Tokenizers (references/huggingface-tokenizers.md)
│         Rust-based, 10x faster than Python tokenizers.
└── Vector store for RAG
    └── → Vector Databases (references/vector-databases.md)
          FAISS, Chroma, Qdrant, Weaviate, Pinecone comparison.
```

## Sub-Skill Reference

| Skill | When to Use | Key Commands |
|-------|-------------|---------------|
| `references/gpu-cloud.md` | Cloud GPU compute | Modal/Lambda setup |
| `references/huggingface-hub.md` | HF model/dataset management | `hf download`, `hf upload`, `hf sync` |
| `references/huggingface-tokenizers.md` | Fast tokenization | `Tokenizer.from_pretrained`, batch encoding |
| `references/vector-databases.md` | RAG vector stores | FAISS, Chroma, Qdrant, Pinecone |

## Absorbed Skills

- `gpu-cloud-providers` → `references/gpu-cloud.md`
- `huggingface-hub` → `references/huggingface-hub.md`
- `huggingface-tokenizers` → `references/huggingface-tokenizers.md`
- `vector-databases` → `references/vector-databases.md`

## Quick Reference

### HuggingFace Hub CLI
```bash
hf download meta-llama/Llama-3-8B-Instruct
hf upload my-account/my-model ./weights/
hf sync my-account/my-dataset ./data/
hf repos create my-model --type model
```

### Fast Tokenization
```python
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8B")
encoded = tokenizer.batch_encode_plus(texts, padding=True, truncation=True)
```

### Vector Database Selection
- **FAISS**: Local, fast, no-server — good for <10M vectors
- **Chroma**: Local-first, easy setup — good for dev/test
- **Qdrant**: Production, filtering, hybrid search
- **Pinecone**: Fully managed, scalable

## Resources

- **HuggingFace Hub**: https://huggingface.co/docs/huggingface_hub
- **GPU Cloud**: Modal (modal.com), Lambda Labs (lambdalabs.com)
- **Tokenizers**: https://github.com/huggingface/tokenizers
- **Vector DBs**: FAISS (GitHub), Chroma, Qdrant, Pinecone