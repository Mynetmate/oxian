use std::net::{IpAddr, Ipv4Addr};

use oxian::{
    discovery::resolve_topology,
    models::{Device, Interface, InterfaceStatus, Neighbor, Vendor},
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
fn test_resolve_topology_with_managed_devices() {
    let ip_a = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 1));
    let ip_b = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 2));

    let device_a = Device {
        ip: Some(ip_a),
        hostname: Some("Switch-A".to_string()),
        description: Some("Cisco 2960".to_string()),
        vendor: Vendor::Cisco,
        interfaces: vec![create_test_interface(1, "GigabitEthernet0/1")],
        chassis_id: Some("0011223344aa".to_string()),
        is_managed: true,
    };

    let device_b = Device {
        ip: Some(ip_b),
        hostname: Some("Switch-B".to_string()),
        description: Some("Cisco 2960".to_string()),
        vendor: Vendor::Cisco,
        interfaces: vec![create_test_interface(2, "GigabitEthernet0/2")],
        chassis_id: Some("0011223344bb".to_string()),
        is_managed: true,
    };

    let neighbor_records = vec![
        (
            ip_a,
            Neighbor {
                chassis_id: "0011223344bb".to_string(),
                remote_port_id: "Gi0/2".to_string(),
                remote_port_description: Some("GigabitEthernet0/2".to_string()),
                hostname: Some("Switch-B".to_string()),
                remote_ip: Some(ip_b),
                local_interface: 1,
            },
        ),
        (
            ip_b,
            Neighbor {
                chassis_id: "0011223344aa".to_string(),
                remote_port_id: "Gi0/1".to_string(),
                remote_port_description: Some("GigabitEthernet0/1".to_string()),
                hostname: Some("Switch-A".to_string()),
                remote_ip: Some(ip_a),
                local_interface: 2,
            },
        ),
    ];

    let result = resolve_topology(vec![device_a, device_b], neighbor_records, vec![]);

    assert_eq!(result.devices.len(), 2);
    assert!(result.devices.iter().all(|d| d.is_managed));
    assert_eq!(result.links.len(), 1);
    assert_eq!(result.links[0].source_ip, Some(ip_a));
    assert_eq!(result.links[0].target_ip, Some(ip_b));
    assert_eq!(result.unresolved_neighbors.len(), 0);
}

#[test]
fn test_resolve_topology_with_unresolved_neighbor() {
    let ip_a = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 1));
    let ip_unresolved = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 50));

    let device_a = Device {
        ip: Some(ip_a),
        hostname: Some("Switch-A".to_string()),
        description: Some("Managed Switch".to_string()),
        vendor: Vendor::Cisco,
        interfaces: vec![create_test_interface(5, "GigabitEthernet0/5")],
        chassis_id: Some("0011223344aa".to_string()),
        is_managed: true,
    };

    let neighbor_records = vec![(
        ip_a,
        Neighbor {
            chassis_id: "aabbccddeeff".to_string(),
            remote_port_id: "eth0".to_string(),
            remote_port_description: Some("AP Port".to_string()),
            hostname: Some("Unresolved-AP".to_string()),
            remote_ip: Some(ip_unresolved),
            local_interface: 5,
        },
    )];

    let result = resolve_topology(vec![device_a], neighbor_records, vec![]);

    assert_eq!(result.devices.len(), 2);

    let managed = result.devices.iter().find(|d| d.is_managed).unwrap();
    assert_eq!(managed.hostname.as_deref(), Some("Switch-A"));

    let unresolved = result.devices.iter().find(|d| !d.is_managed).unwrap();
    assert_eq!(unresolved.hostname.as_deref(), Some("Unresolved-AP"));
    assert_eq!(unresolved.chassis_id.as_deref(), Some("aabbccddeeff"));
    assert_eq!(unresolved.ip, Some(ip_unresolved));
    assert!(!unresolved.is_managed);

    assert_eq!(result.links.len(), 1);
    assert_eq!(result.links[0].source_ip, Some(ip_a));
    assert_eq!(
        result.links[0].source_interface.as_deref(),
        Some("GigabitEthernet0/5")
    );
    assert_eq!(result.links[0].target_ip, Some(ip_unresolved));
    assert_eq!(
        result.links[0].target_chassis_id.as_deref(),
        Some("aabbccddeeff")
    );
    assert_eq!(result.links[0].target_port_id, "eth0");
    assert_eq!(result.unresolved_neighbors.len(), 0);
}

#[test]
fn test_resolve_topology_unresolved_node_deduplication() {
    let ip_a = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 1));
    let ip_b = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 2));

    let device_a = Device {
        ip: Some(ip_a),
        hostname: Some("Switch-A".to_string()),
        description: None,
        vendor: Vendor::Cisco,
        interfaces: vec![create_test_interface(1, "Gi0/1")],
        chassis_id: Some("0011223344aa".to_string()),
        is_managed: true,
    };

    let device_b = Device {
        ip: Some(ip_b),
        hostname: Some("Switch-B".to_string()),
        description: None,
        vendor: Vendor::Cisco,
        interfaces: vec![create_test_interface(1, "Gi0/1")],
        chassis_id: Some("0011223344bb".to_string()),
        is_managed: true,
    };

    // Both Switch-A and Switch-B connect to the same unresolved switch (chassis_id: "deadbeef0001")
    let neighbor_records = vec![
        (
            ip_a,
            Neighbor {
                chassis_id: "deadbeef0001".to_string(),
                remote_port_id: "port1".to_string(),
                remote_port_description: None,
                hostname: Some("Unresolved-Switch".to_string()),
                remote_ip: None,
                local_interface: 1,
            },
        ),
        (
            ip_b,
            Neighbor {
                chassis_id: "deadbeef0001".to_string(),
                remote_port_id: "port2".to_string(),
                remote_port_description: None,
                hostname: Some("Unresolved-Switch".to_string()),
                remote_ip: None,
                local_interface: 1,
            },
        ),
    ];

    let result = resolve_topology(vec![device_a, device_b], neighbor_records, vec![]);

    // 2 managed + 1 deduplicated unresolved switch = 3 devices
    assert_eq!(result.devices.len(), 3);
    let unresolved_count = result.devices.iter().filter(|d| !d.is_managed).count();
    assert_eq!(unresolved_count, 1);

    // 2 separate links: A -> Unresolved-Switch and B -> Unresolved-Switch
    assert_eq!(result.links.len(), 2);
}

#[test]
fn test_resolve_topology_anonymous_unresolved_neighbor() {
    let ip_a = IpAddr::V4(Ipv4Addr::new(192, 168, 1, 1));

    let device_a = Device {
        ip: Some(ip_a),
        hostname: Some("Switch-A".to_string()),
        description: None,
        vendor: Vendor::Cisco,
        interfaces: vec![create_test_interface(1, "Gi0/1")],
        chassis_id: Some("0011223344aa".to_string()),
        is_managed: true,
    };

    let neighbor_records = vec![(
        ip_a,
        Neighbor {
            chassis_id: "".to_string(),
            remote_port_id: "".to_string(),
            remote_port_description: None,
            hostname: None,
            remote_ip: None,
            local_interface: 1,
        },
    )];

    let result = resolve_topology(vec![device_a], neighbor_records, vec![]);

    // Only 1 device (cannot infer node with zero identifiers)
    assert_eq!(result.devices.len(), 1);
    assert_eq!(result.links.len(), 0);
    assert_eq!(result.unresolved_neighbors.len(), 1);
}
