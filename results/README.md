# Early Exploratory Simulation Output

This note records the first exploratory `compare` output from the initial
synchronous KVFlow simulator, before overlap-aware pipeline modeling was
introduced. These are not benchmark results. They are an early simulation
snapshot meant to expose the design space and make the initial modeling limits
explicit.

## Workload Assumptions

The current default workload is:

- `model_layers: 32`
- `num_heads: 32`
- `head_dim: 128`
- `batch_size: 4`
- `context_length: 8192`
- `decode_steps: 128`
- `dtype_bytes: 2`
- `kv_block_tokens: 16`

Under the current simplified model, the assumed KV block size is `8,192`
bytes. Default memory-tier assumptions are:

| Tier | Capacity | Bandwidth | Latency |
| --- | ---: | ---: | ---: |
| SRAM | 512 MiB | 20,000 GB/s | 25 ns |
| HBM | 8 GiB | 3,000 GB/s | 300 ns |
| CXL | 24 GiB | 300 GB/s | 900 ns |
| host DRAM | 64 GiB | 120 GB/s | 1,800 ns |

## Recorded Exploratory Output

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

The main takeaway from this early output is specific and limited: the model
showed substantially reduced HBM traffic under KV-aware tiering, but it also
showed higher simulated latency. That higher latency was expected because the
first model treated movement, decompression, and attention consumption in a
conservative, largely synchronous way.

## Visual Summary

```text
HBM Reads
Baseline : ########################
KVFlow   : #

SRAM Hit Rate
Baseline : 0%
KVFlow   : 51%

Compression Savings
KVFlow   : 164 MB
```

## Latency Breakdown

| Path | Components |
| --- | --- |
| Baseline | compute, HBM read, exposed transfer |
| KVFlow | compute, HBM read, CXL read, decompression, hidden transfer, exposed transfer |

The current compare output also reports:

- `compute_latency_ns`
- `transfer_latency_ns`
- `decompression_latency_ns`
- `hidden_transfer_ns`
- `exposed_transfer_ns`
- `overlap_ratio`

## Current Limitations In The First Model

- DMA overlap is not yet modeled.
- decompression overlap is not yet modeled.
- prefetch windows are simplified.
- compute/movement pipelining is incomplete.
- CXL and tier movement costs are approximate.

## What This Result Does Show

- KVFlow can model KV-cache tiering.
- KVFlow can model hot/warm/cold residency.
- KVFlow can model compression savings.
- KVFlow can quantify HBM traffic reduction.

## What This Result Does Not Show

- It does not prove production speedup.
- It does not model real GPU kernels.
- It does not model full asynchronous execution.
- It does not represent silicon performance.

## Next Modeling Milestone

- asynchronous DMA prefetch
- overlapped decompression
- SRAM staging queues
- exposed vs hidden latency accounting
- token-level pipeline simulation

The simulator has now started moving in that direction, but this file preserves
the first exploratory output as historical context.
