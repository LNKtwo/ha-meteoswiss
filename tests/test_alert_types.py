"""Regression tests for MeteoSwiss warning type names."""

from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from custom_components.meteoswiss.alerts import MeteoSwissAlertsAPI


class TestGroundFrostWarnings(unittest.TestCase):
    """Recognize the ground-frost warning published by the App API."""

    def setUp(self) -> None:
        """Use public warning fields observed on 2026-10-11.

        Source: https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail?plz=830200
        Validity: 2026-10-12 from 00:00 to 06:00 UTC.
        """
        self.warning = {
            "warnType": 5,
            "warnLevel": 2,
            "text": "Lowest temperatures near ground: 0 to -4 degrees (moderate ground frost)",
            "validFrom": 1791763200000,
            "validTo": 1791784800000,
            "outlook": False,
        }
        self.api = MeteoSwissAlertsAPI()

    def test_parse_ground_frost_warning(self) -> None:
        """Recognize ground frost in both supported response formats."""
        for warnings in (self.warning, [self.warning]):
            with self.subTest(as_list=isinstance(warnings, list)):
                alerts = self.api._parse_alerts({"warnings": warnings}, "8302")
                self.assertEqual(len(alerts), 1)
                alert = alerts[0]
                self.assertEqual(alert.warn_type, 5)
                self.assertEqual(alert.warn_type_name, "Ground Frost")
                self.assertEqual(alert.title, "Ground Frost - Level 2 - Moderate danger")
                self.assertEqual(alert.warn_level, 2)
                self.assertFalse(alert.is_critical())
                self.assertEqual(alert.description, self.warning["text"])
                self.assertEqual(alert.alert_id, "8302_2_5_1791763200000")
                self.assertEqual(alert.valid_from, datetime(2026, 10, 12, tzinfo=timezone.utc))
                self.assertEqual(alert.valid_to, datetime(2026, 10, 12, 6, tzinfo=timezone.utc))
                self.assertFalse(alert.outlook)

    def test_ground_frost_serialized_attributes(self) -> None:
        """Expose the recognized name while preserving public warning fields."""
        alert, = self.api._parse_alerts({"warnings": [self.warning]}, "8302")
        attrs = alert.to_dict()
        self.assertEqual(attrs["warn_type"], 5)
        self.assertEqual(attrs["warn_type_name"], "Ground Frost")
        self.assertEqual(attrs["title"], "Ground Frost - Level 2 - Moderate danger")
        self.assertEqual(attrs["warn_level"], 2)
        self.assertEqual(attrs["valid_from"], "2026-10-12T00:00:00+00:00")
        self.assertEqual(attrs["valid_to"], "2026-10-12T06:00:00+00:00")

    def test_ground_frost_activity_and_severity(self) -> None:
        """Type 5 remains a level-2 warning only during its validity window."""
        alert, = self.api._parse_alerts({"warnings": [self.warning]}, "8302")
        for now, active, sensor_state in (
            (datetime(2026, 10, 11, 23, tzinfo=timezone.utc), False, "clear"),
            (datetime(2026, 10, 12, 1, tzinfo=timezone.utc), True, "warning"),
            (datetime(2026, 10, 12, 7, tzinfo=timezone.utc), False, "clear"),
        ):
            with self.subTest(now=now), patch("custom_components.meteoswiss.alerts.datetime") as clock:
                clock.now.return_value = now
                self.assertEqual(alert.is_active(), active)
                self.assertEqual(alert.to_sensor_state(), sensor_state)
                self.assertFalse(alert.is_critical())

    def test_unrecognized_warning_type(self) -> None:
        """Keep an unknown warning visible with its numeric type."""
        warning = {**self.warning, "warnType": 99}
        alert, = self.api._parse_alerts({"warnings": [warning]}, "8302")
        self.assertEqual(alert.warn_type, 99)
        self.assertEqual(alert.warn_type_name, "Unknown (99)")
        self.assertEqual(alert.title, "Unknown (99) - Level 2 - Moderate danger")
        self.assertEqual(alert.warn_level, 2)


if __name__ == "__main__":
    unittest.main()
