import logging
try:
    from src.models.state import DeviceStatus, OperatingMode, AlarmType
    from src.models.telemetry import HVACTelemetry
    from src.simulator.temperature import TemperatureSubsystem
    from src.simulator.fan import FanSubsystem
    from src.simulator.filter import FilterSubsystem
    from src.simulator.alarms import AlarmDetector
    from src.simulator.energy import EnergySubsystem
    from src.simulator.predictive import PredictiveAnalytics
except ImportError:
    from models.state import DeviceStatus, OperatingMode, AlarmType
    from models.telemetry import HVACTelemetry
    from simulator.temperature import TemperatureSubsystem
    from simulator.fan import FanSubsystem
    from simulator.filter import FilterSubsystem
    from simulator.alarms import AlarmDetector
    from simulator.energy import EnergySubsystem
    from simulator.predictive import PredictiveAnalytics

logger = logging.getLogger("hvac.simulator")


class HVACController:
    def __init__(self, mode: OperatingMode = OperatingMode.NORMAL, filter_speed: float = 0.015):
        self.mode = mode
        self.is_started = True
        self.status = DeviceStatus.RUNNING

        self.temperature = TemperatureSubsystem(target_temp=21.5)
        self.fans = FanSubsystem(target_percent=85.0)
        self.filter = FilterSubsystem(initial_dirty_percent=25.0, loading_speed=filter_speed)
        self.alarm_detector = AlarmDetector()
        self.energy = EnergySubsystem()
        self.predictive = PredictiveAnalytics()

        self.temperature.configure_mode(self.mode)
        logger.info(f"HVACController initialized in {self.mode.value} mode")

    def set_mode(self, mode: OperatingMode) -> None:
        logger.info(f"Switching HVAC mode from {self.mode.value} to {mode.value}")
        self.mode = mode
        self.temperature.configure_mode(mode)

    @property
    def target_temperature(self) -> float:
        return self.temperature.target_temperature

    def set_target_temperature(self, target: float) -> None:
        logger.info(f"Updating target temperature to {target:.1f} °C")
        self.temperature.target_temperature = target

    def start(self) -> None:
        logger.info("Command: START unit")
        self.is_started = True

    def stop(self) -> None:
        logger.info("Command: STOP unit")
        self.is_started = False

    def reset_filter(self) -> None:
        logger.info("Command: Replace filter cartridge")
        self.filter.reset_filter()

    def tick(self, dt_seconds: float = 5.0) -> HVACTelemetry:
        nominal_status = DeviceStatus.RUNNING if self.is_started else DeviceStatus.STOPPED
        supply_rpm, exhaust_rpm = self.fans.step(nominal_status)

        supply_temp, outdoor_temp, target_temp, humidity, damper_pos, heat_valve, cool_valve = self.temperature.step(
            nominal_status, self.mode
        )

        filter_dp, dirty_pct, _ = self.filter.step(nominal_status, self.mode, supply_rpm)

        self.status, active_alarms = self.alarm_detector.evaluate(
            intended_running=self.is_started,
            supply_temp=supply_temp,
            target_temp=target_temp,
            filter_pressure=filter_dp,
            fan_rpm=supply_rpm,
            mode=self.mode
        )

        instant_power, total_kwh, cop = self.energy.step(
            status=nominal_status,
            supply_rpm=supply_rpm,
            exhaust_rpm=exhaust_rpm,
            supply_temp=supply_temp,
            outdoor_temp=outdoor_temp,
            dt_seconds=dt_seconds
        )

        temp_dev = abs(supply_temp - target_temp)
        rul_hours, health_idx, vibration = self.predictive.step(
            status=nominal_status,
            filter_pressure=filter_dp,
            filter_dirty_percent=dirty_pct,
            supply_rpm=supply_rpm,
            temp_deviation=temp_dev,
            dt_seconds=dt_seconds
        )

        if active_alarms:
            logger.warning(f"Active alarms detected: {[a.value for a in active_alarms]}")

        return HVACTelemetry(
            timestamp=HVACTelemetry.current_timestamp_ms(),
            supply_temperature=supply_temp,
            outdoor_temperature=outdoor_temp,
            target_temperature=target_temp,
            humidity=humidity,
            supply_fan_rpm=supply_rpm,
            exhaust_fan_rpm=exhaust_rpm,
            filter_pressure=filter_dp,
            filter_dirty_percent=dirty_pct,
            damper_position=damper_pos,
            heating_valve=heat_valve,
            cooling_valve=cool_valve,
            status=self.status,
            instant_power_kw=instant_power,
            total_energy_kwh=total_kwh,
            cop_efficiency=cop,
            filter_rul_hours=rul_hours,
            health_index=health_idx,
            bearing_vibration=vibration
        )
