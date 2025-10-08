import React, { useState } from 'react';
import axios from 'axios';
import {
  ChartBarIcon,
  CalendarIcon,
  UserGroupIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AttendanceReport = () => {
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateReport = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Fetch attendance data for the month
      const response = await axios.get(`${API}/attendance/with-absences`, {
        params: { month: selectedMonth }
      });
      
      const records = response.data.attendance || [];
      
      // Calculate statistics
      const stats = {
        totalRecords: records.length,
        presentCount: records.filter(r => r.status === 'present').length,
        lateCount: records.filter(r => r.status === 'late').length,
        absentCount: records.filter(r => r.status === 'absent').length,
        totalLateMinutes: records.filter(r => r.status === 'late').reduce((sum, r) => sum + (r.late_minutes || 0), 0),
        avgLateMinutes: 0
      };
      
      stats.avgLateMinutes = stats.lateCount > 0 ? (stats.totalLateMinutes / stats.lateCount).toFixed(1) : 0;
      
      // Group by employee
      const byEmployee = {};
      records.forEach(record => {
        const empId = record.employee_id;
        if (!byEmployee[empId]) {
          byEmployee[empId] = {
            employee_id: empId,
            employee_name: record.employee_name,
            present: 0,
            late: 0,
            absent: 0,
            totalLateMinutes: 0
          };
        }
        
        if (record.status === 'present') byEmployee[empId].present++;
        else if (record.status === 'late') {
          byEmployee[empId].late++;
          byEmployee[empId].totalLateMinutes += (record.late_minutes || 0);
        }
        else if (record.status === 'absent') byEmployee[empId].absent++;
      });
      
      const employeeStats = Object.values(byEmployee);
      
      setReportData({
        stats,
        employeeStats,
        month: selectedMonth
      });
    } catch (err) {
      console.error('Error generating report:', err);
      setError(err.response?.data?.detail || 'خطأ في إنشاء التقرير');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg shadow-lg mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">📊 تقرير الحضور والغياب</h1>
            <p className="text-blue-100">إحصائيات شاملة عن الحضور والتأخير والغياب</p>
          </div>
          <ChartBarIcon className="h-16 w-16 text-blue-200" />
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <CalendarIcon className="h-4 w-4 inline ml-1" />
              اختر الشهر
            </label>
            <input
              type="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={generateReport}
              disabled={loading}
              className="w-full px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  جاري الإنشاء...
                </>
              ) : (
                <>
                  <ChartBarIcon className="h-5 w-5" />
                  إنشاء التقرير
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Report Results */}
      {reportData && (
        <>
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gradient-to-r from-green-100 to-green-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-700 font-medium">الحضور</p>
                  <p className="text-3xl font-bold text-green-900">{reportData.stats.presentCount}</p>
                </div>
                <CheckCircleIcon className="h-12 w-12 text-green-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-yellow-100 to-yellow-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-yellow-700 font-medium">التأخير</p>
                  <p className="text-3xl font-bold text-yellow-900">{reportData.stats.lateCount}</p>
                </div>
                <ClockIcon className="h-12 w-12 text-yellow-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-red-100 to-red-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-700 font-medium">الغياب</p>
                  <p className="text-3xl font-bold text-red-900">{reportData.stats.absentCount}</p>
                </div>
                <XCircleIcon className="h-12 w-12 text-red-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-100 to-purple-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-700 font-medium">متوسط التأخير</p>
                  <p className="text-2xl font-bold text-purple-900">{reportData.stats.avgLateMinutes} دقيقة</p>
                </div>
                <ExclamationTriangleIcon className="h-12 w-12 text-purple-500" />
              </div>
            </div>
          </div>

          {/* Employee Table */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                إحصائيات الموظفين - {reportData.month}
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الموظف</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الحضور</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">التأخير</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الغياب</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">دقائق التأخير</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">معدل الحضور</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {reportData.employeeStats.map((emp, index) => {
                    const total = emp.present + emp.late + emp.absent;
                    const attendanceRate = total > 0 ? ((emp.present + emp.late) / total * 100).toFixed(1) : 0;
                    
                    return (
                      <tr key={emp.employee_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {emp.employee_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-semibold">
                          {emp.present}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600 font-semibold">
                          {emp.late}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-semibold">
                          {emp.absent}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                          {emp.totalLateMinutes} دقيقة
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                            attendanceRate >= 90 ? 'bg-green-100 text-green-800' :
                            attendanceRate >= 75 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {attendanceRate}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!reportData && !loading && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <ChartBarIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            ابدأ بإنشاء تقرير
          </h3>
          <p className="text-gray-500">
            اختر الشهر واضغط على "إنشاء التقرير"
          </p>
        </div>
      )}
    </div>
  );
};

export default AttendanceReport;