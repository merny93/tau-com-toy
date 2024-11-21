use core::str;
use once_cell::sync::Lazy;
use prost::{self, Message};
use prost_reflect::{DescriptorPool, ReflectMessage};
use prost_validate::{self, Validator};
use std::fs;
use std::io::prelude::*;
use std::io::{Read, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::process::exit;
use std::thread;


// use dif_print::PrettyPrint;
mod state {
    include!(concat!(env!("OUT_DIR"), "/state.rs"));
}
mod substate {
    include!(concat!(env!("OUT_DIR"), "/substate.rs"));
}

mod dynamic {
    include!(concat!(env!("OUT_DIR"), "/dynamic.rs"));
}

mod fmt;
pub use fmt::PrettyPrint;

const FILE_DESCRIPTOR_SET_BYTES: &[u8] =
    include_bytes!(concat!(env!("OUT_DIR"), "/file_descriptor_set.bin"));

static DESCRIPTOR_POOL: Lazy<DescriptorPool> = Lazy::new(|| {
    DescriptorPool::decode(
        include_bytes!(concat!(env!("OUT_DIR"), "/file_descriptor_set.bin")).as_ref(),
    )
    .unwrap()
});

#[derive(Message, ReflectMessage)]
#[prost_reflect(descriptor_pool = "DESCRIPTOR_POOL", message_name = "dynamic.HKsystem")]
pub struct HkSystem {}

mod rich_defaults;
use rich_defaults::DefaultRich;

mod fridge;

fn main() {
    // println!("derived_message {:?}", HkSystem{}.descriptor());
    let message = DESCRIPTOR_POOL
        .get_message_by_name("dynamic.HKsystem")
        .unwrap();

    // let hk_descriptor = DESCRIPTOR_POOL.get_message_by_name("meta.Meta").unwrap();
    let hk_extension = DESCRIPTOR_POOL.get_extension_by_name("hk.channel_options").unwrap();
    for fields in message.fields() {
        
        let options = fields.options();
        let meta_extension = options.get_extension(&hk_extension);
        let meta_extension = meta_extension.as_message().unwrap();
        println!("{}", meta_extension.get_field_by_name("channel_number").unwrap());
        // panic!("stop");
        
    }
    // println!("message {:?}", message.extensions());
    
    //initalize to rich defaults - either monolithic or distributed
    let mut actual = state::State::default_rich();

    //spawn the fridge task - this is a distributed task
    let (send_tx, send_rx) = std::sync::mpsc::channel();
    let (recv_tx, recv_rx) = std::sync::mpsc::channel();
    let (req_tx, req_rx) = std::sync::mpsc::channel();
    let _fridge_thread = thread::spawn(move || {
        fridge::run(recv_rx, req_rx, send_tx);
    });

    let _info_thread = thread::spawn(move || {
        run_info_interface();
    });

    //we can grab the state from the fridge - doing it with channels is silly
    // in reality we will want interprocess communication as if its the same program it might as well be monolithic
    req_tx.send(()).unwrap();
    let fridge_state = send_rx.recv().unwrap();
    actual.fridge = Some(substate::Fridge::decode(&fridge_state[..]).unwrap());

    //this can be serialized efficiently and be sent down so that the ground knows the exact state of the payload
    //state sharing is a huge benefit of this pattern
    let mut buf = Vec::new();
    actual.encode(&mut buf).unwrap();
    println!(
        "State can be shared from payload to ground seemlesly. Here it is encoded {:?}",
        buf
    );

    // open a socket to emulate the wire from the ground
    let socket_path: &str = "../command_socket";
    if fs::metadata(socket_path).is_ok() {
        fs::remove_file(socket_path).unwrap();
    }
    let listener = UnixListener::bind(socket_path).unwrap();
    for stream in listener.incoming() {
        match stream {
            Ok(mut stream) => {
                let mut buf = Vec::new();
                stream.read_to_end(&mut buf).unwrap();

                println!("recieved command sent up the link {:?}", buf);
                //which can be inspected on the payload
                let recieved = state::State::decode(&buf[..]).unwrap();
                // assert!(recieved.validate().is_ok());
                match recieved.validate() {
                    Ok(_) => {}
                    Err(err) => {
                        eprintln!("Validation failed, ignoring: {}", err);
                        continue;
                    }
                }
                // this can be logged ofc using the custom macro called diff-print
                println!(
                    "Global diffs using proc macro seen here: {}",
                    recieved.pretty_print()
                );
                //and it can be applied to the state either in a monolithic way
                actual.merge(&buf[..]).unwrap();

                //or in a distributed way
                if let Some(fridge_command) = recieved.fridge {
                    let mut buf = Vec::new();
                    fridge_command.encode(&mut buf).unwrap();
                    recv_tx.send(buf).unwrap();
                }
                // this redistribution can be proc_macro generated if we want.
                //but we might want fine grained control

                //dunno the logic of the payload - we probably dont want the callback to be doing work but who knows
                actual.internal = Some(internal_task(actual.internal.unwrap()));
            }
            Err(err) => {
                eprintln!("Error accepting connection: {}", err);
            }
        }
    }
}

fn internal_task(state: state::StateInternal) -> state::StateInternal {
    println!(
        "I am the internal task, and this is the param {}",
        state.param1.unwrap()
    );

    state::StateInternal { ..state }
}

// this could be implemented better, just a quick and dirty demo
// TODO Probably what we want is an inteface the sends protobufs
// with lengths sent first so the readers now how far to read
fn run_info_interface() {
    let info_socket_path: &str = "../info_socket";
    if fs::metadata(info_socket_path).is_ok() {
        fs::remove_file(info_socket_path).unwrap();
    }
    let listener = UnixListener::bind(info_socket_path).unwrap();
    for stream in listener.incoming() {
        match stream {
            Ok(mut stream) => {
                let mut buf = Vec::new();
                // change to a BufReader to get access to read_until
                // this is all a hack
                let mut buf_stream = std::io::BufReader::new(stream.try_clone().unwrap());
                let newline = 10;
                buf_stream.read_until(newline, &mut buf).unwrap();

                // use strings for now as the request language
                let buf_str = str::from_utf8(&buf).unwrap();

                println!("recieved info request: {:?}", buf_str);

                if buf_str == "GetFileDescriptorSet\n" {
                    // TODO probably want to sent length first, to know when done receiving
                    stream.write_all(FILE_DESCRIPTOR_SET_BYTES).unwrap();
                }
            }
            Err(err) => {
                eprintln!("Error accepting connection: {}", err);
            }
        }
    }
}
