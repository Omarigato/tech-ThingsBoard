import time
from typing import Any, Dict
from dataclasses import dataclass, asdict
from .state import DeviceStatus


@dataclass(frozen=True)
class HVACTelemetry:
    timestamp: int
    supply_temperature: float
    outdoor_temperature: float
    target_temperature: float
    humidity: float
    supply_fan_rpm: int
    exhaust_fan_rpm: int
    filter_pressure: float
    filter_dirty_percent: float
    damper_position: float
    heating_valve: float
    cooling_valve: float
    status: DeviceStatus
    instant_power_kw: float
    total_energy_kwh: float
    cop_efficiency: float
    filter_rul_hours: float
    health_index: float
    bearing_vibration: float

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def current_timestamp_ms(cls) -> int:
        return int(time.time() * 1000)
