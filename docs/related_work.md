# Related Work

KVFabric was previously named KVFlow. The rename was introduced to avoid
confusion with the separate academic KVFlow project focused on workflow-aware
prefix caching for multi-agent systems.

## Name Collision: KVFlow vs Workflow-Aware KVFlow

This repository is unrelated to the academic project and paper titled
“KVFlow: Efficient Prefix Caching for Accelerating LLM-Based Multi-Agent
Workflows.”

That academic KVFlow focuses on workflow-aware prefix caching for multi-agent
execution. It discusses agent step graphs, steps-to-execution eviction, and
CPU-to-GPU prefetch behavior for agent workflows.

This repository focuses on a different problem: inference memory hierarchy
simulation for KV-cache movement, residency, staging, compression, and
tier-aware orchestration across SRAM, HBM, CXL memory, and host DRAM.

| Dimension | Academic KVFlow | This Repository |
| --- | --- | --- |
| Primary focus | Workflow-aware prefix caching | KV memory hierarchy orchestration |
| Workload | Multi-agent workflows | Long-context inference memory movement |
| Key mechanism | Agent Step Graph | Residency tiering + compression + staging |
| Memory focus | GPU/CPU cache reuse | SRAM/HBM/CXL/DRAM hierarchy |
| Current status | Research paper/system | Exploratory simulator |

## Related Directions

The problem explored in this repository is adjacent to several industry and
research directions:

- vLLM PagedAttention
- TensorRT-LLM KV reuse and other KV cache optimizations
- NVIDIA Dynamo KV-aware routing
- KV cache quantization research such as KIVI
- CXL memory pooling
- multi-tenant inference memory pressure

These are mentioned as surrounding context, not as equivalent systems.
