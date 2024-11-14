use prost_build::Config;
use prost_validate_build::Builder as ProstBuilder;
use std::fs::File;
use std::io::{self, Read};
use std::path::Path;

pub struct Builder {
    inner: ProstBuilder,
    file_descriptor_set_path: PathBuf,
}

impl Builder {
    pub fn new() -> Self {
        Builder {
            inner: ProstBuilder::new(),
        }
    }

    // Method to extract metadata
    fn extract_metadata(&self, proto_file: &Path) -> io::Result<String> {
        let mut file = File::open(proto_file)?;
        let mut contents = String::new();
        file.read_to_string(&mut contents)?;

        // Extract metadata (this is a placeholder, adjust as needed)
        let metadata = contents
            .lines()
            .filter(|line| line.starts_with("//"))
            .collect::<Vec<&str>>()
            .join("\n");

        Ok(metadata)
    }

    // Method to compile protos and handle metadata
    pub fn compile_protos(&mut self, proto_files: &[&str], includes: &[&str]) -> io::Result<()> {
        let mut config = Config::new();

        config
            .file_descriptor_set_path(&self.inner.file_descriptor_set_path)
            .compile_protos(protos, includes)?;

        // Customize the config as needed
        config.out_dir("src/prost");


        // Extract and store metadata
        for proto in proto_files {
            let path = Path::new(proto);
            let metadata = self.extract_metadata(path)?;
            println!("Metadata for {}: {}", proto, metadata);

            // Store metadata (this is a placeholder, adjust as needed)
            // For example, you could write it to a file or store it in a data structure
        }

        // Compile the .proto files using the inner Builder
        self.inner.compile_protos(proto_files, includes)?;

        Ok(())
    }
}
