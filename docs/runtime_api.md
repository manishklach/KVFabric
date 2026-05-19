# KVFabric Runtime API Sketch

KVFabric is not yet a production runtime integration, but the architecture
direction benefits from a concrete API sketch. This document outlines the kind
of control-plane surface a future KV-aware orchestration layer might expose to
vLLM-, SGLang-, or TensorRT-LLM-style systems.

## Conceptual C-Style API

```c
kvfabric_handle_t kvfabric_open(void);

int kvfabric_reserve(
    kvfabric_handle_t handle,
    const kvfabric_block_desc_t* desc,
    kvfabric_block_ref_t* out_ref
);

int kvfabric_prefetch(
    kvfabric_handle_t handle,
    const kvfabric_block_ref_t* refs,
    size_t ref_count,
    kvfabric_tier_t target_tier,
    uint64_t deadline_ns
);

int kvfabric_compress(
    kvfabric_handle_t handle,
    const kvfabric_block_ref_t* refs,
    size_t ref_count,
    kvfabric_compression_t mode
);

int kvfabric_materialize(
    kvfabric_handle_t handle,
    kvfabric_block_ref_t ref,
    kvfabric_tier_t target_tier,
    kvfabric_ptr_t* out_ptr
);
```

This is an architecture sketch rather than a stable ABI. The intent is to make
the control-plane responsibilities explicit: reserve logical KV blocks,
schedule movement, compress colder state, and materialize a block into a tier
that the runtime can consume.

## Required Runtime Hooks

Integrating a KVFabric-like layer into existing inference systems would likely
require several runtime hooks.

### Block Allocation Hook

The runtime needs a place to notify KVFabric when a new logical block is
created. This is where metadata such as layer, head, token span, size, and
request context would be registered.

### Block Access Notification

The control plane needs per-step or per-window visibility into which blocks
were actually touched. Without this signal, hot/warm/cold classification and
reuse-sensitive placement become guesswork.

### Prefetch Hint

A serving stack usually has limited but useful knowledge about what will be
needed next. A prefetch hook lets the runtime issue deadlines or urgency hints
for likely-next blocks without forcing the compute path to own all data motion.

### Eviction / Compression Policy Hook

A serious system will eventually need policy control rather than a fixed
heuristic. That implies a hook for choosing when blocks are demoted,
compressed, or retained in a hotter tier under pressure.

### Release Hook

When a request ends or a block becomes irrelevant, the control plane needs an
explicit release signal. Otherwise the metadata system cannot distinguish
between a cold block and dead state.

### Telemetry Counters

Runtimes need observability to evaluate whether the orchestration layer is
helping. Useful counters include:

- residency by tier
- bytes moved per tier
- prefetch accuracy
- compression activity
- exposed versus hidden transfer latency
- materialization latency
- block lifetime statistics

## Why Existing Runtimes Would Need These Hooks

vLLM, SGLang, TensorRT-LLM, and similar systems already manage KV state
implicitly or explicitly through allocators, paged structures, reuse logic, or
routing decisions. A KVFabric-like layer would not replace those runtimes. It
would require them to expose a cleaner contract around:

- logical block creation
- locality hints
- reuse observation
- movement deadlines
- lifecycle release

The shift is from treating KV as anonymous buffer space toward treating it as a
runtime-visible systems object.

## Non-Goals

The current repository does not attempt any of the following:

- no CUDA kernel replacement
- no real GPU pointer management yet
- no production runtime integration yet
- no ABI stability

This document is meant to make the control-plane concept concrete enough for
discussion and experimentation, not to imply a production integration surface.
