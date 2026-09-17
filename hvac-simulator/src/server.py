import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Optional
try:
    from src.models.state import OperatingMode
    from src.simulator.hvac import HVACController
    from src.thingsboard.publisher import TelemetryPublisher
except ImportError:
    from models.state import OperatingMode
    from simulator.hvac import HVACController
    from thingsboard.publisher import TelemetryPublisher

logger = logging.getLogger("hvac.http")


class HVACRequestHandler(BaseHTTPRequestHandler):
    controller: HVACController
    publisher: TelemetryPublisher

    def _send_json_response(self, status_code: int, data: dict) -> None:
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            is_healthy = self.publisher.client.is_connected
            status_code = 200 if is_healthy or True else 503
            self._send_json_response(status_code, {
                "status": "UP",
                "mqtt_connected": self.publisher.client.is_connected,
                "hvac_status": self.controller.status.value,
                "mode": self.controller.mode.value,
                "running": self.controller.is_started
            })
        elif self.path in ("/telemetry", "/metrics"):
            last = self.publisher.last_telemetry
            if last:
                self._send_json_response(200, last.to_dict())
            else:
                self._send_json_response(200, {"message": "No telemetry recorded yet"})
        else:
            self._send_json_response(404, {"error": "Not Found", "available_routes": ["/health", "/telemetry", "/control"]})

    def do_POST(self) -> None:
        if self.path == "/control":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                payload = json.loads(body.decode("utf-8"))

                if "mode" in payload:
                    requested_mode = OperatingMode(payload["mode"].upper())
                    self.controller.set_mode(requested_mode)

                if "target_temperature" in payload:
                    target = float(payload["target_temperature"])
                    self.controller.set_target_temperature(target)

                if "command" in payload:
                    cmd = payload["command"].upper()
                    if cmd == "START":
                        self.controller.start()
                    elif cmd == "STOP":
                        self.controller.stop()
                    elif cmd == "RESET_FILTER":
                        self.controller.reset_filter()

                self._send_json_response(200, {
                    "status": "OK",
                    "current_mode": self.controller.mode.value,
                    "target_temp": self.controller.temperature.target_temperature,
                    "is_running": self.controller.is_started
                })
            except Exception as e:
                logger.error(f"Error handling /control POST: {e}")
                self._send_json_response(400, {"error": str(e)})
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def log_message(self, format: str, *args) -> None:
        logger.debug("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))


class HTTPServerThread:
    def __init__(self, port: int, controller: HVACController, publisher: TelemetryPublisher):
        self.port = port
        self.controller = controller
        self.publisher = publisher
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[Thread] = None

    def start(self) -> None:
        HVACRequestHandler.controller = self.controller
        HVACRequestHandler.publisher = self.publisher

        self.server = HTTPServer(("0.0.0.0", self.port), HVACRequestHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"HTTP Server listening on http://0.0.0.0:{self.port} (/health, /telemetry, /control)")

    def stop(self) -> None:
        if self.server:
            logger.info("Stopping HTTP server...")
            self.server.shutdown()
            self.server.server_close()
