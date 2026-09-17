"""Telemetry data transfer object for ThingsBoard MQTT payload."""

import time
from typing import Any, Dict
from dataclasses import dataclass, asdict
from .state import DeviceStatus


@dataclass(frozen=True)
class HVACTelemetry:
    """Represents a discrete telemetry sample from the HVAC unit."""
    timestamp: int  # Milliseconds since epoch
    supply_temperature: float  # Celsius, supply air
    outdoor_temperature: float  # Celsius, outdoor ambient
    target_temperature: float  # Celsius, setpoint
    humidity: float  # Relative humidity % (0-100)
    supply_fan_rpm: int  # Supply fan speed (RPM)
    exhaust_fan_rpm: int  # Exhaust fan speed (RPM)
    filter_pressure: float  # Differential pressure over filter (Pa)
    filter_dirty_percent: float  # Filter particulate accumulation (0-100%)
    damper_position: float  # Air intake damper opening % (0-100)
    heating_valve: float  # Hot water coil valve opening % (0-100)
    cooling_valve: float  # Chilled water coil valve opening % (0-100)
    status: DeviceStatus  # RUNNING | STOPPED | ALARM

    def to_dict(self) -> Dict[str, Any]:
        """Convert telemetry to ThingsBoard-compatible JSON dict."""
        data = asdict(self)
        # Ensure status is serialized as its string value
        data["status"] = self.status.value
        return data

    @classmethod
    def current_timestamp_ms(cls) -> int:
        """Returns current epoch time in milliseconds."""
        return int(time.time() * 1000)
