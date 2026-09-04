from __future__ import annotations


def sys_descr() -> str:
    return "1.3.6.1.2.1.1.1.0"


def sys_object_id() -> str:
    return "1.3.6.1.2.1.1.2.0"


def sys_name() -> str:
    return "1.3.6.1.2.1.1.5.0"


def if_descr() -> str:
    return "1.3.6.1.2.1.2.2.1.2"


def if_name() -> str:
    return "1.3.6.1.2.1.31.1.1.1.1"



def if_phys_address() -> str:
    return "1.3.6.1.2.1.2.2.1.6"


def if_admin_status() -> str:
    return "1.3.6.1.2.1.2.2.1.7"


def if_oper_status() -> str:
    return "1.3.6.1.2.1.2.2.1.8"


# LLDP MIB (IEEE 802.1AB)
def lldp_loc_chassis_id() -> str:
    return "1.0.8802.1.1.2.1.3.2.0"


def lldp_rem_sys_name() -> str:
    return "1.0.8802.1.1.2.1.4.1.1.9"


def lldp_rem_port_id() -> str:
    return "1.0.8802.1.1.2.1.4.1.1.7"


def lldp_rem_port_description() -> str:
    return "1.0.8802.1.1.2.1.4.1.1.8"


def lldp_rem_chassis_id() -> str:
    return "1.0.8802.1.1.2.1.4.1.1.5"


def lldp_rem_man_addr_table() -> str:
    return "1.0.8802.1.1.2.1.4.2"


# Cisco CDP MIB (1.3.6.1.4.1.9.9.23.1.2.1.1)
def cdp_cache_address() -> str:
    return "1.3.6.1.4.1.9.9.23.1.2.1.1.4"


def cdp_cache_device_id() -> str:
    return "1.3.6.1.4.1.9.9.23.1.2.1.1.6"


def cdp_cache_device_port() -> str:
    return "1.3.6.1.4.1.9.9.23.1.2.1.1.7"


def cdp_cache_platform() -> str:
    return "1.3.6.1.4.1.9.9.23.1.2.1.1.8"


# Route Tables (RFC 2096 & RFC 1213)
def ip_cidr_route_next_hop() -> str:
    return "1.3.6.1.2.1.4.24.4.1.4"


def ip_route_next_hop() -> str:
    return "1.3.6.1.2.1.4.21.1.7"


def ip_route_if_index() -> str:
    return "1.3.6.1.2.1.4.21.1.2"


# IP-MIB (RFC 1213 / RFC 2011)
def ip_ad_ent_if_index() -> str:
    return "1.3.6.1.2.1.4.20.1.2"


def ip_ad_ent_net_mask() -> str:
    return "1.3.6.1.2.1.4.20.1.3"



