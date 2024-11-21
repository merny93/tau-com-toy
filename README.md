# Protobuf is State - Command model

This is a simple toy example showing the basic implementation of "protobuf is state" (PbfS) model. I have used this model in the [Taurus HK](https://docs.google.com/presentation/d/15TPaAStX5nRX9a1pCMtVafDCqUKk7MctL5Bu_GUL8bI/edit?usp=sharing) succesfully to implement commanding between a "agent" running on a pc in rust and the hardware "client" (no_std C), the code for this is currently in a private repo.

## Installation and running

*I am running ubuntu 24.04 and Steve is running 22.04 - This demo should work under all kinds of OSs and package managers but I'll stick to Ubuntu for now*

### Install

The rust side requires a valid `protoc` installation which can be done with `apt install protobuf-compiler`. Running `protoc --version` should return `>3.0.0`. All other requirements are cargo and will automagically be installed with `cargo build`

On the python side you will need a reasonably modern verion of python and a few `pip` packages:
- Python `protobuf` package:  I would strongly recommend installing with `apt` using: `apt install python3-protobuf` as the version needs to match your system `protoc` install. Using `apt` for both guarantees this.
- The rest can be done with `pip` in a `venv` from inside the `python-client` folder as follows:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
  
You will need to turn the `.proto` extensions into python source files with `protoc` from within the `python-client` folder:
```bash
protoc --python_out=pb2 -I=../protos/include ../protos/include/meta.proto ../protos/include/validate.proto
```

### Run

Start the `payload` with `cargo run` and then you can launch the python client server by naviagting to the `python-client` folder and running `python app.py`. This will launch a localhost server on [port 5000](http://127.0.0.1:5000). This can be used to build and send commands to the payload

## Code overview

Any production code that controlls a real device is a huge complex state machine - different models will handle this state in varying ways but in all cases there will be a huge bundle of state somewhere. The PbfS model is agnostic to how you treat state interanlly but it asks that you define as much as possible of it in a [`.proto` IDL](https://protobuf.dev/programming-guides/editions/). Let's dive into the specifics for this example...

The state of this example is contained in the `state.proto` which shows a top level `State` with a hirarchically equivallent `StateInternal` and an included `Fridge` message from `substate.proto`. The `.proto` syntax has all the bells and whistles you might expect from a fully featured interface description language (IDL). In this case it gives us distribution for free - you can easily communicated with the `Fridge` without ever knowing that the top level `State` includes it.

These `.proto` files go through a codegen step which generates idiomatic code in rust. The definitions are a build artifact and are not commited but here is a copy: 
```rust
#[derive(::prost_validate::Validator)]
#[derive(::dif_print::PrettyPrint)]
#[derive(Clone, Copy, PartialEq, ::prost::Message)]
pub struct StateInternal {
    #[prost(uint32, optional, tag = "1")]
    #[validate(name = "state.StateInternal.param1")]
    #[validate(r#type(uint32(lte = 10)))]
    pub param1: ::core::option::Option<u32>,
}
```
This state struct is then consumed by the payload and is used as a basis for what the payload will do. The code reads well and is commented. `main.rs` defines and `internal_task` that reads from the `StateInternal` message and `fridge.rs` demonstrates how a distributed architecture would work. `rich_defaults.rs` shows how the rust code can suplement the `.proto` definitions explicitly and the `dif-print` package demonstrates how this can be done programatically with macros - both have their place imo.

In this architecture a command is nothing but a partial state which can be efficiently seralized and merged into the existing state on the payload. This has a handful of advantages:
- **ALL** stateful bits are commandable for free (as long as you defined them in the `.proto` ofc)
- The serialization works in both direction so the payload can send a **complete** description of current state to the ground for inspection
- Commands are as rich or sparse as desired: any number of parameters can be tweeked at once
- Hirarchical definitions make building distributed systems easy. To include a new system into your payload just include it's top level state somewhere into your state and redirect messages to it!
  
## Barth's list

- Compatible with `<cmd> <params>` style command    
  - Ish? The command structure is much more rich. its more like `<parent>/<tr...ee>/<child> --<named param> <value> --<named param> <value> --<named param> <value>`
- Supports optional/named commands
  - Yes: optional is a pattern of protobuf and rich names (metadata in general) are implement as `options`
- Ease of Rust integration: clients
  - Sure. Runtime reflection is provided by the `prost_reflect` crate based on a set of `descriptors` which are downloaded at runtime.
- Ease of Rust integration: flight code
  - See `payload` 
- Ease of Rust integration: server
  - Server is almost not needed. just a redirect. Clients nativly guarenteed correct type and format
- Ease of Python integration: clients
  - See `python-client`
- Ease of Python integration: flight code
  - Easy!
- Ease of Python integration: server
  - See `python-client`
- C/C++
  - I only have worked experience with the `nanoPB` library which is more restrictive than we want as its designed for `no_std` 
- New Technologies required for maintenance
  - Install everything from `apt`. It just works. These are popular tools with thousands of users!
- In flight logging of command name
  - See `dif-print`
- In flight logging of received parameters
  - See `dif-print`
- String parameters with white space
  - No problem. `string` type supported in protobuf
- Packet size efficiency
  - Binary tree structure with `var int`. `enum` support for named options
- Cmdlist handling
  - `.proto` is type rich command list
- Inconsistent CMD list detection
  - `descriptors` sync at runtime for clients. Consistent field IDs provide backwards compatibility!
- Insensitivity to CMD list changes (Fwd/rev compat)
  - Field IDs provide this. See [docs](https://protobuf.dev/programming-guides/proto3/#deleting)
- Separatability of systems/subsystems
  - Provided example in this repo. `fridge` is fully seperable!
- Direct to system communication option
  - Yes. Everything speaks the same language. Just put the message in the correct tunnel!
- Multi-experiment compatibility
  - `descriptors` at runtime - connect to the correct server...
- CMDlist human readability/editability
  - Subjective: i think its fine
- Parameter type richness
  - Very extendable!
