# KVFabric Overlap Model

Real systems rarely pay all movement cost serially. They try to hide memory
movement, decompression, and staging behind useful compute. KVFabric models
that idea approximately through exposed versus hidden latency accounting.

## Timeline Intuition

```text
Time ------------------------------------------------------------>

GPU Compute:
[ Token N compute ][ Token N+1 compute ][ Token N+2 compute ]

KVFabric DMA:
[ Prefetch N+1 ][ Prefetch N+2 ]

Decompression:
[ Rehydrate N+1 ][ Rehydrate N+2 ]

Exposed Stall:
[ only uncovered transfer ]
```

## Key Concepts

### Hidden Latency

Hidden latency is transfer or decompression work that completes while compute
is already happening. It still consumes resources, but it does not fully
lengthen the critical path.

### Exposed Latency

Exposed latency is the uncovered portion that still stalls forward progress.
This is the part the simulator attributes to the effective step latency.

### Overlap Ratio

The overlap ratio is a simple proxy for how much transfer and decompression
work is hidden instead of exposed. Higher overlap suggests that staging and
prefetch timing are helping.

## Why Synchronous Models Are Pessimistic

Fully synchronous models tend to overstate the latency cost of tiered memory.
They assume that fetch, decompression, and consumption happen one after the
other even when real systems would overlap them.

That makes synchronous baselines useful for early safety checks, but too
pessimistic for later architecture reasoning.

## Why Overlap Matters

If KV-cache movement is going to be orchestrated across HBM, CXL, DRAM, and
SRAM staging tiers, then overlap is central. Without overlap, tiering often
looks strictly punitive. With overlap, the system can trade movement and
staging work for lower exposed stall.

This is one reason future memory-fabric or accelerator concepts are plausible:
the value lies less in tensor compute itself and more in hiding movement under
the inference pipeline.

## Current Scope

The current overlap model is approximate and intended for architecture
exploration. It does not model real GPU kernels, exact DMA firmware, or
production pipeline timing.
