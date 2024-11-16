import socket
import state_pb2 
import substate_pb2
from protoc_gen_validate.validator import ValidationFailed, validate_all

def send_message(socket_path):
    # Create a Unix socket object
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        # Connect to the Unix socket
        s.connect(socket_path)
        
        command = state_pb2.State()
        substate = substate_pb2.State()
        substate.param1 = 37
        substate.print_param1= True
        internal = state_pb2.StateInternal()
        internal.param1 = 40
        command.internal.CopyFrom(internal)
        # command.inherited.CopyFrom(substate)
        command.global_param = 3
        try:
            validate_all(command)
        except ValidationFailed as err:
            print(f"Failed validation with the following error, not sending sorry \n {err}")
            exit()
        # # Serialize the message to a binary format
        serialized_message = command.SerializeToString()
        
        # Send the serialized message
        s.sendall(serialized_message)
        print("Message sent")

# Example usage
if __name__ == "__main__":
    
    # print(command)
    send_message('../command_socket')