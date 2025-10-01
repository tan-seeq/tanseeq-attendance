import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  DocumentArrowDownIcon,
  CalendarIcon,
  UserGroupIcon,
  ChartBarIcon,
  ClockIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';

const ReportsDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });
  const [selectedClient, setSelectedClient] = useState('');
  const [reportType, setReportType] = useState('daily');

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchClients();
    fetchAnalytics();
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [dateRange, selectedClient]);

  const fetchClients = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/work-reports/clients`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClients(response.data);
    } catch (err) {
      console.error('Error fetching clients:', err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Get work logs for analytics
      const queryParams = new URLSearchParams();
      if (dateRange.start_date) queryParams.append('start_date', dateRange.start_date);
      if (dateRange.end_date) queryParams.append('end_date', dateRange.end_date);
      if (selectedClient) queryParams.append('client_id', selectedClient);
      
      const response = await axios.get(`${backendUrl}/api/work-reports/logs?${queryParams}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const workLogs = response.data;
      
      // Calculate analytics
      const totalHours = workLogs.reduce((acc, log) => acc + (log.duration_minutes || 0), 0) / 60;
      const billableHours = workLogs.filter(log => log.is_billable).reduce((acc, log) => acc + (log.duration_minutes || 0), 0) / 60;
      const totalRevenue = workLogs.filter(log => log.is_billable).reduce((acc, log) => acc + (log.total_amount || 0), 0);
      const avgHourlyRate = billableHours > 0 ? totalRevenue / billableHours : 0;
      
      // Client breakdown
      const clientBreakdown = {};
      workLogs.forEach(log => {
        const clientName = log.client_name || 'Unknown';
        if (!clientBreakdown[clientName]) {
          clientBreakdown[clientName] = { hours: 0, revenue: 0, tasks: 0 };
        }
        clientBreakdown[clientName].hours += (log.duration_minutes || 0) / 60;
        clientBreakdown[clientName].revenue += log.total_amount || 0;
        clientBreakdown[clientName].tasks += 1;
      });
      
      // Activity breakdown
      const activityBreakdown = {};
      workLogs.forEach(log => {
        const activityName = log.activity_name || 'Unknown';
        if (!activityBreakdown[activityName]) {
          activityBreakdown[activityName] = { hours: 0, revenue: 0, tasks: 0 };
        }
        activityBreakdown[activityName].hours += (log.duration_minutes || 0) / 60;
        activityBreakdown[activityName].revenue += log.total_amount || 0;
        activityBreakdown[activityName].tasks += 1;
      });
      
      // Daily breakdown
      const dailyBreakdown = {};
      workLogs.forEach(log => {
        const date = new Date(log.date).toISOString().split('T')[0];
        if (!dailyBreakdown[date]) {
          dailyBreakdown[date] = { hours: 0, revenue: 0, tasks: 0 };
        }
        dailyBreakdown[date].hours += (log.duration_minutes || 0) / 60;
        dailyBreakdown[date].revenue += log.total_amount || 0;
        dailyBreakdown[date].tasks += 1;
      });
      
      setAnalytics({
        totalHours: totalHours.toFixed(1),
        billableHours: billableHours.toFixed(1),
        totalRevenue: totalRevenue.toFixed(2),
        avgHourlyRate: avgHourlyRate.toFixed(2),
        utilization: totalHours > 0 ? ((billableHours / totalHours) * 100).toFixed(1) : 0,
        totalTasks: workLogs.length,
        clientBreakdown: Object.entries(clientBreakdown)
          .sort((a, b) => b[1].revenue - a[1].revenue)
          .slice(0, 5),
        activityBreakdown: Object.entries(activityBreakdown)
          .sort((a, b) => b[1].hours - a[1].hours)
          .slice(0, 5),
        dailyBreakdown: Object.entries(dailyBreakdown)
          .sort((a, b) => new Date(a[0]) - new Date(b[0]))
      });
      
      setError(null);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const generatePDFReport = async (type) => {
    try {
      const token = localStorage.getItem('token');
      let url = '';
      
      if (type === 'daily') {
        url = `${backendUrl}/api/work-reports/reports/daily/${dateRange.start_date}`;
      } else if (type === 'monthly') {
        const date = new Date(dateRange.start_date);
        url = `${backendUrl}/api/work-reports/reports/monthly/${date.getFullYear()}/${date.getMonth() + 1}`;
      } else if (type === 'client' && selectedClient) {
        url = `${backendUrl}/api/work-reports/reports/client/${selectedClient}?start_date=${dateRange.start_date}&end_date=${dateRange.end_date}`;
      }
      
      if (!url) {
        alert('Please select appropriate parameters for the report');
        return;
      }
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      // Download the PDF
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${type}_report_${dateRange.start_date}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
    } catch (err) {
      console.error('Error generating PDF report:', err);
      alert('Failed to generate PDF report. Please try again.');
    }
  };

  const exportToExcel = async () => {
    try {
      const token = localStorage.getItem('token');
      const queryParams = new URLSearchParams();
      if (dateRange.start_date) queryParams.append('start_date', dateRange.start_date);
      if (dateRange.end_date) queryParams.append('end_date', dateRange.end_date);
      if (selectedClient) queryParams.append('client_id', selectedClient);
      
      const response = await axios.get(`${backendUrl}/api/work-reports/export/excel?${queryParams}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      // Download the Excel file
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `work_logs_export_${dateRange.start_date}_to_${dateRange.end_date}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
    } catch (err) {
      console.error('Error exporting to Excel:', err);
      alert('Failed to export to Excel. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Reports Dashboard</h1>
        <p className="text-gray-600 mt-2">لوحة التقارير - تحليل شامل لبيانات العمل</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Report Filters - مرشحات التقرير</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={dateRange.start_date}
              onChange={(e) => setDateRange({...dateRange, start_date: e.target.value})}
              className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={dateRange.end_date}
              onChange={(e) => setDateRange({...dateRange, end_date: e.target.value})}
              className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Client</label>
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Clients</option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.company_name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setDateRange({
                  start_date: new Date().toISOString().split('T')[0],
                  end_date: new Date().toISOString().split('T')[0]
                });
                setSelectedClient('');
              }}
              className="w-full bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              Reset Filters
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Analytics Summary */}
      {analytics && (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="bg-blue-500 rounded-md p-3">
                  <ClockIcon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Hours</p>
                  <p className="text-2xl font-bold text-blue-600">{analytics.totalHours}h</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="bg-green-500 rounded-md p-3">
                  <CurrencyDollarIcon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total Revenue</p>
                  <p className="text-2xl font-bold text-green-600">{analytics.totalRevenue} AED</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="bg-purple-500 rounded-md p-3">
                  <ChartBarIcon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Utilization</p>
                  <p className="text-2xl font-bold text-purple-600">{analytics.utilization}%</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="bg-orange-500 rounded-md p-3">
                  <DocumentTextIcon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Tasks</p>
                  <p className="text-2xl font-bold text-orange-600">{analytics.totalTasks}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Charts and Breakdowns */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Top Clients */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Clients by Revenue</h3>
              <div className="space-y-4">
                {analytics.clientBreakdown.map(([client, stats], index) => (
                  <div key={client} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold text-sm mr-3">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 truncate max-w-48">{client}</p>
                        <p className="text-sm text-gray-500">{stats.hours.toFixed(1)}h • {stats.tasks} tasks</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-green-600">${stats.revenue.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Activities */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Activities by Hours</h3>
              <div className="space-y-4">
                {analytics.activityBreakdown.map(([activity, stats], index) => (
                  <div key={activity} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 font-semibold text-sm mr-3">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 truncate max-w-48">{activity}</p>
                        <p className="text-sm text-gray-500">{stats.tasks} tasks • AED {stats.revenue.toFixed(2)}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-purple-600">{stats.hours.toFixed(1)}h</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Daily Breakdown */}
          {analytics.dailyBreakdown.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6 mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Breakdown</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hours</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Revenue</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tasks</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {analytics.dailyBreakdown.map(([date, stats]) => (
                      <tr key={date} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {new Date(date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {stats.hours.toFixed(1)}h
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          AED {stats.revenue.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {stats.tasks}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Export Options */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Reports - تصدير التقارير</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => generatePDFReport('daily')}
            className="bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-4 rounded-md flex items-center justify-center space-x-2 transition-colors"
          >
            <DocumentArrowDownIcon className="h-5 w-5" />
            <span>Daily PDF</span>
          </button>

          <button
            onClick={() => generatePDFReport('monthly')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-md flex items-center justify-center space-x-2 transition-colors"
          >
            <CalendarIcon className="h-5 w-5" />
            <span>Monthly PDF</span>
          </button>

          <button
            onClick={() => generatePDFReport('client')}
            disabled={!selectedClient}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-md flex items-center justify-center space-x-2 transition-colors"
          >
            <UserGroupIcon className="h-5 w-5" />
            <span>Client PDF</span>
          </button>

          <button
            onClick={exportToExcel}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 px-4 rounded-md flex items-center justify-center space-x-2 transition-colors"
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            <span>Excel Export</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportsDashboard;