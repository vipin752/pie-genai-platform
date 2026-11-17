"""In-memory usage tracking — Section 7.2's "usage tracking"/"token
accounting"/"cost estimation". In-memory only: no database is wired yet
(Stage F/persistence), so this does not survive a restart. That is an
honest, stated limitation, not a design goal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class UsageRecord:
    model: str
    provider_name: str
    success: bool
    retryable_failure: bool
    latency_ms: float
    tokens: int
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class UsageTracker:
    def __init__(self) -> None:
        self._records: list[UsageRecord] = []

    def record(self, record: UsageRecord) -> None:
        self._records.append(record)

    def all(self) -> list[UsageRecord]:
        return list(self._records)

    def total_tokens(self, model: str | None = None) -> int:
        return sum(r.tokens for r in self._records if model is None or r.model == model)

    def success_rate(self, model: str | None = None) -> float | None:
        matching = [r for r in self._records if model is None or r.model == model]
        if not matching:
            return None
        return sum(1 for r in matching if r.success) / len(matching)
