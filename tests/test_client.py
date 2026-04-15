from __future__ import annotations

import unittest

from imgwire import ImgwireClient


class ClientTests(unittest.TestCase):
    def test_client_sets_default_headers(self) -> None:
        client = ImgwireClient(
            api_key="sk_test",
            base_url="https://api.example.com",
            environment_id="env_123",
            timeout=12.0,
            max_retries=3,
        )

        self.assertEqual(
            client.api_client.configuration.host, "https://api.example.com"
        )
        self.assertEqual(
            client.api_client.default_headers["Authorization"], "Bearer sk_test"
        )
        self.assertEqual(
            client.api_client.default_headers["X-Environment-Id"], "env_123"
        )
        self.assertEqual(client.api_client.configuration.retries, 3)


if __name__ == "__main__":
    unittest.main()
