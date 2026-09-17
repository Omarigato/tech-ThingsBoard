import logging
from typing import Optional
try:
    from src.models.telemetry import HVACTelemetry
    from src.models.device_info import DeviceMetadata
    from src.simulator.hvac import HVACController
    from src.thingsboard.mqtt_client import ThingsBoardMQTTClient
except ImportError:
    from models.telemetry import HVACTelemetry
    from models.device_info import DeviceMetadata
    from simulator.hvac import HVACController
    from thingsboard.mqtt_client import ThingsBoardMQTTClient

logger = logging.getLogger("hvac.publisher")


class TelemetryPublisher:
    def __init__(self, controller: HVACController, client: ThingsBoardMQTTClient, metadata: Optional[DeviceMetadata] = None):
        self.controller = controller
        self.client = client
        self.metadata = metadata or DeviceMetadata()
        self.last_telemetry: Optional[HVACTelemetry] = None
        self.client.set_on_connect_callback(self._on_client_connected)

    def _on_client_connected(self) -> None:
        logger.info("Publishing static device attributes to ThingsBoard...")
        self.client.publish_attributes(self.metadata.to_dict())

    def publish_cycle(self) -> HVACTelemetry:
        telemetry = self.controller.tick()
        self.last_telemetry = telemetry

        payload = telemetry.to_dict()
        sent = self.client.publish_telemetry(payload)

        status_flag = "[OK] SENT" if sent else "[WAIT] QUEUED"
        logger.info(
            f"{status_flag} | State={telemetry.status.value:<7} | "
            f"T_sup={telemetry.supply_temperature:5.1f} C (T_tgt={telemetry.target_temperature:4.1f} C, T_out={telemetry.outdoor_temperature:5.1f} C) | "
            f"Fans={telemetry.supply_fan_rpm:4d}/{telemetry.exhaust_fan_rpm:4d} RPM | "
            f"Filter={telemetry.filter_pressure:5.1f} Pa ({telemetry.filter_dirty_percent:4.1f}%) | "
            f"Valves(H/C)={telemetry.heating_valve:4.1f}%/{telemetry.cooling_valve:4.1f}%"
        )

        return telemetry
