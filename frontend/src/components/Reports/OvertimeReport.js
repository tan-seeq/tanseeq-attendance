import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ArrowPathIcon, CalculatorIcon, ClockIcon, DocumentArrowDownIcon,
  ExclamationCircleIcon, InformationCircleIcon, MagnifyingGlassIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../config';

const OvertimeReport = () => {
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [overtimeData, setOvertimeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { user } = useAuth();

  const fetchOvertimeReport = async () => {
    try {
      setLoading(true);
      setMessage('');
      const response = await axios.get(`${API}/overtime-reports/${selectedMonth}`);
      setOvertimeData(response.data);
      
      if (response.data.total_records === 0) {
        setMessage({ 
          type: 'info', 
          text: 'لا توجد ساعات عمل إضافية مسجلة في هذا الشهر' 
        });
      }
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في تحميل تقرير العمل الإضافي' 
      });
      setOvertimeData(null);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async (format) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/overtime-reports/export/${selectedMonth}?format=${format}`, {
        responseType: 'blob'
      });

      const blob = new Blob([response.data]);
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `TANSEEQ_overtime_report_${selectedMonth}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setMessage({ type: 'success', text: `تم تصدير التقرير بصيغة ${format.toUpperCase()} بنجاح` });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في تصدير التقرير' 
      });
    } finally {
      setLoading(false);
    }
  };

  const getOvertimeTypeColor = (type) => {
    switch (type) {
      case 'Early Start': return 'bg-blue-100 text-blue-800';
      case 'Late Finish': return 'bg-orange-100 text-orange-800';
      case 'Mixed': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getOvertimeTypeText = (type) => {
    switch (type) {
      case 'Early Start': return 'بداية مبكرة';
      case 'Late Finish': return 'انتهاء متأخر';
      case 'Mixed': return 'مختلط';
      default: return type;
    }
  };

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      fetchOvertimeReport();
    }
  }, [selectedMonth, user]);

  if (user?.role !== 'admin' && user?.role !== 'super_admin') {
    return (
      <div className="text-center py-8">
        <ExclamationCircleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
        <p className="text-gray-500">هذه الصفحة متاحة للإدارة فقط</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-gray-800">⏰ تقرير العمل الإضافي (Overtime Report)</h2>
          <div className="bg-green-50 px-3 py-1 rounded-lg">
            <span className="text-sm text-green-700 font-medium">Admin/Super Admin</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex flex-col">
            <label className="block text-sm font-medium text-gray-700 mb-1">الشهر</label>
            <input
              type="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="text-xs text-gray-500 mt-1">
              📅 Cycle: 29th prev month → 28th current month
            </div>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={fetchOvertimeReport}
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex items-center"
            >
              {loading ? <ArrowPathIcon className="h-4 w-4 animate-spin mr-2" /> : <MagnifyingGlassIcon className="h-4 w-4 mr-2" />}
              عرض التقرير
            </button>

            <button
              onClick={() => exportReport('excel')}
              disabled={loading || !overtimeData}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400 flex items-center"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Excel
            </button>

            <button
              onClick={() => exportReport('pdf')}
              disabled={loading || !overtimeData}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:bg-gray-400 flex items-center"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              PDF
            </button>
          </div>
        </div>

        {message && (
          <div className={`p-4 mb-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 
            message.type === 'error' ? 'bg-red-50 text-red-700' : 
            'bg-blue-50 text-blue-700'
          }`}>
            {message.text}
          </div>
        )}

        {/* Statistics */}
        {overtimeData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center">
                <ClockIcon className="h-8 w-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-blue-600">إجمالي السجلات</p>
                  <p className="text-2xl font-bold text-blue-900">{overtimeData.total_records}</p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center">
                <UserGroupIcon className="h-8 w-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-green-600">عدد الموظفين</p>
                  <p className="text-2xl font-bold text-green-900">{overtimeData.total_employees}</p>
                </div>
              </div>
            </div>

            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="flex items-center">
                <ClockIcon className="h-8 w-8 text-orange-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-orange-600">إجمالي الساعات الإضافية</p>
                  <p className="text-2xl font-bold text-orange-900">{overtimeData.total_overtime_hours}h</p>
                </div>
              </div>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center">
                <CalculatorIcon className="h-8 w-8 text-purple-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-purple-600">المتوسط/موظف</p>
                  <p className="text-2xl font-bold text-purple-900">
                    {overtimeData.total_employees > 0 ? (overtimeData.total_overtime_hours / overtimeData.total_employees).toFixed(1) : '0'}h
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Overtime Records Table */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-500" />
            <span className="ml-2 text-gray-600">جاري تحميل التقرير...</span>
          </div>
        ) : overtimeData && overtimeData.overtime_records.length > 0 ? (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-medium text-gray-800 mb-4">تفاصيل العمل الإضافي</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الموظف</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">التاريخ</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الحضور</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الانصراف</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">إجمالي الساعات</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">ساعات مبكرة</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">ساعات متأخرة</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">إجمالي إضافي</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">النوع</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {overtimeData.overtime_records.map((record, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {record.employee_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {record.date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {record.check_in_time}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {record.check_out_time}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span className="font-medium">{record.total_working_hours}h</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-medium">
                        {record.early_overtime_hours}h
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-600 font-medium">
                        {record.late_overtime_hours}h
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-bold">
                        {record.total_overtime_hours}h
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getOvertimeTypeColor(record.overtime_type)}`}>
                          {getOvertimeTypeText(record.overtime_type)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {/* Info Box */}
        <div className="mt-6 bg-blue-50 border-l-4 border-blue-400 p-4">
          <div className="flex">
            <InformationCircleIcon className="h-5 w-5 text-blue-400" />
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                <strong>ملاحظة:</strong> يتم حساب العمل الإضافي بناءً على ساعات العمل الرسمية (9:00 صباحاً - 6:00 مساءً). 
                أي وقت قبل 9:00 صباحاً أو بعد 6:00 مساءً يُحسب كساعات إضافية، حتى للموظفين ذوي العمل المرن.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


export default OvertimeReport;
