# KVFlow Architecture

KVFlow explores a future inference-memory control plane in which KV-cache is managed as a first-class runtime object rather than as anonymous tensor storage. The project is intentionally framed as a research prototype: it models policy, movement, and compression behavior, but it does not claim to represent production silicon or a full serving stack.

## System overview

The simulated system has four parts:

1. A workload generator that emits decode-time KV block access patterns.
2. A metadata layer that tracks per-block temperature, access count, compression state, and current residency.
3. A scheduler that decides what should stay close, what should be demoted, what should be compressed, and what should be prefetched.
4. A memory-tier model spanning SRAM staging, HBM, CXL-attached memory, and host DRAM.

Each decode step can be thought of as a control loop:

1. Determine which KV blocks are likely to be used.
2. Classify blocks as hot, warm, or cold.
3. Prefetch likely-hot blocks toward SRAM.
4. Compress and demote colder blocks to lower-cost tiers.
5. Service the current attention read and accumulate simulated movement cost.

## Design thesis

KVFlow starts from an increasingly plausible systems hypothesis:

- Long-context inference places growing pressure on memory capacity and bandwidth.
- Reuse is uneven across the KV footprint.
- A single flat residency policy is unlikely to remain efficient.
- A metadata-aware orchestration layer may become useful, whether embedded in software, a SmartNIC-like controller, a CXL-attached device, or a future accelerator block.

The project therefore models a semantic memory path for KV-cache rather than a conventional allocator-only view.

## Baseline versus KVFlow

The repository compares two simplified paths.

### Baseline GPU-style path

- KV blocks are admitted into HBM when possible.
- If HBM is pressured, spillover goes to lower tiers with minimal semantic guidance.
- No explicit hot/warm/cold temperature model is used.
- No policy-driven compression is applied.
- SRAM staging is not proactively prefetched.

This approximates a system where KV-cache is primarily treated as tensor memory with limited semantic scheduling.

### KVFlow path

- Recent blocks are treated as hot.
- Reused blocks become warm if they continue to matter but are not in the hottest window.
- Cold blocks are candidates for compression and demotion.
- Prefetch attempts to stage the next likely attention window into SRAM.
- Residency is tracked across SRAM, HBM, CXL, and host DRAM.

This is not a claim that real systems already operate this way in full. It is a model of what a more explicit KV-aware memory plane could look like.

## Why this abstraction matters

The key idea is that a KV block is not just bytes:

- It has expected temporal locality.
- It may be shared or re-read.
- Its useful precision may depend on residency tier and access frequency.
- Its movement timing may matter as much as its final location.

Those properties are why KVFlow centers metadata and scheduling rather than raw allocation alone.
