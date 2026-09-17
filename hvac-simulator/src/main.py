import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Optional

current_dir = Path(__file__).resolve().parent
hvac_root = current_dir.parent
for p in [str(hvac_root), str(current_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from src.config import config, SimulationMode
    from src.models.state import OperatingMode
    from src.models.device_info import DeviceMetadata
    from src.simulator.hvac import HVACController
    from src.thingsboard.mqtt_client import ThingsBoardMQTTClient
    from src.thingsboard.publisher import TelemetryPublisher
    from src.server import HTTPServerThread
except ImportError:
    from config import config, SimulationMode
    from models.state import OperatingMode
    from models.device_info import DeviceMetadata
    from simulator.hvac import HVACController
    from thingsboard.mqtt_client import ThingsBoardMQTTClient
    from thingsboard.publisher import TelemetryPublisher
    from server import HTTPServerThread


def configure_logging(level_name: str) -> None:
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


class HVACApplication:
    def __init__(self):
        self.running = True

        mode_map = {
            SimulationMode.NORMAL: OperatingMode.NORMAL,
            SimulationMode.SUMMER: OperatingMode.SUMMER,
            SimulationMode.WINTER: OperatingMode.WINTER,
            SimulationMode.FAILURE_TEST: OperatingMode.FAILURE_TEST,
        }
        operating_mode = mode_map.get(config.simulation_mode, OperatingMode.NORMAL)

        self.controller = HVACController(
            mode=operating_mode,
            filter_speed=config.filter_speed
        )

        self.mqtt_client = ThingsBoardMQTTClient(
            host=config.tb_mqtt_host,
            port=config.tb_mqtt_port,
            token=config.tb_device_token
        )

        self.metadata = DeviceMetadata(
            manufacturer=config.manufacturer,
            model=config.model,
            firmware_version=config.firmware_version
        )
        self.publisher = TelemetryPublisher(
            controller=self.controller,
            client=self.mqtt_client,
            metadata=self.metadata
        )

        self.http_server = HTTPServerThread(
            port=config.http_port,
            controller=self.controller,
            publisher=self.publisher
        )

        self._setup_signals()

    def _setup_signals(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame: Any) -> None:
        logging.info(f"Received termination signal ({signum}). Initiating graceful shutdown...")
        self.running = False

    def start(self) -> None:
        logging.info("=" * 70)
        logging.info("  ORIONMETER Industrial HVAC Unit Simulator - Starting")
        logging.info(f"  Device Name   : {config.device_name} ({config.model})")
        logging.info(f"  Target MQTT   : {config.tb_mqtt_host}:{config.tb_mqtt_port}")
        logging.info(f"  Mode          : {config.simulation_mode.value}")
        logging.info(f"  Interval      : {config.simulation_interval}s")
        logging.info(f"  HTTP Health   : port {config.http_port}")
        logging.info("=" * 70)

        self.http_server.start()
        self.mqtt_client.connect()

        logging.info("Entering simulation loop...")
        try:
            while self.running:
                cycle_start = time.time()
                try:
                    self.publisher.publish_cycle()
                except Exception as ex:
                    logging.error(f"Error during simulation cycle: {ex}", exc_info=True)

                elapsed = time.time() - cycle_start
                sleep_duration = max(0.1, config.simulation_interval - elapsed)

                stop_time = time.time() + sleep_duration
                while self.running and time.time() < stop_time:
                    time.sleep(0.2)
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        logging.info("Shutting down HVAC Application...")
        self.http_server.stop()
        self.mqtt_client.disconnect()
        logging.info("HVAC Application shutdown complete. Goodbye.")


def main():
    configure_logging(config.log_level)
    app = HVACApplication()
    app.start()


if __name__ == "__main__":
    main()
