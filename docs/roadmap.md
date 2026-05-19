# KVFabric Roadmap

## Current Scope vs Future Direction

| Current Repository Scope | Future Architectural Exploration |
| --- | --- |
| Simulator | Accelerator architecture studies |
| Scheduler policies | DMA offload engines |
| Trace replay | Runtime integration |
| Compression models | Compression acceleration |
| Residency tracking | Hardware residency engines |
| Memory hierarchy modeling | Memory-side orchestration hardware |
| Overlap simulation | FPGA experiments |
| Systems exploration | Silicon implementation research |

## Maturity Ladder

| Stage | Scope | Status |
| --- | --- | --- |
| Stage 1 | Simulator, workload models, residency policies | Current |
| Stage 2 | Trace-driven replay, policy comparison, overlap refinement | In progress |
| Stage 3 | Runtime API contract and integration shims | Planned |
| Stage 4 | Cost-aware memory tiering and multi-tenant modeling | Planned |
| Stage 5 | FPGA / accelerator datapath exploration | Future research |
| Stage 6 | Production die studies, final hardware architecture, silicon implementation research | Long-term exploration |

These stages are research-oriented waypoints rather than committed product
plans. They are meant to clarify scope and maturity, not to imply a fixed
execution roadmap.

## v0.2.0 Target: Trace-Driven and Policy-Comparative Simulation

Priorities:

1. token-level trace replay
2. workload JSON configs
3. scheduler policy comparison
4. latency breakdown
5. overlap-aware pipeline refinements
6. more realistic decompression assumptions
7. CXL-aware residency heuristics
