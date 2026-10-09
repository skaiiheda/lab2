"""Модель события распределённой системы."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    event_id: int
    process_id: int
    event_type: str
    lamport_timestamp: int
    vector_clock: list[int]
    description: str = ""
    target_process: int | None = None
    message_id: str | None = None
    conflict: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def process_name(self) -> str:
        return f"P{self.process_id + 1}"

    def vector_string(self) -> str:
        return "[" + ", ".join(map(str, self.vector_clock)) + "]"
