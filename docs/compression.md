# KVFlow Compression Model

KVFlow models compression as a scheduling tradeoff rather than a numeric
quantization study.

## Current Compression Assumptions

This is not real numerical KV quantization. It is a capacity and latency
simulation model.

- `none` is modeled as `1.0x` size
- `int8` is modeled as `0.5x` size
- `int4` is modeled as `0.25x` size

Default decompression penalties are approximate and configurable:

- `none = 0 ns`
- `int8 = 120 ns`
- `int4 = 260 ns`

These parameters live in `CompressionConfig` and can be changed without
changing the rest of the simulator structure.

Future work may use more empirical assumptions informed by KV quantization
papers such as KIVI, but the current model should be read only as a footprint
and latency abstraction.

## States

- `none`
- `int8`
- `int4`

The simulator uses these states to adjust effective storage footprint and
later access cost.

## Policy Choice

KVFlow currently uses a simple policy:

- warm blocks may remain uncompressed
- cold blocks are candidates for compression before demotion
- colder and more distant blocks are more likely to use `int4`

This keeps the simulator legible while still allowing measurable differences
between baseline and KV-aware behavior.

## What Compression Does Not Mean Here

KVFlow is not making claims about:

- real KV quantization quality
- layer-specific precision sensitivity
- accuracy retention
- production compression kernels

In this repository, compression is a systems-level abstraction for footprint
and access-cost tradeoffs.
