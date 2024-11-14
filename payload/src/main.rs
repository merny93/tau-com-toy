use capnp;
use prost;
use prost_validate::{self, Validator};
mod commands_capnp {
    include!(concat!(env!("OUT_DIR"), "/commands_capnp.rs"));
}

mod commands_proto {
    include!(concat!(env!("OUT_DIR"), "/commands.rs"));
}

mod validate_proto {
    include!(concat!(env!("OUT_DIR"), "/validate.example.rs"));
}
fn main() {
    {
        let mut message = capnp::message::Builder::new_default();
        let mut command = message.init_root::<commands_capnp::command::Builder>();
        command.init_command1();
        //serialzie the message to a buffer
        let mut serialized = Vec::new();
        capnp::serialize_packed::write_message(&mut serialized, &message).unwrap();
        println!(
            "Serialized message length {:?}: {:?}",
            serialized.len(),
            serialized
        );
    }

    //same but for protobuf
    {
        let mut command = commands_proto::Command::default();
        command.command = Some(commands_proto::command::Command::Command1(
            commands_proto::Command1 {},
        ));
        let mut serialized = Vec::new();
        prost::Message::encode(&command, &mut serialized).unwrap();
        println!(
            "Serialized message length {:?}: {:?}",
            serialized.len(),
            serialized
        );
    }

    //try the validation stuff
    {
        match validate_proto::ExampleMessage::default().validate() {
            Ok(_) => println!("Validation passed"),
            Err(e) => eprintln!("Validation failed: {}", e),
        }
        let msg = validate_proto::ExampleMessage {
            content: "Hello, world!".to_string(),
        };
        match msg.validate() {
            Ok(_) => println!("Validation passed"),
            Err(e) => eprintln!("Validation failed: {}", e),
        }
    }
}
