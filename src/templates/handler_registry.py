from __future__ import annotations

from src.core.logging.debug_flag import debug_flag
from dataclasses import dataclass
from multiprocessing.util import debug
from typing import Any, Callable, Dict, Optional, Tuple

HandlerFn = Callable[[Any, dict], None]
Key = Tuple[str, Optional[str]]  # (msg_type, msg_version or None)

@dataclass(frozen=True)
class DispatchResult:
    handled: bool
    handler_name: Optional[str] = None
    reason: Optional[str] = None

class HandlerRegistry:
    """
    Instance-based handler registry.
    Resolve order:
      1) (msg_type, msg_version)
      2) (msg_type, None)    -> any version
      3) ("*", None)         -> default handler
    """
    def __init__(self) -> None:
        self._handlers: Dict[Key, HandlerFn] = {}

    def register(self, msg_type: str, msg_version: Optional[str] = None):
        def decorator(func: HandlerFn) -> HandlerFn:
            key = (msg_type, msg_version)
            if key in self._handlers:
                raise ValueError(f"Handler already registered for {key}")
            self._handlers[key] = func
            return func
        return decorator

    def resolve(self, msg_type: str, msg_version: Optional[str]) -> Optional[HandlerFn]:
        fn = self._handlers.get((msg_type, msg_version))
        if fn:
            return fn
        fn = self._handlers.get((msg_type, None))
        if fn:
            return fn
        return self._handlers.get(("*", None))

    def dispatch(self, message: Any, ctx: Any):
        msg_type = getattr(message, "msg_type", None)
        msg_version = getattr(message, "msg_version", None)

        if not isinstance(msg_type, str) or not msg_type:
            return DispatchResult(False, reason="Message missing valid msg_type")

        fn = self.resolve(msg_type, msg_version)
        if fn is None:
            return DispatchResult(
                False,
                reason=f"No handler for msg_type='{msg_type}' version='{msg_version}'"
            )

        return fn(message, ctx)
    def list_handlers(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for (t, v), fn in self._handlers.items():
            k = f"{t}:{v}" if v else f"{t}:*"
            out[k] = getattr(fn, "__name__", "<handler>")
        return out