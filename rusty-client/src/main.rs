use protobuf::{self, descriptor::FileDescriptorProto};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut protofile = FileDescriptorProto::new();
    protofile.set_name("validate.proto".to_string());

    let protos = protobuf::reflect::FileDescriptor::new_dynamic(protofile, dependencies)
    )?;
    Ok(())
}
