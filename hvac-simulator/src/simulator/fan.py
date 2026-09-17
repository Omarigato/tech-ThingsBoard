import random
from typing import Tuple
from ..models.state import DeviceStatus


class FanSubsystem:
    NOMINAL_RPM = 1450

    def __init__(self, target_percent: float = 85.0):
        self.target_percent = target_percent
        self.supply_fan_rpm = 0.0
        self.exhaust_fan_rpm = 0.0

    def set_target_percent(self, percent: float) -> None:
        self.target_percent = max(60.0, min(100.0, percent))

    def step(self, status: DeviceStatus) -> Tuple[int, int]:
        if status == DeviceStatus.RUNNING:
            target_supply_rpm = (self.target_percent / 100.0) * self.NOMINAL_RPM
            target_exhaust_rpm = target_supply_rpm * 0.96

            self.supply_fan_rpm += (target_supply_rpm - self.supply_fan_rpm) * 0.25
            self.exhaust_fan_rpm += (target_exhaust_rpm - self.exhaust_fan_rpm) * 0.25

            jitter_supply = random.gauss(0, 7.0)
            jitter_exhaust = random.gauss(0, 6.0)

            actual_supply = max(0, int(round(self.supply_fan_rpm + jitter_supply)))
            actual_exhaust = max(0, int(round(self.exhaust_fan_rpm + jitter_exhaust)))
        else:
            self.supply_fan_rpm = max(0.0, self.supply_fan_rpm * 0.4)
            self.exhaust_fan_rpm = max(0.0, self.exhaust_fan_rpm * 0.4)
            if self.supply_fan_rpm < 10:
                self.supply_fan_rpm = 0.0
            if self.exhaust_fan_rpm < 10:
                self.exhaust_fan_rpm = 0.0

            actual_supply = int(self.supply_fan_rpm)
            actual_exhaust = int(self.exhaust_fan_rpm)

        return actual_supply, actual_exhaust
