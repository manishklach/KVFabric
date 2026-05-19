# Policy Comparison

This note records an exploratory policy comparison on the default synthetic
`default_8k.json` workload. It is not a benchmark. The goal is to show how
different policy shapes can shift movement, compression, and exposed stall in
the simulator.

## Policy Compare Output

```text
policy               | hbm_bytes_read  | cxl_bytes_read | sram_hit_rate | exposed_latency_ns | compression_savings_bytes
------------------------------------------------------------------------------------------------------------------------
LRUHotWindowPolicy   | 165,150,720     | 524,288        | 0.1296        | 2,036,710.59       | 524,288
LFUCompressionPolicy | 133,693,440     | 15,990,784     | 0.0918        | 4,215,207.91       | 7,864,320
HotWarmColdPolicy    | 165,412,864     | 393,216        | 0.1107        | 2,182,295.40       | 393,216
```

## Visual Summary

```text
HBM Reads
LRUHot    : ########################
LFUComp   : ###################
HotWarm   : ########################

Exposed Latency
LRUHot    : ############
LFUComp   : ########################
HotWarm   : ############
```

## What This Suggests

- `LRUHotWindowPolicy` is the most locality-friendly of the three under this
  default workload. It maintains the highest SRAM hit rate and the lowest
  exposed latency, but it does not reduce HBM reads much relative to the
  other locality-first profiles.
- `LFUCompressionPolicy` is more aggressive about footprint reduction. It
  lowers HBM reads and increases compression savings, but does so at the cost
  of much higher CXL traffic and exposed latency.
- `HotWarmColdPolicy` stays closer to the current default balance. It is less
  aggressive than the LFU-heavy profile and slightly less latency-friendly
  than the larger recent-window LRU profile.

## Workload Assumptions

This comparison uses the default synthetic workload:

- `model_layers: 32`
- `num_heads: 32`
- `head_dim: 128`
- `batch_size: 4`
- `context_length: 8192`
- `decode_steps: 128`
- `dtype_bytes: 2`
- `kv_block_tokens: 16`

## Interpretation Limits

Policy comparison results are especially workload-sensitive. The values here
should be read as policy-shape differences inside the simulator, not as claims
about which production runtime policy would win in practice.
