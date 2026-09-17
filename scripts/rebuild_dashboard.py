import json
import requests

TB_URL = "http://localhost:9090"

r = requests.post(f"{TB_URL}/api/auth/login", json={"username": "tenant@thingsboard.org", "password": "tenant"})
token = r.json()["token"]
headers = {"X-Authorization": f"Bearer {token}", "Content-Type": "application/json"}

dev_res = requests.get(f"{TB_URL}/api/tenant/devices?deviceName=HVAC-01", headers=headers)
device_id = dev_res.json()["id"]["id"]
print(f"[OK] Found HVAC-01 Device ID: {device_id}")

thermo_dash = requests.get(f"{TB_URL}/api/dashboard/9aafad10-b29d-11f1-bfef-cd60615d7885", headers=headers).json()
thermo_widgets = thermo_dash["configuration"]["widgets"]

base_table_widget = thermo_widgets["f33c746c-0dfc-c212-395b-b448c8a17209"]
base_chart_widget = thermo_widgets["eda8a397-0959-690c-405c-11e2c9b2bc7e"]
base_alarm_widget = thermo_widgets["7943196b-eedb-d422-f9c3-b32d379ad172"]

ALIAS_ID = "hvac_device_alias"

w_table = json.loads(json.dumps(base_table_widget))
w_table["id"] = "w_telemetry_table"
w_table["config"]["title"] = "Текущая телеметрия и состояние установки"
w_table["config"]["settings"]["entitiesTitle"] = "Приточно-вытяжная установка (ПВУ)"
w_table["config"]["settings"]["entityNameColumnTitle"] = "Оборудование"

default_key_settings = {"columnWidth": "0px", "useCellStyleFunction": False, "useCellContentFunction": False}

w_table["config"]["datasources"] = [{
    "type": "entity",
    "name": "HVAC-01",
    "entityAliasId": ALIAS_ID,
    "dataKeys": [
        {"name": "status", "type": "timeseries", "label": "Статус", "color": "#10b981", "settings": default_key_settings},
        {"name": "supply_temperature", "type": "timeseries", "label": "Т притока (°C)", "color": "#06b6d4", "units": "°C", "decimals": 1, "settings": default_key_settings},
        {"name": "target_temperature", "type": "timeseries", "label": "Уставка (°C)", "color": "#ffffff", "units": "°C", "decimals": 1, "settings": default_key_settings},
        {"name": "outdoor_temperature", "type": "timeseries", "label": "Т улицы (°C)", "color": "#f97316", "units": "°C", "decimals": 1, "settings": default_key_settings},
        {"name": "humidity", "type": "timeseries", "label": "Влажность (%)", "color": "#38bdf8", "units": "%", "decimals": 1, "settings": default_key_settings},
        {"name": "supply_fan_rpm", "type": "timeseries", "label": "Приточный вентилятор (об/мин)", "color": "#10b981", "units": "об/мин", "decimals": 0, "settings": default_key_settings},
        {"name": "filter_pressure", "type": "timeseries", "label": "Перепад ΔP (Па)", "color": "#ec4899", "units": "Па", "decimals": 1, "settings": default_key_settings},
        {"name": "filter_dirty_percent", "type": "timeseries", "label": "Засорение фильтра (%)", "color": "#f59e0b", "units": "%", "decimals": 1, "settings": default_key_settings},
        {"name": "damper_position", "type": "timeseries", "label": "Заслонка (%)", "color": "#3b82f6", "units": "%", "decimals": 0, "settings": default_key_settings},
        {"name": "heating_valve", "type": "timeseries", "label": "Клапан нагревателя (%)", "color": "#ef4444", "units": "%", "decimals": 0, "settings": default_key_settings},
        {"name": "cooling_valve", "type": "timeseries", "label": "Клапан охладителя (%)", "color": "#0284c7", "units": "%", "decimals": 0, "settings": default_key_settings}
    ]
}]

w_chart_temps = json.loads(json.dumps(base_chart_widget))
w_chart_temps["id"] = "w_chart_temps"
w_chart_temps["config"]["title"] = "Динамика температур: приток, задание и наружный воздух"
w_chart_temps["config"]["settings"]["thresholds"] = []
w_chart_temps["config"]["datasources"] = [{
    "type": "entity",
    "name": "HVAC-01",
    "entityAliasId": ALIAS_ID,
    "dataKeys": [
        {"name": "supply_temperature", "type": "timeseries", "label": "Т притока (°C)", "color": "#06b6d4", "units": "°C", "decimals": 1, "settings": {"yAxisId": "default", "showInLegend": True, "type": "line", "lineSettings": {"showLine": True, "smooth": True, "lineWidth": 2.5}}},
        {"name": "target_temperature", "type": "timeseries", "label": "Уставка задания (°C)", "color": "#ffffff", "units": "°C", "decimals": 1, "settings": {"yAxisId": "default", "showInLegend": True, "type": "line", "lineSettings": {"showLine": True, "smooth": False, "lineWidth": 1.5, "lineType": "dashed"}}},
        {"name": "outdoor_temperature", "type": "timeseries", "label": "Наружный воздух (°C)", "color": "#f97316", "units": "°C", "decimals": 1, "settings": {"yAxisId": "default", "showInLegend": True, "type": "line", "lineSettings": {"showLine": True, "smooth": True, "lineWidth": 1.5}}}
    ]
}]

w_chart_filter = json.loads(json.dumps(base_chart_widget))
w_chart_filter["id"] = "w_chart_filter"
w_chart_filter["config"]["title"] = "Перепад давления на фильтре и запыленность"
w_chart_filter["config"]["settings"]["thresholds"] = []
w_chart_filter["config"]["datasources"] = [{
    "type": "entity",
    "name": "HVAC-01",
    "entityAliasId": ALIAS_ID,
    "dataKeys": [
        {"name": "filter_pressure", "type": "timeseries", "label": "Перепад ΔP (Па)", "color": "#ec4899", "units": "Па", "decimals": 1, "settings": {"yAxisId": "default", "showInLegend": True, "type": "line", "lineSettings": {"showLine": True, "smooth": True, "lineWidth": 2.5}}},
        {"name": "filter_dirty_percent", "type": "timeseries", "label": "Запыленность фильтра (%)", "color": "#f59e0b", "units": "%", "decimals": 1, "settings": {"yAxisId": "default", "showInLegend": True, "type": "line", "lineSettings": {"showLine": True, "smooth": True, "lineWidth": 1.5}}}
    ]
}]

w_chart_fans = json.loads(json.dumps(base_chart_widget))
w_chart_fans["id"] = "w_chart_fans"
w_chart_fans["config"]["title"] = "Аэродинамика вентиляторов и регулирующие клапаны"
w_chart_fans["config"]["settings"]["thresholds"] = []
w_chart_fans["config"]["datasources"] = [{
    "type": "entity",
    "name": "HVAC-01",
    "entityAliasId": ALIAS_ID,
    "dataKeys": [
        {"name": "supply_fan_rpm", "type": "timeseries", "label": "Приточный вентилятор (об/мин)", "color": "#10b981", "units": "об/мин", "decimals": 0, "settings": {"yAxisId": "default", "showInLegend": True, "type": "line", "lineSettings": {"showLine": True, "smooth": True, "lineWidth": 2.0}}},
        {"name": "exhaust_fan_rpm", "type": "timeseries", "label": "Вытяжной вентилятор (об/мин)", "color": "#3b82f6", "units": "об/мин", "decimals": 0, "settings": {"yAxisId": "default", "showInLegend": True, "type": "line", "lineSettings": {"showLine": True, "smooth": True, "lineWidth": 1.5}}},
        {"name": "heating_valve", "type": "timeseries", "label": "Клапан нагрева (%)", "color": "#ef4444", "units": "%", "decimals": 0, "settings": {"yAxisId": "default", "showInLegend": True, "type": "line", "lineSettings": {"showLine": True, "smooth": True, "lineWidth": 1.5}}},
        {"name": "cooling_valve", "type": "timeseries", "label": "Клапан охлаждения (%)", "color": "#06b6d4", "units": "%", "decimals": 0, "settings": {"yAxisId": "default", "showInLegend": True, "type": "line", "lineSettings": {"showLine": True, "smooth": True, "lineWidth": 1.5}}}
    ]
}]

w_alarms = json.loads(json.dumps(base_alarm_widget))
w_alarms["id"] = "w_alarms_table"
w_alarms["config"]["title"] = "Журнал аварийных событий (ThingsBoard Rule Engine)"
w_alarms["config"]["settings"]["alarmsTitle"] = "Активные и архивные аварии"
w_alarms["config"]["datasources"] = []
w_alarms["config"]["alarmSource"] = {
    "type": "entity",
    "name": "alarms",
    "entityAliasId": ALIAS_ID,
    "filterId": None,
    "dataKeys": [
        {"name": "createdTime", "type": "alarm", "label": "Время", "color": "#2196f3", "settings": {}},
        {"name": "originator", "type": "alarm", "label": "Источник", "color": "#4caf50", "settings": {}},
        {"name": "type", "type": "alarm", "label": "Тип аварии", "color": "#f44336", "settings": {}},
        {"name": "severity", "type": "alarm", "label": "Важность", "color": "#ffc107", "settings": {}},
        {"name": "status", "type": "alarm", "label": "Статус", "color": "#607d8b", "settings": {}}
    ]
}

new_dashboard = {
    "title": "Промышленный мониторинг ПВУ (HVAC)",
    "image": None,
    "mobileHide": False,
    "mobileOrder": None,
    "configuration": {
        "description": "Дашборд мониторинга и диагностики промышленной приточно-вытяжной вентиляции (ПВУ)",
        "widgets": {
            "w_telemetry_table": w_table,
            "w_chart_temps": w_chart_temps,
            "w_chart_filter": w_chart_filter,
            "w_chart_fans": w_chart_fans,
            "w_alarms_table": w_alarms
        },
        "states": {
            "default": {
                "name": "Промышленный мониторинг ПВУ (HVAC)",
                "root": True,
                "layouts": {
                    "main": {
                        "widgets": {
                            "w_telemetry_table": {"sizeX": 24, "sizeY": 7, "row": 0, "col": 0},
                            "w_chart_temps": {"sizeX": 12, "sizeY": 8, "row": 7, "col": 0},
                            "w_chart_filter": {"sizeX": 12, "sizeY": 8, "row": 7, "col": 12},
                            "w_chart_fans": {"sizeX": 12, "sizeY": 8, "row": 15, "col": 0},
                            "w_alarms_table": {"sizeX": 12, "sizeY": 8, "row": 15, "col": 12}
                        },
                        "gridSettings": {
                            "columns": 24,
                            "backgroundColor": "#0f172a",
                            "color": "rgba(255, 255, 255, 0.87)",
                            "margins": [10, 10]
                        }
                    }
                }
            }
        },
        "entityAliases": {
            ALIAS_ID: {
                "id": ALIAS_ID,
                "alias": "HVAC-01",
                "filter": {
                    "type": "singleEntity",
                    "singleEntity": {
                        "entityType": "DEVICE",
                        "id": device_id
                    }
                }
            }
        },
        "filters": {},
        "timewindow": {
            "realtime": {
                "realtimeType": 0,
                "timewindowMs": 900000,
                "quickInterval": "CURRENT_DAY"
            }
        },
        "settings": {
            "stateControllerId": "entity",
            "showTitle": True,
            "showDashboardsSelect": True,
            "showEntitiesSelect": False,
            "showDashboardTimewindow": True,
            "showDashboardExport": True,
            "toolbarAlwaysOpen": True
        }
    }
}

dash_list = requests.get(f"{TB_URL}/api/tenant/dashboards?pageSize=10&page=0", headers=headers).json()
hvac_dash_id = None
for d in dash_list.get("data", []):
    if d.get("title") in ["Industrial HVAC Monitoring", "Промышленный мониторинг ПВУ (HVAC)"]:
        hvac_dash_id = d["id"]["id"]
        break

if hvac_dash_id:
    new_dashboard["id"] = {"entityType": "DASHBOARD", "id": hvac_dash_id}
    res = requests.post(f"{TB_URL}/api/dashboard", json=new_dashboard, headers=headers)
    print(f"[OK] Successfully updated existing dashboard {hvac_dash_id}: status {res.status_code}")
else:
    res = requests.post(f"{TB_URL}/api/dashboard", json=new_dashboard, headers=headers)
    hvac_dash_id = res.json()["id"]["id"]
    print(f"[OK] Successfully created new dashboard {hvac_dash_id}: status {res.status_code}")

with open("thingsboard/dashboards/hvac_dashboard.json", "w", encoding="utf-8") as f:
    json.dump(new_dashboard, f, ensure_ascii=False, indent=2)
print(f"[OK] Updated local thingsboard/dashboards/hvac_dashboard.json")
print(f"\nView dashboard at: {TB_URL}/dashboards/{hvac_dash_id}")
