from flask import Flask, render_template, request, jsonify
from google.protobuf.descriptor import FieldDescriptor
import state_pb2 # Replace with your compiled protobuf files
import meta.meta_pb2 as meta_pb2

app = Flask(__name__)

# In-memory change log
change_log = {}


def get_message_metadata(descriptor):
    """Extract field-level and message-level metadata."""
    metadata = []
    for field in descriptor.fields:
        meta = {
            "name": field.name,
            "type": field.type,
            "is_message": field.type == FieldDescriptor.TYPE_MESSAGE,
            "meta_name": field.GetOptions().Extensions[meta_pb2.field_data].name,
            "meta_description": field.GetOptions().Extensions[meta_pb2.field_data].description,
        }
        metadata.append(meta)
    return metadata

def track_changes(change_log, field_name, new_value):
    """Track changed fields."""
    change_log[field_name] = new_value


@app.route("/")
def homepage():
    # Parse top-level message and its metadata
    message_descriptor = state_pb2.State.DESCRIPTOR
    metadata = get_message_metadata(message_descriptor)
    return render_template("homepage.html", fields=metadata, changes=change_log)

@app.route("/nested/<field_name>")
def nested_page(field_name):
    # Access nested message
    message_descriptor = state_pb2.State.DESCRIPTOR.fields_by_name[field_name].message_type
    metadata = get_message_metadata(message_descriptor)
    return render_template("nested.html", fields=metadata, changes=change_log, field_name=field_name)

@app.route("/update", methods=["POST"])
def update_field():
    # Handle field updates and track changes
    data = request.json
    field_name = data["field_name"]
    new_value = data["value"]
    
    # Validation placeholder
    is_valid = True  # Replace with actual validation logic
    
    if is_valid:
        track_changes(change_log, field_name, new_value)
        return jsonify({"success": True, "changes": change_log})
    else:
        return jsonify({"success": False, "error": "Invalid value"}), 400

if __name__ == "__main__":
    app.run(debug=True)




