use std::net::{IpAddr, Ipv4Addr};

use oxian::{
    discovery::resolve_topology,
    models::{DefaultRoute, Device, Interface, InterfaceStatus, Vendor},
};

fn create_test_interface(index: u32, desc: &str) -> Interface {
    Interface {
        index,
        description: Some(desc.to_string()),
        mac_address: None,
        admin_status: Some(InterfaceStatus::Up),
        oper_status: Some(InterfaceStatus::Up),
    }
}

#[test]
fn test_resolve_topology_with_default_gateway() {
    let ip_router = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 1));
    let ip_gateway = IpAddr::V4(Ipv4Addr::new(203, 0, 113, 1));

    let router = Device {
        ip: Some(ip_router),
        hostname: Some("Edge-Router".to_string()),
        description: Some("Cisco ISR 4331".to_string()),
        vendor: Vendor::Cisco,
        interface: vec![
            create_test_interface(1, "GigabitEthernet0/0/0 (WAN)"),
            create_test_interface(2, "GigabitEthernet0/0/1 (LAN)"),
        ],
        chassis_id: Some("0011223344aa".to_string()),
        is_managed: true,
    };

    let default_routes = vec![(
        ip_router,
        DefaultRoute {
            next_hop: ip_gateway,
            local_interface: 1,
        },
    )];

    let result = resolve_topology(vec![router], vec![], default_routes);

    assert_eq!(result.devices.len(), 2);

    let managed = result.devices.iter().find(|d| d.is_managed).unwrap();
    assert_eq!(managed.hostname.as_deref(), Some("Edge-Router"));

    let gateway = result.devices.iter().find(|d| !d.is_managed).unwrap();
    assert_eq!(gateway.hostname.as_deref(), Some("Default Gateway"));
    assert_eq!(gateway.ip, Some(ip_gateway));
    assert!(!gateway.is_managed);

    assert_eq!(result.links.len(), 1);
    assert_eq!(result.links[0].source_ip, Some(ip_router));
    assert_eq!(
        result.links[0].source_interface.as_deref(),
        Some("GigabitEthernet0/0/0 (WAN)")
    );
    assert_eq!(result.links[0].target_ip, Some(ip_gateway));
    assert_eq!(result.links[0].target_port_id, "default-route");
}

#[test]
fn test_resolve_topology_default_gateway_already_known() {
    let ip_router_a = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 1));
    let ip_core_switch = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 254));

    let router_a = Device {
        ip: Some(ip_router_a),
        hostname: Some("Branch-Router".to_string()),
        description: None,
        vendor: Vendor::Cisco,
        interface: vec![create_test_interface(1, "Gi0/0")],
        chassis_id: Some("0011223344aa".to_string()),
        is_managed: true,
    };

    let core_switch = Device {
        ip: Some(ip_core_switch),
        hostname: Some("Core-Switch".to_string()),
        description: None,
        vendor: Vendor::Cisco,
        interface: vec![create_test_interface(24, "Gi1/0/24")],
        chassis_id: Some("0011223344bb".to_string()),
        is_managed: true,
    };

    // Default route points to Core-Switch which is already a known managed device
    let default_routes = vec![(
        ip_router_a,
        DefaultRoute {
            next_hop: ip_core_switch,
            local_interface: 1,
        },
    )];

    let result = resolve_topology(vec![router_a, core_switch], vec![], default_routes);

    // Should NOT create duplicate node, exactly 2 devices
    assert_eq!(result.devices.len(), 2);
    assert!(result.devices.iter().all(|d| d.is_managed));

    // Link connects Router A to Core-Switch
    assert_eq!(result.links.len(), 1);
    assert_eq!(result.links[0].source_ip, Some(ip_router_a));
    assert_eq!(result.links[0].target_ip, Some(ip_core_switch));
}

#[test]
fn test_resolve_topology_default_gateway_deduplication() {
    let ip_router_a = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 1));
    let ip_router_b = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 2));
    let ip_shared_gateway = IpAddr::V4(Ipv4Addr::new(203, 0, 113, 1));

    let router_a = Device {
        ip: Some(ip_router_a),
        hostname: Some("Router-A".to_string()),
        description: None,
        vendor: Vendor::Cisco,
        interface: vec![create_test_interface(1, "WAN1")],
        chassis_id: Some("0011223344aa".to_string()),
        is_managed: true,
    };

    let router_b = Device {
        ip: Some(ip_router_b),
        hostname: Some("Router-B".to_string()),
        description: None,
        vendor: Vendor::Cisco,
        interface: vec![create_test_interface(1, "WAN1")],
        chassis_id: Some("0011223344bb".to_string()),
        is_managed: true,
    };

    let default_routes = vec![
        (
            ip_router_a,
            DefaultRoute {
                next_hop: ip_shared_gateway,
                local_interface: 1,
            },
        ),
        (
            ip_router_b,
            DefaultRoute {
                next_hop: ip_shared_gateway,
                local_interface: 1,
            },
        ),
    ];

    let result = resolve_topology(vec![router_a, router_b], vec![], default_routes);

    assert_eq!(result.devices.len(), 3);
    let unmanaged_count = result.devices.iter().filter(|d| !d.is_managed).count();
    assert_eq!(unmanaged_count, 1);

    assert_eq!(result.links.len(), 2);
}
