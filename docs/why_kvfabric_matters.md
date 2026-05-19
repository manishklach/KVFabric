# Why KVFabric Could Matter

KVFabric starts from a simple systems question: what happens when long-context
inference is constrained less by tensor math alone and more by the cost of
placing, moving, staging, and reusing KV state?

This document summarizes why that question may matter to infrastructure teams,
runtime architects, and accelerator researchers.

## Why Inference Economics Matter

Inference infrastructure is ultimately shaped by economics as much as by raw
performance. The cost of serving long-context workloads depends not only on
how fast a model computes, but also on how efficiently the system uses scarce
close memory, how much state it moves per token, and how much useful overlap it
can sustain under contention.

As persistent decode-time state grows, the economics of memory movement,
placement, and reuse can become a central systems concern.

## Why Memory Movement Matters

When the active working set is smaller than the total retained KV footprint,
every decode step becomes partly a movement problem. The system must decide:

- which blocks stay in the hottest tier
- which blocks can be compressed
- which blocks should be prefetched
- which transfers can be hidden
- which requests deserve scarce close-memory capacity

That is why memory movement increasingly matters. The bottleneck is not only
whether bytes exist somewhere in the system, but whether they are in the right
place at the right time.

## Why FLOPS Alone Are Insufficient

Higher FLOPS do not automatically solve decode-time memory orchestration. A
powerful compute accelerator can still stall if the relevant KV blocks are in a
colder tier, if rehydration arrives too late, or if the runtime lacks a good
policy for reusing state across active sessions.

This is one reason the industry has started to expose KV management more
explicitly in serving systems. KV placement and reuse are no longer only
allocator details. They are becoming visible parts of the inference stack.

## Why KV-Cache Scales Brutally

KV-cache grows with context, concurrency, model structure, and retention
behavior. That growth is painful because the hottest tier rarely scales as
quickly as the total state footprint. As a result, systems face a widening gap
between:

- the amount of KV that exists
- the amount of KV that can remain near compute

That gap creates pressure for tiering, locality-aware placement, compression,
and overlap-aware movement.

## Why HBM Alone May Not Scale

HBM remains the most attractive tier for immediate consumption, but it is both
finite and expensive. Long-context inference pushes against HBM capacity and
bandwidth at the same time. If all useful KV must remain in HBM, then serving
systems are forced into an increasingly rigid operating point.

That makes alternative tiers and orchestration strategies relevant:

- SRAM staging for the imminent working set
- CXL memory pools for larger warm-state capacity
- host DRAM for colder retained state
- future spill tiers for archival or low-priority retention

KVFabric studies what happens when those tiers are treated as part of a policy
surface rather than as fallback overflow.

## Why KV Locality Matters

Decode workloads are not uniformly random. Access patterns often reflect
recency, locality, reuse distance, and workload structure. Even approximate
locality signals can change whether prefetching, compression, or demotion are
useful.

This is why KV locality matters. A system that understands which blocks are
about to matter can hide movement cost much more effectively than one that
treats all retained state equally.

## Why Orchestration Layers Emerge

Orchestration layers tend to appear when multiple resources must be coordinated
under policy and timing constraints. That pattern already exists in several
adjacent industry directions:

- vLLM PagedAttention made KV layout and paging explicit
- TensorRT-LLM has explored KV reuse and other cache optimizations
- NVIDIA Dynamo has highlighted KV-aware routing behavior
- CXL memory pools are expanding the design space for tiered memory
- overlap-aware execution is becoming more important in long-context serving

KVFabric interprets these not as isolated features, but as signals that
inference-memory orchestration may be becoming a systems layer in its own
right.

## Why Memory-Side Acceleration Is Plausible

Dedicated acceleration tends to become plausible when scheduling overhead,
movement overhead, or coordination overhead become too large to treat as a
secondary concern. KV residency tracking, prefetch timing, compression control,
and overlap-aware movement may eventually fit that pattern.

That does not imply a fixed hardware answer. The right form factor could range
from a smarter runtime to a CXL-attached controller to a memory-side service or
accelerator block. The common idea is that decode-time memory orchestration may
deserve more explicit machinery than today’s stacks typically provide.

KVFabric explores that possibility through simulation, architecture modeling,
and policy experimentation rather than through hardware claims.
