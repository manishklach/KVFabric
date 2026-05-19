# KVFlow Accelerator Sketch

KVFlow does not describe a finished chip. It sketches a hypothetical control-plane or memory-side accelerator that could help orchestrate KV-cache movement and residency.

## Hypothetical blocks

### PCIe / CXL interface

Provides attachment into a host inference node and access to pooled or expanded memory. In a future implementation, this interface could carry runtime commands, metadata updates, and data movement requests.

### KV metadata table

Tracks per-block state such as:

- logical identity
- layer/head provenance
- recency
- access count
- compression state
- current residency tier
- expected reuse class

This is central to the KVFlow thesis: metadata becomes a scheduling primitive.

### DMA scheduler

Simulates block movement between tiers. In a more concrete hardware concept, this block would prioritize prefetches, demotions, and eviction traffic while respecting bandwidth budgets and attention deadlines.

### Compression / decompression engine

Models policy-based KV compression. KVFlow keeps this deliberately abstract: `int8` and `int4` represent simulated footprint reductions plus decode penalties, not numeric fidelity studies.

### SRAM staging buffers

Represent a tightly bounded hot-data region adjacent to the attention path. The goal is not to hold the full cache, but to hold the most imminent working set.

### Residency tracker

Maintains occupancy and placement state across HBM, CXL memory, and host DRAM. This block enables policy decisions such as "compress before demote" or "keep recent tokens near the datapath."

### Runtime command queue

Represents software-to-controller coordination. A production realization could expose enqueue, classify, prefetch, and retire operations, allowing the model runtime to issue semantic hints rather than only raw buffer pointers.

## Why this is framed carefully

The point of this document is not to imply that a dedicated KVFlow device should exist today. The point is to give systems teams a structured vocabulary for discussing how KV-cache orchestration might evolve if memory movement becomes a dominant bottleneck in long-context inference.
