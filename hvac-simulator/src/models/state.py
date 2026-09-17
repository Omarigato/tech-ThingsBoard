"""Enums and state representations for HVAC physical components."""

from enum import Enum


class DeviceStatus(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ALARM = "ALARM"


class OperatingMode(str, Enum):
    NORMAL = "NORMAL"
    SUMMER = "SUMMER"
    WINTER = "WINTER"
    FAILURE_TEST = "FAILURE_TEST"


class AlarmSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    WARNING = "WARNING"
    INFO = "INFO"


class AlarmType(str, Enum):
    FILTER_DIRTY = "FILTER_DIRTY"
    FILTER_CLOGGED = "FILTER_CLOGGED"
    TEMPERATURE_DEVIATION = "TEMPERATURE_DEVIATION"
    DEVICE_FAILURE = "DEVICE_FAILURE"
