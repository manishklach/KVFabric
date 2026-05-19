# Industry Context

KVFabric is motivated by trends already visible in production inference
systems and adjacent infrastructure work.

## Relation To Existing Work

### vLLM and PagedAttention

PagedAttention helped popularize the view that KV-cache management is not a
trivial buffer problem. It made fragmentation, paging behavior, and efficient
KV layout central to serving performance. KVFabric builds on that broader
idea, but shifts attention from page management alone toward semantic
placement and tiered residency.

### TensorRT-LLM KV Cache Reuse and Quantized KV Cache

Modern serving systems increasingly expose reuse-aware caching and compressed
KV representations. KVFabric aligns with that trajectory by modeling
compression and lifecycle state as first-class policy dimensions, without
claiming to reproduce TensorRT-LLM internals.

### NVIDIA Dynamo and KV-Aware Routing

Routing and scheduling are becoming increasingly aware of request state and
cache locality. KVFabric is compatible with that systems direction: if request
routing already depends on cache placement, then cache metadata itself is
becoming part of the serving control plane.

### CXL Memory Pooling

CXL makes it more realistic to talk about expanded memory tiers for
inference-serving nodes. Even if latency remains meaningfully worse than HBM,
larger pooled capacity may still be valuable for colder KV state. KVFabric
explicitly models this kind of intermediate tier.

### Long-Context and Multi-Tenant Serving

As context windows grow and tenant mixes become more dynamic, the probability
that all useful KV state can remain in one flat fast tier declines. That
pressure makes demotion, prefetch, and reuse classification increasingly
relevant.

## Why This Repo Exists

The purpose of KVFabric is not to replace those systems. It exists to ask a
narrower architecture question:

What would change if the inference stack treated KV-cache as a semantic
systems object with its own orchestration plane?

That question is relevant to:

- model-serving runtime teams
- accelerator architecture teams
- AI infrastructure research groups
- memory-hierarchy and interconnect teams

## Careful Positioning

KVFabric should be read as:

- a simulator
- a research artifact
- an architecture hypothesis

It should not be read as:

- a claim of vendor superiority
- a product announcement
- a statement that current systems are obsolete

The value is in making the design space more concrete and easier to discuss.
