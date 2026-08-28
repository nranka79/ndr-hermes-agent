---
name: gpu-cloud-providers
description: "GPU cloud providers for ML training and inference — Modal (serverless GPUs) or Lambda Labs (reserved/on-demand GPUs). Both support Python-native execution, Jupyter, and SSH."
umbrella: gpu-cloud-providers
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GPU Cloud, Modal, Lambda Labs, Serverless GPU, Reserved GPU, Training, Inference, Cloud Infrastructure]
---

# GPU Cloud Providers — Choosing the Right Platform

Serverless and reserved GPU cloud options for ML workloads.

## Decision Tree

```
Need GPU compute in the cloud?
├── Serverless — pay-per-second, auto-scale, no provisioning
│   └── → Modal (references/modal.md)
│         Python-native, fast cold starts, ephemeral.
├── Reserved / on-demand — dedicated GPUs, predictable pricing
│   └── → Lambda Labs (references/lambda-labs.md)
│         A100/H100, Jupyter, SSH, multi-GPU, persistent.
└── Both support:
    • Python execution
    • Jupyter-compatible environments
    • SSH access (Lambda) / Volume mounts (Modal)
    • PyTorch / JAX / TensorFlow
```

## Reference Files

| Provider | Model | Use Case |
|----------|-------|---------|
| `references/modal.md` | Serverless, pay-per-second | Inference APIs, batch jobs, dev/test |
| `references/lambda-labs.md` | Reserved/on-demand A100/H100 | Training, large inference, persistent infra |

## Key Differences

| Feature | Modal | Lambda Labs |
|---------|-------|------------|
| Pricing | Per-second | Per-hour (reserved) |
| Scaling | Auto (serverless) | Manual (you manage) |
| Cold starts | Yes (fast) | No (dedicated) |
| GPU types | A100, H100, L40S | A100, H100 |
| Persistence | Ephemeral (volumes optional) | Persistent instances |
| Jupyter | Via tunneling | Native |
| Best for | Inference APIs, batch | Training, large jobs |

---

## Related Skills (absorbed into this umbrella)

### lambda-labs-gpu-cloud → gpu-cloud-providers

**Absorbed:** lambda-labs-gpu-cloud (2026-05-08)

**Reason:** Class-level umbrella already exists. lambda-labs is the reserved-GPU branch of the same class as modal (serverless GPU). gpu-cloud-providers already references lambda-labs as the reserved/on-demand path in its decision tree.

**Content:** Full SKILL.md copied to `references/lambda-labs.md`

---

### modal-serverless-gpu → gpu-cloud-providers

**Absorbed:** modal-serverless-gpu (2026-05-08)

**Reason:** Class-level umbrella already exists. modal is the serverless-GPU branch of the same class as lambda-labs. gpu-cloud-providers already references modal as the serverless path in its decision tree.

**Content:** Full SKILL.md copied to `references/modal.md`

**Both skills archived** — content absorbed into gpu-cloud-providers umbrella.
