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
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage
from src.core.messages.message_module import MessageType
from src.core.cmb.cmb_channel_config import get_channel_port, get_ack_Egress_port
from src.core.messages.ack_message import AckMessage 
from src.core.cmb.cmb_channel_router_port import ChannelRouterPort

class CMBDemoGUI:
    def __init__(self, master):
        self.master = master
        master.title("CMB Demo Interface")
    
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
        #self.endpoint.close()
        self.master.quit()
        self.master.destroy()


    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def send_message_thread(self): 
        threading.Thread(target=self.send_message).start()

    def send_message(self):
        print("[GUI] Send button clicked")
        self.log("[GUI] Send button clicked")

        # Connect to the appropriate router port based on selected channel
        router_port = get_channel_port(self.channel_entry.get())
        print(f"[GUI] Connecting to router port: {router_port}")
        self.log(f"[GUI] Connecting to router port: {router_port}")

        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        socket.setsockopt_string(zmq.IDENTITY, "gui")
        socket.connect(f"tcp://localhost:{router_port}")
        self.log("[GUI] Connected to router.")

        # Connect to Ack port
        ack_port = get_ack_Egress_port(self.channel_entry.get())
        print(f"[GUI] Connecting to ACK port: {ack_port}")
        self.log(f"[GUI] Connecting to ACK port: {ack_port}")
        context2 = zmq.Context()
        ack_socket = context2.socket(zmq.DEALER)
        ack_socket.setsockopt_string(zmq.IDENTITY, "gui")
        ack_socket.connect(f"tcp://localhost:{ack_port}")

        try:
            #Build the message details
            msg_type = MessageType.COMMAND.value
            msg_version = "0.1.0"
            source = self.source_entry.get()
            targets = self.target_entry.get()
            context_tag ="demo"
            correlation_id = "demo 01"
            payload_text = self.payload_text.get("1.0", tk.END)
            payload = json.loads(payload_text)
            priority = 1
            ttl = 10
            signature = None

            #Create the message
            msg = CognitiveMessage.create(
            schema_version="1.0",
            msg_type=msg_type,
            msg_version=msg_version,
            source=source,
            targets=[targets],
            context_tag=context_tag,
            correlation_id=correlation_id,
            payload=payload,
            priority=priority,
            ttl=ttl,
            signature=signature
            )

            print("[GUI] Message created:", msg.to_dict())
            print("[GUI] Sending message via ModuleEndpoint...")
            self.log(f"[GUI] Sending message from {source} to {targets} on {self.channel_entry.get()}...")

            try:
                socket.send_multipart([
                msg.source.encode(),
                msg.to_bytes()
                ])
                self.log("[GUI] Message sent successfully.")

                # Wait for ACK
    
                while True:
                    frames = ack_socket.recv_multipart()
                    print("[GUI] ACK received.")
                    self.log("[GUI] ACK received.")
                    identity = frames[0]
                    raw_msg = frames[-1]
                    msg = AckMessage.from_bytes(raw_msg)
                    print(f"[GUI] {self.channel_entry.get()} received message from {msg.source} {msg.msg_type}")
                    self.log(f"[GUI] {self.channel_entry.get()} received ACK from {msg.source} {msg.msg_type}")
                    break

            except zmq.Again:
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
