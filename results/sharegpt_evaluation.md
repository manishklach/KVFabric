# ShareGPT-Inspired Evaluation

This note combines the new trace-replay path with the existing short, medium,
and long canned workloads. The goal is not to prove a win. The goal is to show
where KVFabric helps, where it changes little, and where orchestration
overhead still dominates.

## ShareGPT-Inspired Trace Replay

Running:

```bash
python simulator/run_experiment.py --trace examples/traces/sharegpt_small.jsonl
```

currently produces:

```text
metric                      | baseline       | kvfabric       | delta
------------------------------------------------------------------------------
total_bytes_moved           | 0              | 619,839,488    | 619,839,488
hbm_bytes_read              | 841,482,240    | 648,282,112    | -193,200,128
cxl_bytes_read              | 0              | 94,568,448     | 94,568,448
host_bytes_read             | 0              | 0              | 0
compression_savings_bytes   | 0              | 89,849,856     | 89,849,856
simulated_latency_ns        | 32,889,470.68  | 46,266,850.90  | 13,377,380.22
compute_latency_ns          | 18,489,600.00  | 18,489,600.00  | 0.0000
transfer_latency_ns         | 32,874,569.73  | 43,409,112.92  | 10,534,543.19
decompression_latency_ns    | 0.0000         | 2,491,840.00   | 2,491,840.00
hidden_latency_ns           | 18,482,659.05  | 18,489,600.00  | 6,940.95
exposed_latency_ns          | 14,399,870.68  | 27,777,250.90  | 13,377,380.22
overlap_ratio               | 0.5621         | 0.3996         | -0.1625
sram_hit_rate               | 0.0000         | 0.0964         | 0.0964
```

This is the kind of honest result that matters. The trace replay cuts HBM
traffic substantially, but it still hurts latency because the current
orchestration model introduces movement and decompression work that the default
compute window cannot hide well enough.

## Context-Length Sweep

| Workload | Context length | HBM bytes read | CXL bytes read | SRAM hit rate | Exposed latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `short_2k` | `2,048` | `20,316,160` | `131,072` | `0.2846` | `127,639.21 ns` |
| `medium_32k` | `32,768` | `31,064,064` | `0` | `0.2186` | `273,035.16 ns` |
| `long_128k_cold` | `131,072` | `41,549,824` | `0` | `0.2029` | `390,228.12 ns` |

![HBM Bytes vs Context Length](./figures/hbm_vs_context_length.png)

## Failure Modes

- Small contexts do not benefit much because the hot set is already easy to
  keep close to compute.
- The ShareGPT-inspired trace shows that reducing HBM pressure alone is not
  enough. If movement and decompression are not hidden effectively, latency
  can still worsen.
- Compression can save bytes and still hurt latency if the system pulls too
  much state from colder tiers under tight compute windows.

## Why This Still Matters

These failure modes are useful. They make KVFabric more scientifically
grounded because they show where the thesis is weak under current assumptions,
not only where it looks attractive.

## Current Limitations

- The replay format is request-level and still simplified.
- The overlap model is approximate.
- No GPU kernels or real DMA hardware are modeled.
- Arrival timing is quantized rather than driven by a live runtime.
