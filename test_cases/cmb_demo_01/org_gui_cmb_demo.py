"""
Module: gui_cmb_demo.py
Location: test_cases/cmb_demo_01/
Version: 0.1.0

Provides a simple Tkinter GUI for sending messages through the CMB and displaying log output.
Allows user to select source module, target, channel, and enter payload interactively.

Depends on: module_endpoint >= 0.1.0, cognitive_message >= 0.1.0, cmb_channel_config >= 0.1.0
"""


import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.cmb.cmb_channel_config import get_channel_port
from src.core.messages.cognitive_message import CognitiveMessage

class CMBGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CMB Demo Interface")

        self.module_names = ["executive", "behavior", "perception"]
        self.channel_names = ["CC", "SMC", "VB", "BFC"]  # Extend as needed

        self.build_ui()
        self.log("[GUI] Ready.")

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Source Module:").grid(row=0, column=0)
        self.source_var = tk.StringVar(value=self.module_names[0])
        ttk.Combobox(frame, textvariable=self.source_var, values=self.module_names).grid(row=0, column=1)

        ttk.Label(frame, text="Target Module:").grid(row=1, column=0)
        self.target_var = tk.StringVar(value=self.module_names[1])
        ttk.Combobox(frame, textvariable=self.target_var, values=self.module_names).grid(row=1, column=1)

        ttk.Label(frame, text="Channel:").grid(row=2, column=0)
        self.channel_var = tk.StringVar(value=self.channel_names[0])
        ttk.Combobox(frame, textvariable=self.channel_var, values=self.channel_names).grid(row=2, column=1)

        ttk.Label(frame, text="Payload (JSON):").grid(row=3, column=0)
        self.payload_entry = tk.Text(frame, height=5, width=40)
        self.payload_entry.grid(row=3, column=1)
        self.payload_entry.insert("1.0", '{"directive": "start_behavior", "behavior": "explore_area"}')

        self.send_button = ttk.Button(frame, text="Send Message", command=self.send_message)
        self.send_button.grid(row=4, column=1, pady=5)

        ttk.Label(frame, text="Log:").grid(row=5, column=0, sticky="nw")
        self.log_box = tk.Text(frame, height=10, width=70)
        self.log_box.grid(row=5, column=1)

    def log(self, text):
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)

    def send_message(self):
        try:
            source = self.source_var.get()
            target = self.target_var.get()
            channel = self.channel_var.get()
            payload_text = self.payload_entry.get("1.0", tk.END).strip()
            payload = json.loads(payload_text)

            pub_port = get_channel_port(channel) + 1
            push_port = get_channel_port(channel) + 0
            endpoint = ModuleEndpoint(source, pub_port, push_port)

            msg = CognitiveMessage.create(
                source=source,
                targets=[target],
                payload=payload,
                priority=50
            )
            endpoint.send(msg)
            self.log(f"[GUI] Sent message from {source} to {target} on {channel}: {msg.payload}")
            endpoint.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log(f"[ERROR] {e}")


def run_gui():
    root = tk.Tk()
    app = CMBGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
