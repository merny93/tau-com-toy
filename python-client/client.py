'''
Compile protos as
protoc --python_out=. -I=../ -I=../validate -I=../meta ../state.proto ../substate.proto ../validate/validate.proto ../meta/meta.proto 

'''

import socket
import state_pb2 
import substate_pb2
import meta.meta_pb2 as meta_pb2
from protoc_gen_validate.validator import ValidationFailed, validate_all

def send_message(socket_path):
    # Create a Unix socket object
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        # Connect to the Unix socket
        s.connect(socket_path)
        
        command = state_pb2.State()
        fridge_state = substate_pb2.Fridge()
        fridge_params = substate_pb2.FridgeParams()
        fridge_params.delay1 = 10
        fridge_params.delay2 = 1
        fridge_params.delay3 = 1
        fridge_state.params.CopyFrom(fridge_params)
        fridge_state.cycle.SetInParent()
        # internal = state_pb2.StateInternal()
        # internal.param1 = 40
        # command.internal.CopyFrom(internal)
        # command.inherited.CopyFrom(substate)
        # command.global_param = 3
        command.fridge.CopyFrom(fridge_state)
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
    #meta data can be obtained as

    for i in state_pb2.StateInternal.DESCRIPTOR.fields:
        print(f"field {i.full_name} has meta {i.GetOptions().Extensions[meta_pb2.field_data]}".strip())
    print(f"message meta {state_pb2.StateInternal.DESCRIPTOR.GetOptions().Extensions[meta_pb2.message_data]}".strip())
    # print(command)
    send_message('../command_socket')