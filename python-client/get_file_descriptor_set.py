import socket
import time


def get_info(socket_path):
    # Create a Unix socket object
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        # Connect to the Unix socket
        s.connect(socket_path)
        s.sendall(b"GetFileDescriptorSet")
        # response = recv_timeout(s, 2)
        response = s.recv(8)
        print(f"Got response: {response}")

def recv_timeout(the_socket, timeout=2):
    # make socket non blocking
    the_socket.setblocking(0)

    # total data partwise in an array
    total_data = []

    # beginning time
    begin = time.time()
    while 1:
        # if you got some data, then break after timeout
        if total_data and time.time() - begin > timeout:
            break

        # if you got no data at all, wait a little longer, twice the timeout
        elif time.time() - begin > timeout * 2:
            break

        # recv something
        try:
            data = the_socket.recv(8192)
            if data:
                total_data.append(data)
                # change the beginning time for measurement
                begin = time.time()
            else:
                # sleep for sometime to indicate a gap
                time.sleep(0.1)
        except BlockingIOError:
            time.sleep(0.1)

    # join all parts to make final string
    return b"".join(total_data)


# Example usage
if __name__ == "__main__":
    get_info("../info_socket")
