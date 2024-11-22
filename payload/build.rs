extern crate prost_build;
extern crate prost_reflect_build;
extern crate prost_validate_build;

fn main() {
    let proto_files = vec!["../protos/state.proto"];
    let includes = vec!["../protos", "../protos/include"];
    println!("cargo:rerun-if-changed=../protos");

    let mut config = prost_build::Config::new();

    config.message_attribute(".", "#[derive(::dif_print::PrettyPrint)]");
    config.message_attribute("HKsystem", "#[derive(::prost_reflect::ReflectMessage)]");
    config.message_attribute("HKsystem", "#[prost_reflect(descriptor_pool = \"DESCRIPTOR_POOL\", message_name = \"dynamic.HKsystem\")]");
    // config.protoc_arg("--include_imports"); //this appear to already have been called as it gives an error "include_imports may only be passed once"
    // config.protoc_arg("--include_source_info"); //this appear to already have been called as it gives an error "include_source_info may only be passed once"
    prost_validate_build::Builder::new()
        .compile_protos_with_config(config, &proto_files, &includes)
        .unwrap();
}
