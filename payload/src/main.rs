use prost::{self, Message};
use prost_validate::{self, Validator};
use std::fs;
use std::io::{Read, Write};
use std::os::unix::net::{UnixListener, UnixStream};
use std::thread;

use dif_print::PrettyPrint;
mod state {
    include!(concat!(env!("OUT_DIR"), "/state.rs"));
}
mod substate {
    include!(concat!(env!("OUT_DIR"), "/substate.rs"));
}
mod combined {
    include!(concat!(env!("OUT_DIR"), "/combined.rs"));
}
mod action {
    include!(concat!(env!("OUT_DIR"), "/action.rs"));
}

trait DefaultRich {
    fn default_rich() -> Self;
}

/// Each subsystem can define it's defualts
impl DefaultRich for substate::State {
    fn default_rich() -> Self {
        substate::State {
            param1: Some(42),
            print_param1: Some(false),
        }
    }
}

/// propagate it up!
impl DefaultRich for state::State {
    fn default_rich() -> Self {
        state::State {
            global_param: Some(33),
            internal: Some(state::StateInternal { param1: 11 }),
            inherited: Some(substate::State::default_rich()), // we can make a nicer way to traverse this tree....
        }
    }
}

fn main() {
    //initalize to rich defaults
    let mut actual = state::State::default_rich();
    println!("Inital state {:?}", actual);

    //this can be serialized efficiently and be sent down so that the ground knows the exact state of the payload
    let mut buf = Vec::new();
    actual.encode(&mut buf).unwrap();
    println!(
        "State can be shared from payload to ground seemlesly. Here it is encoded {:?}",
        buf
    );

    let socket_path: &str = "../command_socket";
    // let socket_path = "/tmp/command_socket";
    // Remove the socket file if it already exists
    if fs::metadata(socket_path).is_ok() {
        fs::remove_file(socket_path).unwrap();
    }

    let listener = UnixListener::bind(socket_path).unwrap();
    println!("Listening on {}\n", socket_path);

    for stream in listener.incoming() {
        match stream {
            Ok(mut stream) => {
                let mut buf = Vec::new();
                stream.read_to_end(&mut buf).unwrap();

                println!("recieved command sent up the link {:?}", buf);

                //which can be inspected on the payload
                let recieved = combined::CombinedMessage::decode(&buf[..]).unwrap();
                // this can be logged ofc, and validated (see prost_validate)
                println!("... decoded: {:?}", recieved);
                match recieved.combined {
                    Some(combined::combined_message::Combined::Action(act)) => {
                        println!("... Received action message: {:?}", act);
                        // logic for this action would go here
                        // either directly, or queueing an async thing
                    }
                    Some(combined::combined_message::Combined::State(state)) => {
                        println!("... Received state message: {:?}", state);

                        println!(
                            "... Diffs using proc macro seen here: {}",
                            recieved.pretty_print()
                        );
                        //and it can be applied
                        // re-encoding here is maybe dumb, and if we want to go this route
                        // we can find/make a less dumb way
                        // but I guess if we were fine with decoding twice, and an extra encode is also fine
                        actual.merge(&state.encode_to_vec()[..]).unwrap();
                        // yes i know this is silly as it is deserialized twice. but memory is cheap and so are cpu cycles
                        // this can be fixed with the merge crate!

                        //finally the payload can act upon it. Either by passing it to the subsystems or by acting on it directly
                        actual.inherited = Some(inherited_task(actual.inherited.unwrap()));
                    }
                    None => println!("Received no message"),
                }
            }
            Err(err) => {
                eprintln!("Error accepting connection: {}", err);
            }
        }
        println!("State after command: {:?}\n", actual);
    }
}

fn inherited_task(state: substate::State) -> substate::State {
    if state.print_param1() {
        println!(
            "I am the inherited task, and this is the param {}",
            state.param1()
        );
    }
    substate::State {
        print_param1: Some(false),
        ..state
    }
}
