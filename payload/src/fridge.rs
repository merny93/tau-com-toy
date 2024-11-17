use std::sync::mpsc;

use prost::Message;
use prost_validate::Validator;

use crate::rich_defaults::DefaultRich;

pub fn run(
    pipe_recieve: mpsc::Receiver<Vec<u8>>,
    pipe_request: mpsc::Receiver<()>,
    pipe_response: mpsc::Sender<Vec<u8>>,
) {
    let mut state = crate::substate::Fridge::default_rich();

    loop {
        match pipe_recieve.try_recv() {
            Ok(msg) => {
                let recieved = crate::substate::Fridge::decode(&msg[..]).unwrap();
                match recieved.validate() {
                    Ok(_) => {}
                    Err(err) => {
                        eprintln!("Validation failed: {}", err);
                        continue;
                    }
                }
                println!("Fridge scripts recieved diffs: {}", recieved.pretty_print());
                //these can be merged into the state
                state.merge(&msg[..]).unwrap();
                //and used for a more advanced state machine
                let fridge = Fridge {
                    state: Idle {},
                    params: &state.params.unwrap(),
                };
                //which runs in here - this really should use tokio or something
                if let Some(()) = state.cycle {
                    println!("Starting fridge cycle");
                    state.cycle = None;
                    fridge.next().next().next();
                    println!("Fridge cycle complete");
                }
            }
            Err(_err) => {}
        }
        match pipe_request.try_recv() {
            Ok(_) => {
                let mut buf = Vec::new();
                state.encode(&mut buf).unwrap();
                pipe_response.send(buf).unwrap();
            }
            Err(_err) => {}
        }
    }
}

/// typestate pattern for fridge. Start in idle then delay1, delay2 and finally back to idle
/// this is completely silly here as its just a demo but this shows how payload subsystems can
/// build more complex state on top of the exposed state in the protobuf

struct Idle {}
struct Delay1 {}
struct Delay2 {}
struct Fridge<'a, S> {
    state: S,
    params: &'a crate::substate::FridgeParams,
}

impl<'a> Fridge<'a, Idle> {
    fn next(self) -> Fridge<'a, Delay1> {
        println!("delaying for {} seconds", self.params.delay1);
        std::thread::sleep(std::time::Duration::from_secs(self.params.delay1 as u64));
        Fridge {
            state: Delay1 {},
            params: self.params,
        }
    }
}

impl<'a> Fridge<'a, Delay1> {
    fn next(self) -> Fridge<'a, Delay2> {
        println!("delaying for {} seconds", self.params.delay2);
        std::thread::sleep(std::time::Duration::from_secs(self.params.delay2 as u64));
        Fridge {
            state: Delay2 {},
            params: self.params,
        }
    }
}

impl<'a> Fridge<'a, Delay2> {
    fn next(self) -> Fridge<'a, Idle> {
        println!("delaying for {} seconds", self.params.delay3);
        std::thread::sleep(std::time::Duration::from_secs(self.params.delay3 as u64));
        Fridge {
            state: Idle {},
            params: self.params,
        }
    }
}
