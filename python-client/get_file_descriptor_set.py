import socket
import time
from google.protobuf import descriptor_pb2, message_factory

def get_info(socket_path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(socket_path)
        s.sendall(b"GetFileDescriptorSet\n")
        response = s.recv(1000000)
        print(f"Got response with length: {len(response)}")
        return response


def parse_descriptors(descriptors):

    fd_set = descriptor_pb2.FileDescriptorSet()
    fd_set.ParseFromString(descriptors)
    # print(fd_set)  # this is big

    message_classes = message_factory.GetMessages(fd_set.file)
    return fd_set, message_classes


if __name__ == "__main__":
    descriptors = get_info("../info_socket")
    fd_set, message_classes = parse_descriptors(descriptors)
    print("Known message types:")
    print(message_classes.keys())
