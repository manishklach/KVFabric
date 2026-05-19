# KVFlow Scheduler Policy

KVFlow uses simple policies that are intentionally transparent and easy to inspect.

## Temperature classes

Each block has one of three semantic classes:

- `hot`
- `warm`
- `cold`

These are not hardware cache states. They are scheduler-visible signals used to guide placement and compression.

## Policies

### `recent-window-hot`

Blocks accessed within a recent decode window are classified as hot. The intuition is that decode attention tends to revisit nearby context more aggressively than far history.

### `access-count-warm`

Blocks with repeated reuse but outside the immediate recent window become warm. They are still valuable, but not urgent enough to prioritize for the smallest, closest tier.

### `cold-compress`

Blocks that are neither recent nor frequently reused are eligible for compression and demotion. This models the idea that colder history can be retained in a cheaper footprint at the cost of later decompression.

### `prefetch-next-window`

Before servicing the next attention step, the scheduler speculatively stages likely-hot blocks into SRAM. This approximates DMA-driven staging for imminent reuse.

## Placement logic

The simulator follows a simple placement philosophy:

- Hot blocks prefer SRAM, then HBM.
- Warm blocks prefer HBM, then CXL.
- Cold blocks prefer compressed placement in CXL, then host DRAM.

When a target tier lacks space, the scheduler tries alternative tiers in descending preference order. Evictions are approximate and conservative: colder blocks are removed from the most capacity-constrained tiers first.

## What is intentionally omitted

KVFlow does not currently model:

- token-level variable importance inside a block
- cross-request prefix sharing
- separate QoS classes
- overlapping copy and attention execution
- control-queue backpressure

The present goal is clarity, not completeness.
