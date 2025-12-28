import zmq

context = zmq.Context()

socket = context.socket(zmq.REQ)
socket.connect("tcp://127.0.0.1:5555")

print("Sending message...")
socket.send_string("Hello from client")

reply = socket.recv_string()
print(f"Reply: {reply}")
