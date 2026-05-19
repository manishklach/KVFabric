from __future__ import annotations

from dataclasses import dataclass, field

from .config import TierConfig


@dataclass(slots=True)
class MemoryTier:
    """Simple capacity and transfer model for one memory tier."""

    name: str
    capacity_bytes: int
    bandwidth_gbps: float
    latency_ns: float
    used_bytes: int = 0
    resident_blocks: set[str] = field(default_factory=set)

    @classmethod
    def from_config(cls, config: TierConfig) -> "MemoryTier":
        return cls(
            name=config.name,
            capacity_bytes=config.capacity_bytes,
            bandwidth_gbps=config.bandwidth_gbps,
            latency_ns=config.latency_ns,
        )

    def available_bytes(self) -> int:
        return self.capacity_bytes - self.used_bytes

    def can_fit(self, size_bytes: int) -> bool:
        return size_bytes <= self.available_bytes()

    def allocate(self, block_id: str, size_bytes: int) -> bool:
        if not self.can_fit(size_bytes):
            return False
        self.used_bytes += size_bytes
        self.resident_blocks.add(block_id)
        return True

    def free(self, block_id: str, size_bytes: int) -> None:
        if block_id in self.resident_blocks:
            self.resident_blocks.remove(block_id)
            self.used_bytes = max(0, self.used_bytes - size_bytes)

    def transfer_time_ns(self, moved_bytes: int) -> float:
        if moved_bytes <= 0:
            return 0.0
        bytes_per_ns = self.bandwidth_gbps / 8.0
        return moved_bytes / bytes_per_ns
