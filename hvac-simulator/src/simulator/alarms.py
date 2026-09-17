from typing import List, Tuple
from ..models.state import DeviceStatus, OperatingMode, AlarmType


class AlarmDetector:
    TEMP_DEVIATION_THRESHOLD = 5.0
    PRESSURE_THRESHOLD = 250.0

    def __init__(self):
        self.active_alarms: List[AlarmType] = []

    def evaluate(
        self,
        intended_running: bool,
        supply_temp: float,
        target_temp: float,
        filter_pressure: float,
        fan_rpm: int,
        mode: OperatingMode
    ) -> Tuple[DeviceStatus, List[AlarmType]]:
        alarms: List[AlarmType] = []

        if filter_pressure >= self.PRESSURE_THRESHOLD:
            alarms.append(AlarmType.FILTER_DIRTY)

        if fan_rpm > 200:
            deviation = abs(supply_temp - target_temp)
            if deviation >= self.TEMP_DEVIATION_THRESHOLD:
                alarms.append(AlarmType.TEMPERATURE_DEVIATION)

        if mode == OperatingMode.FAILURE_TEST and fan_rpm < 100 and intended_running:
            alarms.append(AlarmType.DEVICE_FAILURE)

        self.active_alarms = alarms

        if not intended_running:
            status = DeviceStatus.STOPPED
        elif len(alarms) > 0:
            status = DeviceStatus.ALARM
        else:
            status = DeviceStatus.RUNNING

        return status, alarms
