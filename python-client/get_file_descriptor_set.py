import socket
import time
from google.protobuf import descriptor_pool, descriptor_pb2

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
    print(fd_set)  # this is big

    # it's not clear to me the pool is more useful than the set
    pool = descriptor_pool.DescriptorPool()
    for fd in fd_set.file:
        pool.Add(fd)


if __name__ == "__main__":
    descriptors = get_info("../info_socket")
    # with open("descriptors.dat", "wb") as f:
    #     f.write(descriptors)
    parse_descriptors(descriptors)
