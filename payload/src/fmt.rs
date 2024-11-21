use crate::dynamic;

pub trait PrettyPrint {
    fn pretty_print(&self) -> String;
}

impl PrettyPrint for u32 {
    fn pretty_print(&self) -> String {
        self.to_string()
    }
}

impl PrettyPrint for () {
    fn pretty_print(&self) -> String {
        String::new()
    }
}

impl PrettyPrint for crate::dynamic::rtd_channel::Excitation {
    fn pretty_print(&self) -> String {
        match self {
            crate::dynamic::rtd_channel::Excitation::Logdac(value) => value.pretty_print(),
            crate::dynamic::rtd_channel::Excitation::Uvolts(value) => value.pretty_print(),
        }
    }
}

impl PrettyPrint for i32 {
    fn pretty_print(&self) -> String {
        self.to_string()
    }
}