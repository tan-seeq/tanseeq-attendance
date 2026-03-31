import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { ArrowPathIcon, ServerIcon, ClockIcon, UserGroupIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LiveMonitoring = () => {
  const [metrics, setMetrics] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchMetrics = useCallback(async () => {
    try {
      const [metricsRes, logsRes] = await Promise.all([
        axios.get(`${API}/live/metrics`),
        axios.get(`${API}/live/logs`)
      ]);
      setMetrics(metricsRes.data.metrics);
      setLogs(logsRes.data.lines || []);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchMetrics, 5000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, fetchMetrics]);

  const getStatusColor = (code) => {
    if (code >= 200 && code < 300) return 'text-green-600';
    if (code >= 400 && code < 500) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>;

  return (
    <div className="p-6 max-w-7xl mx-auto" data-testid="live-monitoring-page">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">لوحة المراقبة المباشرة</h2>
        <div className="flex items-center space-x-3 space-x-reverse">
          <label className="flex items-center space-x-2 space-x-reverse text-sm">
            <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} className="h-4 w-4" />
            <span>تحديث تلقائي (5 ثوانٍ)</span>
          </label>
          <button onClick={fetchMetrics} className="flex items-center px-3 py-1.5 bg-blue-100 text-blue-700 rounded-md text-sm hover:bg-blue-200"
            data-testid="refresh-metrics">
            <ArrowPathIcon className="h-4 w-4 ml-1" /> تحديث
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm border p-4" data-testid="metric-total-requests">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">إجمالي الطلبات</p>
              <p className="text-2xl font-bold text-gray-800">{metrics?.total_requests || 0}</p>
            </div>
            <ServerIcon className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4" data-testid="metric-success-rate">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">نسبة النجاح</p>
              <p className="text-2xl font-bold text-green-600">
                {metrics?.total_requests > 0 ? Math.round(((metrics?.success_count || 0) / metrics.total_requests) * 100) : 100}%
              </p>
            </div>
            <CheckCircleIcon className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4" data-testid="metric-avg-response">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">متوسط الاستجابة</p>
              <p className="text-2xl font-bold text-gray-800">{Math.round(metrics?.avg_response_ms || 0)} ms</p>
            </div>
            <ClockIcon className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4" data-testid="metric-errors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">الأخطاء</p>
              <p className="text-2xl font-bold text-red-600">{metrics?.error_count || 0}</p>
            </div>
            <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 space-x-reverse mb-4 bg-gray-100 rounded-lg p-1">
        {[
          { id: 'overview', label: 'نظرة عامة' },
          { id: 'endpoints', label: 'نقاط النهاية' },
          { id: 'logs', label: 'السجلات' }
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-600 hover:text-gray-800'
            }`} data-testid={`live-tab-${tab.id}`}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="bg-white rounded-lg shadow-sm border p-6" data-testid="overview-section">
          <h3 className="text-lg font-semibold mb-4">حالة النظام</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-2">توزيع رموز الحالة</h4>
              <div className="space-y-2">
                {Object.entries(metrics?.status_codes || {}).map(([code, count]) => (
                  <div key={code} className="flex items-center justify-between">
                    <span className={`text-sm font-mono ${getStatusColor(parseInt(code))}`}>HTTP {code}</span>
                    <div className="flex items-center">
                      <div className="w-32 bg-gray-200 rounded-full h-2 ml-2">
                        <div className={`h-2 rounded-full ${parseInt(code) < 300 ? 'bg-green-500' : parseInt(code) < 500 ? 'bg-yellow-500' : 'bg-red-500'}`}
                          style={{width: `${Math.min(100, (count / (metrics?.total_requests || 1)) * 100)}%`}} />
                      </div>
                      <span className="text-sm text-gray-600 w-12 text-left">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-2">توزيع طرق الطلب</h4>
              <div className="space-y-2">
                {Object.entries(metrics?.methods || {}).map(([method, count]) => (
                  <div key={method} className="flex items-center justify-between">
                    <span className="text-sm font-mono font-medium">{method}</span>
                    <span className="text-sm text-gray-600 bg-gray-100 px-2 py-0.5 rounded">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'endpoints' && (
        <div className="bg-white rounded-lg shadow-sm border p-6" data-testid="endpoints-section">
          <h3 className="text-lg font-semibold mb-4">أكثر نقاط النهاية استخداماً</h3>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">نقطة النهاية</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">الطلبات</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">متوسط الاستجابة</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {(metrics?.top_endpoints || []).map((ep, i) => (
                <tr key={i}>
                  <td className="px-4 py-3 text-sm font-mono">{ep.path}</td>
                  <td className="px-4 py-3 text-sm">{ep.count}</td>
                  <td className="px-4 py-3 text-sm">{Math.round(ep.avg_ms || 0)} ms</td>
                </tr>
              ))}
              {(!metrics?.top_endpoints || metrics.top_endpoints.length === 0) && (
                <tr><td colSpan="3" className="px-4 py-8 text-center text-gray-400">لا توجد بيانات بعد</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="bg-white rounded-lg shadow-sm border p-6" data-testid="logs-section">
          <h3 className="text-lg font-semibold mb-4">آخر السجلات</h3>
          <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto font-mono text-xs">
            {logs.length === 0 ? (
              <p className="text-gray-500">لا توجد سجلات</p>
            ) : (
              logs.slice(-50).reverse().map((line, i) => (
                <div key={i} className="text-green-400 py-0.5 border-b border-gray-800">{line}</div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveMonitoring;
