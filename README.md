# KVFlow

KVFlow is a research prototype for semantic KV-cache orchestration in long-context LLM inference.

It explores a simple but increasingly relevant systems hypothesis: as inference context windows grow, KV-cache management becomes less of a raw tensor-allocation problem and more of a memory-orchestration problem. Instead of treating KV-cache only as bytes in HBM, KVFlow models each KV block as a first-class systems object with lifecycle, reuse probability, residency tier, compression state, and movement schedule.

KVFlow is intentionally scoped as a simulator and architecture study. It does not replace a model-serving stack, a GPU runtime, or an accelerator vendor roadmap. It is meant to help infrastructure, runtime, and accelerator teams reason about what a KV-aware control plane or memory-side accelerator could look like.

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
                         movement + metadata decisions
                                        |
        +-------------------------------+------------------------------+
        |                               |                              |
   +----v----+                    +-----v-----+                  +-----v------+
   |  SRAM   |                    |    HBM    |                  |    CXL     |
   | staging | <---- DMA-like --->| main tier | <---- DMA -----> | expansion  |
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
pytest
```

Python 3.11+ is recommended. The simulator uses the standard library only. `pytest` is optional for test execution.

## Sample output

The simulator prints a compact comparison table:

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

The exact numbers above come from the current default workload and policy settings. They are meant to illustrate tradeoffs in residency, movement, and compression behavior, not claim hardware performance or guaranteed end-to-end wins.

## Model assumptions

KVFlow keeps the math intentionally approximate and documented:

- KV block sizes are derived from layer, head, token, and dtype parameters.
- Memory reads accumulate tier latency plus transfer time based on configured bandwidth.
- Compression changes effective byte footprint and adds a decompression penalty.
- Prefetch improves expected SRAM residency but still incurs transfer cost.

See [docs/memory_model.md](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/memory_model.md) and [docs/compression.md](/C:/Users/ManishKL/Documents/Playground/KVFlow/docs/compression.md) for details.

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
- [Architecture Diagram Source](/C:/Users/ManishKL/Documents/Playground/KVFlow/diagrams/kvflow_architecture.md)
- [Systems Blog Draft](/C:/Users/ManishKL/Documents/Playground/KVFlow/blog/kv-cache-is-the-new-memory-hierarchy.md)
