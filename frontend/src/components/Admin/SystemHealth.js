import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const ServiceCard = ({ name, status, responseTime, details, icon }) => {
  const isUp = status === 'up';
  return (
    <div data-testid={`health-card-${name}`} className={`rounded-xl border-2 p-5 transition-all duration-300 ${isUp ? 'border-emerald-200 bg-emerald-50/50' : 'border-red-200 bg-red-50/50'}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${isUp ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'}`}>
            {icon}
          </div>
          <div>
            <h3 className="font-bold text-gray-800">{name}</h3>
            <p className="text-xs text-gray-500">{details || '-'}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-block w-3 h-3 rounded-full animate-pulse ${isUp ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
          <span className={`text-sm font-semibold ${isUp ? 'text-emerald-700' : 'text-red-700'}`}>
            {isUp ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>
      {responseTime !== undefined && (
        <div className="flex items-center gap-1 text-xs text-gray-500 mt-2">
          <span>Response:</span>
          <span className="font-mono font-bold">{responseTime}ms</span>
        </div>
      )}
    </div>
  );
};

const CalibrationCard = ({ calibration }) => {
  if (!calibration) return null;

  const statusColors = {
    expired: 'border-emerald-200 bg-emerald-50/50',
    active: 'border-amber-200 bg-amber-50/50',
    disabled: 'border-gray-200 bg-gray-50/50',
  };

  const statusLabels = {
    expired: { text: 'Expired & Auto-Disabled', color: 'text-emerald-700', bg: 'bg-emerald-100' },
    active: { text: 'Active', color: 'text-amber-700', bg: 'bg-amber-100' },
    disabled: { text: 'Disabled', color: 'text-gray-700', bg: 'bg-gray-100' },
  };

  const st = statusLabels[calibration.status] || statusLabels.disabled;

  return (
    <div data-testid="calibration-status" className={`rounded-xl border-2 p-6 ${statusColors[calibration.status] || statusColors.disabled}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center text-lg bg-blue-100 text-blue-600">
            <i className="fas fa-sliders-h"></i>
          </div>
          <div>
            <h3 className="font-bold text-gray-800">October 2025 Calibration Mode</h3>
            <p className="text-xs text-gray-500">Deduction calculation adjustment period</p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-bold ${st.color} ${st.bg}`}>
          {st.text}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
        <div>
          <span className="text-gray-500">Window Start</span>
          <p className="font-bold">{calibration.window_from}</p>
        </div>
        <div>
          <span className="text-gray-500">Window End</span>
          <p className="font-bold">{calibration.window_to}</p>
        </div>
        <div>
          <span className="text-gray-500">Current Date</span>
          <p className="font-bold">{calibration.current_date}</p>
        </div>
        <div>
          <span className="text-gray-500">ENV Enabled</span>
          <p className="font-bold">{calibration.env_enabled ? 'Yes' : 'No'}</p>
        </div>
      </div>

      {calibration.status === 'expired' && (
        <div className="bg-emerald-100 border border-emerald-300 rounded-lg p-3 mb-3">
          <p className="text-emerald-800 text-sm font-medium">
            <i className="fas fa-check-circle mr-2"></i>
            Calibration mode has been automatically disabled. Current payroll cycles use standard deduction rates.
          </p>
        </div>
      )}

      {calibration.auto_off_logged && calibration.audit_entries?.length > 0 && (
        <div className="mt-3">
          <h4 className="text-sm font-bold text-gray-700 mb-2">
            <i className="fas fa-history mr-1"></i> Auto-Off Audit Log
          </h4>
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="min-w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Timestamp</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Period</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Note</th>
                </tr>
              </thead>
              <tbody>
                {calibration.audit_entries.map((entry, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-3 py-2 text-gray-600">{entry.created_at?.slice(0, 19) || '-'}</td>
                    <td className="px-3 py-2 text-gray-600 font-mono">{entry.payload?.period?.slice(0, 21) || '-'}</td>
                    <td className="px-3 py-2 text-gray-600">{entry.payload?.note || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!calibration.auto_off_logged && calibration.status === 'expired' && (
        <p className="text-sm text-gray-500 mt-2">
          <i className="fas fa-info-circle mr-1"></i>
          No audit entries yet. The auto-off log will be recorded when a payroll cycle beyond October 2025 is first calculated.
        </p>
      )}
    </div>
  );
};

const SystemHealth = () => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastCheck, setLastCheck] = useState(null);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/system/health-check`);
      setHealthData(res.data);
      setLastCheck(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Health check failed:', err);
      setHealthData({
        overall: 'down',
        services: {
          database: { status: 'down', details: 'Connection failed' },
          smtp: { status: 'down', details: 'Connection failed' },
          api: { status: 'down', details: 'Connection failed' },
        }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 60000);
    return () => clearInterval(interval);
  }, []);

  const services = healthData?.services || {};
  const overallUp = healthData?.overall === 'up';
  const upCount = Object.values(services).filter(s => s.status === 'up').length;
  const totalCount = Object.keys(services).length;

  const icons = {
    database: <i className="fas fa-database"></i>,
    smtp: <i className="fas fa-envelope"></i>,
    api: <i className="fas fa-server"></i>,
    storage: <i className="fas fa-hdd"></i>,
    auth: <i className="fas fa-shield-alt"></i>,
  };

  return (
    <div data-testid="system-health-page" className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">System Health</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time service monitoring</p>
        </div>
        <button
          data-testid="refresh-health-btn"
          onClick={fetchHealth}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all"
        >
          <i className={`fas fa-sync-alt ${loading ? 'animate-spin' : ''}`}></i>
          {loading ? 'Checking...' : 'Refresh'}
        </button>
      </div>

      {/* Overall Status Banner */}
      <div className={`rounded-xl p-6 text-center border-2 ${overallUp ? 'bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-200' : 'bg-gradient-to-r from-red-50 to-orange-50 border-red-200'}`}>
        <div className={`inline-flex items-center gap-3 px-6 py-3 rounded-full text-lg font-bold ${overallUp ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
          <span className={`w-4 h-4 rounded-full animate-pulse ${overallUp ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
          {overallUp ? 'All services are running normally' : 'Some services have issues'}
        </div>
        <p className="text-sm text-gray-500 mt-3">
          {upCount} of {totalCount} services online
          {lastCheck && ` | Last check: ${lastCheck}`}
        </p>
      </div>

      {/* Services Grid */}
      {loading && !healthData ? (
        <div className="text-center py-12">
          <i className="fas fa-spinner fa-spin text-4xl text-blue-500 mb-4"></i>
          <p className="text-gray-500">Checking services...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(services).map(([key, svc]) => (
            <ServiceCard
              key={key}
              name={svc.name || key}
              status={svc.status}
              responseTime={svc.response_time}
              details={svc.details}
              icon={icons[key] || <i className="fas fa-cog"></i>}
            />
          ))}
        </div>
      )}

      {/* October Calibration Status */}
      {healthData?.calibration && (
        <CalibrationCard calibration={healthData.calibration} />
      )}

      {/* System Info */}
      {healthData?.system_info && (
        <div className="bg-gray-50 rounded-xl border p-5">
          <h3 className="font-bold text-gray-700 mb-3">
            <i className="fas fa-info-circle mr-2"></i>
            System Information
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Version</span>
              <p className="font-bold">{healthData.system_info.version || '1.0'}</p>
            </div>
            <div>
              <span className="text-gray-500">Environment</span>
              <p className="font-bold">{healthData.system_info.environment || 'production'}</p>
            </div>
            <div>
              <span className="text-gray-500">Active Employees</span>
              <p className="font-bold">{healthData.system_info.employee_count || 0}</p>
            </div>
            <div>
              <span className="text-gray-500">Uptime</span>
              <p className="font-bold">{healthData.system_info.uptime || '-'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemHealth;
