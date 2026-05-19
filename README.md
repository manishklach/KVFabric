# KVFlow

KVFlow explores semantic KV-cache orchestration for long-context LLM
inference.

It is an exploratory simulator for studying whether future inference systems
may require more explicit KV-aware memory orchestration layers. The project
models KV residency tiering, compression, SRAM staging, prefetch scheduling,
HBM/CXL movement tradeoffs, and hot/warm/cold KV classification. The goal is
not to replace GPU compute or serving frameworks, but to give infrastructure
and systems teams a concrete environment for reasoning about KV-cache
movement, placement, and reuse.

KVFlow is intentionally positioned as a careful architecture exploration. It
uses approximate workload and memory models to investigate how KV-cache might
evolve from a tensor allocation concern into a first-class inference memory
orchestration problem.

## About KVFlow

KVFlow is a systems-oriented research prototype for infrastructure engineers,
runtime teams, systems researchers, and accelerator architects who want to
study KV-cache placement and movement as an inference-memory orchestration
problem rather than only as a buffer-allocation problem.

## Architecture

```text
                +----------------------+
                |    GPU Compute       |
                | Attention / Matmul   |
                +----------+-----------+
                           |
                 KV Commands / Requests
                           |
                +----------v-----------+
                |      KVFlow          |
                |----------------------|
                | DMA Scheduler        |
                | Residency Tracker    |
                | Compression Engine   |
                | SRAM Staging Buffers |
                | Prefetch Queue       |
                +----------+-----------+
                           |
         +----------------+----------------+
         |                |                |
      +--v---+        +---v---+        +---v---+
      | HBM  |        |  CXL  |        | DRAM  |
      +------+        +-------+        +-------+
```

KVFlow does not replace GPU compute. It explores orchestration of KV-cache
movement and residency around the compute path, especially when long-context
decode becomes constrained by memory placement, bandwidth, and reuse behavior.

## Why This Matters Now

Long-context inference, multi-tenant serving, and reuse-heavy decode workloads
are pushing KV-cache toward the center of serving system design. As context
windows grow, KV state expands quickly, HBM pressure rises, memory bandwidth
becomes a larger share of the bottleneck, and inference economics depend more
on how efficiently that state is placed and moved.

The industry is already moving toward more explicit KV management. vLLM
PagedAttention made KV layout and paging a first-order systems topic.
TensorRT-LLM has brought more attention to KV reuse and compressed cache
representations. NVIDIA Dynamo has highlighted KV-aware routing as part of
runtime control. CXL memory pools and other expanded-memory designs add
another dimension: orchestration across tiers may matter as much as raw
capacity.

KVFlow exists to study that trend in a restrained way.

## What KVFlow Models

- KV residency tiering across SRAM, HBM, CXL memory, and host DRAM
- hot/warm/cold block classification
- simulated KV compression states and decompression penalties
- SRAM staging and prefetch queues
- DMA-like movement scheduling
- baseline versus KV-aware compare runs

## What KVFlow Is Not

- Not a production accelerator
- Not a GPU replacement
- Not a CUDA competitor
- Not a benchmark suite
- Not production silicon

KVFlow is currently an exploratory systems simulator and architecture
prototype.

## Repository Layout

```text
KVFlow/
  docs/
  results/
  simulator/
    kvflow/
    examples/
    results/
  diagrams/
  blog/
  tests/
```

## Quickstart

```bash
cd KVFlow
python simulator/run_experiment.py --mode baseline
python simulator/run_experiment.py --mode kvflow
python simulator/run_experiment.py --mode compare
python -m pytest
```

Python 3.11+ is recommended. The simulator uses the standard library only.
`pytest` is optional for test execution.

## Early Exploratory Simulation Output

The first synchronous version of the simulator produced the following
exploratory output:

```text
metric                      | baseline       | kvflow         | delta
------------------------------------------------------------------------------
total_bytes_moved           | 0              | 850,919,424    | 850,919,424
hbm_bytes_read              | 1,329,594,368  | 27,262,976     | -1,302,331,392
cxl_bytes_read              | 0              | 227,540,992    | 227,540,992
host_bytes_read             | 0              | 0              | 0
compression_savings_bytes   | 0              | 164,626,432    | 164,626,432
simulated_latency_ns        | 9,631,984.98   | 72,242,087.30  | 62,610,102.32
sram_hit_rate               | 0.0000         | 0.5126         | 0.5126
blocks_evicted              | 0              | 0              | 0
blocks_compressed           | 0              | 5,696          | 5,696
```

These are not benchmark results. The early model showed reduced HBM traffic
but higher simulated latency. That behavior is expected in the original
version because movement, decompression, and consumption were modeled
conservatively and largely synchronously.

The fuller note is in [results/README.md](/C:/Users/ManishKL/Documents/Playground/KVFlow/results/README.md).

## Why Overlap Matters

The first simulator revision made the movement tradeoff visible, but it also
overstated stall cost because DMA movement, decompression, and attention
consumption were treated too serially. The current simulator now includes an
overlap-aware pipeline with asynchronous prefetch, SRAM staging, exposed
versus hidden transfer accounting, and partial decompression overlap.

This remains simulated and approximate. It is meant to improve the realism of
the orchestration model, not to imply production performance claims.

## Current Compare Snapshot

The current overlap-aware model still shows higher simulated latency than the
baseline path, but the gap is materially smaller than in the first fully
synchronous version and is now broken into exposed versus hidden transfer
components.

| Signal | Baseline | KVFlow |
| --- | --- | --- |
| HBM traffic | `1,329,594,368` bytes | `708,837,376` bytes |
| Exposed latency | `5,936,655.36` ns | `12,917,341.91` ns |
| SRAM hit rate | `0.0000` | `0.1441` |

KVFlow currently demonstrates a modeling framework for studying KV-cache
residency and movement tradeoffs.

## Future Work

- asynchronous DMA overlap refinements
- overlapped decompression with richer staging behavior
- token-level pipeline simulation
- realistic decode traces and reuse-distance studies
- CXL-aware residency policies
- KV locality prediction heuristics
- scheduler policy comparisons across workloads
- optional FPGA prototype exploration
- runtime integration experiments with serving stacks

## Releases

- [v0.1.0 — Initial architecture and simulation prototype](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/releases/v0.1.0.md)

## Documentation

- [Architecture](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/architecture.md)
- [Memory Model](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/memory_model.md)
- [Accelerator Sketch](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/accelerator.md)
- [Scheduler Policy](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/scheduler.md)
- [Compression Model](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/compression.md)
- [Industry Context](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/industry_context.md)
- [Methodology](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/methodology.md)
- [Repository Description](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/repository_description.md)
- [Recommended GitHub Topics](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/github_topics.md)
- [Release Notes v0.1.0](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/releases/v0.1.0.md)
- [Exploratory Results Note](/C:/Users/ManishKL/Documents/Playground/KVFlow/results/README.md)
- [Architecture Diagram Source](/C:/Users/ManishKL/Documents/Playground/KVFlow/diagrams/kvflow_architecture.md)
- [Systems Blog Draft](/C:/Users/ManishKL/Documents/Playground/KVFlow/blog/kv-cache-is-the-new-memory-hierarchy.md)

## Research Prototype Disclaimer

KVFlow is an exploratory research simulator intended for studying KV-cache
residency, movement, and compression tradeoffs in long-context inference
systems.

The project does not model real GPU kernels, production runtimes, or
production silicon performance.

Current latency numbers are conservative and largely synchronous because
asynchronous overlap and pipeline execution are still under development.
