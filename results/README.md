# KVFabric Results Notes

This directory records exploratory simulator outputs for KVFabric. These are
not benchmark results. They are architecture-oriented simulation snapshots
used to study how residency, movement, staging, compression, and overlap
assumptions interact.

## Current Compare Snapshot

The current overlap-aware `compare` run on the default `default_8k.json`
workload produces:

```text
metric                      | baseline       | kvfabric       | delta
------------------------------------------------------------------------------
total_bytes_moved           | 0              | 153,878,528    | 153,878,528
hbm_bytes_read              | 166,199,296    | 165,150,720    | -1,048,576
cxl_bytes_read              | 0              | 524,288        | 524,288
host_bytes_read             | 0              | 0              | 0
compression_savings_bytes   | 0              | 524,288        | 524,288
simulated_latency_ns        | 6,505,681.92   | 5,841,815.40   | -663,866.52
compute_latency_ns          | 3,651,840.00   | 3,651,840.00   | 0.0000
transfer_latency_ns         | 6,498,700.97   | 5,819,828.76   | -678,872.21
decompression_latency_ns    | 0.0000         | 7,680.00       | 7,680.00
hidden_transfer_ns          | 3,644,859.05   | 3,637,533.35   | -7,325.70
exposed_transfer_ns         | 2,853,841.92   | 2,182,295.40   | -671,546.52
overlap_ratio               | 0.5609         | 0.6242         | 0.0633
sram_hit_rate               | 0.0000         | 0.1107         | 0.1107
blocks_evicted              | 0              | 0              | 0
blocks_compressed           | 0              | 128            | 128
prefetched_blocks           | 0              | 2,208          | 2,208
staged_blocks               | 0              | 2,160          | 2,160
```

## Visual Summary

```text
HBM Reads
Baseline  : ########################
KVFabric  : #######################

Exposed Latency
Baseline  : ########################
KVFabric  : ##################

SRAM Hit Rate
Baseline  :
KVFabric  : ########################
```

## Latency Breakdown

| Path | Compute | Transfer | Decompression | Hidden transfer | Exposed transfer |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | `3,651,840.00` ns | `6,498,700.97` ns | `0.00` ns | `3,644,859.05` ns | `2,853,841.92` ns |
| KVFabric | `3,651,840.00` ns | `5,819,828.76` ns | `7,680.00` ns | `3,637,533.35` ns | `2,182,295.40` ns |

The current model shows slightly lower HBM traffic and lower exposed transfer
latency on the default workload, while also introducing CXL reads,
compression, and explicit staging activity. That should be interpreted as a
modeling result, not as a production performance claim.

## Cost Model Proxy

Running `python simulator/run_experiment.py --mode compare --cost-model`
currently reports:

| Signal | Baseline | KVFabric | Delta |
| --- | ---: | ---: | ---: |
| HBM capacity proxy | `144.00` | `144.00` | `0.00` |
| CXL capacity proxy | `0.00` | `108.00` | `108.00` |
| Latency penalty proxy | `975.85` | `876.27` | `-99.58` |
| Cost / 1M tokens proxy | `219.85` | `221.49` | `1.64` |

This proxy is intentionally rough. It is meant to help reason about whether a
memory-tier tradeoff shifts cost pressure, not to estimate deployment spend.

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

That early result is preserved because it clearly showed the risk of treating
all movement and decompression costs synchronously. It reduced HBM traffic but
overstated end-to-end latency by leaving too little overlap in the model.
