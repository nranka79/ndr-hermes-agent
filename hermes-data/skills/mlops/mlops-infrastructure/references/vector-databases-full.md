---
name: vector-databases
description: "Vector similarity search for RAG — choose the right database: Chroma (open-source dev), FAISS (high-performance compute), Pinecone (managed production), Qdrant (Rust production with filtering)."
umbrella: vector-databases
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Vector Database, RAG, Embeddings, Similarity Search, FAISS, Chroma, Pinecone, Qdrant]
---

# Vector Databases — Choosing the Right One

This umbrella covers all vector database options for RAG and semantic search applications.

## Decision Tree

```
What is your deployment context?
├── Local development / open-source project
│   └── → Chroma (references/chroma.md)
│         Easiest setup, 4-function API, self-hosted.
├── Billions of vectors on GPU / high-performance compute
│   └── → FAISS (references/faiss.md)
│         Facebook's optimized library, no server needed.
├── Managed production / serverless / auto-scaling
│   └── → Pinecone (references/pinecone.md)
│         Fully managed, low latency, hybrid search.
└── Production with advanced filtering / Rust-powered
    └── → Qdrant (references/qdrant.md)
          HNSW + sparse vectors + multi-tenancy.
```

## Reference Files

| Database | Type | Best For |
|----------|------|---------|
| `chroma.md` | Open-source | Local dev, open-source projects, semantic search |
| `faiss.md` | Library | Billion-scale on GPU, no server, HPC |
| `pinecone.md` | Managed cloud | Serverless production, auto-scaling |
| `qdrant.md` | Self-hosted / cloud | Production with filtering, sparse+dense |

## Quick Comparison

| Feature | Chroma | FAISS | Pinecone | Qdrant |
|---------|--------|-------|----------|--------|
| Deployment | Self-hosted | Library | Managed cloud | Self-hosted / cloud |
| Scalability | Medium | Billions | Unlimited | Unlimited |
| GPU support | No | Yes | Yes | No |
| Filtering | Metadata | No | Yes | Yes |
| Latency | Low | Very Low | Low | Low |
| Setup effort | Very Low | Low | Very Low | Medium |
| Cost | Free (self) | Free | Pay-per-use | Free (self) / Paid cloud |
