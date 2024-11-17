from flask import Flask, render_template, request, jsonify
from google.protobuf.descriptor import FieldDescriptor
import state_pb2 # Replace with your compiled protobuf files
import meta.meta_pb2 as meta_pb2

app = Flask(__name__)

# In-memory change log
change_log = {}
message = state_pb2.State()


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
    return render_message_view("TopLevel", [])

@app.route("/nested/<path:field_path>")
def nested_view(field_path):
    path_parts = field_path.split("/")
    return render_message_view("TopLevel", path_parts)

def render_message_view(base_name, path_parts):
    # Traverse to the correct descriptor based on the path
    descriptor = state_pb2.State.DESCRIPTOR
    for part in path_parts:
        descriptor = descriptor.fields_by_name[part].message_type
    
    metadata = get_message_metadata(descriptor)

    # Generate breadcrumbs
    breadcrumbs = []
    for i in range(len(path_parts)):
        breadcrumb_path = "/nested/" + "/".join(path_parts[:i+1])
        breadcrumbs.append((path_parts[i], breadcrumb_path))
    
    return render_template(
        "message_view.html",
        message_name=" > ".join([base_name] + path_parts),
        fields=metadata,
        full_path="/" + "/".join(path_parts),
        breadcrumbs=breadcrumbs,
        changes=change_log
    )

@app.route("/update", methods=["POST"])
def update_field():
    """Handle field updates and build the protobuf message dynamically."""
    data = request.json
    field_path = data["field_name"].split("/")  # Split hierarchical path
    new_value = data["value"]
    
    # Start with the top-level message
    message = state_pb2.State()
    
    try:
        current_descriptor = state_pb2.State.DESCRIPTOR
        current_message = message
        
        # Traverse the field path
        for part in field_path[1:-1]:
            field = current_descriptor.fields_by_name[part]
            
            # Ensure the field exists
            if field.type != field.TYPE_MESSAGE:
                return jsonify({"success": False, "error": f"Invalid path: {part} is not a message"}), 400
            
            # Set the nested message if not already set
            nested_message = getattr(current_message, part)
            if nested_message is None:
                nested_message = current_message.__getattribute__(part)
            
            current_message = nested_message
            current_descriptor = field.message_type
        
        # Update the final field
        final_field_name = field_path[-1]
        final_field = current_descriptor.fields_by_name[final_field_name]
        
        # Validate the field type (only numeric for now)
        if final_field.type not in [final_field.TYPE_INT32, final_field.TYPE_INT64, final_field.TYPE_FLOAT, final_field.TYPE_DOUBLE, final_field.TYPE_UINT32, final_field.TYPE_UINT64]:
            return jsonify({"success": False, "error": f"Field {final_field_name} type not supported"}), 400
        
        # Set the new value
        setattr(current_message, final_field_name, int(new_value))  # Convert to int for numeric fields
        
        # Track the change
        track_changes(change_log, "/".join(field_path), new_value)
        
        return jsonify({"success": True, "changes": change_log})
    
    except KeyError as e:
        return jsonify({"success": False, "error": f"Invalid field: {e}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)




