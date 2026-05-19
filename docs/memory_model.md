# KVFlow Memory Model

KVFlow models a four-tier hierarchy:

- SRAM staging buffer
- HBM
- CXL-attached memory
- host DRAM

The model is intentionally approximate. It is meant to support thought experiments about scheduling and movement, not cycle-accurate hardware analysis.

## Tier fields

Each memory tier is represented by:

- `capacity_bytes`
- `bandwidth_gbps`
- `latency_ns`
- `used_bytes`

The simulator treats `bandwidth_gbps` as effective transfer bandwidth for KV movement. Transfer time is computed as:

```text
transfer_time_ns = moved_bytes / bytes_per_ns
bytes_per_ns = (bandwidth_gbps * 1e9) / 8 / 1e9
```

Which simplifies to:

```text
bytes_per_ns = bandwidth_gbps / 8
```

And therefore:

```text
transfer_time_ns = moved_bytes * 8 / bandwidth_gbps
```

The total service cost of reading a block from a tier is:

```text
tier_latency_ns + transfer_time_ns + decompression_penalty_ns
```

## Default intuition

The default configuration reflects a common systems intuition rather than a specific product:

- SRAM has very low latency and limited capacity.
- HBM is the primary high-bandwidth working set.
- CXL memory offers larger capacity with higher access cost.
- host DRAM is the farthest tier and represents spill capacity.

## Residency model

A block occupies one current tier at a time. KVFlow also allows a block to be compressed, which changes its effective footprint and therefore tier occupancy pressure.

The simulator does not explicitly model:

- cacheline granularity
- page tables
- overlapping DMA engines
- coherence traffic
- contention between independent compute streams

Those are future extensions, not current claims.

## Why SRAM exists in the model

SRAM in KVFlow is a staging buffer, not a full KV store. It represents the idea that a narrow hot set can be brought close to the attention datapath if the runtime predicts imminent reuse well enough.

This is useful for exploring whether a metadata-aware scheduler can improve effective hit rate without pretending all KV should permanently reside in the closest memory.
