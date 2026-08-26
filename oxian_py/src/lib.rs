use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
mod oxian_py {
    use std::net::IpAddr;

    use oxian_core::discovery;
    use pyo3::prelude::*;
    use pythonize::pythonize;

    /// Discover network devices starting from a target IP address.
    #[pyfunction]
    fn discover(py: Python<'_>, target: String) -> PyResult<Bound<'_, PyAny>> {
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let ip = target.parse::<IpAddr>()?;

            let result = discovery::scan(ip, None).await;

            match result {
                Ok(discovery) => {
                    Python::attach(|py| {
                        pythonize(py, &discovery) // serialize แค่ค่า Ok เท่านั้น
                            .map(|bound| bound.unbind())
                            .map_err(Into::into)
                    })
                }
                Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(e.to_string())),
            }
        })
    }
}
