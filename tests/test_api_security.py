import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


class ApiSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        get_settings.cache_clear()

    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_operational_endpoint_requires_key_when_configured(self) -> None:
        with patch.dict(os.environ, {"MODEL_OPS_API_KEY": "test-key"}):
            get_settings.cache_clear()
            without_key = TestClient(app).get("/api/v1/demo/walkthrough")
            with_key = TestClient(app).get(
                "/api/v1/demo/walkthrough",
                headers={"X-API-Key": "test-key"},
            )

        self.assertEqual(without_key.status_code, 401)
        self.assertEqual(with_key.status_code, 200)

    def test_production_without_key_is_unavailable(self) -> None:
        with patch.dict(
            os.environ,
            {"APP_ENV": "production", "MODEL_OPS_API_KEY": ""},
            clear=False,
        ):
            get_settings.cache_clear()
            response = TestClient(app).get("/api/v1/demo/walkthrough")

        self.assertEqual(response.status_code, 503)

    def test_health_stays_public(self) -> None:
        with patch.dict(os.environ, {"MODEL_OPS_API_KEY": "test-key"}):
            get_settings.cache_clear()
            response = TestClient(app).get("/health")

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
