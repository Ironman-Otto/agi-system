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
