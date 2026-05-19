# KVFlow Compression Model

KVFlow models compression as a scheduling tradeoff rather than a numeric quantization study.

## States

- `none` = 1.0x size
- `int8` = 0.5x size
- `int4` = 0.25x size

These ratios are treated as effective storage compression factors.

## Penalties

Compressed blocks incur a simulated decompression penalty when they are read:

- `none` = 0 ns additional cost
- `int8` = small penalty
- `int4` = larger penalty

The exact values live in code and are easy to tune. They are chosen to express qualitative tradeoffs:

- smaller footprint reduces capacity pressure and movement cost
- heavier compression increases access overhead

## Policy choice

KVFlow uses a simple policy:

- Warm blocks may remain uncompressed.
- Cold blocks are compressed before demotion when helpful.
- The coldest blocks prefer `int4` when pushed far from the active window.

This keeps the simulator legible while still allowing measurable differences between baseline and KV-aware behavior.

## What compression does not mean here

KVFlow is not making claims about:

- real KV quantization quality
- layer-specific precision sensitivity
- error bounds
- model accuracy retention

Those belong to future work. In this repository, compression is a systems-level abstraction for footprint and access-cost tradeoffs.
