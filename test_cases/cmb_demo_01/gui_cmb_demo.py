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
import json
import threading
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage

class CMBDemoGUI:
    def __init__(self, master):
        self.master = master
        master.title("CMB Demo Interface")

        #self.endpoint = ModuleEndpoint("gui", channel="CC")
        self.endpoint = ModuleEndpoint("gui")

        # Layout components
        self.create_widgets()
        self.log("[GUI] Ready.")

    def create_widgets(self):
        # Source Module
        tk.Label(self.master, text="Source Module:").grid(row=0, column=0, sticky="w")
        self.source_entry = ttk.Combobox(self.master, values=["executive", "gui", "behavior"])
        self.source_entry.grid(row=0, column=1)
        self.source_entry.set("executive")

        # Target Module
        tk.Label(self.master, text="Target Module:").grid(row=1, column=0, sticky="w")
        self.target_entry = ttk.Combobox(self.master, values=["behavior", "executive", "router"])
        self.target_entry.grid(row=1, column=1)
        self.target_entry.set("behavior")

        # Channel
        tk.Label(self.master, text="Channel:").grid(row=2, column=0, sticky="w")
        self.channel_entry = ttk.Combobox(self.master, values=["CC", "VB", "SMC", "BFC", "DAC", "EIG"])
        self.channel_entry.grid(row=2, column=1)
        self.channel_entry.set("CC")

        # Payload
        tk.Label(self.master, text="Payload (JSON):").grid(row=3, column=0, sticky="nw")
        self.payload_text = tk.Text(self.master, height=5, width=50)
        self.payload_text.grid(row=3, column=1)
        self.payload_text.insert("1.0", '{"directive": "start_behavior", "behavior": "explore_area"}')

        # Send button
        self.send_button = tk.Button(self.master, text="Send Message", command=self.send_message_thread)
        self.send_button.grid(row=4, column=1, pady=10)

        # Log box
        tk.Label(self.master, text="Log:").grid(row=5, column=0, sticky="nw")
        self.log_box = tk.Text(self.master, height=10, width=70)
        self.log_box.grid(row=5, column=1)

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def send_message_thread(self):
        threading.Thread(target=self.send_message).start()

    def send_message(self):
        print("[GUI] Send button clicked")
        try:
            source = self.source_entry.get()
            target = self.target_entry.get()
            channel = self.channel_entry.get()
            payload_text = self.payload_text.get("1.0", tk.END)
            payload = json.loads(payload_text)

            msg = CognitiveMessage(
                source=source,
                targets=[target],
                channel=channel,
                payload=payload
            )

            print("[GUI] Message created:", msg.to_dict())
            print("[GUI] Sending message via ModuleEndpoint...")
            self.log(f"[GUI] Sending message from {source} to {target} on {channel}...")

            try:
                self.endpoint.socket.send_json(msg.to_dict(), flags=self.endpoint.zmq.NOBLOCK)
                self.log("[GUI] Message sent successfully.")
            except self.endpoint.zmq.Again:
                self.log("[GUI ERROR] Could not send message: ZMQ queue full or router unavailable.")

        except json.JSONDecodeError:
            self.log("[GUI ERROR] Invalid JSON payload.")
        except Exception as e:
            self.log(f"[GUI ERROR] Exception occurred: {str(e)}")


def main():
    root = tk.Tk()
    app = CMBDemoGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
