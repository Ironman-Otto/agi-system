# module_endpoint.py
from __future__ import annotations

import threading
import time
import queue
from typing import Optional, Callable, Any
from typing import Dict
import zmq
import json

from src.core.cmb.utils import extract_message_id
from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.channel_registry import InboundDelivery
from src.core.cmb.transaction_registry import TransactionRegistry
from src.core.messages.ack_message import AckMessage
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_entry import LogEntry
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink


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

        # Logging
        self.log_manager = LogManager(min_severity=LogSeverity.INFO)
        self.log_manager.register_sink(
        FileLogSink("logs/system.jsonl")
        )
        self.logger = Logger(self.cfg.module_id, self.log_manager)

        # Old logger function fallback
        self._log = None

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
        
        self.logger.info(
            event_type="ENDPOINT_START",
            message=f"ModuleEndpoint started {self.cfg.module_id}",
            payload={
                "channels": list(self.cfg.channels.keys())
            }
        )

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=join_timeout)
        
        self.logger.info(
            event_type="ENDPOINT_STOP",
            message=f"ModuleEndpoint stopped {self.cfg.module_id}",
            payload={
                "channels": list(self.cfg.channels.keys())
            }
        )

    
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
            self.logger.info(
                event_type="ENDPOINT_EXCEPTION",
                message=f"ModuleEndpoint exception in {self.cfg.module_id}: {e!r}",
                payload={
                    "channels": list(self.cfg.channels.keys())
                }
            )
     
        finally:
            self._teardown_zmq()
            self.logger.info(
                    event_type="ENDPOINT_TEARDOWN",
                    message=f"ModuleEndpoint {self.cfg.module_id}  teardown complete ",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )

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

            self.logger.info(
                event_type="ENDPOINT_OUTBOUND_SETUP",
                message=f"ModuleEndpoint {self.cfg.module_id} setup outbound {ch_name} ",
                payload={
                    "channels": list(self.cfg.channels.keys())
                }
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

                self.logger.info(
                    event_type="ENDPOINT_INBOUND_SETUP",
                    message=f"ModuleEndpoint {self.cfg.module_id} setup inbound {ch_name} ",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
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

                self.logger.info(
                    event_type="ENDPOINT_ACK_SETUP",
                    message=f"ModuleEndpoint {self.cfg.module_id} setup ACK {ch_name} ",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
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
            """
            self._tx_registry.tick()
            self._tx_registry.cleanup_completed()
            """

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

                self.logger.info(
                    event_type="ENDPOINT_ZMQ_ERROR",
                    message=f"ModuleEndpoint {self.cfg.module_id} poller error : {e!r}",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )

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

            # Get outbound socket for channel
            out_sock = self._out_socks.get(ch_name)
            if out_sock is None:

                self.logger.info(
                    event_type="ENDPOINT_NO_OUTBOUND_SOCKET",
                    message=f"ModuleEndpoint {self.cfg.module_id} out_sock None {ch_name} ",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )

                continue

            # Send message
            try:                
                message_id = extract_message_id(payload)
                tx = self._tx_registry.create(
                    message_id=message_id,
                    channel=ch_name,
                    source=self.cfg.module_id,
                    target=dest.decode("utf-8"),
                    payload=payload,
                )

                
                self.logger.info(
                    event_type="ENDPOINT_TRANSACTION_CREATED",
                    message=f"ModuleEndpoint {self.cfg.module_id} channel: {ch_name} outgoing message_id={message_id}",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )

                # ROUTER addressing pattern:
                # [dest_identity][empty][payload]
                out_sock.send_multipart(
                    [payload],
                    flags=zmq.NOBLOCK
                )

                sent += 1

                self._log(f"[Endpoint.{self.cfg.module_id}] SEND ch={ch_name} dest={dest!r}")

                self.logger.info(
                    event_type="ENDPOINT_SENT_MESSAGE",
                    message=f"ModuleEndpoint {self.cfg.module_id} sent message on channel {ch_name} to {dest!r}",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )
                

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
        payload = frames[-1]
        msg_obj = json.loads(payload.decode("utf-8"))
        
        self.logger.info(
                    event_type="ENDPOINT_RECEIVED_MESSAGE",
                    message=f"ModuleEndpoint {self.cfg.module_id} received message from {msg_obj.get('source')!r}",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )
        # Most common cases:
        # - ROUTER->DEALER: [sender_id, b"", payload] or [sender_id, payload]
        payload = frames[-1]

        if is_ack:
            ack = AckMessage.from_bytes(payload)
            event = self._tx_registry.apply_ack(ack)
            
            self.logger.info(
                    event_type="ENDPOINT_RECEIVED_ACK",
                    message=f"ModuleEndpoint {self.cfg.module_id} received ACK for correlation_id={ack.correlation_id}, event={event} ack type = {ack.ack_type}",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )
            
            if event != "ERROR 1" and event != "ERROR 2":
                self._ack_q.put(ack)
            else:
                                
                self.logger.info(
                    event_type="ENDPOINT_ERROR_INVALID_ACK",
                    message=f"ModuleEndpoint {self.cfg.module_id} Received invalid ACK: {ack!r}",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )

        else:
            msg_obj = CognitiveMessage.from_bytes(payload)
            self._in_q.put(msg_obj)
            message_id = msg_obj.message_id
            tx = self._tx_registry.create(
                    message_id=message_id,
                    channel = None,
                    source=msg_obj.source,
                    target=msg_obj.targets,
                    payload=payload,
                )
            print(f"[Endpoint.{self.cfg.module_id} DEBUG] Created transaction for incoming message_id={message_id}\n")
             # send ACK back
            try:
                ack = AckMessage.create(
                    msg_type="ACK",
                    ack_type="MESSAGE_DELIVERED_ACK",
                    status="SUCCESS",
                    source=self.cfg.module_id,
                    targets=[msg_obj.source],
                    correlation_id=msg_obj.message_id,
                    payload={ 
                        "status": "published",
                        "message_id": msg_obj.message_id
                    }
                )

                self.send("CC", msg_obj.source, AckMessage.to_bytes(ack))

                self.logger.info(
                    event_type="ENDPOINT_SENT_ACK",
                    message=f"ModuleEndpoint {self.cfg.module_id} sent ACK to {msg_obj.source}",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )

            except Exception as e:
                self.logger.info(
                    event_type="ENDPOINT_ACK_SEND_ERROR",
                    message=f"ModuleEndpoint {self.cfg.module_id} outbound ACK send error: {e!r}",
                    payload={
                        "channels": list(self.cfg.channels.keys())
                    }
                )

            

