import socket
import time
import action_pb2
import combined_pb2
import state_pb2
import substate_pb2

def get_state_message():
    command = state_pb2.State()
    substate = substate_pb2.State()
    substate.param1 = 390
    substate.print_param1 = True
    command.inherited.CopyFrom(substate)
    command.global_param = 150

    # put command into the top-level combined message
    combined = combined_pb2.CombinedMessage()
    combined.state.CopyFrom(command)
    return combined

def get_action_message():
    combined = combined_pb2.CombinedMessage()
    action = action_pb2.ExampleAction()
    combined.action.CopyFrom(action)
    return combined

def send_message(socket_path, message):
    # Create a Unix socket object
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        # Connect to the Unix socket
        s.connect(socket_path)

        # # Serialize the message to a binary format
        serialized_message = message.SerializeToString()
        # Send the serialized message
        s.sendall(serialized_message)
        print("Message sent")


# Example usage
if __name__ == "__main__":
    state_message = get_state_message()
    print(f"State message: {state_message}")
    send_message('../command_socket', state_message)

    time.sleep(1)

    action_message = get_action_message()
    print(f"Action message: {action_message}")
    send_message('../command_socket', action_message)
