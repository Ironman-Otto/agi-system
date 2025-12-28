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
