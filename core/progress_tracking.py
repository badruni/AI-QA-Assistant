"""Reusable progress events for long-running QA work."""

from dataclasses import dataclass
from typing import Callable


PROGRESS_STATUSES = frozenset({
    "running", "waiting", "completed", "failed", "stopped",
})


@dataclass(frozen=True)
class ProgressEvent:
    stage: str
    status: str
    activity: str
    current: int | None = None
    total: int | None = None


class ProgressReporter:
    """Validate and publish factual stage/item progress to an optional sink."""

    def __init__(self, sink: Callable[[ProgressEvent], object] | None = None):
        if sink is not None and not callable(sink):
            raise TypeError("Progress sink must be callable.")
        self._sink = sink

    def emit(
        self, stage, status, activity, current=None, total=None,
    ):
        if not isinstance(stage, str) or not stage.strip():
            raise ValueError("Progress stage must be a non-empty string.")
        if status not in PROGRESS_STATUSES:
            raise ValueError("Unsupported progress status.")
        if not isinstance(activity, str) or not activity.strip():
            raise ValueError("Progress activity must be a non-empty string.")
        for name, value in (("current", current), ("total", total)):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"Progress {name} must be a non-negative integer.")
        if current is not None and total is not None and current > total:
            raise ValueError("Progress current cannot exceed total.")

        event = ProgressEvent(stage, status, activity, current, total)
        if self._sink is not None:
            self._sink(event)
        return event


def emit_progress(progress, stage, status, activity, current=None, total=None):
    """Publish an event when a caller supplied the shared reporter."""
    if progress is not None:
        return progress.emit(stage, status, activity, current, total)
    return None


def terminal_status_for_results(statuses):
    """Map observed QA outcomes to one unambiguous processing terminal state."""
    values = tuple(getattr(status, "value", status) for status in statuses)
    if "Access Restricted" in values:
        return "stopped"
    if any(value in ("Failed", "Blocked", "Timeout") for value in values):
        return "failed"
    return "completed"


def result_outcome_labels(statuses):
    """Return distinct non-passing outcomes for clear progress activity text."""
    labels = []
    for status in statuses:
        value = getattr(status, "value", status)
        if value != "Passed" and value not in labels:
            labels.append(value)
    return ", ".join(labels)
