from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class SimulationMetrics:
    total_bytes_moved: int = 0
    hbm_bytes_read: int = 0
    cxl_bytes_read: int = 0
    host_bytes_read: int = 0
    compression_savings_bytes: int = 0
    simulated_latency_ns: float = 0.0
    overlapped_transfer_ns: float = 0.0
    exposed_transfer_ns: float = 0.0
    overlapped_decompression_ns: float = 0.0
    exposed_decompression_ns: float = 0.0
    sram_hits: int = 0
    total_accesses: int = 0
    blocks_evicted: int = 0
    blocks_compressed: int = 0
    prefetched_blocks: int = 0
    staged_blocks: int = 0

    @property
    def sram_hit_rate(self) -> float:
        if self.total_accesses == 0:
            return 0.0
        return self.sram_hits / self.total_accesses

    @property
    def dma_overlap_ratio(self) -> float:
        total = self.overlapped_transfer_ns + self.exposed_transfer_ns
        if total == 0.0:
            return 0.0
        return self.overlapped_transfer_ns / total

    @property
    def decompression_overlap_ratio(self) -> float:
        total = self.overlapped_decompression_ns + self.exposed_decompression_ns
        if total == 0.0:
            return 0.0
        return self.overlapped_decompression_ns / total

    def as_dict(self) -> dict[str, float | int]:
        data = asdict(self)
        data["sram_hit_rate"] = self.sram_hit_rate
        data["dma_overlap_ratio"] = self.dma_overlap_ratio
        data["decompression_overlap_ratio"] = self.decompression_overlap_ratio
        return data
