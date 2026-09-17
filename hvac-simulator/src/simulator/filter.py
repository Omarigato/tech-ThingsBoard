import random
from typing import Tuple
from ..models.state import DeviceStatus, OperatingMode


class FilterSubsystem:
    CLEAN_PRESSURE_NOMINAL = 95.0
    ALARM_PRESSURE_THRESHOLD = 250.0

    def __init__(self, initial_dirty_percent: float = 35.0, loading_speed: float = 0.015):
        self.dirty_percent = initial_dirty_percent
        self.loading_speed = loading_speed
        self.current_pressure = 110.0

    def reset_filter(self) -> None:
        self.dirty_percent = 5.0
        self.current_pressure = self.CLEAN_PRESSURE_NOMINAL

    def step(self, status: DeviceStatus, mode: OperatingMode, supply_rpm: int, nominal_rpm: int = 1450) -> Tuple[float, float, bool]:
        if status == DeviceStatus.RUNNING and supply_rpm > 100:
            flow_ratio = supply_rpm / nominal_rpm
            speed_multiplier = 40.0 if mode == OperatingMode.FAILURE_TEST else 1.0
            accumulation = self.loading_speed * flow_ratio * speed_multiplier
            self.dirty_percent = min(100.0, self.dirty_percent + accumulation)

        if supply_rpm > 50:
            flow_factor = (supply_rpm / nominal_rpm) ** 2
            clogging_factor = 1.0 + 2.4 * ((self.dirty_percent / 100.0) ** 1.3)

            base_pressure = self.CLEAN_PRESSURE_NOMINAL * flow_factor * clogging_factor
            noise = random.gauss(0, 1.2)
            self.current_pressure = max(0.0, base_pressure + noise)
        else:
            self.current_pressure = 0.0

        is_clogged = self.current_pressure >= self.ALARM_PRESSURE_THRESHOLD or self.dirty_percent >= 90.0

        return (
            round(self.current_pressure, 1),
            round(self.dirty_percent, 2),
            is_clogged
        )
