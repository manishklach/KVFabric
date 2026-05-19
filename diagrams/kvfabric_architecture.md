# KVFabric Architecture Diagram

```text
                                      +----------------------+
                                      |  Inference Runtime   |
                                      | decode step stream   |
                                      +----------+-----------+
                                                 |
                                                 v
                                  +--------------+---------------+
                                  |    KVFabric Runtime Layer    |
                                  |------------------------------|
                                  | block metadata table         |
                                  | hot/warm/cold classifier     |
                                  | residency tracker            |
                                  | compression policy engine    |
                                  | DMA / prefetch scheduler     |
                                  +------+-----------------+-----+
                                         |                 |
                               placement |                 | movement
                                         |                 |
                    +--------------------+-----+     +-----+------------------+
                    |                          |     |                        |
                    v                          v     v                        v
              +-----+------+             +-----+-----+                 +------+------+
              |    SRAM    |             |    HBM    |                 |     CXL     |
              | staging    |             | active KV |                 | warm / cold |
              +-----+------+             +-----+-----+                 +------+------+
                    ^                          |                               |
                    |                          |                               |
                    |     KVFabric Prefetch    ||                               |
                    |                          ||                               |
              +-----+------+                   ||                         +------+------+
              | GPU Compute |==================++========================>| Attention   |
              | current tok |                                              | consumption |
              +------------+                                              +-------------+
                                               |
                                               v
                                         +-----+------+
                                         | host DRAM  |
                                         | deep spill |
                                         +------------+
```
