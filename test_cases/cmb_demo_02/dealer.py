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
