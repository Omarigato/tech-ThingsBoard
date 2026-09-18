from typing import Tuple
from ..models.state import DeviceStatus


class EnergySubsystem:
    RATED_FLOW_M3S = 3500.0 / 3600.0
    AIR_HEAT_CAPACITY = 1.005
    AIR_DENSITY = 1.204

    def __init__(self, initial_kwh: float = 142.8):
        self.total_energy_kwh = initial_kwh
        self.instant_power_kw = 0.0
        self.cop_efficiency = 3.5

    def step(
        self,
        status: DeviceStatus,
        supply_rpm: int,
        exhaust_rpm: int,
        supply_temp: float,
        outdoor_temp: float,
        dt_seconds: float = 5.0
    ) -> Tuple[float, float, float]:
        if status == DeviceStatus.RUNNING and supply_rpm > 50:
            supply_ratio = supply_rpm / 1450.0
            exhaust_ratio = exhaust_rpm / 1450.0

            p_supply = 2.2 * (supply_ratio ** 3)
            p_exhaust = 1.8 * (exhaust_ratio ** 3)
            p_controls = 0.15
            self.instant_power_kw = round(p_supply + p_exhaust + p_controls, 3)

            mass_flow = self.RATED_FLOW_M3S * supply_ratio * self.AIR_DENSITY
            delta_t = abs(supply_temp - outdoor_temp)
            thermal_kw = mass_flow * self.AIR_HEAT_CAPACITY * delta_t

            if self.instant_power_kw > 0.2:
                raw_cop = thermal_kw / self.instant_power_kw
                self.cop_efficiency = round(max(1.5, min(6.5, raw_cop)), 2)
            else:
                self.cop_efficiency = 1.0
        else:
            self.instant_power_kw = 0.04
            self.cop_efficiency = 0.0

        energy_increment = (self.instant_power_kw * dt_seconds) / 3600.0
        self.total_energy_kwh = round(self.total_energy_kwh + energy_increment, 4)

        return (
            self.instant_power_kw,
            self.total_energy_kwh,
            self.cop_efficiency
        )
