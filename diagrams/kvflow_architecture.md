# KVFlow Architecture Diagram

```text
                                      +----------------------+
                                      |  Inference Runtime   |
                                      | decode step stream   |
                                      +----------+-----------+
                                                 |
                                                 v
                                  +--------------+---------------+
                                  |     KVFlow Control Plane     |
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
              | staging    |<----------->| active KV |<--------------->| warm / cold |
              +-----+------+             +-----+-----+                 +------+------+
                    |                          |                               |
                    +--------------------------+-------------------------------+
                                               |
                                               v
                                         +-----+------+
                                         | host DRAM  |
                                         | deep spill |
                                         +------------+
```
