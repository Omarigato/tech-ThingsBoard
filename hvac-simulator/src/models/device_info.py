"""Device metadata and client-side attributes."""

from typing import Any, Dict
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class DeviceMetadata:
    """Device client attributes for ThingsBoard."""
    manufacturer: str = "ORIONMETER"
    model: str = "HVAC-VENT-001"
    serial_number: str = "ONM-2026-HVAC-01"
    rated_airflow_m3h: int = 3500
    filter_type: str = "Pocket Filter F7 (ePM1 70%)"
    supply_fan_power_kw: float = 2.2
    exhaust_fan_power_kw: float = 1.8
    firmware_version: str = "v1.2.0-prod"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
