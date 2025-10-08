import React, { useState } from 'react';
import axios from 'axios';
import {
  DocumentChartBarIcon,
  CalendarIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  ArrowDownTrayIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DeductionsReport = () => {
  const [reportType, setReportType] = useState('monthly');
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateReport = async () => {
    try {
      setLoading(true);
      setError('');
      
      if (reportType === 'monthly') {
        const response = await axios.post(`${API}/deductions/calculate-monthly?month=${selectedMonth}`, {});
        setReportData(response.data);
      }
    } catch (err) {
      console.error('Error generating report:', err);
      setError(err.response?.data?.detail || 'خطأ في إنشاء التقرير');
    } finally {
      setLoading(false);
    }
  };

  const exportToPDF = () => {
    window.print();
  };

  return (
    <div className="p-6 max-w-7xl mx-auto" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white p-6 rounded-lg shadow-lg mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">📊 تقارير الخصومات الشاملة</h1>
            <p className="text-purple-100">تقارير تفصيلية عن خصومات التأخير والغياب والسلف</p>
          </div>
          <DocumentChartBarIcon className="h-16 w-16 text-purple-200" />
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <FunnelIcon className="h-5 w-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">إعدادات التقرير</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">نوع التقرير</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
            >
              <option value="monthly">تقرير شهري</option>
              <option value="employee">تقرير حسب الموظف</option>
              <option value="type">تقرير حسب النوع</option>
            </select>
          </div>

          {/* Month Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <CalendarIcon className="h-4 w-4 inline ml-1" />
              الشهر
            </label>
            <input
              type="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
            />
          </div>

          {/* Generate Button */}
          <div className="flex items-end">
            <button
              onClick={generateReport}
              disabled={loading}
              className="w-full px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  جاري الإنشاء...
                </>
              ) : (
                <>
                  <DocumentChartBarIcon className="h-5 w-5" />
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
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-gradient-to-r from-blue-100 to-blue-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-700 font-medium">الموظفين المتأثرين</p>
                  <p className="text-3xl font-bold text-blue-900">{reportData.employee_count}</p>
                </div>
                <UserGroupIcon className="h-12 w-12 text-blue-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-red-100 to-red-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-700 font-medium">إجمالي الخصومات</p>
                  <p className="text-2xl font-bold text-red-900">
                    {reportData.total_deductions?.toFixed(2)} <span className="text-lg">درهم</span>
                  </p>
                </div>
                <CurrencyDollarIcon className="h-12 w-12 text-red-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-100 to-purple-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-700 font-medium">الشهر</p>
                  <p className="text-2xl font-bold text-purple-900">{reportData.month}</p>
                </div>
                <CalendarIcon className="h-12 w-12 text-purple-500" />
              </div>
            </div>
          </div>

          {/* Export Button */}
          <div className="mb-6 flex justify-end">
            <button
              onClick={exportToPDF}
              className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center gap-2"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
              تصدير PDF
            </button>
          </div>

          {/* Detailed Table */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">تفاصيل الخصومات - {reportData.month}</h2>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الموظف</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">التأخير</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الغياب</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">السلف</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الإجمالي</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">التفاصيل</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {reportData.employees?.map((emp, index) => (
                    <tr key={emp.employee_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {emp.employee_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600 font-semibold">
                        {emp.late_deduction > 0 ? `${emp.late_deduction.toFixed(2)} درهم` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-semibold">
                        {emp.absence_deduction > 0 ? `${emp.absence_deduction.toFixed(2)} درهم` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-600 font-semibold">
                        {emp.advance_deduction > 0 ? `${emp.advance_deduction.toFixed(2)} درهم` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-700">
                        {emp.total_deduction.toFixed(2)} درهم
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        <ul className="list-disc list-inside">
                          {emp.deduction_details?.map((detail, idx) => (
                            <li key={idx} className="text-xs">{detail}</li>
                          ))}
                        </ul>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-100">
                  <tr>
                    <td className="px-6 py-4 text-sm font-bold text-gray-900">الإجمالي:</td>
                    <td className="px-6 py-4 text-sm font-bold text-yellow-700">
                      {reportData.employees?.reduce((sum, e) => sum + e.late_deduction, 0).toFixed(2)} درهم
                    </td>
                    <td className="px-6 py-4 text-sm font-bold text-red-700">
                      {reportData.employees?.reduce((sum, e) => sum + e.absence_deduction, 0).toFixed(2)} درهم
                    </td>
                    <td className="px-6 py-4 text-sm font-bold text-purple-700">
                      {reportData.employees?.reduce((sum, e) => sum + e.advance_deduction, 0).toFixed(2)} درهم
                    </td>
                    <td colSpan="2" className="px-6 py-4 text-sm font-bold text-red-700">
                      {reportData.total_deductions?.toFixed(2)} درهم
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!reportData && !loading && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <DocumentChartBarIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            ابدأ بإنشاء تقرير
          </h3>
          <p className="text-gray-500">
            اختر نوع التقرير والشهر ثم اضغط على "إنشاء التقرير"
          </p>
        </div>
      )}
    </div>
  );
};

export default DeductionsReport;