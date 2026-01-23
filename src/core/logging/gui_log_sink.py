import queue
from typing import Optional

from src.core.logging.log_entry import LogEntry


class GuiSubscriptionSink:
    """
    Log sink that forwards log entries to a GUI via a thread-safe queue.

    This sink performs no UI operations and is safe to use
    from any thread.
    """

    def __init__(self, gui_queue: queue.Queue):
        self._queue = gui_queue

    def emit(self, entry: LogEntry) -> None:
        """
        Forward a log entry to the GUI queue.

        This method must not block or raise exceptions.
        """
        try:
            self._queue.put_nowait(entry)
        except Exception:
            pass
