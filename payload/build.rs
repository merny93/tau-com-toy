extern crate prost_build;
extern crate prost_validate_build;
use std::env;
use std::path::Path;

fn main() {
    let proto_file = "../state.proto";
    let includes = vec!["../", "../validate"];
    println!("cargo:rerun-if-changed={}", proto_file);

    let mut config = prost_build::Config::new();

    config.message_attribute(".", "#[derive(::dif_print::PrettyPrint)]");
    // config.compile_protos(&[proto_file], &["../"]).unwrap();
    prost_validate_build::Builder::new().compile_protos_with_config(config, &vec![proto_file], &includes).unwrap();
}
