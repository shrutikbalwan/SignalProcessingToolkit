"""Runtime health aggregation independent of presentation widgets."""

from __future__ import annotations

from signal_processing_toolkit.dashboard.state import ProcessingHealth


class MonitoringService:
    def __init__(self) -> None:
        self._health = ProcessingHealth()

    def update(self, **values: float | int) -> ProcessingHealth:
        for name, value in values.items():
            if hasattr(self._health, name):
                setattr(self._health, name, value)
        return (
            ProcessingHealth(**self._health.__dict__)
            if hasattr(self._health, "__dict__")
            else ProcessingHealth(
                processing_latency_ms=self._health.processing_latency_ms,
                inference_latency_ms=self._health.inference_latency_ms,
                queue_depth=self._health.queue_depth,
                dropped_frames=self._health.dropped_frames,
                packet_loss=self._health.packet_loss,
                cpu_percent=self._health.cpu_percent,
                memory_mb=self._health.memory_mb,
            )
        )

    def snapshot(self) -> ProcessingHealth:
        return self.update()
