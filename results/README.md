# Early Exploratory Simulation Output

This note records the first exploratory `compare` output from the initial synchronous KVFlow simulator before overlap-aware pipeline modeling was added. These are not benchmark results. They are an early simulation snapshot intended to make the design space concrete and highlight where the original latency model was too conservative.

## Recorded exploratory output

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

The main qualitative takeaway from that early output is narrow but useful: the model showed substantially reduced HBM traffic under KV-aware tiering, but it also showed higher simulated latency. That higher latency was expected in the first version because the simulator treated movement, decompression, and attention consumption in a conservative and largely synchronous way.

## Current limitations in the first model

- DMA overlap is not yet modeled.
- decompression overlap is not yet modeled.
- prefetch windows are simplified.
- compute/movement pipelining is incomplete.
- CXL and tier movement costs are approximate.

## What this result does show

- KVFlow can model KV-cache tiering.
- KVFlow can model hot/warm/cold residency.
- KVFlow can model compression savings.
- KVFlow can quantify HBM traffic reduction.

## What this result does not show

- It does not prove production speedup.
- It does not model real GPU kernels.
- It does not model full asynchronous execution.
- It does not represent silicon performance.

## Next modeling milestone

- asynchronous DMA prefetch
- overlapped decompression
- SRAM staging queues
- exposed vs hidden latency accounting
- token-level pipeline simulation

The simulator has now started moving in that direction, but this file preserves the first exploratory output as historical context.
