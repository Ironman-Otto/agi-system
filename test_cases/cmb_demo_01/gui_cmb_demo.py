"""
Module: gui_cmb_demo.py
Location: test_cases/cmb_demo_01/
Version: 0.1.0

Provides a simple Tkinter GUI for sending messages through the CMB and displaying log output.
Allows user to select source module, target, channel, and enter payload interactively.

Depends on: module_endpoint >= 0.1.0, cognitive_message >= 0.1.0, cmb_channel_config >= 0.1.0
"""


from socket import socket
import time
import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import zmq

from src.core.messages.message_module import MessageType
from src.core.cmb.cmb_channel_config import get_channel_port, get_ack_port
from src.core.cmb.cmb_channel_router_port import ChannelRouterPort

from src.core.cmb.channel_registry import ChannelRegistry
from src.core.cmb.endpoint_config import MultiChannelEndpointConfig
from src.core.cmb.module_endpoint import ModuleEndpoint

from src.core.messages.ack_message import AckMessage
from src.core.messages.cognitive_message import CognitiveMessage


class CMBDemoGUI:
    def __init__(self, master):
        self.master = master
        master.title("CMB Demo Interface")
    
        # Layout components
        self.create_widgets()
        self.log("[GUI] Ready.")

        self.endpoint = None
        # Build ChannelRegistry once
        ChannelRegistry.initialize()

        # Decide which channels the GUI participates in.
        # Start minimal for the demo: choose the channel(s) you use in the dropdown.
        gui_channels = ["CC", "SMC", "VB", "BFC", "DAC", "EIG", "PC", "MC", "IC", "TC"]

        cfg = MultiChannelEndpointConfig.from_channel_names(
            module_id="executive",  # Identity of this module on the bus
            channel_names=gui_channels,
            host="localhost",
            poll_timeout_ms=50,
        )

        # Create endpoint (logger uses your GUI log function)
        self.endpoint = ModuleEndpoint(
            config=cfg,
            logger=self.log,
            serializer=lambda x: x if isinstance(x, (bytes, bytearray)) else str(x).encode("utf-8"),
            deserializer=lambda b: b,  # Keep bytes; GUI will parse ACK vs MSG
        )
        self.master.after(100, self._poll_endpoint)

        self.endpoint.start()
        self.log("[GUI] Endpoint started.")


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
        self.send_button = tk.Button(self.master, text="Send Message", command=self.send_message)
        self.send_button.grid(row=4, column=1, pady=10)

        # Log box
        tk.Label(self.master, text="Log:").grid(row=5, column=0, sticky="nw")
        self.log_box = tk.Text(self.master, height=10, width=70)
        self.log_box.grid(row=5, column=1)

        self.exit_button = tk.Button(
        self.master,
        text="Exit",
        command=self.shutdown)
        self.exit_button.grid(row=6, column=1, pady=5)

    def shutdown(self):
        self.log("[GUI] Shutting down...")
        if self.endpoint:
            self.endpoint.stop()
        self.master.quit()
        self.master.destroy()


    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def _poll_endpoint(self) -> None:
        assert self.endpoint is not None
        
        #Drain a few ACKs per tick
        for _ in range(10):
            raw = self.endpoint.recv_ack(timeout=0)
            if raw is None:
                break
            try:
                #ack = AckMessage.from_bytes(raw)
                self.log(f"[GUI] ACK: {raw.ack_type} status={raw.status} corr id = {raw.correlation_id} from {raw.source}")
            except Exception:
                self.log("[GUI] ACK: (unparsed bytes)")

        # Drain a few inbound messages per tick
        for _ in range(10):
            raw = self.endpoint.recv(timeout=0)
            if raw is None:
                break
            try:
               #msg = CognitiveMessage.from_bytes(raw)
                self.log(f"[GUI] IN: {raw.msg_type} from {raw.source} -> {raw.targets}")
            except Exception:
                self.log("[GUI] IN: (unparsed bytes)")

        # Schedule next poll
        self.master.after(100, self._poll_endpoint)


    def send_message_thread(self): 
        threading.Thread(target=self.send_message).start()

    def send_message(self):
        print("[GUI] Send button clicked")
        self.log("[GUI] Send button clicked")

    
        try:
            #Build the message details
            msg_type = MessageType.COMMAND.value
            msg_version = "0.1.0"
            source = self.source_entry.get()
            target = self.target_entry.get().strip()
            context_tag ="demo"
            correlation_id = None
            payload_text = self.payload_text.get("1.0", tk.END)
            payload = json.loads(payload_text)
            priority = 1
            ttl = 10
            signature = None

            channel = self.channel_entry.get().strip()

            #Create the message
            msg = CognitiveMessage.create(
            schema_version="1.0",
            msg_type=msg_type,
            msg_version=msg_version,
            source=source,
            targets=[target],
            context_tag=context_tag,
            correlation_id=correlation_id,
            payload=payload,
            priority=priority,
            ttl=ttl,
            signature=signature
            )

           # IMPORTANT: endpoint now sends bytes payload
            self.endpoint.send(channel=channel, target_id=target, message=msg.to_bytes())

            self.log(f"[GUI] Queued message on {channel} from {source} to {target}.")
        
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
