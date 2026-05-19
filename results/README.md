# Early Exploratory Simulation Output

This note records the first exploratory `compare` output from the initial
synchronous KVFlow simulator, before overlap-aware pipeline modeling was
introduced. These are not benchmark results. They are an early simulation
snapshot meant to expose the design space and make the initial modeling limits
explicit.

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
