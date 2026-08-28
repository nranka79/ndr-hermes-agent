# PyTorch FSDP — Reference
*Source skill: pytorch-fsdp (absorbed into distributed-training umbrella)*
*Source path: mlops/training/pytorch-fsdp/SKILL.md*

## When to Use

- Training very large models where you need fine-grained control over sharding
- When Accelerate's abstraction is too limiting
- Custom sharding strategies beyond what Accelerate/DeepSpeed offer
- Research requiring access to low-level distributed primitives

## Key Concepts

**Sharding Strategies:**
- `FULL_SHARD` — shards model parameters, gradients, and activations
- `SHARD_GRAD_OP` — shards gradients and activations only
- `NO_SHARD` — DDP-like, no parameter sharding
- `HYBRID_SHARD` — shard within a node, replicate across nodes

**Core API:**
```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import ShardingStrategy

model = FSDP(
    model,
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    device_id=torch.cuda.current_device(),
    use_orig_params=True,
)
```

## Key Commands / Patterns

**Initialization:**
```python
torch.distributed.init_process_group(backend="nccl")
```

**Device Mesh (recommended):**
```python
from torch.distributed.device_mesh import init_device_mesh

mesh_1d = init_device_mesh("cuda", mesh_shape=(8,))
mesh_2d = init_device_mesh("cuda", mesh_shape=(2, 8), mesh_dim_names=("dp", "tp"))
```

**Join Context Manager (uneven inputs):**
```python
with torch.distributed.algorithms.Join(
    [model],
    enable=True,
    throw_on_early_termination=False
):
    # training loop
```

**Static Graph (DDP):**
```python
model_DDP = DistributedDataParallel(model, static_graph=True)
```

## Mixed Precision with FSDP

```python
from torch.distributed.fsdp import MixedPrecision

mp_policy = MixedPrecision(
    param_dtype=torch.bfloat16,
    reduce_dtype=torch.float32,
    buffer_dtype=torch.bfloat16,
)
model = FSDP(model, mixed_precision=mp_policy)
```

## CPU Offloading

```python
from torch.distributed.fsdp import CPUOffload

model = FSDP(model, cpu_offload=CPUOffload(offload_params=True))
```
