# KVFabric Cost Model Proxy

KVFabric includes a rough cost proxy for interpreting simulator output in more
economic terms. This is intentionally lightweight. It is not a cloud pricing
calculator and should not be read as a deployment cost forecast.

## Purpose

Infrastructure teams often care about more than bytes and nanoseconds in
isolation. Long-context inference decisions eventually become questions about:

- cost per token
- the price of close memory capacity
- the penalty of added latency
- whether colder tiers are economically worthwhile

The KVFabric cost model exists to provide a first-order way to reason about
those tradeoffs.

## Inputs

The current proxy consumes:

- `hbm_cost_per_gb`
- `cxl_cost_per_gb`
- `dram_cost_per_gb`
- `gpu_hour_cost`
- `latency_penalty_per_ms`
- `tokens_per_second`
- `request_volume`

These values are configurable in `SimulationConfig.cost`.

## Outputs

The current CLI reports:

- `estimated_hbm_capacity_cost`
- `estimated_cxl_capacity_cost`
- `estimated_memory_cost_delta`
- `estimated_latency_penalty`
- `rough_cost_per_1m_tokens_proxy`

## Assumptions

The model makes several simplifying assumptions:

- configured tier capacity acts as a rough memory-cost proxy
- latency penalty is modeled as a linear penalty per request-millisecond
- GPU cost is converted to a coarse `$ / 1M tokens` proxy using assumed throughput
- request volume is treated as a comparison horizon, not as a production SLA model

## Limitations

- It does not model bursting, queueing, or utilization dynamics.
- It does not model real cloud SKUs or actual provider pricing.
- It does not incorporate power or network cost.
- It does not model opportunity cost from reduced concurrency.
- It assumes a simplified relationship between latency and economic penalty.

## Why Infrastructure Teams Care About $/Token

Serving systems are shaped by economic efficiency as much as by raw speed.
Even small memory-placement decisions can matter if they change:

- how much HBM must be provisioned
- whether CXL-backed capacity becomes viable
- how much exposed latency remains on the critical path
- how many requests fit into a useful operating envelope

That is why memory tiering decisions are also economic decisions.

## CLI Usage

```bash
python simulator/run_experiment.py --mode compare --cost-model
```

The output should be interpreted as a rough architecture tradeoff model rather
than as a pricing statement.
