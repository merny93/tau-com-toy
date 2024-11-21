import socket
import time
from google.protobuf import descriptor_pb2, message_factory

__all__ = ["get_file_descriptors"]

def get_file_descriptor_set(socket_path, bufsize=1000000, messages=True):
    """
    Get and optionally parse the FileDescriptorSet from a server.

    Parameters
    ==========
    socket_path : str/path
        The name of the UNIX socket on which to request info.
    bufsize : int, optional
        The number of bytes to try to read (can be larger than message)
        TODO change to reading this from the stream
    messages : bool, optional
        If True (default), return a dict from message name (str) to message classes.
        Otherwise return the FileDescriptorSet
    """
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(socket_path)
        s.sendall(b"GetFileDescriptorSet\n")
        # TODO update if changed to receving length + data
        # 1M is more than enough for this demo
        response = s.recv(bufsize)
        print(f"Got FileDescriptorSet with length: {len(response)}")

    fd_set = descriptor_pb2.FileDescriptorSet()
    fd_set.ParseFromString(response)

    if messages:
        return message_factory.GetMessages(fd_set.file)

    return fd_set


if __name__ == "__main__":
    message_classes = get_file_descriptor_set("../info_socket")
    print("Known message types:")
    print(message_classes.keys())
