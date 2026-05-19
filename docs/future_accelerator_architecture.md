# Conceptual Future KVFabric Accelerator Architecture

KVFabric is currently a simulator, architecture prototype, and control-plane
model. This document describes a conceptual future accelerator architecture
that the repository is intended to help reason about. It should not be read as
production silicon, a hardware roadmap, or a performance claim.

## High-Level Overview

The conceptual KVFabric accelerator would sit alongside GPU compute and
orchestrate KV-cache movement, residency, staging, compression, and prefetch
behavior across HBM, CXL memory, and host DRAM tiers.

The GPU would still execute attention and matmul compute. KVFabric would focus
on memory orchestration around inference, especially for long-context decode
paths where memory movement, tier placement, and latency hiding increasingly
shape end-to-end behavior.

## System-Level Diagram

```text
                    +----------------------+
                    |     GPU Compute      |
                    | Attention / Matmul   |
                    +----------+-----------+
                               |
                      KV Requests / Hints
                               |
                +--------------v---------------+
                |          KVFabric            |
                |------------------------------|
                | Runtime Command Queue        |
                | Policy Microcontroller       |
                | Residency Tracker            |
                | DMA / Prefetch Scheduler     |
                | Compression Engine           |
                | Rehydration Engine           |
                | SRAM Staging Buffers         |
                | KV Metadata SRAM             |
                | Telemetry / Profiling        |
                +--------------+---------------+
                               |
          +-------------------+-------------------+
          |                   |                   |
       +--v---+           +---v---+           +---v---+
       | HBM  |           |  CXL  |           | DRAM  |
       +------+           +-------+           +-------+
```

## Detailed Accelerator Block Diagram

```text
+-----------------------------------------------------------+
| KVFabric Accelerator                                      |
| --------------------------------------------------------- |
| Runtime Command Queue                                     |
| --------------------------------------------------------- |
| Policy Microcontroller                                    |
| --------------------------------------------------------- |
| Residency Prediction Engine                               |
| --------------------------------------------------------- |
| KV Metadata SRAM                                          |
| --------------------------------------------------------- |
| DMA Engines                                               |
| - HBM DMA                                                 |
| - CXL DMA                                                 |
| - DRAM DMA                                                |
| --------------------------------------------------------- |
| Compression Cluster                                       |
| - INT8 Pack/Unpack                                        |
| - INT4 Pack/Unpack                                        |
| - Sparse KV Engine                                        |
| --------------------------------------------------------- |
| SRAM Staging Banks                                        |
| --------------------------------------------------------- |
| Prefetch Scheduler                                        |
| --------------------------------------------------------- |
| Telemetry / Profiling                                     |
| --------------------------------------------------------- |
| PCIe / CXL Interface                                      |
+-----------------------------------------------------------+
```

## Runtime Command Queue

The runtime command queue represents the software-facing entry point into the
control plane. A serving runtime or model executor could issue commands such
as classify, prefetch, promote, demote, compress, and retire. The point of
this block is not to replace compute scheduling; it is to make KV-cache
management explicit and programmable.

Long-context inference may need this kind of queue because KV decisions are
increasingly driven by decode-time context rather than by static buffer
allocation alone.

## Policy Microcontroller

The policy microcontroller is a conceptual control unit that interprets
runtime hints and local telemetry and chooses residency or movement actions.
In research terms, this is where scheduler policies, heuristics, and future
learned placement strategies could live.

Inference systems may need a block like this because long-context KV behavior
is dynamic, workload-sensitive, and often too stateful to be captured by a
fixed allocator policy.

## Residency Tracker

The residency tracker maintains the current placement of each KV block across
SRAM, HBM, CXL memory, and host DRAM. It also tracks lifecycle attributes
such as hot/warm/cold state, recent access behavior, and compression status.

This matters because future inference systems may need to reason about
placement explicitly rather than only about allocation success or failure.

## KV Metadata SRAM

A compact metadata SRAM would store the high-frequency control state needed
for scheduling decisions. Keeping metadata close to the orchestration logic
reduces the cost of constantly reevaluating which blocks should be promoted,
demoted, prefetched, or rehydrated.

In long-context inference, the metadata path may become almost as important as
the data path because the control plane is repeatedly making locality
decisions under latency pressure.

## DMA / Prefetch Engines

The DMA and prefetch engines are the transport machinery of the conceptual
architecture. They move KV blocks between tiers and attempt to hide those
transfers behind useful compute.

Inference systems may need this because memory movement often becomes exposed
only when prefetch timing is wrong or when the control plane fails to stage
the right data ahead of use.

## Compression Cluster

The compression cluster is responsible for footprint reduction and possibly
format conversion for colder KV state. In the current repository, compression
is only modeled abstractly, but a future architecture study could explore when
and where such compression should occur.

This block matters because long-context serving pressures both capacity and
movement cost, and cold-state compression can affect both.

## Rehydration Pipeline

The rehydration pipeline reverses the compression path when compressed blocks
are needed again for attention. In practice, this is where decompression
latency and overlap behavior matter.

Long-context inference may need such a pipeline if compressed or remote KV
state must be pulled back into a hotter tier without stalling the decode path
more than necessary.

## SRAM Staging Buffers

SRAM staging buffers hold the imminent working set closest to the consumption
path. The goal is not to make SRAM a universal KV store, but to make it a
predictive staging tier that absorbs the most latency-sensitive accesses.

This is relevant to long-context inference because the hottest portion of KV
state is usually much smaller than the full context footprint.

## Telemetry / Counters

Telemetry and counters provide the observability needed to tune policies,
debug stalls, and compare scheduler designs. This includes residency
occupancy, promotion/demotion frequency, prefetch accuracy, exposed transfer
latency, and compression activity.

Any serious control-plane concept needs this, because without telemetry it is
hard to reason about whether a policy is reducing movement cost or simply
moving work around.

## PCIe / CXL Interface

The PCIe / CXL interface is the external attachment point for commands,
metadata exchange, and access to expanded memory tiers. In a future system,
this could make KVFabric either a host-side control-plane device, a
memory-attached controller, or a CXL-visible orchestration layer.

This becomes relevant as memory pooling and tier expansion become more common
in inference infrastructure.

## Memory Movement Pipeline

At a conceptual level, the architecture would aim to support a decode pipeline
like this:

Token N:

- compute executing on GPU

Meanwhile:

- KVFabric prefetches Token N+1 KV blocks
- compressed KV blocks promoted into SRAM
- residency tracker updates hot/warm/cold state
- DMA overlap hides transfer latency

The goal is reducing exposed memory stalls rather than accelerating tensor
compute itself.

## Future Research Questions

- semantic KV eviction
- attention-aware residency prediction
- KV locality forecasting
- multi-tenant scheduling
- distributed KV fabrics
- CXL-aware inference orchestration
- KV compression scheduling
- overlap-aware DMA policies

## Current Repository Scope

The current repository includes:

- simulation
- policy modeling
- architecture exploration
- workload experimentation

## Not Yet Implemented

The current repository does not implement:

- RTL
- FPGA
- production hardware
- CUDA kernels
- silicon timing
- real DMA firmware

That boundary is important. The present project is an architecture exploration
and control-plane model, not a hardware implementation.
