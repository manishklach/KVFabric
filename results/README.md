# KVFabric Results Notes

This directory records exploratory simulator outputs for KVFabric. These are
not benchmark results. They are reproducible simulation artifacts intended to
make the memory-hierarchy and overlap tradeoffs inspectable.

## Current Compare Snapshot

The current default `compare` run on `examples/workloads/default_8k.json`
produces:

```text
metric                      | baseline       | kvfabric       | delta
------------------------------------------------------------------------------
total_bytes_moved           | 0              | 153,878,528    | 153,878,528
hbm_bytes_read              | 166,199,296    | 165,150,720    | -1,048,576
cxl_bytes_read              | 0              | 524,288        | 524,288
host_bytes_read             | 0              | 0              | 0
compression_savings_bytes   | 0              | 524,288        | 524,288
simulated_latency_ns        | 6,510,761.92   | 6,520,374.68   | 9,612.76
compute_latency_ns          | 3,651,840.00   | 3,651,840.00   | 0.0000
transfer_latency_ns         | 6,498,700.97   | 5,819,828.76   | -678,872.21
decompression_latency_ns    | 0.0000         | 7,680.00       | 7,680.00
hidden_latency_ns           | 3,644,899.05   | 3,651,840.00   | 6,940.95
exposed_latency_ns          | 2,858,921.92   | 2,868,534.68   | 9,612.76
hidden_transfer_ns          | 3,644,859.05   | 3,651,840.00   | 6,980.95
exposed_transfer_ns         | 2,853,841.92   | 2,863,174.68   | 9,332.76
overlap_ratio               | 0.5604         | 0.5601         | -0.0004
sram_hit_rate               | 0.0000         | 0.1107         | 0.1107
blocks_evicted              | 0              | 0              | 0
blocks_compressed           | 0              | 128            | 128
prefetched_blocks           | 0              | 2,208          | 2,208
staged_blocks               | 0              | 2,208          | 2,208
```

## Visual Summary

![HBM Bytes vs Context Length](./figures/hbm_vs_context_length.png)

![Exposed vs Hidden Latency](./figures/exposed_vs_hidden_latency.png)

## Interpretation

The current default run is intentionally modest. It reduces HBM reads only
slightly and improves SRAM locality, but it still increases total latency by a
small amount. That is an honest result: on smaller or easier workloads, the
orchestration machinery can add overhead without enough memory pressure to pay
for itself.

## Cost Model Proxy

Running `python simulator/run_experiment.py --mode compare --cost-model`
currently reports:

| Signal | Baseline | KVFabric | Delta |
| --- | ---: | ---: | ---: |
| HBM capacity proxy | `144.00` | `144.00` | `0.00` |
| CXL capacity proxy | `0.00` | `108.00` | `108.00` |
| Latency penalty proxy | `976.61` | `978.06` | `1.44` |
| Cost / 1M tokens proxy | `220.00` | `241.37` | `21.38` |

The cost proxy therefore tells a similar story to the latency numbers: under
the default 8k workload, orchestration is visible, but it is not yet strongly
beneficial.

## Historical Early Exploratory Output

The first synchronous version of the simulator produced the following
exploratory output before overlap-aware modeling was introduced:

```text
metric                      | baseline       | kvfabric       | delta
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

That early result is still useful because it showed exactly why a synchronous
movement model is too pessimistic for serious architecture exploration.

## Current Limitations

- The overlap model is still approximate.
- There is no GPU kernel execution.
- DMA engines are simulated scheduling constructs, not real hardware.
- Scheduler decisions remain heuristic and synthetic.
- Live runtime integration is still not implemented.
