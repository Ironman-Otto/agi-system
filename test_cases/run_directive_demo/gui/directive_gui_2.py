"""directive_gui.py

Minimal GUI for entering a directive and viewing the resulting plan.

- Sends DIRECTIVE_SUBMIT to NLP via CMB
- Receives PLAN_READY from Executive
- Periodically tails the JSONL log file

This is intentionally simple (Tkinter) and can be replaced later.
"""

from __future__ import annotations

import json
import os
import threading
import queue
import time
import tkinter as tk
from tkinter import scrolledtext

from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.logging.log_manager import LogManager, Logger
from src.core.logging.log_severity import LogSeverity
from src.core.logging.file_log_sink import FileLogSink
from src.core.intent.schema import DirectiveSource

class DirectiveGUI:
    def __init__(self, *, logfile: str = "logs/system.jsonl"):
        self.module_id = "GUI"
        self.logfile = logfile
         # -----------------------------
        # Logging setup
        # -----------------------------
        log_manager = LogManager(min_severity=LogSeverity.INFO)
        log_manager.register_sink(FileLogSink("logs/system.jsonl"))
        logger = Logger("DIRGUI", log_manager)

        logger.info(
            event_type="DIRECTIVE_GUI_INIT",
            message="GUI module initializing",
        )

        
        self.root = tk.Tk()
        self.root.title("AGI-System Demo – Directive → Plan")
        self.root.geometry("1000x700")

        self.create_widgets()
        # Decide which channels the GUI participates in.
        # Start minimal for the demo: choose the channel(s) you use in the dropdown.
        _channels = ["CC", "SMC", "VB", "BFC", "DAC", "EIG", "PC", "MC", "IC", "TC"]

        cfg = MultiChannelEndpointConfig.from_channel_names(
            module_id=self.module_id,  # Identity of this module on the bus
            channel_names=_channels,
            host="localhost",
            poll_timeout_ms=50,
        )

        self.ep = ModuleEndpoint(
            config=cfg,
            logger=logger.info,
            serializer=lambda b: b,
            deserializer=lambda b: b,
        )

        self.ep.start()

        self.gui_inbox = queue.Queue()

        threading.Thread(
            target=self._endpoint_listener,
            daemon=True
        ).start()

        # Poll loops
        self.root.after(100, self.poll_incoming)

    def create_widgets(self):
        # Directive input
        tk.Label(self.root, text="Directive").pack(anchor="w")
        self.directive_text = scrolledtext.ScrolledText(self.root, height=6)
        self.directive_text.pack(fill="x", padx=6, pady=4)

        # Preferred output format (optional)
        fmt_frame = tk.Frame(self.root)
        fmt_frame.pack(fill="x", padx=6)
        tk.Label(fmt_frame, text="Preferred output format (optional)").pack(side="left")
        self.format_entry = tk.Entry(fmt_frame)
        self.format_entry.pack(side="left", fill="x", expand=True, padx=6)

        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=6, pady=6)
        tk.Button(btn_frame, text="Send directive", command=self.on_send).pack(side="left")
        tk.Button(btn_frame, text="Clear", command=self.on_clear).pack(side="left", padx=6)

        # Output display
        tk.Label(self.root, text="System output").pack(anchor="w")
        self.output_text = scrolledtext.ScrolledText(self.root, height=16)
        self.output_text.pack(fill="both", expand=True, padx=6, pady=4)

        # Log tail
        tk.Label(self.root, text="System log (tail)").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(self.root, height=10)
        self.log_text.pack(fill="both", expand=False, padx=6, pady=4)

        self._last_log_size = 0
    
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _append_output(self, s: str):
        self.output_text.insert("end", s)
        self.output_text.see("end")

    def on_clear(self):
        self.directive_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        
    def on_close(self):
        try:
            self.ep.stop()
        finally:
            self.root.destroy()
            
            
    def run(self):
        self.root.mainloop()

    def _endpoint_listener(self):
        cnt = 0
        while True:
            if cnt % 100 == 0:
                self._append_output("[GUI listener] Waiting for messages...\n")
                cnt = 0
            cnt += 1 
            try:
                msg = self.ep.recv(timeout=0.1)
                if msg is not None and isinstance(msg, CognitiveMessage):
                    self._append_output(f"[GUI listener] Received message: {msg.msg_type}\n")
                    self.gui_inbox.put(msg)
            except Exception as e:
                print("[GUI listener]", e)
        
    def poll_incoming(self):
        try:
            while True:
                msg = self.gui_inbox.get_nowait()
                self._append_output(f"[INCOMING] {msg.msg_type}\n")
        except queue.Empty:
            pass

        self.root.after(100, self.poll_incoming)

    
    def on_send(self):
        directive = self.directive_text.get("1.0", "end").strip()
        preferred = self.format_entry.get().strip()

        if not directive:
            return

        msg = CognitiveMessage.create(
            schema_version=str(CognitiveMessage.get_schema_version()),
            msg_type="DIRECTIVE_SUBMIT",
            msg_version="0.1.0",
            source=self.module_id,
            targets=["NLP"],
            context_tag=None,
            correlation_id=None,
            payload={
                "directive_source":DirectiveSource.HUMAN.value,
                "directive_text": directive,
                "context": {
                    "preferred_output_format": preferred or None,
                    "ui_timestamp": time.time(),
                    "llm_model_id": "LLM_STUB",
                },
            },
            priority=60,
            ttl=60.0,
            signature="",
        )

        self.ep.send("CC", "NLP", msg.to_bytes())
        self._append_output(f"[GUI] Sent DIRECTIVE_SUBMIT to NLP (message_id={msg.message_id})\n")

def main():
    gui = DirectiveGUI(logfile="logs/system.jsonl")
    gui.run()


if __name__ == "__main__":
    main()
