"""Asynchronous messaging system for the UI."""

import queue
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class EventType(Enum):
    """Types of events triggered by the backend for the UI."""
    PROGRESS = auto()
    SUCCESS = auto()
    ERROR = auto()
    INFO = auto()

@dataclass
class UIEvent:
    """Interface event data."""
    type: EventType
    payload: Any = None
    message: str = ""

class UIEventEmitter:
    """Event emitter for background threads."""

    def __init__(self, event_queue: queue.Queue[UIEvent]) -> None:
        self.queue = event_queue

    def emit_progress(self, current: int, total: int, message: str = "") -> None:
        self.queue.put(UIEvent(EventType.PROGRESS, (current, total), message))

    def emit_success(self, message: str) -> None:
        self.queue.put(UIEvent(EventType.SUCCESS, message=message))

    def emit_error(self, message: str) -> None:
        self.queue.put(UIEvent(EventType.ERROR, message=message))

    def emit_info(self, message: str) -> None:
        self.queue.put(UIEvent(EventType.INFO, message=message))
