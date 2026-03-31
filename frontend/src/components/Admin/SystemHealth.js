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
            {isUp ? 'متصل' : 'غير متصل'}
          </span>
        </div>
      </div>
      {responseTime !== undefined && (
        <div className="flex items-center gap-1 text-xs text-gray-500 mt-2">
          <span>زمن الاستجابة:</span>
          <span className="font-mono font-bold">{responseTime}ms</span>
        </div>
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
      setLastCheck(new Date().toLocaleTimeString('ar-SA'));
    } catch (err) {
      console.error('Health check failed:', err);
      setHealthData({
        overall: 'down',
        services: {
          database: { status: 'down', details: 'فشل الاتصال' },
          smtp: { status: 'down', details: 'فشل الاتصال' },
          api: { status: 'down', details: 'فشل الاتصال' },
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
    <div data-testid="system-health-page" className="max-w-4xl mx-auto space-y-6" dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">صحة النظام</h1>
          <p className="text-sm text-gray-500 mt-1">مراقبة حالة الخدمات في الوقت الفعلي</p>
        </div>
        <button
          data-testid="refresh-health-btn"
          onClick={fetchHealth}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all"
        >
          <i className={`fas fa-sync-alt ${loading ? 'animate-spin' : ''}`}></i>
          {loading ? 'جاري الفحص...' : 'فحص الآن'}
        </button>
      </div>

      {/* Overall Status Banner */}
      <div className={`rounded-xl p-6 text-center border-2 ${overallUp ? 'bg-gradient-to-l from-emerald-50 to-green-50 border-emerald-200' : 'bg-gradient-to-l from-red-50 to-orange-50 border-red-200'}`}>
        <div className={`inline-flex items-center gap-3 px-6 py-3 rounded-full text-lg font-bold ${overallUp ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
          <span className={`w-4 h-4 rounded-full animate-pulse ${overallUp ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
          {overallUp ? 'جميع الخدمات تعمل بشكل طبيعي' : 'بعض الخدمات تواجه مشاكل'}
        </div>
        <p className="text-sm text-gray-500 mt-3">
          {upCount} من {totalCount} خدمات متصلة
          {lastCheck && ` | آخر فحص: ${lastCheck}`}
        </p>
      </div>

      {/* Services Grid */}
      {loading && !healthData ? (
        <div className="text-center py-12">
          <i className="fas fa-spinner fa-spin text-4xl text-blue-500 mb-4"></i>
          <p className="text-gray-500">جاري فحص الخدمات...</p>
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

      {/* System Info */}
      {healthData?.system_info && (
        <div className="bg-gray-50 rounded-xl border p-5">
          <h3 className="font-bold text-gray-700 mb-3">
            <i className="fas fa-info-circle ml-2"></i>
            معلومات النظام
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">الإصدار</span>
              <p className="font-bold">{healthData.system_info.version || '1.0'}</p>
            </div>
            <div>
              <span className="text-gray-500">بيئة التشغيل</span>
              <p className="font-bold">{healthData.system_info.environment || 'production'}</p>
            </div>
            <div>
              <span className="text-gray-500">عدد الموظفين</span>
              <p className="font-bold">{healthData.system_info.employee_count || 0}</p>
            </div>
            <div>
              <span className="text-gray-500">وقت التشغيل</span>
              <p className="font-bold">{healthData.system_info.uptime || '-'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemHealth;
