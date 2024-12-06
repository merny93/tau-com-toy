import typer
from typing import Optional, List
from pathlib import Path
import importlib
from google.protobuf.descriptor import Descriptor, FieldDescriptor
from google.protobuf.message import Message
from google.protobuf.empty_pb2 import Empty
from google.protobuf import descriptor_pb2, message_factory
from protoc_gen_validate.validator import ValidationFailed, validate_all
import socket
import pickle
import os
import time

COMMAND_SOCKET_PATH = "../command_socket"
INFO_SOCKET_PATH = "../info_socket"
DELIMITER = "@"
# something is cursed about calling scripts with typer so here is the work around...
# import sys
# from pathlib import Path

# sys.path.append(str(os.path.join(Path(__file__).parent.resolve(), "pb2")))
# try:
#     import validate_pb2 as validate_pb2
# except:
#     raise ImportError("you need to compile the protos first\nprotoc --python_out=pb2 -I=../protos/include ../protos/include/meta.proto ../protos/include/validate.proto")
# sys.path.pop(0)

from .pb2 import validate_pb2 as validate_pb2
from .pb2 import meta_pb2 as meta_pb2


typemap = {
    1: "float",  # TYPE_DOUBLE
    2: "float",  # TYPE_FLOAT
    3: "int",  # TYPE_INT64
    4: "uint",  # TYPE_UINT64
    5: "int",  # TYPE_INT32
    6: "uint",  # TYPE_FIXED64
    7: "int",  # TYPE_FIXED32
    8: "bool",  # TYPE_BOOL
    9: "str",  # TYPE_STRING
    10: "group",  # TYPE_GROUP (not commonly used)
    11: "message",  # TYPE_MESSAGE
    12: "bytes",  # TYPE_BYTES
    13: "uint",  # TYPE_UINT32
    14: "enum",  # TYPE_ENUM
    15: "int",  # TYPE_SFIXED32
    16: "int",  # TYPE_SFIXED64
    17: "int",  # TYPE_SINT32
    18: "int",  # TYPE_SINT64
}


from typing import Dict, Type

app = typer.Typer(rich_markup_mode="rich")

# Global registry to store message types
message_registry = {}


def load_proto_messages():
    """Load all protobuf message types from a given module."""

    # try to load from the cache. the cache is names .message_cached.pkl
    # check if such a file
    cache_file = ".message_cached.pkl"
    cached = False
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            res = pickle.load(f)
            t = res["time"]
            if time.time() - t < 60:
                response = res["bytes"]
                cached = True
            elif time.time() > t:
                # someone changed the time on the computer
                os.remove(cache_file)

    for attempt in range(3):
        if cached == False:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(INFO_SOCKET_PATH)
                s.sendall(b"GetFileDescriptorSet\n")
                # TODO update if changed to receving length + data
                # 1M is more than enough for this demo
                response = s.recv(1000000)
                # print(f"Got FileDescriptorSet with length: {len(response)}")

        fd_set = descriptor_pb2.FileDescriptorSet()
        try:
            fd_set.ParseFromString(response)
            break
        except Exception as e:
            print(f"Failed to parse FileDescriptorSet on attempt {attempt}: {e}")
    else:
        raise ValueError("Failed to parse FileDescriptorSet")
    res = message_factory.GetMessages(fd_set.file)
    message_registry.update(res)
    if cached == False:
        with open(cache_file, "wb") as f:
            pickle.dump({"bytes": response, "time": time.time()}, f)


# Load all protobuf messages
load_proto_messages()


def complete_protobuf_full_name(incomplete_name: str):
    # parse the incplete name
    # print("incomplete string", incomplete_name)
    message_path = incomplete_name.split(DELIMITER)
    if len(message_path) == 1:
        base_name = message_path[0]
        # user has entered zero or more charachter of the base name
        for key in message_registry.keys():
            if key.startswith(base_name):
                if (
                    key.startswith("google")
                    or key.startswith("validate")
                    or key.startswith("meta")
                ):
                    continue
                yield (key, "help")
    elif len(message_path) > 1:
        # print("hello")
        # user has entered a full parent message name and has entered zero or more charachters of the child message name
        base_name = message_path[0]
        message = message_registry[base_name]()
        current_descriptor = message.DESCRIPTOR
        current_message = message
        # travers the path up to the possibly incomlete last part
        for part in message_path[1:-1]:
            field = current_descriptor.fields_by_name.get(part)
            if field is None or field.type != FieldDescriptor.TYPE_MESSAGE:
                yield from []
            current_message = getattr(current_message, part)
            current_descriptor = field.message_type
        # work on the last part
        final_part = message_path[-1]
        for key in current_descriptor.fields_by_name.keys():
            if key.startswith(final_part):
                field = current_descriptor.fields_by_name.get(key)
                # only complete things that are messages
                if field.type != FieldDescriptor.TYPE_MESSAGE:
                    continue
                # special case for empty
                if field.message_type.full_name == Empty.DESCRIPTOR.full_name:
                    continue
                # assemble the full name to complete
                yield (DELIMITER.join(message_path[:-1] + [key]), "help")


def complete_protobuf_field(ctx: typer.Context, incomplete_fields: str):
    # print ("incomplete", incomplete_fields)
    message_path = ctx.params["protobuf_full_name"].split(DELIMITER)
    message = message_registry[message_path[0]]()

    current_descriptor = message.DESCRIPTOR
    current_message = message

    # Traverse the field path
    for part in message_path[1:]:
        field = current_descriptor.fields_by_name.get(part)

        # Ensure the field exists and is a message
        if field is None or field.type != FieldDescriptor.TYPE_MESSAGE:
            raise ValueError(f"Invalid path: {part} is not a valid message field")

        # Set the nested message if not already initialized
        if not current_message.HasField(part):
            getattr(current_message, part).SetInParent()

        current_message = getattr(current_message, part)
        current_descriptor = field.message_type

    field_parts = incomplete_fields.split(DELIMITER)
    if len(field_parts) == 1:
        partial_name = field_parts[0]
        # still working on the field
        for field_name in current_descriptor.fields_by_name.keys():
            # do not autocomplete already set fields!
            if field_name in map(
                lambda x: x.split(DELIMITER)[0], ctx.params.get("message_data")
            ):
                continue
            # only autocomplete fields that match the start
            if field_name.startswith(partial_name):
                # do not autocomplete fields that are messages as there is no way to set them
                # with an exception for Empty types
                field = current_descriptor.fields_by_name.get(field_name)
                if (
                    field.type == FieldDescriptor.TYPE_MESSAGE
                    and field.message_type.full_name != Empty.DESCRIPTOR.full_name
                ):
                    continue
                # append the possibly useful type?
                # help doesnt work in bash...
                yield (f"{field_name}{DELIMITER}{typemap[field.type]}", "test help")
    elif len(field_parts) == 2:

        field = current_descriptor.fields_by_name.get(field_parts[0])
        if field.type == FieldDescriptor.TYPE_ENUM:
            # we can help with enums!
            for enum_name in getattr(field, "enum_type").values_by_name.keys():
                if enum_name.startswith(field_parts[1]):
                    yield (f"{field_parts[0]}{DELIMITER}{enum_name}", "enum help")
        else:
            # field has been entered, now its = "". no autocomplete just help
            # but help does not work in bash
            yield from [
                (incomplete_fields, "help here"),
            ]


# if this is the only command then it ends up default `typer cli.py run NAME field=value`
# if I add more commands then it will be `typer cli.py run **send** NAME field=value`
@app.command()
def send(
    protobuf_full_name: str = typer.Argument(
        ...,
        help=f"Full name of the protobuf message type (e.g., package.MessageType{DELIMITER}submessage{DELIMITER}subsubmessage)",
        autocompletion=complete_protobuf_full_name,
    ),
    message_data: List[str] = typer.Argument(
        None,
        help=f"Data for the message in field1{DELIMITER}Value1 field2{DELIMITER}Value2 ... format",
        autocompletion=complete_protobuf_field,
    ),
):
    """
    CLI used for building protobuf messages and sending them to payloads.
    
    Try using <tab> for autocompletion and use @ for delimiting strings
    """
    message_path = protobuf_full_name.split(DELIMITER)
    message = message_registry[message_path[0]]()

    current_descriptor = message.DESCRIPTOR
    current_message = message

    # Traverse the field path
    for part in message_path[1:]:
        field = current_descriptor.fields_by_name.get(part)

        # Ensure the field exists and is a message
        if field is None or field.type != field.TYPE_MESSAGE:
            raise ValueError(f"Invalid path: {part} is not a valid message field")

        # Set the nested message if not already initialized
        if not current_message.HasField(part):
            getattr(current_message, part).SetInParent()

        current_message = getattr(current_message, part)
        current_descriptor = field.message_type

    # Update the final field
    for raw_str in message_data:
        key, value = raw_str.split(DELIMITER)
        final_field = current_descriptor.fields_by_name.get(key)

        # Ensure the final field exists
        if final_field is None:
            raise ValueError(f"Field {key} not found")

            # Handle different field types
        if final_field.type in [
            FieldDescriptor.TYPE_INT32,
            FieldDescriptor.TYPE_INT64,
            FieldDescriptor.TYPE_UINT32,
            final_field.TYPE_UINT64,
        ]:
            setattr(current_message, key, int(value))
        elif final_field.type in [
            FieldDescriptor.TYPE_FLOAT,
            FieldDescriptor.TYPE_DOUBLE,
        ]:
            setattr(current_message, key, float(value))
        elif final_field.type == FieldDescriptor.TYPE_BOOL:
            setattr(current_message, key, bool(value))
        elif (
            final_field.message_type
            and final_field.message_type.full_name == Empty.DESCRIPTOR.full_name
        ):
            # Handle `google.protobuf.Empty`
            getattr(current_message, key).SetInParent()
        # from https://stackoverflow.com/a/40345768
        elif final_field.type == FieldDescriptor.TYPE_ENUM:
            enum_number = getattr(final_field, "enum_type").values_by_name[value].number
            setattr(current_message, key, enum_number)
        else:
            raise ValueError(f"Unsupported field type for {key}")

    # Validate the updated message
    try:
        validate_all(message)
    except ValidationFailed as err:
        raise ValueError(str(err))

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        try:
            s.connect(COMMAND_SOCKET_PATH)
        except Exception as e:
            raise ValueError(str(e))
        try:
            validate_all(message)
        except ValidationFailed as err:
            raise ValueError(str(err))
        serialized_message = message.SerializeToString()
        s.sendall(serialized_message)
        typer.echo(f"Sent message: {message}")
        # Clear the message after sending
        message.Clear()


if __name__ == "__main__":
    app()