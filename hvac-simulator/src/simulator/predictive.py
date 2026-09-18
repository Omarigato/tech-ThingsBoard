import random
from typing import Tuple
from collections import deque
from ..models.state import DeviceStatus


class PredictiveAnalytics:
    PRESSURE_LIMIT = 250.0

    def __init__(self, window_size: int = 12):
        self.pressure_history = deque(maxlen=window_size)
        self.filter_rul_hours = 320.0
        self.health_index = 98.5
        self.bearing_vibration = 1.4

    def step(
        self,
        status: DeviceStatus,
        filter_pressure: float,
        filter_dirty_percent: float,
        supply_rpm: int,
        temp_deviation: float,
        dt_seconds: float = 5.0
    ) -> Tuple[float, float, float]:
        self.pressure_history.append((filter_pressure, dt_seconds))

        if len(self.pressure_history) >= 4 and status == DeviceStatus.RUNNING:
            dp_first = self.pressure_history[0][0]
            dp_last = self.pressure_history[-1][0]
            elapsed_sec = sum(t for _, t in list(self.pressure_history)[1:])

            dp_dt_sec = max(0.0001, (dp_last - dp_first) / max(1.0, elapsed_sec))
            dp_dt_hour = dp_dt_sec * 3600.0

            remaining_pa = max(0.0, self.PRESSURE_LIMIT - filter_pressure)
            if dp_dt_hour > 0.05:
                est_hours = remaining_pa / dp_dt_hour
                self.filter_rul_hours = round(max(0.0, min(720.0, est_hours)), 1)
            else:
                remaining_pct = max(0.0, 100.0 - filter_dirty_percent)
                self.filter_rul_hours = round(remaining_pct * 4.5, 1)
        elif filter_pressure >= self.PRESSURE_LIMIT:
            self.filter_rul_hours = 0.0

        if status == DeviceStatus.RUNNING and supply_rpm > 50:
            rpm_factor = supply_rpm / 1450.0
            base_vib = 1.1 + 0.5 * rpm_factor
            noise = random.gauss(0, 0.04)
            self.bearing_vibration = round(max(0.2, base_vib + noise), 2)
        else:
            self.bearing_vibration = 0.05

        penalties = 0.0
        if filter_pressure > 180:
            penalties += min(35.0, (filter_pressure - 180) * 0.45)
        if temp_deviation > 2.0:
            penalties += min(30.0, (temp_deviation - 2.0) * 5.0)
        if self.bearing_vibration > 1.8:
            penalties += min(20.0, (self.bearing_vibration - 1.8) * 15.0)

        self.health_index = round(max(10.0, 100.0 - penalties), 1)

        return (
            self.filter_rul_hours,
            self.health_index,
            self.bearing_vibration
        )
