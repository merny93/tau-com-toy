use prost::{self, Message};
use prost_validate::{self, Validator};
use std::fs;
use std::io::{Read, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::sync::{Arc, Barrier};
use std::thread;

// use dif_print::PrettyPrint;
mod state {
    include!(concat!(env!("OUT_DIR"), "/state.rs"));
}
mod substate {
    include!(concat!(env!("OUT_DIR"), "/substate.rs"));
}

mod rich_defaults;
use rich_defaults::DefaultRich;

mod fridge;

fn main() {
    //initalize to rich defaults - either monolithic or distributed
    let mut actual = state::State::default_rich();

    //spawn the fridge task - this is a distributed task
    let (send_tx, send_rx) = std::sync::mpsc::channel();
    let (recv_tx, recv_rx) = std::sync::mpsc::channel();
    let (req_tx, req_rx) = std::sync::mpsc::channel();
    let _fridge_thread = thread::spawn(move || {
        fridge::run(recv_rx, req_rx, send_tx);
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
        state.param1
    );

    state::StateInternal { ..state }
}
