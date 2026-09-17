import json
import logging
import time
from typing import Any, Callable, Dict, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger("hvac.mqtt")


class ThingsBoardMQTTClient:
    TELEMETRY_TOPIC = "v1/devices/me/telemetry"
    ATTRIBUTES_TOPIC = "v1/devices/me/attributes"

    def __init__(self, host: str, port: int, token: str):
        self.host = host
        self.port = port
        self.token = token
        self.is_connected = False
        self._on_connect_user_cb: Optional[Callable[[], None]] = None

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"hvac_sim_{int(time.time())}"
        )
        self.client.username_pw_set(self.token)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

    def set_on_connect_callback(self, callback: Callable[[], None]) -> None:
        self._on_connect_user_cb = callback

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, rc: mqtt.ReasonCode, properties: Any) -> None:
        if rc.is_failure:
            logger.error(f"Failed to connect to ThingsBoard MQTT at {self.host}:{self.port}, reason: {rc}")
            self.is_connected = False
        else:
            logger.info(f"Successfully connected to ThingsBoard MQTT at {self.host}:{self.port} (RC: {rc})")
            self.is_connected = True
            if self._on_connect_user_cb:
                try:
                    self._on_connect_user_cb()
                except Exception as ex:
                    logger.error(f"Error in on_connect user callback: {ex}", exc_info=True)

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, disconnect_flags: Any, rc: mqtt.ReasonCode, properties: Any) -> None:
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnect from ThingsBoard MQTT (RC: {rc}). Client will automatically reconnect.")
        else:
            logger.info("Gracefully disconnected from ThingsBoard MQTT broker.")

    def _on_publish(self, client: mqtt.Client, userdata: Any, mid: int, reason_code: Any, properties: Any) -> None:
        logger.debug(f"MQTT message mid={mid} published successfully")

    def connect(self) -> None:
        logger.info(f"Connecting to ThingsBoard MQTT broker {self.host}:{self.port}...")
        try:
            self.client.connect_async(self.host, self.port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Initial connection error: {e}. Will retry in background loop.")
            self.client.loop_start()

    def publish_telemetry(self, telemetry_dict: Dict[str, Any]) -> bool:
        if not self.is_connected:
            logger.warning("MQTT not connected yet, skipping telemetry dispatch")
            return False

        try:
            payload = json.dumps(telemetry_dict)
            info = self.client.publish(self.TELEMETRY_TOPIC, payload, qos=1)
            info.wait_for_publish(timeout=2.0)
            return info.is_published()
        except Exception as ex:
            logger.error(f"Failed to publish telemetry: {ex}")
            return False

    def publish_attributes(self, attributes_dict: Dict[str, Any]) -> bool:
        if not self.is_connected:
            logger.warning("MQTT not connected yet, skipping attributes dispatch")
            return False

        try:
            payload = json.dumps(attributes_dict)
            info = self.client.publish(self.ATTRIBUTES_TOPIC, payload, qos=1)
            info.wait_for_publish(timeout=2.0)
            logger.info("Device attributes published to ThingsBoard")
            return info.is_published()
        except Exception as ex:
            logger.error(f"Failed to publish attributes: {ex}")
            return False

    def disconnect(self) -> None:
        logger.info("Disconnecting from ThingsBoard MQTT...")
        try:
            self.client.disconnect()
            self.client.loop_stop()
        except Exception as e:
            logger.error(f"Error during MQTT client disconnect: {e}")
