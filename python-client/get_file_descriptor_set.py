import socket
import time


def get_info(socket_path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(socket_path)
        s.sendall(b"GetFileDescriptorSet\n")
        response = s.recv(1000000)
        print(f"Got response with length: {len(response)}")
        return response


if __name__ == "__main__":
    get_info("../info_socket")
