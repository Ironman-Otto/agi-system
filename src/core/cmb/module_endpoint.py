# module_endpoint.py
from __future__ import annotations

import threading
import time
import queue
from typing import Optional, Callable, Any
from typing import Dict
import zmq

from src.core.cmb.utils import extract_message_id
from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.channel_registry import InboundDelivery
from src.core.cmb.transaction_registry import TransactionRegistry
from src.core.messages.ack_message import AckMessage
from src.core.messages.cognitive_message import CognitiveMessage

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
        config: MultiChannelEndpointConfig,
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

        self._send_q: "queue.Queue[tuple[str,bytes, bytes]]" = queue.Queue()
        self._in_q: "queue.Queue[Any]" = queue.Queue()
        self._ack_q: "queue.Queue[Any]" = queue.Queue()

        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # These exist only in endpoint thread
        self._ctx = None
        self._out_socks: dict[str, zmq.Socket] = {}
        self._in_socks: dict[str, zmq.Socket] = {}
        self._ack_socks: dict[str, zmq.Socket] = {}
        self._poller = None

        self._sock_to_channel: dict[zmq.Socket, str] = {}
        self._sock_is_ack: dict[zmq.Socket, bool] = {}

        self._tx_registry = TransactionRegistry()


    # --------------------------
    # Public API (module side)
    # --------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, name=f"Endpoint[{self.cfg.module_id}]", daemon=False)
        self._thread.start()
        self._log(f"[Endpoint.{self.cfg.module_id}] Started for {self.cfg.module_id}")

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=join_timeout)
        self._log(f"[Endpoint] Stopped for {self.cfg.module_id}")

    
    def send(self, channel: str, target_id: str, message: Any) -> None:
        """
        Enqueue an outbound message. Non-blocking (queue put).
        ROUTER-style addressing: first frame is destination identity.
        """
        dest = target_id.encode("utf-8")
        payload = self._to_bytes(message)
        self._send_q.put((channel, dest, payload))

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
            self._log(f"[Endpoint.{self.cfg.module_id} ERROR] {self.cfg.module_id}: {e!r}")
        finally:
            self._teardown_zmq()

    def _setup_zmq(self) -> None:
        """
        Create and connect ZMQ sockets for all configured channels.
        Runs exclusively inside the endpoint thread.
        """
        self._ctx = zmq.Context.instance()

        # Poller for all inbound + ACK sockets
        self._poller = zmq.Poller()

        for ch_name, ch_cfg in self.cfg.channels.items():
            # ---------------------------
            # Outbound socket (DEALER -> ROUTER)
            # ---------------------------
            out_sock = self._ctx.socket(ch_cfg.outbound_socket_type)
            out_sock.setsockopt_string(zmq.IDENTITY, self.cfg.module_id)
            out_sock.connect(f"tcp://{self.cfg.host}:{ch_cfg.router_port}")

            self._out_socks[ch_name] = out_sock
            self._log(
                f"[Endpoint.{self.cfg.module_id}] outbound[{ch_name}] "
                f"connected to {ch_cfg.router_port}"
            )

            # ---------------------------
            # Inbound socket (optional)
            # ---------------------------
            if ch_cfg.inbound_port is not None:
                if ch_cfg.inbound_delivery == InboundDelivery.BROADCAST:
                    in_sock = self._ctx.socket(zmq.SUB)
                    in_sock.setsockopt(zmq.SUBSCRIBE, b"")
                else:
                    in_sock = self._ctx.socket(zmq.DEALER)
                    in_sock.setsockopt_string(zmq.IDENTITY, self.cfg.module_id)


                # Identity is required for DEALER, ignored for SUB
                in_sock.setsockopt_string(zmq.IDENTITY, self.cfg.module_id)

                # SUB sockets must subscribe explicitly
                if ch_cfg.inbound_delivery.name == "BROADCAST":
                    in_sock.setsockopt(zmq.SUBSCRIBE, b"")

                in_sock.connect(f"tcp://{self.cfg.host}:{ch_cfg.inbound_port}")

                self._in_socks[ch_name] = in_sock
                self._sock_to_channel[in_sock] = ch_name
                self._sock_is_ack[in_sock] = False
                self._poller.register(in_sock, zmq.POLLIN)
                self._log(
                    f"[Endpoint.{self.cfg.module_id}] inbound[{ch_name}] "
                    f"connected to {ch_cfg.inbound_port} "
                    f"({ch_cfg.inbound_delivery.value})"
                )

            # ---------------------------
            # ACK socket (optional, DIRECTED only)
            # ---------------------------
            if ch_cfg.ack_port is not None:
                ack_sock = self._ctx.socket(ch_cfg.ack_socket_type)
                ack_sock.setsockopt_string(zmq.IDENTITY, self.cfg.module_id)
                ack_sock.connect(f"tcp://{self.cfg.host}:{ch_cfg.ack_port}")

                self._ack_socks[ch_name] = ack_sock
                self._sock_to_channel[ack_sock] = ch_name
                self._sock_is_ack[ack_sock] = True
                self._poller.register(ack_sock, zmq.POLLIN)

                self._log(
                    f"[Endpoint.{self.cfg.module_id}] ACK[{ch_name}] "
                    f"connected to {ch_cfg.ack_port}"
                )

    def _teardown_zmq(self) -> None:
        # Close sockets created in thread
        for s in (self._out_socks, self._in_socks, self._ack_socks):
            try:
                if s is not None:
                    s.close(linger=0)
            except Exception:
                pass

        self._out_socks = None
        self._in_socks = None
        self._ack_socks = None
        self._poller = None

        # Do NOT terminate Context.instance() here; other endpoints may use it.
        self._ctx = None

    def _loop(self) -> None:
        """
        Main endpoint event loop.
        Handles outbound flushing and inbound/ACK dispatch
        across all configured channels.
        """
        while not self._stop_evt.is_set():
            self._tx_registry.tick()
            self._tx_registry.cleanup_completed()

            # 1) Flush outbound messages (fair, bounded)
            self._flush_outbound(max_per_tick=50)

            # 2) Poll inbound + ACK sockets
            if self._poller is None:
                time.sleep(0.01)
                continue

            try:
                events = dict(self._poller.poll(self.cfg.poll_timeout_ms))
            except zmq.ZMQError as e:
                # Context terminated or shutting down
                self._log(f"[Endpoint.{self.cfg.module_id}] Poller error: {e!r}")
                return

            # 3) Dispatch ready sockets
            for sock in events:
                is_ack = self._sock_is_ack.get(sock, False)
                self._handle_inbound(sock, is_ack=is_ack)


    def _flush_outbound(self, max_per_tick: int) -> None:
        """
        Flush outbound messages across all channels.
        Respects backpressure and preserves message ordering per channel.
        """
        sent = 0

        while sent < max_per_tick:
            try:
                ch_name, dest, payload = self._send_q.get_nowait()

            except queue.Empty:
                return

            
            out_sock = self._out_socks.get(ch_name)
            if out_sock is None:
                self._log(
                    f"[Endpoint.{self.cfg.module_id} ERROR] No outbound socket for channel '{ch_name}'"
                )
                continue

            try:
                message_id = extract_message_id(payload)
                tx = self._tx_registry.create(
                    message_id=message_id,
                    channel=ch_name,
                    source=self.cfg.module_id,
                    target=dest.decode("utf-8"),
                    payload=payload,
                )

                # ROUTER addressing pattern:
                # [dest_identity][empty][payload]
                out_sock.send_multipart(
                    [payload],
                    flags=zmq.NOBLOCK
                )
                sent += 1
                self._log(f"[Endpoint.{self.cfg.module_id}] SEND ch={ch_name} dest={dest!r}")

            except zmq.Again:
                # Backpressure: requeue and retry next loop
                self._send_q.put((ch_name, dest, payload))
                return

    def _handle_inbound(self, sock, *, is_ack: bool) -> None:
        """
        Handles typical ROUTER->DEALER frames:
          [identity][empty?][payload]
        We keep this tolerant because your framing is still evolving.
        """
        frames = sock.recv_multipart()
        self._log(f"[Endpoint.{self.cfg.module_id} DEBUG] Received frames: {frames}")

        # Most common cases:
        # - ROUTER->DEALER: [sender_id, b"", payload] or [sender_id, payload]
        payload = frames[-1]
        #msg_obj = self._from_bytes(payload)

        if is_ack:
            ack = AckMessage.from_bytes(payload)
            self._tx_registry.apply_ack(ack)
            self._ack_q.put(ack)
        else:
            msg_obj = CognitiveMessage.from_bytes(payload)
            self._in_q.put(msg_obj)

