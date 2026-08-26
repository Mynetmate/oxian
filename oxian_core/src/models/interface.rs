#[derive(Debug, Clone, PartialEq, Eq)]
pub enum InterfaceStatus {
    Up,
    Down,
    Testing,
    Unknown(u32),
}

impl From<u32> for InterfaceStatus {
    fn from(value: u32) -> Self {
        match value {
            1 => Self::Up,
            2 => Self::Down,
            3 => Self::Testing,
            v => Self::Unknown(v),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct Interface {
    pub index: u32,
    pub description: Option<String>,
    pub mac_address: Option<String>,
    pub admin_status: Option<InterfaceStatus>,
    pub oper_status: Option<InterfaceStatus>,
}
