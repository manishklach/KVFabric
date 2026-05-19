# KVFlow Methodology

KVFlow is an approximate simulator for studying KV-cache residency and
movement tradeoffs. It is not a hardware benchmark harness and does not
attempt to reproduce production kernel timing.

## Workload Assumptions

The current default workload is loaded from
`examples/workloads/default_8k.json` and uses:

- `name: default_8k_decode`
- `description: Synthetic 8k-context decode workload for early KVFlow experiments`
- `model_layers: 32`
- `num_heads: 32`
- `head_dim: 128`
- `batch_size: 4`
- `context_length: 8192`
- `decode_steps: 128`
- `dtype_bytes: 2`
- `kv_block_tokens: 16`

Under the current simplified size model, the assumed KV block size is:

```text
kv_block_tokens * head_dim * dtype_bytes * 2 = 16 * 128 * 2 * 2 = 8,192 bytes
```

The access pattern intentionally mixes recent-window reuse, medium-range
reuse, and colder long-tail accesses so the simulator can exercise hot/warm/cold
placement policies.

## Memory Tier Assumptions

KVFlow models four tiers with the following default assumptions:

| Tier | Capacity | Bandwidth | Latency |
| --- | ---: | ---: | ---: |
| SRAM | 512 MiB | 20,000 GB/s | 25 ns |
| HBM | 8 GiB | 3,000 GB/s | 300 ns |
| CXL | 24 GiB | 300 GB/s | 900 ns |
| host DRAM | 64 GiB | 120 GB/s | 1,800 ns |

These values are approximate and intended only to establish a plausible
ordering of capacity and access cost.

## Compression Assumptions

Compression is modeled as effective footprint reduction rather than real
numeric quantization:

- `none = 1.0x`
- `int8 = 0.5x`
- `int4 = 0.25x`

Default decompression penalties are:

- `none = 0 ns`
- `int8 = 120 ns`
- `int4 = 260 ns`

These parameters are configurable through `CompressionConfig`.

## Latency Accounting

The current simulator uses step-level decode accounting. Each step combines:

- current token compute
- transfer time that remains exposed on the critical path
- decompression work that may be partially exposed
- background DMA prefetch
- SRAM staging completion

The core approximation is:

```text
effective_step_latency = max(compute_time, transfer_plus_decompression_window)
```

The compare output now also reports conservative breakdown fields:

- `compute_latency_ns`
- `transfer_latency_ns`
- `decompression_latency_ns`
- `hidden_transfer_ns`
- `exposed_transfer_ns`
- `overlap_ratio`

## Why The First Latency Model Was Conservative

The original exploratory model added movement, decompression, and access costs
largely serially. That was useful for early design sanity checks, but it
overstated stall cost because it did not let DMA, staging, and consumption
overlap in a realistic way.

## Why Future Overlap Modeling Matters

Real inference pipelines are not fully synchronous. Future work should
continue improving:

- asynchronous DMA prefetch behavior
- staged SRAM queue behavior
- decompression overlap with compute
- exposed versus hidden latency accounting
- finer-grained token pipeline simulation

Those improvements matter because residency policy may reduce traffic
meaningfully even when end-to-end latency depends on how much movement can be
hidden behind compute.
