'use client';

import React, { useEffect, useState } from 'react';
import {
  Fan,
  Thermometer,
  Wind,
  Activity,
  Power,
  RotateCcw,
  Sliders,
  Flame,
  Snowflake,
  AlertTriangle,
  Server,
  Lock,
  Eye,
  EyeOff,
  ShieldCheck,
  ExternalLink,
  Download,
  Copy,
  Check,
  TrendingUp,
  Radio,
  ChevronRight,
  AlertCircle,
  LogOut,
  Zap,
  Gauge,
  Cpu,
} from 'lucide-react';

interface TelemetryData {
  timestamp: number;
  supply_temperature: number;
  outdoor_temperature: number;
  target_temperature: number;
  humidity: number;
  supply_fan_rpm: number;
  exhaust_fan_rpm: number;
  filter_pressure: number;
  filter_dirty_percent: number;
  damper_position: number;
  heating_valve: number;
  cooling_valve: number;
  status: 'RUNNING' | 'STOPPED' | 'ALARM';
  instant_power_kw?: number;
  total_energy_kwh?: number;
  cop_efficiency?: number;
  filter_rul_hours?: number;
  health_index?: number;
  bearing_vibration?: number;
}

interface AlarmItem {
  id: string;
  type: string;
  severity: 'CRITICAL' | 'MAJOR' | 'WARNING';
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

const DEFAULT_TELEMETRY: TelemetryData = {
  timestamp: Date.now(),
  supply_temperature: 21.5,
  outdoor_temperature: 15.0,
  target_temperature: 21.5,
  humidity: 48.0,
  supply_fan_rpm: 1420,
  exhaust_fan_rpm: 1360,
  filter_pressure: 112.5,
  filter_dirty_percent: 28.4,
  damper_position: 78.0,
  heating_valve: 22.0,
  cooling_valve: 0.0,
  status: 'RUNNING',
  instant_power_kw: 3.42,
  total_energy_kwh: 142.85,
  cop_efficiency: 3.8,
  filter_rul_hours: 320.0,
  health_index: 98.5,
  bearing_vibration: 1.25,
};

export default function HVACControlPanel() {
  const [activeTab, setActiveTab] = useState<'scada' | 'control' | 'charts' | 'alarms' | 'mqtt'>('scada');

  const [telemetry, setTelemetry] = useState<TelemetryData>(DEFAULT_TELEMETRY);
  const [history, setHistory] = useState<TelemetryData[]>([]);
  const [currentMode, setCurrentMode] = useState<string>('NORMAL');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string>('Подключение...');
  const [targetInput, setTargetInput] = useState<number>(21.5);
  const [copied, setCopied] = useState<boolean>(false);

  const [alarms, setAlarms] = useState<AlarmItem[]>([]);

  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);
  const [tbUsername, setTbUsername] = useState<string>('tenant@thingsboard.org');
  const [tbPassword, setTbPassword] = useState<string>('tenant');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [authLoading, setAuthLoading] = useState<boolean>(false);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [rpcLoading, setRpcLoading] = useState<boolean>(false);
  const [rpcLog, setRpcLog] = useState<string | null>(null);

  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const res = await fetch('http://localhost:8080/telemetry');
        if (res.ok) {
          const data = await res.json();
          if (data && data.supply_temperature !== undefined) {
            setTelemetry(data);
            setIsConnected(true);
            setLastUpdated(new Date().toLocaleTimeString('ru-RU'));

            setHistory((prev) => [...prev.slice(-29), data]);

            const newAlarms: AlarmItem[] = [];
            if (data.filter_pressure > 250) {
              newAlarms.push({
                id: 'alarm_filter',
                type: 'FILTER_DIRTY',
                severity: 'WARNING',
                message: `Высокий перепад давления (${data.filter_pressure.toFixed(1)} Па > 250 Па). Требуется замена карманного фильтра F7.`,
                timestamp: new Date().toLocaleTimeString('ru-RU'),
                acknowledged: false,
              });
            }
            if (Math.abs(data.supply_temperature - data.target_temperature) > 5.0 && data.supply_fan_rpm > 200) {
              newAlarms.push({
                id: 'alarm_temp',
                type: 'TEMPERATURE_DEVIATION',
                severity: 'MAJOR',
                message: `Отклонение температуры притока превышает 5.0 °C (Δ = ${Math.abs(data.supply_temperature - data.target_temperature).toFixed(1)} °C).`,
                timestamp: new Date().toLocaleTimeString('ru-RU'),
                acknowledged: false,
              });
            }
            if (data.status === 'STOPPED' && currentMode === 'FAILURE_TEST') {
              newAlarms.push({
                id: 'alarm_failure',
                type: 'DEVICE_FAILURE',
                severity: 'CRITICAL',
                message: 'Внезапный останов двигателя / отказ оборудования в режиме аварийного тестирования.',
                timestamp: new Date().toLocaleTimeString('ru-RU'),
                acknowledged: false,
              });
            }
            setAlarms(newAlarms);
          }
        } else {
          setIsConnected(false);
        }
      } catch {
        setIsConnected(false);
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 2500);
    return () => clearInterval(interval);
  }, [currentMode]);

  const sendControl = async (payload: object) => {
    try {
      const res = await fetch('http://localhost:8080/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const result = await res.json();
        if (result.current_mode) setCurrentMode(result.current_mode);
      }
    } catch (err) {
      console.error('Ошибка отправки команды управления:', err);
    }
  };

  const handleModeSelect = (mode: string) => {
    setCurrentMode(mode);
    sendControl({ mode });
  };

  const handleTargetChange = (delta: number) => {
    const val = Math.round((targetInput + delta) * 10) / 10;
    const clamped = Math.max(16, Math.min(30, val));
    setTargetInput(clamped);
    sendControl({ target_temperature: clamped });
  };

  const handlePowerToggle = () => {
    const cmd = telemetry.status === 'STOPPED' ? 'START' : 'STOP';
    sendControl({ command: cmd });
  };

  const handleFilterReset = () => {
    sendControl({ command: 'RESET_FILTER' });
  };

  const handleThingsboardLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError(null);
    try {
      const res = await fetch('http://localhost:9090/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: tbUsername, password: tbPassword }),
      });
      if (res.ok) {
        const data = await res.json();
        setAuthToken(data.token);
        setShowAuthModal(false);
      } else {
        setAuthError(`Ошибка авторизации (${res.status}): Неверный логин или пароль`);
      }
    } catch {
      setAuthError('Ошибка сети: Убедитесь, что ThingsBoard запущен на порту :9090');
    } finally {
      setAuthLoading(false);
    }
  };

  const sendThingsBoardRPC = async (method: string, params: any) => {
    setRpcLoading(true);
    setRpcLog(`[RPC OUT] ${method}(${JSON.stringify(params)}) -> ThingsBoard :9090...`);
    try {
      let token = authToken;
      if (!token) {
        const loginRes = await fetch('http://localhost:9090/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: tbUsername, password: tbPassword }),
        });
        if (loginRes.ok) {
          const authData = await loginRes.json();
          token = authData.token;
          setAuthToken(token);
        }
      }

      if (!token) {
        setRpcLog('[RPC ERR] Не удалось получить авторизационный токен ThingsBoard');
        setRpcLoading(false);
        return;
      }

      const devRes = await fetch('http://localhost:9090/api/tenant/devices?deviceName=HVAC-01', {
        headers: { 'X-Authorization': `Bearer ${token}` }
      });
      const devData = await devRes.json();
      const deviceId = devData?.id?.id;

      if (!deviceId) {
        setRpcLog('[RPC ERR] Устройство HVAC-01 не найдено в ThingsBoard');
        setRpcLoading(false);
        return;
      }

      const rpcRes = await fetch(`http://localhost:9090/api/plugins/rpc/twoway/${deviceId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ method, params, timeout: 5000 })
      });

      const rpcData = await rpcRes.json();
      setRpcLog(`[RPC IN 200 OK] Ответ контроллера: ${JSON.stringify(rpcData, null, 2)}`);
    } catch (err: any) {
      setRpcLog(`[RPC ERR] Исключение: ${err?.message || err}`);
    } finally {
      setRpcLoading(false);
    }
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(telemetry, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportCsv = () => {
    if (history.length === 0) return;
    const headers = Object.keys(history[0]).join(',');
    const rows = history.map((h) => Object.values(h).join(','));
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `hvac_telemetry_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const isRunning = telemetry.status === 'RUNNING';
  const isAlarm = telemetry.status === 'ALARM';
  const fanSpinSpeedSec = Math.max(0.4, 2.5 - (telemetry.supply_fan_rpm / 1500) * 2.0);

  const getStatusText = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'РАБОТА';
      case 'STOPPED':
        return 'ОСТАНОВ';
      case 'ALARM':
        return 'АВАРИЯ';
      default:
        return status;
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 24px', minHeight: '100vh' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '20px', borderBottom: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: '#ffffff', color: '#000000', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '18px' }}>
            ON
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '20px', fontWeight: 700, letterSpacing: '-0.02em', color: '#ffffff' }}>
                ORIONMETER HVAC-VENT-001
              </h1>
              <span className={`badge ${isAlarm ? 'badge-alarm' : isRunning ? 'badge-running' : 'badge-stopped'}`}>
                <span className="pulse-active" style={{ width: '6px', height: '6px', borderRadius: '50%', background: isAlarm ? '#ef4444' : isRunning ? '#ffffff' : '#f59e0b' }} />
                {getStatusText(telemetry.status)}
              </span>
              <span className="badge badge-outline mono">HVAC-01</span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '2px' }}>
              АСУ ТП и шлюз телеметрии приточно-вытяжной вентиляционной установки (ПВУ)
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: 'var(--radius-md)', background: '#121215', border: '1px solid var(--border-subtle)', fontSize: '12px' }}>
            <Radio size={14} className={isConnected ? "pulse-active" : ""} color={isConnected ? "#ffffff" : "#71717a"} />
            <span style={{ color: isConnected ? '#ffffff' : 'var(--text-muted)' }}>
              {isConnected ? 'Связь активна' : 'Подключение к ядру...'}
            </span>
          </div>

          {authToken ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button onClick={() => setShowAuthModal(true)} className="btn btn-secondary" title="Профиль">
                <ShieldCheck size={15} color="#ffffff" />
                <span className="mono" style={{ fontSize: '12px' }}>tenant@thingsboard.org</span>
              </button>
              <button onClick={() => setAuthToken(null)} className="btn btn-outline" title="Выйти">
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <button onClick={() => setShowAuthModal(true)} className="btn btn-primary">
              <Lock size={14} /> Подключить ThingsBoard
            </button>
          )}

          <a
            href="http://localhost:9090"
            target="_blank"
            rel="noreferrer"
            className="btn btn-outline"
            title="Открыть нативный интерфейс ThingsBoard CE"
          >
            <Server size={14} /> ThingsBoard :9090 <ExternalLink size={12} />
          </a>
        </div>
      </header>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div className="tab-list">
          <button
            onClick={() => setActiveTab('scada')}
            className={`tab-trigger ${activeTab === 'scada' ? 'tab-trigger-active' : ''}`}
          >
            <Activity size={15} /> Мнемосхема и SCADA
          </button>
          <button
            onClick={() => setActiveTab('control')}
            className={`tab-trigger ${activeTab === 'control' ? 'tab-trigger-active' : ''}`}
          >
            <Sliders size={15} /> Управление
          </button>
          <button
            onClick={() => setActiveTab('charts')}
            className={`tab-trigger ${activeTab === 'charts' ? 'tab-trigger-active' : ''}`}
          >
            <TrendingUp size={15} /> Графики трендов
          </button>
          <button
            onClick={() => setActiveTab('alarms')}
            className={`tab-trigger ${activeTab === 'alarms' ? 'tab-trigger-active' : ''}`}
          >
            <AlertCircle size={15} />
            Аварии
            {alarms.length > 0 && (
              <span style={{ background: '#ef4444', color: 'white', borderRadius: '999px', padding: '1px 6px', fontSize: '10px', fontWeight: 700 }}>
                {alarms.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('mqtt')}
            className={`tab-trigger ${activeTab === 'mqtt' ? 'tab-trigger-active' : ''}`}
          >
            <Radio size={15} /> Пакеты MQTT
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#121215', border: '1px solid var(--border-subtle)', padding: '3px 8px', borderRadius: 'var(--radius-md)' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Уставка:</span>
            <button onClick={() => handleTargetChange(-0.5)} className="btn btn-outline" style={{ padding: '2px 8px', fontSize: '12px' }}>-</button>
            <span className="mono" style={{ fontSize: '14px', fontWeight: 700, minWidth: '50px', textAlign: 'center' }}>
              {targetInput.toFixed(1)}°C
            </span>
            <button onClick={() => handleTargetChange(0.5)} className="btn btn-outline" style={{ padding: '2px 8px', fontSize: '12px' }}>+</button>
          </div>

          <div style={{ display: 'flex', gap: '4px', background: '#09090b', padding: '2px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            {[
              { id: 'NORMAL', label: 'ШТАТНЫЙ' },
              { id: 'SUMMER', label: 'ЛЕТО' },
              { id: 'WINTER', label: 'ЗИМА' },
              { id: 'FAILURE_TEST', label: 'АВАРИЯ' }
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => handleModeSelect(m.id)}
                style={{
                  padding: '5px 10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '11px',
                  fontWeight: currentMode === m.id ? 700 : 500,
                  background: currentMode === m.id ? '#ffffff' : 'transparent',
                  color: currentMode === m.id ? '#000000' : 'var(--text-secondary)',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {m.label}
              </button>
            ))}
          </div>

          <button
            onClick={handlePowerToggle}
            className={`btn ${isRunning ? 'btn-secondary' : 'btn-primary'}`}
            style={{ fontWeight: 600 }}
          >
            <Power size={14} /> {isRunning ? 'Остановить' : 'Запустить'}
          </button>
        </div>
      </div>

      {activeTab === 'scada' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            <div className="shadcn-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>Температура приточного воздуха</span>
                <Thermometer size={18} color="#ffffff" />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                <span className="mono" style={{ fontSize: '36px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.03em' }}>
                  {telemetry.supply_temperature.toFixed(1)}
                </span>
                <span style={{ fontSize: '18px', color: 'var(--text-muted)' }}>°C</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                <span>Уставка: <strong style={{ color: '#ffffff' }}>{telemetry.target_temperature.toFixed(1)} °C</strong></span>
                <span>Отклонение: <strong style={{ color: Math.abs(telemetry.supply_temperature - telemetry.target_temperature) > 3 ? '#ef4444' : '#ffffff' }}>
                  {(telemetry.supply_temperature - telemetry.target_temperature).toFixed(1)} °C
                </strong></span>
              </div>
            </div>

            <div className="shadcn-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>Наружный воздух и влажность</span>
                <Wind size={18} color="#ffffff" />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                <span className="mono" style={{ fontSize: '36px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.03em' }}>
                  {telemetry.outdoor_temperature.toFixed(1)}
                </span>
                <span style={{ fontSize: '18px', color: 'var(--text-muted)' }}>°C</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                <span>Относительная влажность: <strong style={{ color: '#ffffff' }}>{telemetry.humidity.toFixed(1)}%</strong></span>
                <span>Режим: <strong style={{ color: '#ffffff' }}>{currentMode}</strong></span>
              </div>
            </div>

            <div className="shadcn-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>Приточный и вытяжной вентиляторы</span>
                <Fan
                  size={18}
                  color="#ffffff"
                  style={{
                    animation: isRunning && telemetry.supply_fan_rpm > 50 ? `spin ${fanSpinSpeedSec}s linear infinite` : 'none',
                    transformOrigin: 'center'
                  }}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                <span className="mono" style={{ fontSize: '36px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.03em' }}>
                  {telemetry.supply_fan_rpm}
                </span>
                <span style={{ fontSize: '18px', color: 'var(--text-muted)' }}>об/мин</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                <span>Приток: <strong style={{ color: '#ffffff' }}>{telemetry.supply_fan_rpm} об/мин</strong></span>
                <span>Вытяжка: <strong style={{ color: '#ffffff' }}>{telemetry.exhaust_fan_rpm} об/мин</strong></span>
              </div>
            </div>

            <div className={`shadcn-card ${telemetry.filter_pressure > 250 ? 'alarm-pulsing-box' : ''}`}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>Перепад давления на фильтре (ΔP)</span>
                <Activity size={18} color={telemetry.filter_pressure > 250 ? "#ef4444" : "#ffffff"} />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                <span className="mono" style={{ fontSize: '36px', fontWeight: 800, color: telemetry.filter_pressure > 250 ? "#ef4444" : "#ffffff", letterSpacing: '-0.03em' }}>
                  {telemetry.filter_pressure.toFixed(1)}
                </span>
                <span style={{ fontSize: '18px', color: 'var(--text-muted)' }}>Па</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                <span>Засоренность: <strong style={{ color: '#ffffff' }}>{telemetry.filter_dirty_percent.toFixed(1)}%</strong></span>
                <span>Предел аварии: <strong style={{ color: '#ffffff' }}>250 Па</strong></span>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
            <div className="shadcn-card" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)' }}>Мощность вентиляторов P</span>
                <Zap size={16} color="#ffffff" />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                <span className="mono" style={{ fontSize: '26px', fontWeight: 800, color: '#ffffff' }}>
                  {(telemetry.instant_power_kw ?? 0).toFixed(2)}
                </span>
                <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>кВт</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
                Расход: <strong style={{ color: '#ffffff' }}>{(telemetry.total_energy_kwh ?? 0).toFixed(2)} кВт·ч</strong>
              </div>
            </div>

            <div className="shadcn-card" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)' }}>Энергоэффективность COP</span>
                <Gauge size={16} color="#ffffff" />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                <span className="mono" style={{ fontSize: '26px', fontWeight: 800, color: '#ffffff' }}>
                  {(telemetry.cop_efficiency ?? 0).toFixed(1)}
                </span>
                <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>к.п.д.</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
                Класс: <strong style={{ color: '#ffffff' }}>{(telemetry.cop_efficiency ?? 0) >= 3.0 ? 'A++ High Eco' : 'A Normal'}</strong>
              </div>
            </div>

            <div className="shadcn-card" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)' }}>Ресурс фильтра RUL</span>
                <Cpu size={16} color="#ffffff" />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                <span className="mono" style={{ fontSize: '26px', fontWeight: 800, color: (telemetry.filter_rul_hours ?? 0) < 48 ? '#ef4444' : '#ffffff' }}>
                  {(telemetry.filter_rul_hours ?? 0).toFixed(0)}
                </span>
                <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>часов</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
                Прогноз: <strong style={{ color: '#ffffff' }}>{(telemetry.filter_rul_hours ?? 0) > 72 ? 'Штатный ресурс' : 'Скорая замена'}</strong>
              </div>
            </div>

            <div className="shadcn-card" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)' }}>Индекс здоровья (Health)</span>
                <Activity size={16} color="#ffffff" />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                <span className="mono" style={{ fontSize: '26px', fontWeight: 800, color: (telemetry.health_index ?? 0) < 70 ? '#ef4444' : '#ffffff' }}>
                  {(telemetry.health_index ?? 0).toFixed(0)}
                </span>
                <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>%</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
                Вибрация: <strong style={{ color: '#ffffff' }}>{(telemetry.bearing_vibration ?? 0).toFixed(2)} мм/с (ISO 10816)</strong>
              </div>
            </div>
          </div>

          <div className="shadcn-card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>Мнемосхема технологического процесса ПВУ (SCADA)</h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Тракт движения воздуха от наружного воздухозабора до приточного воздуховода</p>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={handleFilterReset} className="btn btn-outline" style={{ fontSize: '12px' }}>
                  <RotateCcw size={13} /> Замена / Очистка фильтра
                </button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '14px', position: 'relative' }}>
              <div style={{ background: '#18181b', borderRadius: 'var(--radius-md)', padding: '16px', border: '1px solid var(--border-medium)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>01. Воздухозабор</div>
                <div style={{ fontSize: '15px', fontWeight: 700, margin: '6px 0', color: '#ffffff' }}>Воздушная заслонка</div>
                <div className="mono" style={{ fontSize: '22px', fontWeight: 700, color: '#ffffff' }}>{telemetry.damper_position.toFixed(0)}%</div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
                  <div style={{ width: `${telemetry.damper_position}%`, height: '100%', background: '#ffffff', transition: 'width 0.5s ease' }} />
                </div>
              </div>

              <div style={{ background: '#18181b', borderRadius: 'var(--radius-md)', padding: '16px', border: `1px solid ${telemetry.filter_pressure > 250 ? '#ef4444' : 'var(--border-medium)'}` }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>02. Фильтрация</div>
                <div style={{ fontSize: '15px', fontWeight: 700, margin: '6px 0', color: '#ffffff' }}>Карманный фильтр F7</div>
                <div className="mono" style={{ fontSize: '22px', fontWeight: 700, color: telemetry.filter_pressure > 250 ? '#ef4444' : '#ffffff' }}>
                  {telemetry.filter_pressure.toFixed(1)} <span style={{ fontSize: '14px' }}>Па</span>
                </div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(100, (telemetry.filter_pressure / 250) * 100)}%`, height: '100%', background: telemetry.filter_pressure > 250 ? '#ef4444' : '#ffffff', transition: 'width 0.5s ease' }} />
                </div>
              </div>

              <div style={{ background: '#18181b', borderRadius: 'var(--radius-md)', padding: '16px', border: '1px solid var(--border-medium)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>03. Охлаждение</div>
                <div style={{ fontSize: '15px', fontWeight: 700, margin: '6px 0', color: '#ffffff' }}>Водяной охладитель</div>
                <div className="mono" style={{ fontSize: '22px', fontWeight: 700, color: '#ffffff' }}>{telemetry.cooling_valve.toFixed(0)}%</div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
                  <div style={{ width: `${telemetry.cooling_valve}%`, height: '100%', background: '#ffffff', transition: 'width 0.5s ease' }} />
                </div>
              </div>

              <div style={{ background: '#18181b', borderRadius: 'var(--radius-md)', padding: '16px', border: '1px solid var(--border-medium)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>04. Подогрев</div>
                <div style={{ fontSize: '15px', fontWeight: 700, margin: '6px 0', color: '#ffffff' }}>Водяной калорифер</div>
                <div className="mono" style={{ fontSize: '22px', fontWeight: 700, color: '#ffffff' }}>{telemetry.heating_valve.toFixed(0)}%</div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
                  <div style={{ width: `${telemetry.heating_valve}%`, height: '100%', background: '#ffffff', transition: 'width 0.5s ease' }} />
                </div>
              </div>

              <div style={{ background: '#18181b', borderRadius: 'var(--radius-md)', padding: '16px', border: '1px solid var(--border-medium)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>05. Аэродинамика</div>
                <div style={{ fontSize: '15px', fontWeight: 700, margin: '6px 0', color: '#ffffff' }}>Приточный вентилятор (ПЧ)</div>
                <div className="mono" style={{ fontSize: '22px', fontWeight: 700, color: '#ffffff' }}>{telemetry.supply_fan_rpm} <span style={{ fontSize: '14px' }}>об/мин</span></div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', marginTop: '10px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(100, (telemetry.supply_fan_rpm / 1450) * 100)}%`, height: '100%', background: '#ffffff', transition: 'width 0.5s ease' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'control' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
          <div className="shadcn-card">
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff', marginBottom: '8px' }}>Климатические режимы работы</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>Выберите сценарий окружающей среды для симуляции физики теплообмена</p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { id: 'NORMAL', title: 'Штатный режим', desc: 'Наружный воздух 15 °C, уставка 21.5 °C. Пропорциональное ПИД-балансирование.', icon: Wind },
                { id: 'SUMMER', title: 'Летний режим (Жара)', desc: 'Наружный воздух 32 °C. Активное водяное охлаждение и осушение воздуха.', icon: Flame },
                { id: 'WINTER', title: 'Зимний режим (Мороз)', desc: 'Наружный воздух -15 °C. Активный водяной подогрев и защита от замораживания.', icon: Snowflake },
                { id: 'FAILURE_TEST', title: 'Тест аварийного сценария', desc: 'Искусственное засорение фильтра (> 250 Па) и останов двигателя для тестирования Rule Engine.', icon: AlertTriangle },
              ].map((p) => {
                const IconComponent = p.icon;
                const isSelected = currentMode === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => handleModeSelect(p.id)}
                    style={{
                      padding: '16px',
                      borderRadius: 'var(--radius-md)',
                      background: isSelected ? '#ffffff' : '#18181b',
                      color: isSelected ? '#000000' : '#ffffff',
                      border: `1px solid ${isSelected ? '#ffffff' : 'var(--border-subtle)'}`,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: isSelected ? '#000000' : '#27272a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <IconComponent size={18} color={isSelected ? '#ffffff' : '#ffffff'} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '14px' }}>{p.title}</div>
                        <div style={{ fontSize: '12px', color: isSelected ? '#52525b' : 'var(--text-secondary)', marginTop: '2px' }}>{p.desc}</div>
                      </div>
                    </div>
                    <ChevronRight size={18} color={isSelected ? '#000000' : 'var(--text-muted)'} />
                  </div>
                );
              })}
            </div>
          </div>

          <div className="shadcn-card">
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff', marginBottom: '8px' }}>Ручные уставки и сервисные команды</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>Точная подстройка параметров задания и аварийные переключатели</p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 600 }}>Задание температуры притока</span>
                  <span className="mono" style={{ fontSize: '16px', fontWeight: 700 }}>{targetInput.toFixed(1)} °C</span>
                </div>
                <input
                  type="range"
                  min="16"
                  max="30"
                  step="0.5"
                  value={targetInput}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    setTargetInput(val);
                    sendControl({ target_temperature: val });
                  }}
                  style={{ width: '100%', accentColor: '#ffffff', cursor: 'pointer' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  <span>Мин: 16.0 °C</span>
                  <span>Макс: 30.0 °C</span>
                </div>
              </div>

              <div style={{ paddingTop: '16px', borderTop: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>Сервис и аварийные команды</span>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <button onClick={handleFilterReset} className="btn btn-secondary" style={{ flex: 1 }}>
                    <RotateCcw size={15} /> Заменить фильтр F7
                  </button>
                  <button onClick={handlePowerToggle} className={`btn ${isRunning ? 'btn-destructive' : 'btn-primary'}`} style={{ flex: 1 }}>
                    <Power size={15} /> {isRunning ? 'Аварийный останов' : 'Запустить установку'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="shadcn-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>Двусторонний Digital Twin RPC (ThingsBoard → MQTT → Контроллер)</h2>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Управление контроллером через шину RPC ThingsBoard по протоколу MQTT (<code className="mono">v1/devices/me/rpc/request/+</code>)
                </p>
              </div>
              <span className="badge badge-outline mono">QoS 1 Server-Side RPC</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '10px', marginTop: '16px' }}>
              <button
                onClick={() => sendThingsBoardRPC('setTargetTemperature', targetInput)}
                disabled={rpcLoading}
                className="btn btn-outline"
                style={{ justifyContent: 'center' }}
              >
                RPC: Задать T={targetInput.toFixed(1)}°C
              </button>
              <button
                onClick={() => sendThingsBoardRPC('setPower', !isRunning)}
                disabled={rpcLoading}
                className="btn btn-outline"
                style={{ justifyContent: 'center' }}
              >
                RPC: {isRunning ? 'Останов (Power Off)' : 'Пуск (Power On)'}
              </button>
              <button
                onClick={() => sendThingsBoardRPC('resetFilter', {})}
                disabled={rpcLoading}
                className="btn btn-outline"
                style={{ justifyContent: 'center' }}
              >
                RPC: Сброс фильтра F7
              </button>
              <button
                onClick={() => sendThingsBoardRPC('setMode', 'SUMMER')}
                disabled={rpcLoading}
                className="btn btn-outline"
                style={{ justifyContent: 'center' }}
              >
                RPC: Режим ЛЕТО
              </button>
              <button
                onClick={() => sendThingsBoardRPC('setMode', 'WINTER')}
                disabled={rpcLoading}
                className="btn btn-outline"
                style={{ justifyContent: 'center' }}
              >
                RPC: Режим ЗИМА
              </button>
            </div>

            {rpcLog && (
              <div style={{ marginTop: '16px', padding: '12px 14px', background: '#09090b', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 600 }}>
                  Терминал ThingsBoard RPC
                </div>
                <pre className="mono" style={{ fontSize: '12px', color: rpcLog.includes('ERR') ? '#ef4444' : '#ffffff', margin: 0, whiteSpace: 'pre-wrap' }}>
                  {rpcLog}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'charts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="shadcn-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff' }}>Временные ряды температур (последние 30 точек)</h2>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Приточный воздух vs Уставка задания vs Наружный воздух</p>
              </div>
              <div style={{ display: 'flex', gap: '16px', fontSize: '12px', flexWrap: 'wrap' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ffffff' }}>
                  <span style={{ width: '10px', height: '3px', background: '#ffffff', display: 'inline-block' }} /> Приточный воздух
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
                  <span style={{ width: '10px', height: '3px', background: '#a1a1aa', display: 'inline-block', borderStyle: 'dashed' }} /> Уставка задания
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)' }}>
                  <span style={{ width: '10px', height: '3px', background: '#52525b', display: 'inline-block' }} /> Наружный воздух
                </span>
              </div>
            </div>

            <div style={{ width: '100%', height: '220px', position: 'relative' }}>
              <svg width="100%" height="100%" viewBox="0 0 800 200" preserveAspectRatio="none" style={{ overflow: 'visible' }}>
                {[40, 80, 120, 160].map((y) => (
                  <line key={y} x1="0" y1={y} x2="800" y2={y} stroke="rgba(255,255,255,0.06)" strokeWidth="1" strokeDasharray="3,3" />
                ))}

                {history.length > 1 && (
                  <>
                    <polyline
                      fill="none"
                      stroke="#ffffff"
                      strokeWidth="2.5"
                      points={history.map((h, i) => {
                        const x = (i / (history.length - 1)) * 800;
                        const y = 200 - ((h.supply_temperature - 10) / 30) * 180;
                        return `${x},${Math.max(10, Math.min(190, y))}`;
                      }).join(' ')}
                    />

                    <polyline
                      fill="none"
                      stroke="#a1a1aa"
                      strokeWidth="1.5"
                      strokeDasharray="4,4"
                      points={history.map((h, i) => {
                        const x = (i / (history.length - 1)) * 800;
                        const y = 200 - ((h.target_temperature - 10) / 30) * 180;
                        return `${x},${Math.max(10, Math.min(190, y))}`;
                      }).join(' ')}
                    />

                    <polyline
                      fill="none"
                      stroke="#52525b"
                      strokeWidth="1.5"
                      points={history.map((h, i) => {
                        const x = (i / (history.length - 1)) * 800;
                        const y = 200 - ((h.outdoor_temperature - 10) / 30) * 180;
                        return `${x},${Math.max(10, Math.min(190, y))}`;
                      }).join(' ')}
                    />
                  </>
                )}
              </svg>
            </div>
          </div>

          <div className="shadcn-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff' }}>Динамика перепада давления на фильтре (ΔP)</h2>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Порог 250 Па активирует тревогу FILTER_DIRTY в Rule Engine</p>
              </div>
              <span className="badge badge-outline">Порог аварии: 250 Па</span>
            </div>

            <div style={{ width: '100%', height: '160px', position: 'relative' }}>
              <svg width="100%" height="100%" viewBox="0 0 800 160" preserveAspectRatio="none">
                <line x1="0" y1="32" x2="800" y2="32" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="5,5" />
                <text x="10" y="24" fill="#ef4444" fontSize="10" fontFamily="monospace">ПОРОГ АВАРИИ: 250 Па</text>

                {history.length > 1 && (
                  <polyline
                    fill="none"
                    stroke="#ffffff"
                    strokeWidth="2"
                    points={history.map((h, i) => {
                      const x = (i / (history.length - 1)) * 800;
                      const y = 160 - (h.filter_pressure / 300) * 140;
                      return `${x},${Math.max(10, Math.min(150, y))}`;
                    }).join(' ')}
                  />
                )}
              </svg>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'alarms' && (
        <div className="shadcn-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>Журнал аварийных событий и состояние Rule Engine</h2>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Синхронизировано с логикой оповещений ThingsBoard Rule Chain</p>
            </div>
            <span className="badge badge-outline">Активных событий: {alarms.length}</span>
          </div>

          {alarms.length === 0 ? (
            <div style={{ padding: '48px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
              <ShieldCheck size={42} color="#ffffff" style={{ margin: '0 auto 12px', opacity: 0.8 }} />
              <div style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff' }}>Все системы работают штатно</div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>На установке HVAC-01 активных аварий не зафиксировано</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {alarms.map((a) => (
                <div
                  key={a.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '14px 18px',
                    borderRadius: 'var(--radius-md)',
                    background: '#18181b',
                    border: `1px solid ${a.severity === 'CRITICAL' ? '#ef4444' : 'rgba(255,255,255,0.15)'}`,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <AlertTriangle size={18} color={a.severity === 'CRITICAL' ? '#ef4444' : '#ffffff'} />
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <strong className="mono" style={{ fontSize: '13px', color: '#ffffff' }}>{a.type}</strong>
                        <span className={`badge ${a.severity === 'CRITICAL' ? 'badge-alarm' : 'badge-stopped'}`}>{a.severity}</span>
                        <span className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{a.timestamp}</span>
                      </div>
                      <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>{a.message}</div>
                    </div>
                  </div>
                  <button onClick={handleFilterReset} className="btn btn-outline" style={{ fontSize: '12px' }}>
                    Квитировать / Сброс
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'mqtt' && (
        <div className="shadcn-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>Инспектор пакетов телеметрии MQTT</h2>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Топик: <strong className="mono" style={{ color: '#ffffff' }}>v1/devices/me/telemetry</strong></p>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={handleCopyJson} className="btn btn-outline">
                {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />} {copied ? 'Скопировано' : 'Копировать JSON'}
              </button>
              <button onClick={handleExportCsv} className="btn btn-primary">
                <Download size={14} /> Экспорт CSV
              </button>
            </div>
          </div>

          <pre
            className="mono"
            style={{
              background: '#09090b',
              padding: '18px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontSize: '13px',
              color: '#ffffff',
              overflowX: 'auto',
              lineHeight: '1.6'
            }}
          >
            {JSON.stringify(telemetry, null, 2)}
          </pre>
        </div>
      )}

      {showAuthModal && (
        <div className="modal-overlay" onClick={() => setShowAuthModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#ffffff', color: '#000000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Lock size={18} />
              </div>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>Портал ThingsBoard CE</h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Вход под учетной записью Tenant Administrator</p>
              </div>
            </div>

            {authError && (
              <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-md)', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontSize: '12px', marginBottom: '16px' }}>
                {authError}
              </div>
            )}

            <form onSubmit={handleThingsboardLogin} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>Email пользователя</label>
                <input
                  type="email"
                  value={tbUsername}
                  onChange={(e) => setTbUsername(e.target.value)}
                  className="shadcn-input"
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>Пароль</label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={tbPassword}
                    onChange={(e) => setTbPassword(e.target.value)}
                    className="shadcn-input"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                <button
                  type="button"
                  onClick={() => { setTbUsername('tenant@thingsboard.org'); setTbPassword('tenant'); }}
                  className="btn btn-outline"
                  style={{ flex: 1, fontSize: '11px', padding: '5px' }}
                >
                  Администратор тенанта
                </button>
                <button
                  type="button"
                  onClick={() => { setTbUsername('sysadmin@thingsboard.org'); setTbPassword('sysadmin'); }}
                  className="btn btn-outline"
                  style={{ flex: 1, fontSize: '11px', padding: '5px' }}
                >
                  Системный админ
                </button>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                <button type="button" onClick={() => setShowAuthModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Отмена
                </button>
                <button type="submit" disabled={authLoading} className="btn btn-primary" style={{ flex: 2 }}>
                  {authLoading ? 'Авторизация...' : 'Войти'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <footer style={{ marginTop: '40px', paddingTop: '20px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', color: 'var(--text-dim)', fontSize: '12px', flexWrap: 'wrap', gap: '10px' }}>
        <div>ORIONMETER Платформа промышленного IoT | ThingsBoard CE v4.2.1.1</div>
        <div>Время пакета телеметрии: <span className="mono" style={{ color: 'var(--text-secondary)' }}>{lastUpdated}</span></div>
      </footer>
    </div>
  );
}
