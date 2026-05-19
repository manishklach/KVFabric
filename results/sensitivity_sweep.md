# Sensitivity Sweep

This note records an exploratory context-length sweep using three synthetic
workloads. The goal is to understand where KVFabric-like orchestration helps,
where it changes little, and where current modeling still misses pressure that
future workloads may expose.

## Sweep Output

```text
workload         | context_length | hbm_bytes_read  | cxl_bytes_read | sram_hit_rate | exposed_latency_ns | compression_savings_bytes
-------------------------------------------------------------------------------------------------------------------------------------
short_2k         | 2,048          | 20,316,160      | 131,072        | 0.2846        | 127,639.21         | 131,072
medium_32k       | 32,768         | 31,064,064      | 0              | 0.2186        | 273,035.16         | 0
long_128k_cold   | 131,072        | 41,549,824      | 0              | 0.2029        | 390,228.12         | 0
```

## Visual Summary

```text
HBM Reads
short_2k  : ############
medium_32k: ##################
long_128k : ########################

Exposed Latency
short_2k  : ########
medium_32k: #################
long_128k : ########################

SRAM Hit Rate
short_2k  : ########################
medium_32k: ##################
long_128k : #################
```

## What This Shows

- Small contexts may not benefit much from elaborate tiering because the
  working set is already compact and locality is easy to preserve.
- Longer contexts increase exposed latency and HBM movement even in this
  reduced synthetic geometry, which is directionally consistent with rising
  memory pressure.
- Cold KV-heavy workloads are where tiering and compression should become more
  interesting, but the current lightweight sweep geometry is still modest
  enough that CXL pressure does not dominate yet.

## Failure Modes To Keep In View

- The longer synthetic workloads here use smaller model geometry than the
  default 8k profile so the repository can run quickly. That means they do not
  yet stress the hierarchy as hard as a production-scale long-context trace.
- `long_128k_cold` does not currently trigger a large compression gain under
  these assumptions, which is an honest sign that the current workload shape
  is not yet severe enough to force the strongest tiering behavior.
- KVFabric should be evaluated across where it helps and where it hurts, not
  only on workloads that are predisposed to show a benefit.

## Current Limitations

- These are still synthetic workloads rather than live serving traces.
- Smaller geometry was chosen deliberately to keep the sweep reproducible in CI-like environments.
- The current overlap model is still approximate.
