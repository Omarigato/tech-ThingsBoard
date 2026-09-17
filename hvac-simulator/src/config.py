from enum import Enum
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SimulationMode(str, Enum):
    NORMAL = "NORMAL"
    SUMMER = "SUMMER"
    WINTER = "WINTER"
    FAILURE_TEST = "FAILURE_TEST"


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    tb_mqtt_host: str = Field(default="localhost", alias="TB_MQTT_HOST")
    tb_mqtt_port: int = Field(default=1883, alias="TB_MQTT_PORT")
    tb_device_token: str = Field(default="HVAC_VENT_SECRET_TOKEN", alias="TB_DEVICE_TOKEN")

    simulation_interval: float = Field(default=5.0, alias="SIMULATION_INTERVAL", gt=0)
    simulation_mode: SimulationMode = Field(default=SimulationMode.NORMAL, alias="SIMULATION_MODE")
    filter_speed: float = Field(default=0.015, alias="FILTER_SPEED", gt=0)

    http_port: int = Field(default=8080, alias="HTTP_PORT")

    device_name: str = Field(default="HVAC-01", alias="HVAC_DEVICE_NAME")
    manufacturer: str = Field(default="ORIONMETER", alias="HVAC_DEVICE_MANUFACTURER")
    model: str = Field(default="HVAC-VENT-001", alias="HVAC_DEVICE_MODEL")
    firmware_version: str = Field(default="1.2.0-prod")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO", alias="LOG_LEVEL")


config = AppConfig()
