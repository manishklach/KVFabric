# KVFabric Scheduler Policy

KVFabric uses simple policies that are intentionally transparent and easy to
inspect.

## Temperature Classes

Each block has one of three semantic classes:

- `hot`
- `warm`
- `cold`

These are not hardware cache states. They are scheduler-visible signals used
to guide placement, staging, and compression.

## Policies

### `recent-window-hot`

Blocks accessed within a recent decode window are classified as hot. The
intuition is that decode attention tends to revisit nearby context more
aggressively than far history.

### `access-count-warm`

Blocks with repeated reuse but outside the immediate recent window become
warm. They are still valuable, but not urgent enough to prioritize for the
smallest, closest tier.

### `cold-compress`

Blocks that are neither recent nor frequently reused are eligible for
compression and demotion. This models the idea that colder history can be
retained in a cheaper footprint at the cost of later decompression.

### `prefetch-next-window`

Before servicing the next attention step, the scheduler speculatively stages
likely-hot blocks into SRAM. This approximates DMA-driven staging for imminent
reuse.

## Policy Interface

Scheduler logic is now exposed through `simulator/kvflow/policies.py`.

The current policy classes are:

- `BasePolicy`
- `LRUHotWindowPolicy`
- `LFUCompressionPolicy`
- `HotWarmColdPolicy`

Each policy exposes the same extension points:

- `select_blocks_for_promotion(...)`
- `select_blocks_for_compression(...)`
- `select_blocks_for_eviction(...)`

This keeps the initial implementation simple while making it obvious how to
add new heuristics for:

- locality-aware promotion
- compression aggressiveness
- tier-specific eviction
- workload-specific residency behavior

## Placement Logic

The simulator follows a simple placement philosophy:

- hot blocks prefer nearby tiers and SRAM staging
- warm blocks prefer HBM, then CXL
- cold blocks prefer compressed placement in CXL, then host DRAM

When a target tier lacks space, the scheduler tries alternative tiers in
descending preference order. Evictions are approximate and conservative:
colder or less recent blocks are removed first.

## What Is Intentionally Omitted

KVFabric does not currently model:

- token-level variable importance inside a block
- cross-request prefix sharing
- separate QoS classes
- control-queue backpressure
- production scheduler feedback loops

The present goal is clarity and extensibility, not completeness.
