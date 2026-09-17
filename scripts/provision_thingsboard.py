import json
import os
import sys
import time
from pathlib import Path
import requests

TB_URL = os.getenv("TB_API_URL", "http://localhost:9090").rstrip("/")
USERNAME = os.getenv("TB_TENANT_USERNAME", "tenant@thingsboard.org")
PASSWORD = os.getenv("TB_TENANT_PASSWORD", "tenant")
DEVICE_NAME = os.getenv("HVAC_DEVICE_NAME", "HVAC-01")
DEVICE_TOKEN = os.getenv("HVAC_DEVICE_TOKEN", "HVAC_VENT_SECRET_TOKEN")
MANUFACTURER = os.getenv("HVAC_DEVICE_MANUFACTURER", "ORIONMETER")
MODEL = os.getenv("HVAC_DEVICE_MODEL", "HVAC-VENT-001")

BASE_DIR = Path(__file__).resolve().parent.parent
RULE_CHAIN_FILE = BASE_DIR / "thingsboard" / "rule_chains" / "hvac_rule_chain.json"
DASHBOARD_FILE = BASE_DIR / "thingsboard" / "dashboards" / "hvac_dashboard.json"


class ThingsBoardProvisioner:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: str = ""
        self.headers = {"Content-Type": "application/json"}

    def wait_for_ready(self, timeout_sec: int = 180) -> bool:
        print(f"[*] Waiting for ThingsBoard REST API at {self.base_url} to become ready...")
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                res = requests.get(f"{self.base_url}/api/noauth/activate", timeout=3)
                if res.status_code in (200, 400, 404):
                    print("[OK] ThingsBoard REST API is operational!")
                    return True
            except requests.RequestException:
                pass
            print("    Still waiting for ThingsBoard initialization...")
            time.sleep(5)
        print("[!] Timed out waiting for ThingsBoard.")
        return False

    def login(self) -> bool:
        print(f"[*] Authenticating as '{USERNAME}'...")
        payload = {"username": USERNAME, "password": PASSWORD}
        try:
            res = requests.post(f"{self.base_url}/api/auth/login", json=payload, timeout=10)
            if res.status_code == 200:
                self.token = res.json().get("token")
                self.headers["X-Authorization"] = f"Bearer {self.token}"
                print("[OK] Successfully authenticated to ThingsBoard!")
                return True
            else:
                print(f"[!] Authentication failed: {res.status_code} - {res.text}")
                return False
        except Exception as e:
            print(f"[!] Login error: {e}")
            return False

    def provision_device(self) -> str:
        print(f"[*] Provisioning device '{DEVICE_NAME}'...")
        check_res = requests.get(
            f"{self.base_url}/api/tenant/devices?deviceName={DEVICE_NAME}",
            headers=self.headers,
            timeout=10
        )
        device_id = None
        if check_res.status_code == 200 and check_res.text:
            try:
                data = check_res.json()
                if "id" in data:
                    device_id = data["id"]["id"]
                    print(f"    Existing device found with ID: {device_id}")
            except ValueError:
                pass

        if not device_id:
            create_payload = {
                "name": DEVICE_NAME,
                "type": "HVAC_AHU",
                "label": f"Air Handling Unit ({MODEL})",
                "additionalInfo": {
                    "description": "Industrial Air Handling Unit monitored via MQTT"
                }
            }
            res = requests.post(f"{self.base_url}/api/device", json=create_payload, headers=self.headers, timeout=10)
            if res.status_code == 200:
                device_id = res.json()["id"]["id"]
                print(f"[OK] Created device '{DEVICE_NAME}' (ID: {device_id})")
            else:
                raise RuntimeError(f"Failed to create device: {res.text}")

        print(f"[*] Setting device credentials (Token: '{DEVICE_TOKEN}')...")
        cred_res = requests.get(f"{self.base_url}/api/device/{device_id}/credentials", headers=self.headers, timeout=10)
        cred_data = cred_res.json() if cred_res.status_code == 200 else {}
        cred_payload = {
            "id": cred_data.get("id"),
            "deviceId": {"entityType": "DEVICE", "id": device_id},
            "credentialsType": "ACCESS_TOKEN",
            "credentialsId": DEVICE_TOKEN,
            "credentialsValue": None
        }
        set_cred_res = requests.post(f"{self.base_url}/api/device/credentials", json=cred_payload, headers=self.headers, timeout=10)
        if set_cred_res.status_code == 200:
            print("[OK] Access Token credentials configured successfully!")
        else:
            print(f"[!] Warning setting credentials: {set_cred_res.text}")

        print("[*] Setting server-scope attributes & metadata...")
        attrs = {
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "commissioning_date": "2026-09-17",
            "rated_airflow_m3h": 3500,
            "location": "Main Facility - Building A, Roof",
            "engineering_contact": "support@orionmeter.com"
        }
        requests.post(
            f"{self.base_url}/api/plugins/telemetry/DEVICE/{device_id}/SERVER_SCOPE",
            json=attrs,
            headers=self.headers,
            timeout=10
        )
        print("[OK] Attributes successfully written to device!")
        return device_id

    def import_rule_chain(self) -> None:
        if not RULE_CHAIN_FILE.exists():
            print(f"[!] Rule chain file not found: {RULE_CHAIN_FILE}")
            return

        print(f"[*] Importing Rule Chain from {RULE_CHAIN_FILE.name}...")
        with open(RULE_CHAIN_FILE, "r", encoding="utf-8") as f:
            rc_data = json.load(f)

        res = requests.post(
            f"{self.base_url}/api/ruleChain",
            json=rc_data["ruleChain"],
            headers=self.headers,
            timeout=10
        )
        if res.status_code == 200:
            saved_rc = res.json()
            rc_id = saved_rc["id"]["id"]
            metadata = rc_data["metadata"]
            metadata["ruleChainId"] = {"entityType": "RULE_CHAIN", "id": rc_id}
            meta_res = requests.post(
                f"{self.base_url}/api/ruleChain/metadata",
                json=metadata,
                headers=self.headers,
                timeout=10
            )
            if meta_res.status_code == 200:
                print(f"[OK] Rule Chain '{saved_rc['name']}' compiled and active!")
            else:
                print(f"[!] Error saving rule chain metadata: {meta_res.text}")
        else:
            print(f"[!] Error saving rule chain: {res.text}")

    def import_dashboard(self, device_id: str) -> None:
        if not DASHBOARD_FILE.exists():
            print(f"[!] Dashboard file not found: {DASHBOARD_FILE}")
            return

        print(f"[*] Importing Dashboard from {DASHBOARD_FILE.name}...")
        with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
            dash_content = f.read()

        dash_content = dash_content.replace("DEVICE_ID_PLACEHOLDER", device_id)
        dash_data = json.loads(dash_content)

        res = requests.post(
            f"{self.base_url}/api/dashboard",
            json=dash_data,
            headers=self.headers,
            timeout=10
        )
        if res.status_code == 200:
            db_obj = res.json()
            db_id = db_obj["id"]["id"]
            print(f"[OK] Dashboard '{db_obj['title']}' created! (ID: {db_id})")
            print(f"    View in browser: {self.base_url}/dashboards/{db_id}")
        else:
            print(f"[!] Error importing dashboard: {res.text}")


def main():
    print("=" * 70)
    print("  ThingsBoard CE Unattended Setup & Provisioning")
    print("=" * 70)
    provisioner = ThingsBoardProvisioner(TB_URL)
    if not provisioner.wait_for_ready():
        sys.exit(1)

    if not provisioner.login():
        sys.exit(1)

    device_id = provisioner.provision_device()
    provisioner.import_rule_chain()
    provisioner.import_dashboard(device_id)

    print("\n" + "=" * 70)
    print("  PROVISIONING SUCCESSFUL!")
    print(f"  ThingsBoard UI: {TB_URL}")
    print(f"  Login         : {USERNAME}")
    print(f"  Password      : {PASSWORD}")
    print(f"  Device Name   : {DEVICE_NAME}")
    print(f"  Access Token  : {DEVICE_TOKEN}")
    print("=" * 70)


if __name__ == "__main__":
    main()
