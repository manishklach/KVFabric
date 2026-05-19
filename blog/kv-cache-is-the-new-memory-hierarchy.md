# KV-Cache Is Becoming the New Memory Hierarchy

For a long time, the default mental model for LLM inference was dominated by
compute: tensor cores, matmul efficiency, and throughput scaling. That picture
is still important, but it is becoming incomplete. As context windows grow and
decode becomes more stateful, more of the systems challenge shifts toward
memory orchestration.

KV-cache sits at the center of that shift.

During long-context inference, a serving system is not only executing matrix
math. It is also carrying forward a large and growing body of key-value state,
deciding where that state should live, determining what is worth keeping close
to the attention path, and paying the cost when data has to move. That starts
to look less like a generic tensor-allocation problem and more like a memory
hierarchy problem.

## Why The Pressure Is Increasing

Several trends are reinforcing each other:

- longer contexts increase the persistent decode-time state footprint
- multi-tenant serving raises contention for the active memory set
- reuse-aware caching is becoming more important to serving efficiency
- memory bandwidth and placement increasingly shape inference economics

As a result, a meaningful part of inference efficiency is no longer only about
compute kernels. It is also about whether the right KV state is in the right
place at the right time.

## KV-Cache As A First-Class Systems Object

Many current stacks still treat KV-cache primarily as tensor memory that must
be allocated, paged, and reclaimed. That abstraction has been productive, but
it may be too narrow for the next stage of long-context serving.

A KV block has richer behavior than a generic buffer:

- it has a recency profile
- it may have a non-uniform reuse probability
- it may tolerate different compression states
- it may benefit from prefetching
- it may belong in different tiers depending on expected future use

Once those properties matter, KV-cache starts to resemble a first-class
systems object with metadata, lifecycle, and policy.

## The Industry Is Already Moving In This Direction

This is not a speculative trend pulled from nowhere. Pieces of it are already
visible in production-oriented systems work.

vLLM PagedAttention made KV layout, fragmentation, and paging behavior central
to the runtime conversation. TensorRT-LLM has brought more attention to KV
cache reuse and compressed-cache representations. NVIDIA Dynamo has made
KV-aware routing part of a broader serving control-plane discussion. CXL
memory pools and other expanded-memory ideas add another layer: not all useful
state will fit in the closest memory tier, so placement policy matters more.

The implication is not that there is already a finished architectural answer.
The implication is that inference systems are moving toward more explicit KV
management.

## Why A KV-Aware Orchestration Layer May Emerge

If a system repeatedly needs to classify KV state, compress it, stage it, move
it across tiers, and route around its placement, it becomes reasonable to ask
whether this logic should remain incidental to the rest of the runtime.

One possible outcome is a more explicit orchestration layer around KV-cache:

- a software control plane
- a memory-side service
- a SmartNIC- or DPU-adjacent controller
- a future runtime layer dedicated to movement and residency decisions

The point is not that one of these architectures is inevitable. The point is
that the design pressure is becoming easier to describe in systems terms.

## What KVFabric Simulates

KVFabric is a small research prototype for exploring that pressure through
simulation.

It models:

- a baseline path where KV is read mostly from HBM without semantic tiering
- a KV-aware path with hot/warm/cold classification
- tiered residency across SRAM, HBM, CXL memory, and host DRAM
- simulated compression and decompression penalties
- DMA-like prefetch and staging behavior
- overlap-aware decode accounting for exposed versus hidden movement

This does not prove a production architecture. It gives infrastructure teams a
way to reason about movement, placement, and latency accounting with a more
explicit KV model.

## Why Overlap Matters

A useful lesson from early KVFabric experiments is that traffic reduction
alone is not enough. A model can reduce HBM reads and still look worse on
latency if it assumes all movement and decompression costs are paid
synchronously in the critical path.

That is why overlap matters. Real systems try to hide movement behind useful
work whenever possible. DMA prefetch, staged SRAM buffers, decompression
pipelines, and decode-time scheduling all influence whether a memory transfer
is fully exposed, partially hidden, or mostly amortized away. Any serious
architecture exploration has to model that distinction, even approximately.

## Limitations

KVFabric remains intentionally approximate.

It does not attempt to model:

- real GPU kernels
- numerical fidelity effects of KV quantization
- fully asynchronous production runtimes
- large distributed cluster contention
- production silicon timing
- exact vendor hardware behavior

Those are meaningful omissions, but they are better treated as explicit
limitations than hidden assumptions.

## Future Directions

There are several useful next steps:

- better asynchronous DMA overlap modeling
- overlapped decompression with more realistic staging queues
- token-level pipeline simulation
- more realistic decode traces and reuse-distance studies
- policy comparisons across workload classes
- runtime integration experiments with serving stacks
- optional hardware prototyping, including FPGA-backed control experiments

The broader goal is modest: make KV-cache orchestration concrete enough that
systems teams can debate it as an architecture problem rather than treating it
as a side effect of tensor execution.
