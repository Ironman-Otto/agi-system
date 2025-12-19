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
