# module_endpoint.py
from __future__ import annotations

import threading
import time
import queue
from dataclasses import dataclass
from typing import Optional, Callable, Any
from dataclasses import dataclass
from typing import Dict
import zmq
from enum import Enum

class InboundDelivery(Enum):
    DIRECTED = "DIRECTED"    # ROUTER -> DEALER
    BROADCAST = "BROADCAST"  # PUB -> SUB
    NONE = "NONE"


@dataclass(frozen=True)
class ChannelConfig:
    """
    Configuration for a single CMB channel.

    Each channel has exactly one inbound delivery semantic.
    """

    name: str

    # Outbound (module -> router)
    router_port: int
    outbound_socket_type: int = zmq.DEALER

    # Inbound semantics
    inbound_delivery: InboundDelivery = InboundDelivery.DIRECTED
    inbound_port: Optional[int] = None

    # ACK path (optional, meaningful only for DIRECTED)
    ack_port: Optional[int] = None
    ack_socket_type: int = zmq.DEALER



@dataclass(frozen=True)
class MultiChannelEndpointConfig:
    """
    Configuration for a module endpoint supporting multiple channels.

    One ModuleEndpoint instance
    One module identity
    Multiple channel connections
    """

    module_id: str                        # e.g. "behavior.executor.1"
    channels: Dict[str, ChannelConfig]   # keyed by channel name
    host: str = "localhost"

    poll_timeout_ms: int = 50

    def channel_names(self) -> list[str]:
        return list(self.channels.keys())

    def get_channel(self, name: str) -> ChannelConfig:
        if name not in self.channels:
            raise KeyError(f"Channel '{name}' not configured for module '{self.module_id}'")
        return self.channels[name]



class ModuleEndpoint:
    """
    ModuleEndpoint: transport + queues boundary.

    Thread ownership model:
      - start() spins a thread
      - thread creates Context + sockets and runs poll loop
      - module logic never touches zmq sockets

    Queues:
      - _send_q: module logic -> endpoint (outbound messages)
      - _in_q: endpoint -> module logic (inbound messages)
      - _ack_q: endpoint -> module logic (ACK messages)
    """

    def __init__(
        self,
        config: EndpointConfig,
        *,
        logger: Optional[Callable[[str], None]] = None,
        serializer: Optional[Callable[[Any], bytes]] = None,
        deserializer: Optional[Callable[[bytes], Any]] = None,
    ):
        self.cfg = config
        self._log = logger or (lambda s: None)

        # Default serializer assumes caller already provides bytes.
        self._to_bytes = serializer or (lambda x: x if isinstance(x, (bytes, bytearray)) else str(x).encode("utf-8"))
        self._from_bytes = deserializer or (lambda b: b)

        self._send_q: "queue.Queue[tuple[bytes, bytes]]" = queue.Queue()
        self._in_q: "queue.Queue[Any]" = queue.Queue()
        self._ack_q: "queue.Queue[Any]" = queue.Queue()

        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # These exist only in endpoint thread
        self._ctx = None
        self._out_sock = None
        self._in_sock = None
        self._ack_sock = None
        self._poller = None

    # --------------------------
    # Public API (module side)
    # --------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, name=f"Endpoint[{self.cfg.module_id}]", daemon=True)
        self._thread.start()
        self._log(f"[Endpoint] Started for {self.cfg.module_id}")

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=join_timeout)
        self._log(f"[Endpoint] Stopped for {self.cfg.module_id}")

    def send(self, target_id: str, message: Any) -> None:
        """
        Enqueue an outbound message. Non-blocking (queue put).
        ROUTER-style addressing: first frame is destination identity.
        """
        dest = target_id.encode("utf-8")
        payload = self._to_bytes(message)
        self._send_q.put((dest, payload))

    def recv(self, timeout: Optional[float] = None) -> Optional[Any]:
        """Receive a normal inbound message (not ACK)."""
        try:
            return self._in_q.get(timeout=timeout)
        except queue.Empty:
            return None

    def recv_ack(self, timeout: Optional[float] = None) -> Optional[Any]:
        """Receive an ACK message."""
        try:
            return self._ack_q.get(timeout=timeout)
        except queue.Empty:
            return None

    def drain_incoming(self, max_items: int = 100) -> list[Any]:
        items = []
        for _ in range(max_items):
            try:
                items.append(self._in_q.get_nowait())
            except queue.Empty:
                break
        return items

    def drain_acks(self, max_items: int = 100) -> list[Any]:
        items = []
        for _ in range(max_items):
            try:
                items.append(self._ack_q.get_nowait())
            except queue.Empty:
                break
        return items

    # --------------------------
    # Endpoint thread internals
    # --------------------------

    def _run(self) -> None:
        try:
            self._setup_zmq()
            self._loop()
        except Exception as e:
            self._log(f"[Endpoint ERROR] {self.cfg.module_id}: {e!r}")
        finally:
            self._teardown_zmq()

    def _setup_zmq(self) -> None:
        self._ctx = zmq.Context.instance()

        # Outbound socket (DEALER -> ROUTER)
        self._out_sock = self._ctx.socket(self.cfg.outbound_socket_type)
        self._out_sock.setsockopt_string(zmq.IDENTITY, self.cfg.module_id)
        self._out_sock.connect(f"tcp://{self.cfg.host}:{self.cfg.router_port}")
        self._log(f"[Endpoint] {self.cfg.module_id} outbound connected to {self.cfg.router_port}")

        # Inbound socket (optional)
        if self.cfg.inbound_port is not None:
            self._in_sock = self._ctx.socket(self.cfg.inbound_socket_type)
            self._in_sock.setsockopt_string(zmq.IDENTITY, self.cfg.module_id)

            # If you later switch inbound_socket_type to SUB, you'll add:
            # self._in_sock.setsockopt(zmq.SUBSCRIBE, b"")
            self._in_sock.connect(f"tcp://{self.cfg.host}:{self.cfg.inbound_port}")
            self._log(f"[Endpoint] {self.cfg.module_id} inbound connected to {self.cfg.inbound_port}")

        # ACK socket (optional)
        if self.cfg.ack_port is not None:
            self._ack_sock = self._ctx.socket(self.cfg.ack_socket_type)
            self._ack_sock.setsockopt_string(zmq.IDENTITY, self.cfg.module_id)
            self._ack_sock.connect(f"tcp://{self.cfg.host}:{self.cfg.ack_port}")
            self._log(f"[Endpoint] {self.cfg.module_id} ACK connected to {self.cfg.ack_port}")

        # Poller for inbound + ack
        self._poller = zmq.Poller()
        if self._in_sock is not None:
            self._poller.register(self._in_sock, zmq.POLLIN)
        if self._ack_sock is not None:
            self._poller.register(self._ack_sock, zmq.POLLIN)

    def _teardown_zmq(self) -> None:
        # Close sockets created in thread
        for s in (self._out_sock, self._in_sock, self._ack_sock):
            try:
                if s is not None:
                    s.close(linger=0)
            except Exception:
                pass

        self._out_sock = None
        self._in_sock = None
        self._ack_sock = None
        self._poller = None

        # Do NOT terminate Context.instance() here; other endpoints may use it.
        self._ctx = None

    def _loop(self) -> None:
        while not self._stop_evt.is_set():
            # 1) Flush outbound send queue
            self._flush_outbound(max_per_tick=50)

            # 2) Poll inbound/ack sockets
            if self._poller is None:
                time.sleep(0.01)
                continue

            events = dict(self._poller.poll(self.cfg.poll_timeout_ms))

            if self._in_sock is not None and self._in_sock in events:
                self._handle_inbound(self._in_sock, is_ack=False)

            if self._ack_sock is not None and self._ack_sock in events:
                self._handle_inbound(self._ack_sock, is_ack=True)

    def _flush_outbound(self, max_per_tick: int) -> None:
        sent = 0
        while sent < max_per_tick:
            try:
                dest, payload = self._send_q.get_nowait()
            except queue.Empty:
                return

            # ROUTER addressing pattern:
            # send_multipart([dest_identity, b"", payload]) is common when talking to ROUTER.
            # If your router expects no empty delimiter, remove b"".
            try:
                self._out_sock.send_multipart([dest, b"", payload], flags=zmq.NOBLOCK)
                sent += 1
            except zmq.Again:
                # router backpressure; requeue and retry next tick
                self._send_q.put((dest, payload))
                return

    def _handle_inbound(self, sock, *, is_ack: bool) -> None:
        """
        Handles typical ROUTER->DEALER frames:
          [identity][empty?][payload]
        We keep this tolerant because your framing is still evolving.
        """
        frames = sock.recv_multipart()

        # Most common cases:
        # - ROUTER->DEALER: [sender_id, b"", payload] or [sender_id, payload]
        payload = frames[-1]
        msg_obj = self._from_bytes(payload)

        if is_ack:
            self._ack_q.put(msg_obj)
        else:
            self._in_q.put(msg_obj)
