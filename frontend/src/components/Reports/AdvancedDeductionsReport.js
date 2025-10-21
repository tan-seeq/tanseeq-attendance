import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const AdvancedDeductionsReport = () => {
  const [loading, setLoading] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [merging, setMerging] = useState(false);
  const [reportData, setReportData] = useState(null);
  
  // Mode: monthly or custom
  const [mode, setMode] = useState('monthly');
  
  // Monthly mode
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  
  // Custom mode
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [expandedEmployee, setExpandedEmployee] = useState(null);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [cycleId, setCycleId] = useState('');

  // Get token from localStorage
  const token = localStorage.getItem('token');
  const config = {
    headers: { Authorization: `Bearer ${token}` }
  };

  // Month names in Arabic
  const monthNames = {
    1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو',
    7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
  };

  // Calculate deductions based on mode
  const handleCalculate = async () => {
    setCalculating(true);
    setError('');
    setSuccessMessage('');
    
    try {
      let url = `${API_URL}/api/deductions/calculate?preview=true`;
      
      if (mode === 'monthly') {
        url += `&mode=monthly&month=${selectedMonth}&year=${selectedYear}`;
      } else {
        // Validate custom dates
        if (!fromDate || !toDate) {
          setError('الرجاء إدخال تاريخ البداية والنهاية');
          setCalculating(false);
          return;
        }
        
        url += `&mode=custom&from_date=${fromDate}&to_date=${toDate}`;
      }
      
      const response = await axios.post(url, {}, config);
      
      // Transform to report format
      const transformedData = {
        mode: response.data.mode,
        cycle_start: response.data.from,
        cycle_end: response.data.to,
        total_employees: response.data.employees_count,
        summaries: response.data.items.map(item => ({
          employee_id: item.employee_id,
          employee_name: item.employee_name,
          total_working_days: item.breakdown.length,
          days_present: item.breakdown.filter(d => d.amount > 0).length,
          days_absent: item.breakdown.filter(d => d.reason === 'absent').length,
          total_late_minutes: item.breakdown.reduce((sum, d) => sum + d.late_minutes, 0),
          total_early_leave_minutes: item.breakdown.reduce((sum, d) => sum + d.early_out_minutes, 0),
          total_deficit_minutes: item.minutes,
          total_deduction_amount: item.amount,
          daily_records: item.breakdown.map(b => ({
            date: b.date,
            check_in: null,
            check_out: null,
            is_working_day: true,
            is_absent: b.reason === 'absent',
            late_minutes: b.late_minutes,
            early_leave_minutes: b.early_out_minutes,
            total_work_minutes: 480 - b.under_hours_minutes,
            deficit_minutes: b.under_hours_minutes,
            deduction_amount: b.amount
          }))
        }))
      };
      
      setReportData(transformedData);
      setSuccessMessage(`تم حساب الخصومات لـ ${response.data.employees_count} موظف`);
      
      setTimeout(() => setSuccessMessage(''), 3000);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'فشل حساب الخصومات';
      setError(errorMsg);
    } finally {
      setCalculating(false);
    }
  };

  // Fetch report data
  const fetchReport = async () => {
    setLoading(true);
    setError('');
    
    try {
      const url = selectedEmployee 
        ? `${API_URL}/api/deductions/report?month=${selectedMonth}&year=${selectedYear}&employee_id=${selectedEmployee}`
        : `${API_URL}/api/deductions/report?month=${selectedMonth}&year=${selectedYear}`;
      
      const response = await axios.get(url, config);
      setReportData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'فشل جلب التقرير');
      setReportData(null);
    } finally {
      setLoading(false);
    }
  };

  // Export to Excel
  const handleExportExcel = () => {
    if (!reportData || !reportData.summaries || reportData.summaries.length === 0) {
      alert('لا توجد بيانات للتصدير');
      return;
    }

    // Create CSV content
    let csvContent = 'الموظف,أيام العمل,الحضور,الغياب,التأخير (دقيقة),الخروج المبكر (دقيقة),نقص الساعات (دقيقة),الخصم (درهم)\n';
    
    reportData.summaries.forEach(summary => {
      csvContent += `${summary.employee_name},${summary.total_working_days},${summary.days_present},${summary.days_absent},${summary.total_late_minutes},${summary.total_early_leave_minutes},${summary.total_deficit_minutes},${summary.total_deduction_amount.toFixed(2)}\n`;
    });

    // Create download link
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `advanced_deductions_${selectedYear}_${selectedMonth}.csv`;
    link.click();
  };

  // Merge with payroll cycle
  const handleMergeWithPayroll = async () => {
    if (!cycleId) {
      alert('الرجاء إدخال معرّف دورة الرواتب (Cycle ID)');
      return;
    }

    if (!window.confirm(`هل تريد دمج الخصومات المتقدمة مع دورة الرواتب؟\n\nسيتم:\n- إضافة الخصومات للموظفين\n- تحديث صافي الراتب\n- إنشاء قيود محاسبية`)) {
      return;
    }

    setMerging(true);
    setError('');
    setSuccessMessage('');

    try {
      const response = await axios.post(
        `${API_URL}/api/payroll/cycles/${cycleId}/merge-advanced-deductions?month=${selectedMonth}&year=${selectedYear}`,
        {},
        config
      );

      setSuccessMessage(response.data.message || 'تم الدمج بنجاح');
      alert(`✅ تم الدمج بنجاح!\n\nالموظفين المحدّثين: ${response.data.employees_updated}\nإجمالي الخصومات: ${response.data.total_deduction_amount} درهم`);

    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'فشل الدمج مع دورة الرواتب';
      setError(errorMsg);
      alert('❌ ' + errorMsg);
    } finally {
      setMerging(false);
    }
  };

  // Toggle employee details
  const toggleEmployeeDetails = (employeeId) => {
    setExpandedEmployee(expandedEmployee === employeeId ? null : employeeId);
  };

  // Format time
  const formatTime = (timeStr) => {
    if (!timeStr) return '-';
    return timeStr.substring(0, 5); // HH:MM
  };

  // Format minutes to hours
  const minutesToHours = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}:${mins.toString().padStart(2, '0')}`;
  };

  // Initial load
  useEffect(() => {
    fetchReport();
  }, [selectedMonth, selectedYear]);

  return (
    <div className="container mx-auto p-6" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg shadow-lg mb-6">
        <h1 className="text-3xl font-bold mb-2">📊 نظام الخصومات المتقدم</h1>
        <p className="text-blue-100">احتساب التأخير والانصراف المبكر - الدورة من 29 إلى 28</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          {/* Month Selector */}
          <div>
            <label className="block text-gray-700 font-bold mb-2">الشهر</label>
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.entries(monthNames).map(([num, name]) => (
                <option key={num} value={num}>{name}</option>
              ))}
            </select>
          </div>

          {/* Year Selector */}
          <div>
            <label className="block text-gray-700 font-bold mb-2">السنة</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {[2024, 2025, 2026].map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          {/* Calculate Button */}
          <div className="flex items-end">
            <button
              onClick={handleCalculate}
              disabled={calculating}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition disabled:bg-gray-400"
            >
              {calculating ? '🔄 جاري الحساب...' : '🧮 حساب الخصومات'}
            </button>
          </div>

          {/* Export Button */}
          <div className="flex items-end">
            <button
              onClick={handleExportExcel}
              disabled={!reportData || !reportData.summaries || reportData.summaries.length === 0}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition disabled:bg-gray-400"
            >
              📥 تصدير Excel
            </button>
          </div>
        </div>

        {/* Payroll Integration Section */}
        <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
          <h3 className="font-bold text-orange-800 mb-3">🔗 الدمج مع دورة الرواتب</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-gray-700 font-bold mb-2">معرّف دورة الرواتب (Cycle ID)</label>
              <input
                type="text"
                value={cycleId}
                onChange={(e) => setCycleId(e.target.value)}
                placeholder="أدخل Cycle ID من صفحة الرواتب"
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <p className="text-xs text-gray-500 mt-1">يمكنك الحصول على Cycle ID من صفحة "إدارة دورات الرواتب"</p>
            </div>
            <div className="flex items-end">
              <button
                onClick={handleMergeWithPayroll}
                disabled={merging || !cycleId || !reportData}
                className="w-full bg-orange-600 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded-lg transition disabled:bg-gray-400"
              >
                {merging ? '🔄 جاري الدمج...' : '🔗 دمج مع الدورة'}
              </button>
            </div>
          </div>
        </div>

        {/* Cycle Info */}
        {reportData && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-800">
              📅 <strong>دورة الحساب:</strong> من {reportData.cycle_start} إلى {reportData.cycle_end}
            </p>
          </div>
        )}
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          ❌ {error}
        </div>
      )}

      {successMessage && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg mb-4">
          ✅ {successMessage}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">جاري تحميل التقرير...</p>
        </div>
      )}

      {/* Report Data */}
      {!loading && reportData && reportData.summaries && reportData.summaries.length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Summary Stats */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-6 border-b">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-600">{reportData.total_employees}</p>
                <p className="text-gray-600 text-sm">عدد الموظفين</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-green-600">
                  {reportData.summaries.reduce((sum, s) => sum + s.days_present, 0)}
                </p>
                <p className="text-gray-600 text-sm">أيام الحضور</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-red-600">
                  {reportData.summaries.reduce((sum, s) => sum + s.days_absent, 0)}
                </p>
                <p className="text-gray-600 text-sm">أيام الغياب</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-orange-600">
                  {reportData.summaries.reduce((sum, s) => sum + s.total_deduction_amount, 0).toFixed(2)}
                </p>
                <p className="text-gray-600 text-sm">إجمالي الخصومات (درهم)</p>
              </div>
            </div>
          </div>

          {/* Employee Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-blue-600 text-white">
                <tr>
                  <th className="px-4 py-3 text-right">#</th>
                  <th className="px-4 py-3 text-right">الموظف</th>
                  <th className="px-4 py-3 text-center">أيام العمل</th>
                  <th className="px-4 py-3 text-center">الحضور</th>
                  <th className="px-4 py-3 text-center">الغياب</th>
                  <th className="px-4 py-3 text-center">التأخير (د)</th>
                  <th className="px-4 py-3 text-center">خروج مبكر (د)</th>
                  <th className="px-4 py-3 text-center">نقص الساعات</th>
                  <th className="px-4 py-3 text-center">الخصم (درهم)</th>
                  <th className="px-4 py-3 text-center">التفاصيل</th>
                </tr>
              </thead>
              <tbody>
                {reportData.summaries.map((summary, index) => (
                  <React.Fragment key={summary.employee_id}>
                    <tr className={`border-b hover:bg-gray-50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                      <td className="px-4 py-3">{index + 1}</td>
                      <td className="px-4 py-3 font-semibold">{summary.employee_name}</td>
                      <td className="px-4 py-3 text-center">{summary.total_working_days}</td>
                      <td className="px-4 py-3 text-center text-green-600 font-bold">{summary.days_present}</td>
                      <td className="px-4 py-3 text-center text-red-600 font-bold">{summary.days_absent}</td>
                      <td className="px-4 py-3 text-center text-orange-600">{summary.total_late_minutes}</td>
                      <td className="px-4 py-3 text-center text-orange-600">{summary.total_early_leave_minutes}</td>
                      <td className="px-4 py-3 text-center text-red-600">{minutesToHours(summary.total_deficit_minutes)}</td>
                      <td className="px-4 py-3 text-center font-bold text-red-700">{summary.total_deduction_amount.toFixed(2)}</td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => toggleEmployeeDetails(summary.employee_id)}
                          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                        >
                          {expandedEmployee === summary.employee_id ? '▲ إخفاء' : '▼ عرض'}
                        </button>
                      </td>
                    </tr>

                    {/* Daily Details */}
                    {expandedEmployee === summary.employee_id && (
                      <tr>
                        <td colSpan="10" className="bg-gray-100 p-4">
                          <div className="overflow-x-auto">
                            <h4 className="font-bold text-lg mb-3 text-gray-700">📅 التفاصيل اليومية</h4>
                            <table className="w-full bg-white rounded-lg shadow">
                              <thead className="bg-gray-200">
                                <tr>
                                  <th className="px-3 py-2 text-right text-sm">التاريخ</th>
                                  <th className="px-3 py-2 text-center text-sm">الحضور</th>
                                  <th className="px-3 py-2 text-center text-sm">الانصراف</th>
                                  <th className="px-3 py-2 text-center text-sm">ساعات العمل</th>
                                  <th className="px-3 py-2 text-center text-sm">التأخير</th>
                                  <th className="px-3 py-2 text-center text-sm">خروج مبكر</th>
                                  <th className="px-3 py-2 text-center text-sm">نقص</th>
                                  <th className="px-3 py-2 text-center text-sm">الخصم</th>
                                  <th className="px-3 py-2 text-center text-sm">الحالة</th>
                                </tr>
                              </thead>
                              <tbody>
                                {summary.daily_records.map((record, idx) => (
                                  <tr key={idx} className={`border-b ${record.is_absent ? 'bg-red-50' : ''}`}>
                                    <td className="px-3 py-2 text-sm">{record.date}</td>
                                    <td className="px-3 py-2 text-center text-sm">{formatTime(record.check_in)}</td>
                                    <td className="px-3 py-2 text-center text-sm">{formatTime(record.check_out)}</td>
                                    <td className="px-3 py-2 text-center text-sm">{minutesToHours(record.total_work_minutes)}</td>
                                    <td className="px-3 py-2 text-center text-sm text-orange-600">{record.late_minutes}</td>
                                    <td className="px-3 py-2 text-center text-sm text-orange-600">{record.early_leave_minutes}</td>
                                    <td className="px-3 py-2 text-center text-sm text-red-600">{record.deficit_minutes}</td>
                                    <td className="px-3 py-2 text-center text-sm font-semibold text-red-700">{record.deduction_amount.toFixed(2)}</td>
                                    <td className="px-3 py-2 text-center text-sm">
                                      {record.is_absent ? (
                                        <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs">غياب</span>
                                      ) : record.deficit_minutes > 0 ? (
                                        <span className="bg-orange-100 text-orange-700 px-2 py-1 rounded text-xs">خصم</span>
                                      ) : (
                                        <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs">مكتمل</span>
                                      )}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* No Data */}
      {!loading && reportData && (!reportData.summaries || reportData.summaries.length === 0) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <p className="text-yellow-700 text-lg">⚠️ لا توجد بيانات للفترة المحددة</p>
          <p className="text-yellow-600 text-sm mt-2">اضغط على "حساب الخصومات" لتوليد التقرير</p>
        </div>
      )}
    </div>
  );
};

export default AdvancedDeductionsReport;
