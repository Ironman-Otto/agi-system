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
