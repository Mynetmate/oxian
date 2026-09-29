use crate::models::Vendor;

pub fn detect_vender(sys_object_id: Option<&str>) -> Vendor {
    match sys_object_id {
        Some(oid) if oid.starts_with("1.3.6.1.4.1.9") => Vendor::Cisco,
        Some(oid) if oid.starts_with("1.3.6.1.4.1.14988") => Vendor::MikroTik,
        _ => Vendor::Unknown,
    }
}
