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
                
                //the presence of an empty message is a "do something" flag
                if let Some(()) = state.cycle {
                    println!("Starting fridge cycle");
                    let params = state.params.unwrap();
                    println!("Delay 1: {}", params.delay1.unwrap());
                    std::thread::sleep(std::time::Duration::from_secs(params.delay1.unwrap() as u64));
                    println!("Delay 2: {}", params.delay2.unwrap());
                    std::thread::sleep(std::time::Duration::from_secs(params.delay2.unwrap() as u64));
                    println!("Delay 3: {}", params.delay3.unwrap());
                    std::thread::sleep(std::time::Duration::from_secs(params.delay3.unwrap() as u64));
                    state.cycle = None;
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

