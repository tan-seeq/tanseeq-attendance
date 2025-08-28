import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ClockIcon, 
  BuildingOfficeIcon, 
  DocumentTextIcon,
  CurrencyDollarIcon,
  UserGroupIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';

const WorkReportsDashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [setupLoading, setSetupLoading] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/work-reports/dashboard`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setDashboard(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const setupSampleData = async () => {
    if (!window.confirm('هل تريد إنشاء بيانات نموذجية للاختبار؟\n\nسيتم إنشاء:\n• عميل نموذجي\n• 3 سجلات عمل\n• بيانات للتقارير')) {
      return;
    }
    
    try {
      setSetupLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(`${backendUrl}/api/work-reports/setup-sample-data`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(`✅ تم إنشاء البيانات النموذجية بنجاح!\n\n📊 تم إنشاء:\n• العميل: ${response.data.sample_client.name}\n• سجلات العمل: ${response.data.work_logs_created}\n• إجمالي الإيرادات: AED ${response.data.total_revenue.toFixed(2)}\n\nيمكنك الآن اختبار التقارير والتصدير!`);
      
      // Refresh dashboard
      fetchDashboard();
    } catch (err) {
      console.error('Error setting up sample data:', err);
      alert('❌ فشل في إنشاء البيانات النموذجية\n\nيرجى المحاولة مرة أخرى');
    } finally {
      setSetupLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  const stats = [
    {
      name: 'Total Clients',
      value: dashboard?.total_clients || 0,
      icon: BuildingOfficeIcon,
      color: 'bg-blue-500',
      textColor: 'text-blue-600'
    },
    {
      name: 'Today\'s Work Logs',
      value: dashboard?.today_logs || 0,
      icon: ClockIcon,
      color: 'bg-green-500',
      textColor: 'text-green-600'
    },
    {
      name: 'This Month\'s Logs',
      value: dashboard?.month_logs || 0,
      icon: DocumentTextIcon,
      color: 'bg-purple-500',
      textColor: 'text-purple-600'
    },
    {
      name: 'Billable Hours (Month)',
      value: `${dashboard?.total_billable_hours || 0}h`,
      icon: CalendarIcon,
      color: 'bg-orange-500',
      textColor: 'text-orange-600'
    },
    {
      name: 'Revenue (Month)',
      value: `AED ${dashboard?.total_revenue || 0}`,
      icon: CurrencyDollarIcon,
      color: 'bg-indigo-500',
      textColor: 'text-indigo-600'
    }
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Work Reports Dashboard</h1>
        <p className="text-gray-600 mt-2">Daily Work Report + Clients Master</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`${stat.color} rounded-md p-3`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <p className={`text-2xl font-bold ${stat.textColor}`}>{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Work Logs</h2>
        </div>
        <div className="p-6">
          {dashboard?.recent_activity?.length > 0 ? (
            <div className="space-y-4">
              {dashboard.recent_activity.map((activity, index) => (
                <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{activity.client_name}</h3>
                    <p className="text-sm text-gray-500">{activity.activity_name}</p>
                    <p className="text-xs text-gray-400">
                      {activity.date} • {activity.duration_minutes} minutes
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Complete
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No recent activity</h3>
              <p className="mt-1 text-sm text-gray-500">
                Start by creating your first work log entry.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button 
              onClick={() => window.location.href = '/work-reports/logs'}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-md transition-colors text-sm sm:text-base"
            >
              Create Work Log
            </button>
            <button 
              onClick={() => window.location.href = '/work-reports/clients'}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-md transition-colors text-sm sm:text-base"
            >
              Add New Client
            </button>
            <button 
              onClick={() => window.location.href = '/work-reports/reports'}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-4 rounded-md transition-colors text-sm sm:text-base"
            >
              View Reports
            </button>
            {(dashboard?.total_clients === 0 || dashboard?.month_logs === 0) && (
              <button 
                onClick={setupSampleData}
                disabled={setupLoading}
                className="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-md transition-colors text-sm sm:text-base"
              >
                {setupLoading ? 'جاري الإنشاء...' : 'إنشاء بيانات نموذجية'}
              </button>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Database</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Connected
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">User Role</span>
              <span className="text-sm font-medium text-gray-900 capitalize">
                {dashboard?.user_role || 'User'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">This Month</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Work Logs</span>
              <span className="text-sm font-bold text-gray-900">
                {dashboard?.month_logs || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Billable Hours</span>
              <span className="text-sm font-bold text-gray-900">
                {dashboard?.total_billable_hours || 0}h
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Total Revenue</span>
              <span className="text-sm font-bold text-green-600">
                AED {dashboard?.total_revenue || 0}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkReportsDashboard;