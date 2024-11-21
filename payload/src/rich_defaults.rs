pub trait DefaultRich {
    fn default_rich() -> Self;
}

/// Each subsystem can define it's defualts
impl DefaultRich for crate::substate::Fridge {
    fn default_rich() -> Self {
        crate::substate::Fridge {
            params: Some(crate::substate::FridgeParams {
                delay1: Some(1),
                delay2: Some(2),
                delay3: Some(3),
            }),
            cycle: None,
        }
    }
}

/// propagate it up!
impl DefaultRich for crate::state::State {
    fn default_rich() -> Self {
        crate::state::State {
            global_param: Some(33),
            internal: Some(crate::state::StateInternal { param1: Some(11) }),
            fridge: None, //distributed means that the parent need not know about the child
            hk_system: None,
        }
    }
}
