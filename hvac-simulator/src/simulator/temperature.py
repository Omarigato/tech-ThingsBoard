import random
from typing import Tuple
from ..models.state import OperatingMode, DeviceStatus


class TemperatureSubsystem:
    def __init__(self, target_temp: float = 22.0):
        self.target_temperature = target_temp
        self.supply_temperature = target_temp - 3.0
        self.outdoor_temperature = 14.0
        self.humidity = 48.0
        self.damper_position = 80.0
        self.heating_valve = 0.0
        self.cooling_valve = 0.0
        self.inertia_factor = 0.07

    def configure_mode(self, mode: OperatingMode) -> None:
        if mode == OperatingMode.NORMAL:
            self.outdoor_temperature = 15.0
            self.target_temperature = 21.5
            self.damper_position = 75.0
        elif mode == OperatingMode.SUMMER:
            self.outdoor_temperature = 31.5
            self.target_temperature = 21.0
            self.damper_position = 85.0
        elif mode == OperatingMode.WINTER:
            self.outdoor_temperature = -8.5
            self.target_temperature = 22.0
            self.damper_position = 60.0
        elif mode == OperatingMode.FAILURE_TEST:
            self.outdoor_temperature = -14.0
            self.target_temperature = 22.0

    def step(self, status: DeviceStatus, mode: OperatingMode) -> Tuple[float, float, float, float, float, float, float]:
        ambient_jitter = random.gauss(0, 0.05)
        self.outdoor_temperature += ambient_jitter

        if mode == OperatingMode.SUMMER:
            self.outdoor_temperature = max(26.0, min(36.0, self.outdoor_temperature))
        elif mode == OperatingMode.WINTER or mode == OperatingMode.FAILURE_TEST:
            self.outdoor_temperature = max(-25.0, min(2.0, self.outdoor_temperature))
        else:
            self.outdoor_temperature = max(8.0, min(25.0, self.outdoor_temperature))

        if status == DeviceStatus.RUNNING:
            if mode == OperatingMode.FAILURE_TEST:
                self.heating_valve = 5.0
                self.cooling_valve = 0.0
                target_drift = self.outdoor_temperature + 5.0
                self.supply_temperature += (target_drift - self.supply_temperature) * 0.05
            else:
                temp_error = self.target_temperature - self.supply_temperature

                if temp_error > 0.3:
                    self.heating_valve = min(100.0, max(0.0, self.heating_valve + temp_error * 12.0))
                    self.cooling_valve = max(0.0, self.cooling_valve - 10.0)
                elif temp_error < -0.3:
                    self.cooling_valve = min(100.0, max(0.0, self.cooling_valve + abs(temp_error) * 12.0))
                    self.heating_valve = max(0.0, self.heating_valve - 10.0)
                else:
                    self.heating_valve = max(0.0, self.heating_valve * 0.95)
                    self.cooling_valve = max(0.0, self.cooling_valve * 0.95)

                sensor_noise = random.gauss(0, 0.03)
                delta = (self.target_temperature - self.supply_temperature) * self.inertia_factor
                self.supply_temperature += delta + sensor_noise
        else:
            self.heating_valve = 0.0
            self.cooling_valve = 0.0
            self.supply_temperature += (self.outdoor_temperature - self.supply_temperature) * 0.02

        target_humidity = 50.0
        if self.cooling_valve > 30.0:
            target_humidity = 42.0
        elif mode == OperatingMode.WINTER:
            target_humidity = 38.0

        humidity_delta = (target_humidity - self.humidity) * 0.03 + random.gauss(0, 0.05)
        self.humidity = max(20.0, min(85.0, self.humidity + humidity_delta))

        if status == DeviceStatus.RUNNING:
            self.damper_position = max(20.0, min(100.0, self.damper_position + random.uniform(-0.5, 0.5)))
        else:
            self.damper_position = 0.0

        return (
            round(self.supply_temperature, 2),
            round(self.outdoor_temperature, 2),
            round(self.target_temperature, 2),
            round(self.humidity, 1),
            round(self.damper_position, 1),
            round(self.heating_valve, 1),
            round(self.cooling_valve, 1),
        )
