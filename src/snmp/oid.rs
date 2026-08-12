use async_snmp::{Oid, oid};

pub fn sys_descr() -> Oid {
    oid!(1, 3, 6, 1, 2, 1, 1, 1, 0)
}

pub fn sys_object_id() -> Oid {
    oid!(1, 3, 6, 1, 2, 1, 1, 2, 0)
}

pub fn sys_name() -> Oid {
    oid!(1, 3, 6, 1, 2, 1, 1, 5, 0)
}

pub fn if_descr() -> Oid {
    oid!(1, 3, 6, 1, 2, 1, 2, 2, 1, 2)
}

pub fn if_phys_address() -> Oid {
    oid!(1, 3, 6, 1, 2, 1, 2, 2, 1, 6)
}

pub fn if_admin_status() -> Oid {
    oid!(1, 3, 6, 1, 2, 1, 2, 2, 1, 7)
}

pub fn if_oper_status() -> Oid {
    oid!(1, 3, 6, 1, 2, 1, 2, 2, 1, 8)
}

#[allow(dead_code)]
pub fn lldp_mib() -> Oid {
    oid!(1, 0, 8802, 1, 1, 2, 1, 4, 1, 1)
}

pub fn lldp_rem_sys_name() -> Oid {
    oid!(1, 0, 8802, 1, 1, 2, 1, 4, 1, 1, 9)
}

pub fn lldp_rem_port_id() -> Oid {
    oid!(1, 0, 8802, 1, 1, 2, 1, 4, 1, 1, 7)
}

pub fn lldp_rem_man_addr() -> Oid {
    oid!(1, 0, 8802, 1, 1, 2, 1, 4, 2, 1, 2)
}
