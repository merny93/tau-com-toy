@0xb442fa51f368510c;

struct Command {
  union {
    command1 @0 :Command1;
    command2 @1 :Command2;
    command3 @2 :Command3;
  } 
}

struct Command1 {}

struct Command2 {}

struct Command3 {}
