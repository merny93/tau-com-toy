"""
compile into descriptors.pb
protoc --descriptor_set_out=descriptors.pb -I=../ -I=../validate -I=../meta --include_imports --include_source_info ../state.proto

we still need the meta so that needs to be compiled into meta_pb2.py
protoc --python_out=. -I=../meta meta.proto
"""

from flask import Flask, render_template, request, jsonify
from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.empty_pb2 import Empty
from google.protobuf.json_format import MessageToDict

from get_file_descriptor_set import get_file_descriptor_set

# import the custom generated files
try:
    import pb2.meta_pb2 as meta_pb2  # custom generated - needs to be included with install (oh well)
except ModuleNotFoundError:
    print(
        "Meta needs to be compiled using\nprotoc --python_out=pb2 -I=../protos/include ../protos/include/meta.proto ../protos/include/validate.proto "
    )
    raise ModuleNotFoundError
try:
    import pb2.validate_pb2 as validate_pb2  # custom generated - needs to be included with install (oh well)
    #your linter may think this import is not needed but it does things to the globals without which things wont validate
except ModuleNotFoundError:
    print(
        "Validate needs to be compiled using\nprotoc --python_out=pb2 -I=../protos/include ../protos/include/meta.proto ../protos/include/validate.proto"
    )
    raise ModuleNotFoundError
from protoc_gen_validate.validator import ValidationFailed, validate_all
import socket

app = Flask(__name__)

# New globals for dynamic protocol buffers
message = None  # Will be initialized after loading descriptors
command_socket_path = None


def initialize_protocol_buffers(descriptor_socket, root_message_name, socket_path):
    """Initialize protocol buffers from a descriptor file."""
    global message, command_socket_path

    try:

        # Request the descriptor set from the payload binary (server)
        messages = get_file_descriptor_set(descriptor_socket, messages=True)

        message = messages[root_message_name]()
        command_socket_path = socket_path

    except Exception as e:
        print(f"Error initializing protocol buffers: {str(e)}")
        print(
            """You need to compile to descriptors.pb first
            protoc --descriptor_set_out=pb2/descriptors.pb -I=../protos -I=../protos/include --include_imports --include_source_info ../protos/state.proto"""
        )
        raise


def get_message_metadata(descriptor):
    """Extract field-level and message-level metadata."""
    metadata = []
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

    for field in descriptor.fields:
        # Check if the field is a message and specifically an Empty message
        is_message = field.type == FieldDescriptor.TYPE_MESSAGE
        is_empty = (
            is_message and field.message_type.full_name == Empty.DESCRIPTOR.full_name
        )

        meta = {
            "name": field.name,
            "type": "empty" if is_empty else typemap[field.type],
            "is_message": False if is_empty else is_message,
            "is_empty": is_empty,  # Add a flag to indicate Empty type
            "meta_name": field.GetOptions().Extensions[meta_pb2.field_data].name,
            "meta_description": field.GetOptions()
            .Extensions[meta_pb2.field_data]
            .description,
        }
        metadata.append(meta)

    print(f"metadata {metadata}")
    return metadata


def track_changes(change_log, field_name, new_value):
    """Track changed fields."""
    change_log[field_name] = new_value


@app.route("/")
def homepage():
    return render_message_view("State", [])


@app.route("/nested/<path:field_path>")
def nested_view(field_path):
    path_parts = field_path.split("/")
    return render_message_view("State", path_parts)


def render_message_view(base_name, path_parts):
    # Traverse to the correct descriptor based on the path
    descriptor = message.DESCRIPTOR
    for part in path_parts:
        descriptor = descriptor.fields_by_name[part].message_type

    metadata = get_message_metadata(descriptor)

    # Generate breadcrumbs
    breadcrumbs = []
    for i in range(len(path_parts)):
        breadcrumb_path = "/nested/" + "/".join(path_parts[: i + 1])
        breadcrumbs.append((path_parts[i], breadcrumb_path))
    full_path = "/".join(path_parts)
    if full_path:
        full_path = f"{full_path}/"
    print(f"full_path {full_path}")
    return render_template(
        "message_view.html",
        message_name=" > ".join([base_name] + path_parts),
        fields=metadata,
        full_path=full_path,
        breadcrumbs=breadcrumbs,
        changes=MessageToDict(
            message,
            preserving_proto_field_name=True,
        ),
    )


@app.route("/update", methods=["POST"])
def update_field():
    """Handle field updates and build the protobuf message dynamically."""
    data = request.json
    field_path = data["field_name"].split("/")  # Split hierarchical path
    new_value = data["value"]

    try:
        current_descriptor = message.DESCRIPTOR
        current_message = message

        # Traverse the field path
        for part in field_path[:-1]:
            field = current_descriptor.fields_by_name.get(part)

            # Ensure the field exists and is a message
            if field is None or field.type != field.TYPE_MESSAGE:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"Invalid path: {part} is not a valid message field",
                        }
                    ),
                    400,
                )

            # Set the nested message if not already initialized
            if not current_message.HasField(part):
                getattr(current_message, part).SetInParent()

            current_message = getattr(current_message, part)
            current_descriptor = field.message_type

        # Update the final field
        final_field_name = field_path[-1]
        final_field = current_descriptor.fields_by_name.get(final_field_name)

        # Ensure the final field exists
        if final_field is None:
            return (
                jsonify(
                    {"success": False, "error": f"Field {final_field_name} not found"}
                ),
                400,
            )

        # Handle different field types
        if final_field.type in [
            final_field.TYPE_INT32,
            final_field.TYPE_INT64,
            final_field.TYPE_UINT32,
            final_field.TYPE_UINT64,
        ]:
            setattr(current_message, final_field_name, int(new_value))
        elif final_field.type in [final_field.TYPE_FLOAT, final_field.TYPE_DOUBLE]:
            setattr(current_message, final_field_name, float(new_value))
        elif final_field.type == final_field.TYPE_BOOL:
            setattr(current_message, final_field_name, bool(new_value))
        elif (
            final_field.message_type
            and final_field.message_type.full_name == Empty.DESCRIPTOR.full_name
        ):
            # Handle `google.protobuf.Empty`
            getattr(current_message, final_field_name).SetInParent()
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Unsupported field type for {final_field_name}",
                    }
                ),
                400,
            )

        # Validate the updated message
        try:
            validate_all(message)
        except ValidationFailed as err:
            return jsonify({"success": False, "error": str(err)}), 400

        # Return the updated changes
        return jsonify(
            {
                "success": True,
                "changes": MessageToDict(
                    message,
                    preserving_proto_field_name=True,
                ),
            }
        )

    except KeyError as e:
        return jsonify({"success": False, "error": f"Invalid field: {e}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/submit", methods=["POST"])
def submit_message():
    """Submit the message we have been building"""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        try:
            s.connect(command_socket_path)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
        try:
            validate_all(message)
        except ValidationFailed as err:
            return jsonify({"success": False, "error": str(err)}), 400
        serialized_message = message.SerializeToString()
        s.sendall(serialized_message)
        print(f"Sent message: {message}")
        # Clear the message after sending
        message.Clear()
        return jsonify({"success": True})


@app.route("/remove", methods=["POST"])
def remove_field():
    """Handle field removal from the protobuf message."""
    data = request.json
    field_path = data["field_name"].split("/")  # Split hierarchical path
    try:
        current_message = message
        message_stack = [(message, None, None)]  # [(message, parent, field_name)]

        # Traverse to the target field, keeping track of the path
        for part in field_path[:-1]:
            if not current_message.HasField(part):
                return jsonify({"success": True})  # Field already doesn't exist
            current_message = getattr(current_message, part)
            message_stack.append((current_message, message_stack[-1][0], part))

        # Clear the final field
        final_field = field_path[-1]
        current_message.ClearField(final_field)

        # Work backwards through the stack, clearing empty parent messages
        for msg, parent, field_name in reversed(
            message_stack[1:]
        ):  # Skip the root message
            if not any(msg.HasField(field) for field in msg.DESCRIPTOR.fields_by_name):
                # Message is empty, clear it from its parent
                parent.ClearField(field_name)

        # Return the updated changes
        return jsonify(
            {
                "success": True,
                "changes": MessageToDict(
                    message,
                    preserving_proto_field_name=True,
                ),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Hard-coded configuration
    descriptor_socket = "../info_socket"
    root_message = "state.State"
    socket_path = "../command_socket"

    initialize_protocol_buffers(descriptor_socket, root_message, socket_path)
    app.run(debug=True)
