# Architecture Glossary

## Residency

The current placement of a KV block within the modeled memory hierarchy.

## Hot/Warm/Cold KV

A simplified semantic classification describing how likely a block is to be
used again soon and therefore how aggressively it should be kept in a near
tier.

## Exposed Latency

Latency that remains visible on the critical path and cannot be hidden behind
other useful work.

## Hidden Latency

Latency that is overlapped with compute or other pipeline stages and therefore
is not fully exposed to the decode step.

## Rehydration

The act of restoring compressed or colder KV state into a hotter or directly
consumable form.

## SRAM Staging

The use of SRAM as a bounded, predictive staging tier for imminent KV
consumption rather than as a full-capacity KV store.

## Overlap Ratio

A coarse simulator metric describing how much transfer-related latency was
hidden relative to the total transfer/decompression window.

## Semantic KV Orchestration

Managing KV state using metadata-aware policies such as recency, reuse class,
temperature, compression state, and predicted future access rather than
treating KV only as anonymous tensor memory.

## KV Fabric

A conceptual orchestration layer or memory-side control plane that manages
KV-cache movement, residency, staging, and related policies across memory
tiers.
