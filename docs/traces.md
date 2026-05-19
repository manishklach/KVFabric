# KVFabric Trace Support

KVFabric now supports request-level JSONL traces for replay-like experiments.
These traces are still lightweight compared with production runtime telemetry,
but they make the simulator more grounded than purely synthetic fixed-pattern
workloads.

## Supported Trace Format

Each JSONL line represents one request:

```json
{"request_id":"sg_0","prompt_length":384,"decode_length":96,"arrival_time_ns":0,"source":"sharegpt-inspired"}
```

Supported fields:

- `request_id`
- `prompt_length`
- `decode_length`
- `arrival_time_ns`
- `source`

## Included Trace Files

- `examples/traces/synthetic_chat.jsonl`
- `examples/traces/sharegpt_small.jsonl`
- `examples/traces/mixed_context_trace.jsonl`

## What These Traces Are

- `synthetic_chat.jsonl` is a small deterministic chat-style replay fixture.
- `sharegpt_small.jsonl` is ShareGPT-inspired in shape and length distribution,
  but it is still synthetic and anonymized.
- `mixed_context_trace.jsonl` mixes short, medium, and longer prompts to
  stress replay behavior under heterogeneous arrivals.

## What These Traces Are Not

These are not live vLLM traces, not production TensorRT-LLM traces, and not
drop-in runtime telemetry. They are request-level replay inputs designed to
exercise:

- prompt-length variation
- decode-length variation
- overlapping arrivals
- more realistic locality pressure than a single synthetic stream

## Why Real Distributions Matter

Trace-informed replay matters because fixed synthetic workloads can hide or
overstate locality effects. Real serving systems see:

- highly variable prompt lengths
- diverse decode lengths
- bursty arrivals
- mixed short and long requests in the same time window

Even a lightweight trace format helps move the simulator closer to runtime
adjacent experimentation.

## CLI Usage

```bash
python simulator/run_experiment.py --trace examples/traces/sharegpt_small.jsonl
python simulator/run_experiment.py --mode compare --trace examples/traces/mixed_context_trace.jsonl
```
