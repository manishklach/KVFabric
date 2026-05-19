# KVFlow Methodology

KVFlow is an approximate simulator for studying KV-cache residency and movement tradeoffs. It is not a hardware benchmark harness and does not attempt to reproduce production kernel timing.

## Workload assumptions

The default workload uses a fixed-size synthetic decode trace derived from:

- `model_layers: 32`
- `num_heads: 32`
- `head_dim: 128`
- `batch_size: 4`
- `context_length: 8192`
- `decode_steps: 128`
- `dtype_bytes: 2`

The access pattern intentionally mixes recent-window reuse, medium-range reuse, and colder long-tail accesses so the simulator can exercise hot/warm/cold placement policies.

## Memory tier assumptions

KVFlow models four tiers:

- SRAM staging buffer
- HBM
- CXL-attached memory
- host DRAM

Each tier has approximate capacity, bandwidth, and latency parameters. These are not intended to represent a specific shipping platform. They are chosen to provide a plausible ordering of closeness and movement cost.

## Compression assumptions

Compression is modeled as effective footprint reduction rather than real numeric quantization:

- `none = 1.0x`
- `int8 = 0.5x`
- `int4 = 0.25x`

Compressed blocks also carry simulated decompression penalties during access or staging.

## Latency accounting

The current simulator uses step-level decode accounting. Each step combines:

- current token compute
- synchronous reads that are still exposed to the step
- DMA prefetch that can overlap in the background
- decompression work that may be partially hidden
- SRAM staging completion

The core approximation is:

```text
effective_step_latency = max(compute_time, overlapped_transfer_time)
```

Where the transfer side may include decompression work when it cannot be hidden.

## Why the first latency model was conservative

The original exploratory model added movement, decompression, and access costs largely serially. That was useful for early design sanity checks, but it overstated stall cost because it did not let DMA, staging, and consumption overlap in a realistic way.

## Why future overlap modeling matters

Real inference pipelines are not fully synchronous. Future work should continue improving:

- asynchronous DMA prefetch behavior
- staged SRAM queue behavior
- decompression overlap with compute
- exposed versus hidden latency accounting
- finer-grained token pipeline simulation

Those improvements matter because residency policy may reduce traffic meaningfully even when end-to-end latency depends on how much movement can be hidden behind compute.
