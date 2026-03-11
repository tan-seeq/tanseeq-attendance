import React, { useState } from 'react';
import axios from 'axios';
import {
  ChartBarIcon,
  CalendarIcon,
  UserGroupIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  DocumentArrowDownIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AttendanceReport = () => {
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [applyingDeductions, setApplyingDeductions] = useState(false);
  const [deductionsResult, setDeductionsResult] = useState(null);

  // Custom Report Modal State
  const [showCustomReportModal, setShowCustomReportModal] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [customReportForm, setCustomReportForm] = useState({
    employee_ids: [],
    start_date: '',
    end_date: '',
    format: 'excel'
  });
  const [generatingReport, setGeneratingReport] = useState(false);

  const applyDeductions = async () => {
    if (!window.confirm(`هل أنت متأكد من تطبيق خصومات التأخير والغياب للشهر ${selectedMonth}؟\n\nسيتم حساب:\n- خصومات التأخير\n- خصومات الغياب\n- أقساط السلف المستحقة`)) {
      return;
    }

    try {
      setApplyingDeductions(true);
      setError('');
      
      // Calculate deductions
      const response = await axios.post(`${API}/deductions/calculate-monthly?month=${selectedMonth}`);
      
      if (response.data.success) {
        setDeductionsResult(response.data);
        alert(`✅ تم حساب الخصومات بنجاح!\n\n` +
              `عدد الموظفين المتأثرين: ${response.data.employee_count}\n` +
              `إجمالي الخصومات: ${response.data.total_deductions.toFixed(2)} درهم\n\n` +
              `يمكنك الآن مراجعة الخصومات في صفحة "نظام خصومات التأخير المتقدم"`);
      }
    } catch (err) {
      console.error('Error applying deductions:', err);
      const errorMsg = err.response?.data?.detail || 'خطأ في تطبيق الخصومات';
      setError(errorMsg);
      alert('❌ خطأ: ' + errorMsg);
    } finally {
      setApplyingDeductions(false);
    }
  };

  const generateReport = async () => {
    try {
      setLoading(true);
      setError('');
      setDeductionsResult(null);
      
      // Fetch attendance data
      const response = await axios.get(`${API}/attendance/with-absences`);
      
      // Response is array directly
      let records = Array.isArray(response.data) ? response.data : [];
      
      // Filter by selected month
      records = records.filter(r => {
        const recordDate = r.date || '';
        return recordDate.startsWith(selectedMonth);
      });
      
      // Normalize status values (Present/Late/Absent to lowercase)
      records = records.map(r => ({
        ...r,
        status: (r.original_status || r.status || '').toLowerCase(),
        employee_id: r.user_id,
        employee_name: r.user_name,
        late_minutes: r.is_late ? 30 : 0  // Default 30 minutes if late (can be enhanced)
      }));
      
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
  // Custom Report Functions
  const toggleEmployeeSelection = (employeeId) => {
    setCustomReportForm(prev => ({
      ...prev,
      employee_ids: prev.employee_ids.includes(employeeId)
        ? prev.employee_ids.filter(id => id !== employeeId)
        : [...prev.employee_ids, employeeId]
    }));
  };

  const handleGenerateCustomReport = async () => {
    if (customReportForm.employee_ids.length === 0) {
      alert('يرجى اختيار موظف واحد على الأقل');
      return;
    }

    if (!customReportForm.start_date || !customReportForm.end_date) {
      alert('يرجى تحديد تاريخ البداية والنهاية');
      return;
    }

    try {
      setGeneratingReport(true);
      
      const response = await axios.post(`${API}/reports/attendance/custom`, {
        employee_ids: customReportForm.employee_ids,
        start_date: customReportForm.start_date,
        end_date: customReportForm.end_date,
        format: customReportForm.format
      }, {
        responseType: 'blob'
      });

      // Create download link
      const blob = new Blob([response.data], {
        type: customReportForm.format === 'excel' 
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'text/csv'
      });
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const extension = customReportForm.format === 'excel' ? 'xlsx' : 'csv';
      const filename = `attendance_report_${customReportForm.start_date}_to_${customReportForm.end_date}.${extension}`;
      link.download = filename;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // Close modal and reset form
      setShowCustomReportModal(false);
      setCustomReportForm({
        employee_ids: [],
        start_date: '',
        end_date: '',
        format: 'excel'
      });

      alert('تم تصدير التقرير بنجاح!');
    } catch (error) {
      console.error('Error generating custom report:', error);
      alert('حدث خطأ في تصدير التقرير: ' + (error.response?.data?.detail || error.message));
    } finally {
      setGeneratingReport(false);
    }
  };

  // Fetch employees when modal opens
  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  // Open custom report modal
  const openCustomReportModal = () => {
    setShowCustomReportModal(true);
    fetchEmployees();
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
          
          <div className="flex items-end gap-2">
            <button
              onClick={generateReport}
              disabled={loading}
              className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
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
            
            <button
              onClick={applyDeductions}
              disabled={applyingDeductions || !selectedMonth}
              className="flex-1 px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {applyingDeductions ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  جاري التطبيق...
                </>
              ) : (
                <>
                  <ExclamationTriangleIcon className="h-5 w-5" />
                  تطبيق خصومات التأخير
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

      {/* NEW: Custom Report Modal */}
      {showCustomReportModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-6 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-gray-900 mb-4">تقرير حضور مخصص</h3>
            
            {/* Employee Selection */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-blue-900 mb-3">1️⃣ اختر الموظفين</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-60 overflow-y-auto">
                {employees.map(emp => (
                  <label key={emp.id} className="flex items-center space-x-2 space-x-reverse bg-white p-2 rounded border hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={customReportForm.employee_ids.includes(emp.id)}
                      onChange={() => toggleEmployeeSelection(emp.id)}
                      className="h-4 w-4"
                    />
                    <span className="text-sm">{emp.name}</span>
                  </label>
                ))}
              </div>
              <div className="mt-3 flex items-center space-x-2">
                <button
                  onClick={() => setCustomReportForm({
                    ...customReportForm,
                    employee_ids: employees.map(e => e.id)
                  })}
                  className="text-sm text-blue-600 hover:underline"
                >
                  اختيار الكل
                </button>
                <span className="text-gray-400">|</span>
                <button
                  onClick={() => setCustomReportForm({
                    ...customReportForm,
                    employee_ids: []
                  })}
                  className="text-sm text-gray-600 hover:underline"
                >
                  إلغاء الاختيار
                </button>
                <span className="flex-1 text-left text-sm text-gray-700">
                  محدد: {customReportForm.employee_ids.length} موظف
                </span>
              </div>
            </div>

            {/* Date Range */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-green-900 mb-3">2️⃣ حدد الفترة</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">من تاريخ</label>
                  <input
                    type="date"
                    value={customReportForm.start_date}
                    onChange={(e) => setCustomReportForm({...customReportForm, start_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">إلى تاريخ</label>
                  <input
                    type="date"
                    value={customReportForm.end_date}
                    onChange={(e) => setCustomReportForm({...customReportForm, end_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>
            </div>

            {/* Export Format */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-purple-900 mb-3">3️⃣ اختر صيغة التصدير</h4>
              <div className="flex space-x-4 space-x-reverse">
                <label className="flex items-center space-x-2 space-x-reverse cursor-pointer">
                  <input
                    type="radio"
                    value="excel"
                    checked={customReportForm.format === 'excel'}
                    onChange={(e) => setCustomReportForm({...customReportForm, format: e.target.value})}
                    className="h-4 w-4"
                  />
                  <span className="flex items-center space-x-2">
                    <span>📊 Excel (.xlsx)</span>
                  </span>
                </label>
                <label className="flex items-center space-x-2 space-x-reverse cursor-pointer">
                  <input
                    type="radio"
                    value="csv"
                    checked={customReportForm.format === 'csv'}
                    onChange={(e) => setCustomReportForm({...customReportForm, format: e.target.value})}
                    className="h-4 w-4"
                  />
                  <span className="flex items-center space-x-2">
                    <span>📄 CSV (.csv)</span>
                  </span>
                </label>
              </div>
            </div>

            {/* Summary */}
            {customReportForm.employee_ids.length > 0 && customReportForm.start_date && customReportForm.end_date && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-yellow-800">
                  📋 سيتم تصدير تقرير حضور لـ <strong>{customReportForm.employee_ids.length}</strong> موظف
                  من <strong>{customReportForm.start_date}</strong> إلى <strong>{customReportForm.end_date}</strong>
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 space-x-reverse pt-4 border-t">
              <button
                onClick={() => {
                  setShowCustomReportModal(false);
                  setCustomReportForm({
                    employee_ids: [],
                    start_date: '',
                    end_date: '',
                    format: 'excel'
                  });
                }}
                className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
              >
                إلغاء
              </button>
              <button
                onClick={handleGenerateCustomReport}
                disabled={generatingReport || customReportForm.employee_ids.length === 0}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center space-x-2"
              >
                {generatingReport ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>جاري التصدير...</span>
                  </>
                ) : (
                  <>
                    <DocumentArrowDownIcon className="h-5 w-5" />
                    <span>تصدير التقرير</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendanceReport;