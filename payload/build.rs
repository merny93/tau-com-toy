extern crate prost_build;
extern crate prost_reflect_build;
extern crate prost_validate_build;

fn main() {
    let proto_files = vec!["../protos/state.proto"];
    let includes = vec!["../protos", "../protos/include"];
    println!("cargo:rerun-if-changed=../protos");

    let mut config = prost_build::Config::new();

    config.message_attribute(".", "#[derive(::dif_print::PrettyPrint)]");
    prost_validate_build::Builder::new()
        .compile_protos_with_config(config, &proto_files, &includes)
        .unwrap();
}
