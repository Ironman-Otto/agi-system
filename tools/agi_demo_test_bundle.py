
# ==================================================
# FILE: C:\dev\agi-system\test_cases\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\agent\run_agent_demo.py
# ==================================================

from src.core.intent.intent_extractor import IntentExtractor
from src.core.intent.router import DirectiveRouter
from src.core.intent.llm_adapter_mock import MockLLMAdapter

from src.core.agent.agent_loop import AgentLoop
from src.core.agent.behavior_registry import BehaviorRegistry
from src.core.agent.llm_consultant_stub import LLMConsultantStub

from src.core.agent.skill_executor import SkillExecutor


def main():
    # Existing intent components
    intent_extractor = IntentExtractor(
        llm_adapter=MockLLMAdapter(),
        min_confidence=0.6
    )
    router = DirectiveRouter()

    # New agent components
    registry = BehaviorRegistry()
    registry.register("create_docx", risk="low", requires_approval=False)

    llm_stub = LLMConsultantStub()

    executor = SkillExecutor()

    agent = AgentLoop(
        intent_extractor=intent_extractor,
        router=router,
        behavior_registry=registry,
        llm_consultant=llm_stub,
        skill_executor=executor
    )

    directives = [
        "Explain the history of TCP/IP.",
        "Design a test plan for the CMB router ACK flow."
    ]

    for d in directives:
        result = agent.run(d)
        print("[Result]", result)


if __name__ == "__main__":
    main()

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_01\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_01\gui_cmb_demo.py
# ==================================================

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

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_01\org_gui_cmb_demo.py
# ==================================================

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

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_01\run_cmb_demo.py
# ==================================================

"""
Module: run_cmb_demo.py
Location: test_cases/cmb_demo_01/
Version: 0.1.0

Launches core components for the CMB demo:
- Control Channel Router
- Behavior Stub
- Executive Stub (optional)
- GUI (Tkinter or Streamlit)

Use command-line args to choose configuration.
"""

import subprocess
import argparse
import sys
import os


"""
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
PYTHON = sys.executable  # Path to Python interpreter (uses .venv)

MODULES = {
    "router":      ["python", f"{BASE_PATH}/src/core/cmb/cmb_router.py"],
    "behavior":    ["python", f"{BASE_PATH}/src/core/modulesbehaviors/behavior_stub.py"],
    "executive":   ["python", f"{BASE_PATH}/src/core/executive/executive_stub.py"],
    "tk_gui":      ["python", f"{BASE_PATH}/test_cases/cmb_demo_01/gui_cmb_demo.py"],
    "streamlit_gui": ["streamlit", "run", f"{BASE_PATH}/test_cases/cmb_demo_01/streamlit_gui.py"]
}
"""
PYTHON = sys.executable

MODULES = {
    "router":     [PYTHON, "-m", "src.core.cmb.cmb_router_entry"],
    "behavior":   [PYTHON, "-m", "src.core.modules.behavior_module"],
    "executive":  [PYTHON, "-m", "src.core.executive.executive_stub"],
    "tk_gui":     [PYTHON, "-m", "test_cases.cmb_demo_01.gui_cmb_demo"],
}

# Dictionary mapping each channel acronym to a TCP port base
# These ports must match bindings in the CMB routers and the endpoints
CMB_CHANNEL_PORTS = {
    "CC": 6001,   # Control Channel
    "SMC": 6002,  # Symbolic Message Channel
    "VB": 6003,   # Vector Bus
    "BFC": 6004,  # Behavioral Flow Channel
    "DAC": 6005,  # Diagnostic and Awareness Channel
    "EIG": 6006,  # External Interface Gateway
    "PC": 6007,   # Perception Channel
    "MC": 6008,   # Memory Channel
    "IC": 6009,   # Introspection Channel
    "TC": 6010    # Threat Channel
}

def launch(name):
    print(f"[Launcher] Starting {name}...")
    return subprocess.Popen(MODULES[name])

def launch_router(channel):
    print(f"[Launcher] Starting router for channel {channel}...")
    return subprocess.Popen(MODULES["router"] + ["--channel", channel])


def main():
    parser = argparse.ArgumentParser(description="Launch CMB demo components")
    parser.add_argument("--gui", choices=["tk", "streamlit"], default="tk")
    parser.add_argument("--exec", action="store_true", help="Launch executive stub")

    args = parser.parse_args()

    procs = []
    #for channel in CMB_CHANNEL_PORTS:
     #   procs.append(launch_router(channel))
    procs.append(launch_router("CC"))
    procs.append(launch("behavior"))

    if args.exec:
        procs.append(launch("executive"))

    if args.gui == "tk":
        procs.append(launch("tk_gui"))
    elif args.gui == "streamlit":
        procs.append(launch("streamlit_gui"))

    print("[Launcher] All components launched. Press Ctrl+C to stop.")

    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        print("[Launcher] Shutting down...")
        for p in procs:
            p.send_signal(subprocess.signal.SIGINT)

        # Give children time to exit cleanly
        for p in procs:
            try:
                p.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                p.terminate()


if __name__ == "__main__":
    main()

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_01\streamlit_gui.py
# ==================================================

"""
Module: streamlit_gui.py
Location: test_cases/cmb_demo_01/
Version: 0.1.0

Streamlit-based GUI for sending messages into the Cognitive Message Bus (CMB).
Lets the user select source, target, channel, and input payload JSON.
Displays logs and confirmation of successful message delivery.

Depends on: streamlit, module_endpoint >= 0.1.0, cognitive_message >= 0.1.0
"""



import streamlit as st
import json
from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.cmb.cmb_channel_config import get_channel_port
from src.core.messages.cognitive_message import CognitiveMessage

st.set_page_config(page_title="CMB Demo UI", layout="wide")
st.title("🧠 AGI Cognitive Message Bus Demo (Streamlit)")

st.sidebar.header("Message Settings")

module_names = ["executive", "behavior", "perception"]
channel_names = ["CC", "SMC", "VB", "BFC"]

source = st.sidebar.selectbox("Source Module", module_names)
target = st.sidebar.selectbox("Target Module", module_names)
channel = st.sidebar.selectbox("CMB Channel", channel_names)
priority = st.sidebar.slider("Message Priority", min_value=1, max_value=100, value=50)

default_payload = {
    "directive": "start_behavior",
    "behavior": "explore_area"
}

payload_input = st.sidebar.text_area("Payload (JSON)", value=json.dumps(default_payload, indent=2), height=200)

if st.sidebar.button("Send Message"):
    try:
        payload = json.loads(payload_input)
        pub_port = get_channel_port(channel) + 1
        push_port = get_channel_port(channel) + 0

        endpoint = ModuleEndpoint(source, pub_port, push_port)

        msg = CognitiveMessage.create(
            source=source,
            targets=[target],
            payload=payload,
            priority=priority
        )
        endpoint.send(msg)
        endpoint.close()

        st.success(f"✅ Message sent from '{source}' to '{target}' on channel '{channel}'")
        st.json(asdict(msg))

    except Exception as e:
        st.error(f"❌ Error sending message: {str(e)}")


st.markdown("---")
st.markdown("""
### ℹ️ Instructions:
- Use the sidebar to select a module, channel, and enter a JSON payload.
- Click **Send Message** to push it into the bus.
- Launch `behavior_stub.py` and `cmb_router.py` to receive and route the message.
""")

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_02\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_02\client.py
# ==================================================

import zmq

context = zmq.Context()

socket = context.socket(zmq.REQ)
socket.connect("tcp://127.0.0.1:5555")

print("Sending message...")
socket.send_string("Hello from client")

reply = socket.recv_string()
print(f"Reply: {reply}")

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_02\dealer.py
# ==================================================

import zmq
import sys
import time

if len(sys.argv) < 2:
    print("Usage: python dealer.py <module_name>")
    sys.exit(1)

module_name = sys.argv[1]

context = zmq.Context()

socket = context.socket(zmq.DEALER)
socket.setsockopt_string(zmq.IDENTITY, module_name)
socket.connect("tcp://127.0.0.1:6000")

print(f"[DEALER:{module_name}] Connected to router")

for i in range(3):
    message = f"Hello {i} from {module_name}"
    socket.send_multipart([
        b"",
        message.encode()
    ])

    reply = socket.recv_multipart()
    print(f"[DEALER:{module_name}] Received: {reply[1].decode()}")

    time.sleep(1)

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_02\publisher.py
# ==================================================

import zmq
import time
import random

context = zmq.Context()

socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:7000")

print("[PUB] Publisher started on port 7000")

topics = ["LOG", "STATUS", "METRIC"]

time.sleep(1)  # IMPORTANT: allow subscribers to connect

while True:
    topic = random.choice(topics)
    message = f"{topic} Message at {time.time()}"

    socket.send_string(message)
    print(f"[PUB] Sent: {message}")

    time.sleep(1)

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_02\router.py
# ==================================================

import zmq

context = zmq.Context()

socket = context.socket(zmq.ROUTER)
socket.bind("tcp://127.0.0.1:6000")

print("[ROUTER] Channel router running on port 6000")

while True:
    frames = socket.recv_multipart()

    identity = frames[0]
    empty = frames[1]
    payload = frames[2]

    print(f"[ROUTER] From {identity.decode()}: {payload.decode()}")

    reply = f"ACK to {identity.decode()}".encode()

    socket.send_multipart([
        identity,
        b"",
        reply
    ])

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_02\server.py
# ==================================================

import zmq

context = zmq.Context()

socket = context.socket(zmq.REP)
socket.bind("tcp://127.0.0.1:5555")

print("Server listening on port 5555...")

while True:
    message = socket.recv_string()
    print(f"Received: {message}")
    socket.send_string("ACK from server")

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_02\subscriber.py
# ==================================================

import zmq
import sys

if len(sys.argv) < 2:
    print("Usage: python subscriber.py <TOPIC>")
    sys.exit(1)

topic_filter = sys.argv[1]

context = zmq.Context()

socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:7000")

socket.setsockopt_string(zmq.SUBSCRIBE, topic_filter)

print(f"[SUB] Subscribed to topic: {topic_filter}")

while True:
    message = socket.recv_string()
    print(f"[SUB:{topic_filter}] Received: {message}")

# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_03\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\cmb_demo_03\simulated_threading_demo_cmb.py
# ==================================================

import uuid
import time
import queue
import threading
from concurrent.futures import Future


command_queue = queue.Queue()
ack_queue = queue.Queue()
pending_acks = {}

def executive_send_command(action: str):
    msg_id = str(uuid.uuid4())

    message = {
        "message_id": msg_id,
        "type": "COMMAND",
        "payload": {"action": action}
    }

    future = Future()
    pending_acks[msg_id] = future

    print("[Executive] Sending command:", message)
    command_queue.put(message)

    return future

def behavior_worker():
    while True:
        message = command_queue.get()

        print("[Behavior] Received:", message)

        # Simulate processing
        time.sleep(1)

        ack = {
            "correlation_id": message["message_id"],
            "type": "ACK",
            "status": "OK",
            "payload": {"result": "action_completed"}
        }

        print("[Behavior] Sending ACK:", ack)
        ack_queue.put(ack)

def executive_ack_listener():
    while True:
        ack = ack_queue.get()
        corr_id = ack["correlation_id"]

        future = pending_acks.pop(corr_id, None)
        if future:
            future.set_result(ack)
def main():
    threading.Thread(target=behavior_worker, daemon=True).start()
    threading.Thread(target=executive_ack_listener, daemon=True).start()

    future = executive_send_command("move_arm")

    print("[Executive] Waiting for ACK...")
    ack = future.result(timeout=5)

    print("[Executive] ACK received:", ack)

if __name__ == "__main__":
    main()


# ==================================================
# FILE: C:\dev\agi-system\test_cases\executive\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\gui_dir_demo\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\gui_dir_demo\gui.py
# ==================================================

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

def main():
    gui = DirectiveGUI(logfile="logs/system.jsonl")
    gui.run()


if __name__ == "__main__":
    main()

# ==================================================
# FILE: C:\dev\agi-system\test_cases\intent\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\intent\run_intent_demo.py
# ==================================================

from pathlib import Path

from src.core.intent.llm_adapter_mock import MockLLMAdapter
from src.core.intent.intent_extractor import IntentExtractor
from src.core.intent.router import DirectiveRouter
from src.core.intent.logging import IntentLogger


def main() -> None:
    adapter = MockLLMAdapter()
    extractor = IntentExtractor(llm_adapter=adapter, min_confidence=0.60)
    router = DirectiveRouter()
    logger = IntentLogger(log_path=Path("logs/intent_log.jsonl"))

    directives = [
        "Explain the history of TCP/IP.",
        "Compare PCIe and optical backplanes for a blade server.",
        "Design a test plan for the CMB router ACK flow.",
        "Monitor temperature and alert if it exceeds threshold.",
        "What do you think of what happened",
        "Hello what",
        "Design the system.",
        "Fix it",
        "Explain and implement the architecture.",
        "monitor performance",
        'Deploy the solution'
    ]

    for d in directives:
        intent = extractor.extract_intent(d)
        route = router.route(intent)
        logger.log(directive_text=d, intent=intent, route=route)
        print("Directive:", d)
        print("Intent:", intent.to_dict())
        print("Route:", route)
        print("-" * 60)


if __name__ == "__main__":
    main()

# ==================================================
# FILE: C:\dev\agi-system\test_cases\intent\test_intent_models.py
# ==================================================

import pytest
from src.core.intent.schema import from_dict, IntentValidationError


def test_from_dict_valid() -> None:
    data = {
        "intent_id": "123",
        "directive_source": "human",
        "directive_type": "cognitive",
        "planning_required": False,
        "urgency_level": "normal",
        "risk_level": "none",
        "expected_response_type": "textual_response",
        "confidence_score": 0.9,
    }
    intent = from_dict(data)
    assert intent.intent_id == "123"
    assert intent.confidence_score == 0.9


def test_from_dict_missing_required() -> None:
    with pytest.raises(IntentValidationError):
        from_dict({"intent_id": "123"})

# ==================================================
# FILE: C:\dev\agi-system\test_cases\intent\test_intent_router.py
# ==================================================

from src.core.intent.models import IntentObject
from src.core.intent.router import DirectiveRouter, Route


def test_router_direct_response() -> None:
    router = DirectiveRouter()
    intent = IntentObject(planning_required=False, clarification_required=False)
    assert router.route(intent) == Route.DIRECT_RESPONSE


def test_router_invoke_planner() -> None:
    router = DirectiveRouter()
    intent = IntentObject(planning_required=True, clarification_required=False)
    assert router.route(intent) == Route.INVOKE_PLANNER


def test_router_clarification() -> None:
    router = DirectiveRouter()
    intent = IntentObject(planning_required=False, clarification_required=True)
    assert router.route(intent) == Route.REQUEST_CLARIFICATION

# ==================================================
# FILE: C:\dev\agi-system\test_cases\questioning\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\reflection\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\run_directive_demo\gui\__init__.py
# ==================================================


# ==================================================
# FILE: C:\dev\agi-system\test_cases\run_directive_demo\gui\directive_gui.py
# ==================================================

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
import time
import tkinter as tk
from tkinter import scrolledtext

from core.cmb.endpoint_config import MultiChannelEndpointConfig

from src.core.cmb.module_endpoint import ModuleEndpoint
from src.core.messages.cognitive_message import CognitiveMessage



class DirectiveGUI:
    def __init__(self, *, logfile: str = "logs/system.jsonl"):
        self.module_id = "GUI"
        self.logfile = logfile

        # Decide which channels the GUI participates in.
        # Start minimal for the demo: choose the channel(s) you use in the dropdown.
        gui_channels = ["CC", "SMC", "VB", "BFC", "DAC", "EIG", "PC", "MC", "IC", "TC"]

        cfg = MultiChannelEndpointConfig.from_channel_names(
            module_id=self.module_id,  # Identity of this module on the bus
            channel_names=gui_channels,
            host="localhost",
            poll_timeout_ms=50,
        )

        self.ep = ModuleEndpoint(
            config=cfg,
            logger=lambda s: None,
            serializer=lambda msg: msg.to_bytes(),
            deserializer=lambda b: b,
        )
        self.ep.start()

        self.root = tk.Tk()
        self.root.title("AGI-System Demo – Directive → Plan")
        self.root.geometry("1000x700")

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

        # Poll loops
        self.root.after(100, self.poll_incoming)
        self.root.after(500, self.poll_log)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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
            msg = self.ep.recv(timeout=0.0)
            if msg is not None and isinstance(msg, CognitiveMessage):
                if msg.msg_type == "PLAN_READY":
                    plan = msg.payload.get("plan")
                    self._append_output("\n=== PLAN_READY ===\n")
                    self._append_output(json.dumps(plan, indent=2) + "\n")
                elif msg.msg_type == "CLARIFICATION_REQUEST":
                    self._append_output("\n=== CLARIFICATION_REQUEST ===\n")
                    self._append_output(json.dumps(msg.payload, indent=2) + "\n")
                else:
                    self._append_output(f"\n=== {msg.msg_type} ===\n")
                    self._append_output(json.dumps(msg.payload, indent=2) + "\n")
        finally:
            self.root.after(100, self.poll_incoming)

    def poll_log(self):
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
            self.root.after(500, self.poll_log)

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

# ==================================================
# FILE: C:\dev\agi-system\test_cases\run_directive_demo\gui\directive_gui_2.py
# ==================================================

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

# ==================================================
# FILE: C:\dev\agi-system\test_cases\run_directive_demo\run_directive_demo.py
# ==================================================

"""
Module: run_cmb_demo.py
Location: test_cases/cmb_demo_01/
Version: 0.1.0

Launches core components for the CMB demo:
- Control Channel Router
- Behavior Stub
- Executive Stub (optional)
- GUI (Tkinter or Streamlit)

Use command-line args to choose configuration.
"""
from __future__ import annotations
import subprocess
import argparse
import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

PYTHON = sys.executable

MODULES = {
    "router":     [PYTHON, "-m", "src.core.cmb.cmb_router_entry"],
    "behavior":   [PYTHON, "-m", "src.core.behaviors.behavior_stub"],
    "executive":  [PYTHON, "-m", "src.core.modules.executive_module"],
    "nlp":        [PYTHON, "-m", "src.core.modules.nlp_module"],
    "planner":    [PYTHON, "-m", "src.core.modules.planner_module"],
    "tk_gui":     [PYTHON, "-m", "test_cases.run_directive_demo.gui.directive_gui_2"],
}

# Dictionary mapping each channel acronym to a TCP port base
# These ports must match bindings in the CMB routers and the endpoints
CMB_CHANNEL_PORTS = {
    "CC": 6001,   # Control Channel
    "SMC": 6002,  # Symbolic Message Channel
    "VB": 6003,   # Vector Bus
    "BFC": 6004,  # Behavioral Flow Channel
    "DAC": 6005,  # Diagnostic and Awareness Channel
    "EIG": 6006,  # External Interface Gateway
    "PC": 6007,   # Perception Channel
    "MC": 6008,   # Memory Channel
    "IC": 6009,   # Introspection Channel
    "TC": 6010    # Threat Channel
}

def _ensure_dirs() -> None:
    os.makedirs("logs", exist_ok=True)


def launch(name):
    print(f"[Launcher] Starting {name}...")
    return subprocess.Popen(MODULES[name])

def launch_router(channel):
    print(f"[Launcher] Starting router for channel {channel}...")
    return subprocess.Popen(MODULES["router"] + ["--channel", channel])


def main():
    _ensure_dirs()
    parser = argparse.ArgumentParser(description="Launch CMB demo components")
    parser.add_argument("--gui", choices=["tk", "streamlit"], default="tk")
    parser.add_argument("--exec", action="store_true", help="Launch executive stub")

    args = parser.parse_args()

    procs = []

    procs.append(launch_router("CC"))
    procs.append(launch("behavior"))
    procs.append(launch("executive"))
    procs.append(launch("nlp"))
    procs.append(launch("planner"))
    procs.append(launch("tk_gui"))

    print("[Launcher] All components launched. Press Ctrl+C to stop.")

    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        print("[Launcher] Shutting down...")
        for p in procs:
            p.terminate()

        # Give children time to exit cleanly
        for p in procs:
            try:
                p.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                p.terminate()


if __name__ == "__main__":
    main()
