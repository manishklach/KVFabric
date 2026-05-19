# KVFlow

KVFlow is a research prototype for semantic KV-cache orchestration in long-context LLM inference.

It explores a simple but increasingly relevant systems hypothesis: as inference context windows grow, KV-cache management becomes less of a raw tensor-allocation problem and more of a memory-orchestration problem. Instead of treating KV-cache only as bytes in HBM, KVFlow models each KV block as a first-class systems object with lifecycle, reuse probability, residency tier, compression state, and movement schedule.

KVFlow is intentionally scoped as a simulator and architecture study. It does not replace a model-serving stack, a GPU runtime, or an accelerator vendor roadmap. It is meant to help infrastructure, runtime, and accelerator teams reason about what a KV-aware control plane or memory-side accelerator could look like.

KVFlow currently demonstrates a modeling framework for studying KV-cache residency and movement tradeoffs.

## Why KV-cache matters

Modern inference stacks increasingly spend engineering effort on KV-cache placement, reuse, paging, routing, and movement:

- Long-context decoding grows memory footprint roughly with generated context.
- Multi-tenant serving adds contention and residency pressure.
- Reuse-aware runtimes already differentiate between recently used and spillable state.
- Emerging designs increasingly rely on tiered memory, prefetched movement, and compressed cache state.

That trend suggests a broader architectural shift: KV-cache is starting to behave like its own memory hierarchy problem.

## What KVFlow is

KVFlow models:

- KV blocks with semantic metadata such as hot/warm/cold temperature
- A tiered memory path across SRAM, HBM, CXL memory, and host DRAM
- Policy-driven prefetch, demotion, eviction, and compression
- A DMA-like movement scheduler and decompression penalties
- Baseline versus KV-aware execution for comparative analysis

## What KVFlow is not

- Not another GPU
- Not a model-serving framework replacement
- Not a fantasy chip startup deck
- Not a claim of production advantage over existing vendors

KVFlow is a careful architecture and runtime exploration.

## Architecture

```text
                    +--------------------------------------+
                    |             KVFlow Runtime           |
                    |--------------------------------------|
                    |  access stream + block metadata      |
                    |  hot/warm/cold classifier            |
                    |  residency tracker                   |
                    |  prefetch / eviction scheduler       |
                    |  compression policy engine           |
                    +-------------------+------------------+
                                        |
                                        v
                         +--------------+---------------+
                         |         GPU Compute          |
                         +--------------+---------------+
                                        ||
                                        || KVFlow DMA Prefetch
                                        \/
                         +--------------+---------------+
                         |         SRAM staging         |
                         +--------------+---------------+
                                        ||
                                        || Attention consumption
                                        \/
        +-------------------------------+------------------------------+
        |                               |                              |
   +----v----+                    +-----v-----+                  +-----v------+
   |  SRAM   |                    |    HBM    |                  |    CXL     |
   | staging |                    | main tier |                  | expansion  |
   +----+----+                    +-----+-----+                  +-----+------+
        |                               |                              |
        +-------------------------------+------------------------------+
                                        |
                                  +-----v------+
                                  | host DRAM  |
                                  | cold spill |
                                  +------------+
```

## Repository layout

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

Python 3.11+ is recommended. The simulator uses the standard library only. `pytest` is optional for test execution.

## Early Exploratory Simulation Output

The first synchronous version of the simulator produced the following exploratory output:

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

These are not benchmark results. The early model showed reduced HBM traffic but higher simulated latency. That outcome is expected in the original version because movement, decompression, and consumption were treated conservatively and largely synchronously.

The fuller note is in [results/README.md](/C:/Users/ManishKL/Documents/Playground/KVFlow/results/README.md).

## Why overlap matters

The first simulator revision made it easy to see traffic tradeoffs, but it overstated stall cost because it added DMA movement, decompression, and attention consumption too serially. The current simulator now includes an overlap-aware decode pipeline with:

- asynchronous DMA prefetch
- prefetch queues
- SRAM staging
- partially overlapped decompression
- exposed versus hidden transfer accounting

This remains approximate and exploratory, but it is a better framework for asking whether KV-aware movement can be hidden behind decode compute.

## Current compare chart

The compare CLI now emits additional overlap metrics. A current overlap-aware snapshot looks like this:

| Signal | Baseline | KVFlow |
| --- | --- | --- |
| HBM traffic | `1,329,594,368` bytes | `708,837,376` bytes |
| Exposed latency | `5,936,655.36` ns | `12,917,341.91` ns |
| SRAM hit rate | `0.0000` | `0.1441` |

This remains simulated and approximate. The current overlap-aware model still shows higher simulated latency than baseline, but the gap is substantially smaller than in the first fully synchronous version and is now broken into exposed versus hidden transfer components.

## Model assumptions

KVFlow keeps the math intentionally approximate and documented:

- KV block sizes are derived from layer, head, token, and dtype parameters.
- Memory reads accumulate tier latency plus transfer time based on configured bandwidth.
- Compression changes effective byte footprint and adds a decompression penalty.
- Prefetch improves expected SRAM residency and may hide movement behind compute.

See [docs/memory_model.md](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/memory_model.md), [docs/compression.md](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/compression.md), and [docs/methodology.md](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/methodology.md) for details.

## Roadmap

- Add richer multi-tenant traces and reuse-distance distributions
- Model attention window skew and prompt-prefix sharing
- Simulate QoS-aware placement under concurrent decode streams
- Explore metadata-plane costs and scheduling queue contention
- Add visualization for tier occupancy and access heat over time
- Compare alternative compression and admission heuristics

## Documentation

- [Architecture](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/architecture.md)
- [Memory Model](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/memory_model.md)
- [Accelerator Sketch](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/accelerator.md)
- [Scheduler Policy](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/scheduler.md)
- [Compression Model](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/compression.md)
- [Industry Context](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/industry_context.md)
- [Methodology](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/methodology.md)
- [Exploratory Results Note](/C:/Users/ManishKL/Documents/Playground/KVFlow/results/README.md)
- [Architecture Diagram Source](/C:/Users/ManishKL/Documents/Playground/KVFlow/diagrams/kvflow_architecture.md)
- [Systems Blog Draft](/C:/Users/ManishKL/Documents/Playground/KVFlow/blog/kv-cache-is-the-new-memory-hierarchy.md)
