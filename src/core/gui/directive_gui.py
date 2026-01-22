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
import time
import tkinter as tk
from tkinter import scrolledtext
import queue

from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage


class DirectiveGUI:
    def __init__(self, *, logfile: str = "logs/system.jsonl"):
        self.module_id = "GUI"
        self.logfile = logfile
        
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
            logger=lambda s: None,
            serializer=lambda msg: msg.to_bytes(),
            deserializer=lambda b: b,
        )


        self.gui_inbox = queue.Queue()
        # Poll loops
        self.root.after(100, self.poll_incoming)
        self.root.after(1500, self.poll_log)

        self.ep.start()

        self._listener_thread = threading.Thread(
            target=self._endpoint_listener,
            daemon=True
        )
        self._listener_thread.start() 


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

    def _endpoint_listener(self):

        while True:
            try:
               msg = self.ep.recv(timeout=1.0)
               if msg is not None:
                   self.gui_inbox.put(msg)
            except Exception:
                pass

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

    def on_clear(self):
        self.directive_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")

    def _append_output(self, s: str):
        self.output_text.insert("end", s)
        self.output_text.see("end")

    def poll_incoming(self):
        try:
            while True:
                msg = self.gui_inbox.get_nowait()

                if isinstance(msg, CognitiveMessage):
                    if msg.msg_type == "PLAN_READY":
                        self._append_output("\n=== PLAN_READY ===\n")
                        self._append_output(json.dumps(msg.payload, indent=2) + "\n")
                    elif msg.msg_type == "CLARIFICATION_REQUEST":
                        self._append_output("\n=== CLARIFICATION_REQUEST ===\n")
                        self._append_output(json.dumps(msg.payload, indent=2) + "\n")
                    else:
                        self._append_output(f"\n=== {msg.msg_type} ===\n")
                        self._append_output(json.dumps(msg.payload, indent=2) + "\n")
                else:
                    break
        except queue.Empty:
            pass

        self.root.after(100, self.poll_incoming)


    def poll_log(self):
        if not self.root.winfo_exists():
            return

        try:
            if not os.path.exists(self.logfile):
                self.root.after(500, self.poll_log)
                return

            size = os.path.getsize(self.logfile)
            if size == self._last_log_size:
                self.root.after(500, self.poll_log)
                return

            # Read new content (simple approach for demo)
            with open(self.logfile, "r", encoding="utf-8") as f:
                lines = f.readlines()[-50:]  # tail 50

            self.log_text.delete("1.0", "end")
            self.log_text.insert("end", "".join(lines))
            self.log_text.see("end")
            self._last_log_size = size

        finally:
            self.root.after(1500, self.poll_log)

    def on_close(self):
        try:
            self.ep.stop()
        finally:
            self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    gui = DirectiveGUI(logfile="logs/system.jsonl")
    gui.run()


if __name__ == "__main__":
    main()
