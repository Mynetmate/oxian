import unittest
import oxian_py


class TestOxianPy(unittest.IsolatedAsyncioTestCase):
    def test_discover_callable(self):
        self.assertTrue(callable(oxian_py.discover))

    async def test_discover_invalid_ip(self):
        with self.assertRaises(ValueError):
            await oxian_py.discover("invalid_ip")

    async def test_discover_valid_ip(self):
        result = await oxian_py.discover("0.0.0.0")
        self.assertIsInstance(result, dict)
        self.assertIn("devices", result)
        self.assertIn("links", result)
        self.assertIn("unresolved_neighbors", result)


if __name__ == "__main__":
    unittest.main()
