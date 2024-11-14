extern crate capnpc;
extern crate prost_build;
extern crate prost_validate_build;
extern crate prost_metadata;
fn main() {
    capnpc::CompilerCommand::new()
        .src_prefix("../")
        .file("../commands.capnp")
        .run()
        .expect("schema compiler command");
    prost_build::compile_protos(&["../commands.proto"], &["../"]).unwrap();
    prost_metadata::Builder::new()
        .compile_protos(&["../validate.proto"], &["../", "../validate"])
        .unwrap();
}
