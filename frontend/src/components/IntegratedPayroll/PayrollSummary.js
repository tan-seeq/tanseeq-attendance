import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { DocumentArrowDownIcon, CalculatorIcon, LockClosedIcon, LockOpenIcon, PencilIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useParams } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PayrollSummary = () => {
  const { id } = useParams();
  const [cycle, setCycle] = useState(null);
  const [employeeSummaries, setEmployeeSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editedData, setEditedData] = useState([]);
  const [saving, setSaving] = useState(false);

  const fetchCycleData = async () => {
    try {
      setLoading(true);
      const cycleRes = await axios.get(`${API}/payroll/cycles/${id}`);
      setCycle(cycleRes.data);
      
      // Fetch employee summaries
      try {
        const summariesRes = await axios.get(`${API}/payroll/cycles/${id}/summary`);
        if (summariesRes.data && Array.isArray(summariesRes.data.employee_summaries)) {
          setEmployeeSummaries(summariesRes.data.employee_summaries);
        }
      } catch (err) {
        console.warn('Could not fetch employee summaries:', err);
      }
      
      setError('');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'تعذر تحميل بيانات دورة الرواتب');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCycleData();
  }, [id]);

  const handleCalculate = async () => {
    try {
      await axios.post(`${API}/payroll/cycles/${id}/recalculate`);
      alert('تم حساب الرواتب بنجاح');
      fetchCycleData();
    } catch (err) {
      alert(err.response?.data?.detail || 'فشل حساب الرواتب');
    }
  };

  const handleViewSalaryLetter = async (employeeId, format) => {
    try {
      const response = await axios.get(
        `${API}/payroll/cycles/${id}/employees/${employeeId}/letter?format=${format}`,
        { responseType: format === 'pdf' ? 'blob' : 'text' }
      );
      
      if (format === 'html') {
        // Open HTML in new window
        const newWindow = window.open('', '_blank');
        newWindow.document.write(response.data);
        newWindow.document.close();
      }
    } catch (error) {
      console.error('Error viewing salary letter:', error);
      alert('حدث خطأ في عرض رسالة الراتب');
    }
  };

  const handleDownloadSalaryLetter = async (employeeId, format) => {
    try {
      const response = await axios.get(
        `${API}/payroll/cycles/${id}/employees/${employeeId}/letter?format=${format}`,
        { responseType: 'blob' }
      );
      
      // Create download link
      const blob = new Blob([response.data], { 
        type: format === 'pdf' ? 'application/pdf' : 'text/html' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `salary_letter_${employeeId.slice(0, 8)}_${id.slice(0, 8)}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading salary letter:', error);
      alert('حدث خطأ في تحميل رسالة الراتب');
    }
  };

  const handleExportCycle = async (format) => {
    try {
      const response = await axios.get(
        `${API}/payroll/cycles/${id}/export/${format}`,
        { responseType: 'blob' }
      );
      
      // Create download link
      const blob = new Blob([response.data], { 
        type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `payroll_cycle_${cycle.month}_${id.slice(0, 8)}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting cycle:', error);
      alert('حدث خطأ في تصدير الملف');
    }
  };

  const handleLock = async () => {
    const lock_reason = prompt('الرجاء إدخال سبب القفل (10 أحرف على الأقل):');
    if (!lock_reason || lock_reason.length < 10) {
      alert('يجب إدخال سبب القفل (10 أحرف على الأقل)');
      return;
    }
    try {
      await axios.post(`${API}/payroll/cycles/${id}/lock`, { lock_reason });
      alert('تم قفل الدورة بنجاح');
      fetchCycleData();
    } catch (err) {
      alert(err.response?.data?.detail || 'فشل قفل الدورة');
    }
  };

  const handleUnlock = async () => {
    const reason = prompt('الرجاء إدخال سبب فتح الدورة (10 أحرف على الأقل):');
    if (!reason || reason.length < 10) {
      alert('يجب إدخال سبب فتح الدورة (10 أحرف على الأقل)');
      return;
    }
    try {
      await axios.post(`${API}/payroll/cycles/${id}/unlock`, { reason });
      alert('تم فتح الدورة بنجاح');
      fetchCycleData();
    } catch (err) {
      alert(err.response?.data?.detail || 'فشل فتح الدورة');
    }
  };

  const handleStartEdit = () => {
    // Initialize edited data with current employee summaries
    const initialData = employeeSummaries.map(emp => ({
      employee_id: emp.employee_id,
      employee_name: emp.employee_name,
      base_salary: emp.base_salary || 0,
      allowances: emp.total_allowances || 0,
      manual_deductions: emp.manual_deductions || 0,
      attendance_deductions: emp.attendance_deductions || 0,
      advance_deductions: emp.advance_deductions || 0,
      gross_salary: emp.gross_salary || 0,
      total_deductions: emp.total_deductions || 0,
      net_salary: emp.net_salary || 0
    }));
    // Support setting nested manual_override in editedData
    if (field === 'manual_override') {
      setEditedData(prev => prev.map(emp => {
        if (emp.employee_id === employeeId) {
          const newEmp = { ...emp, manual_override: value };
          // Optionally recompute attendance_deductions based on manual overrides if provided
          const hasAbsenceAmt = value && value.absence_amount !== undefined && value.absence_amount !== null;
          const hasLateAmt = value && value.late_amount !== undefined && value.late_amount !== null;
          if (hasAbsenceAmt || hasLateAmt) {
            const attendance = (hasAbsenceAmt ? parseFloat(value.absence_amount) || 0 : (emp.attendance_deductions || 0))
              + (hasLateAmt ? parseFloat(value.late_amount) || 0 : 0);
            newEmp.attendance_deductions = attendance;
            const gross = (newEmp.base_salary || 0) + (newEmp.allowances || 0);
            const total = (newEmp.manual_deductions || 0) + (newEmp.attendance_deductions || 0) + (newEmp.advance_deductions || 0);
            newEmp.gross_salary = gross;
            newEmp.total_deductions = total;
            newEmp.net_salary = gross - total;
          }
          return newEmp;
        }
        return emp;
      }));
      return;
    }

    setEditedData(initialData);
    setEditMode(true);
  };

  const handleCancelEdit = () => {
    setEditMode(false);
    setEditedData([]);
  };

  const handleFieldChange = (employeeId, field, value) => {
    setEditedData(prev => {
      const updated = prev.map(emp => {
        if (emp.employee_id === employeeId) {
          const newEmp = { ...emp, [field]: parseFloat(value) || 0 };
          
          // Auto-calculate totals
          newEmp.gross_salary = newEmp.base_salary + newEmp.allowances;
          newEmp.total_deductions = (newEmp.manual_deductions || 0) + (newEmp.attendance_deductions || 0) + (newEmp.advance_deductions || 0);
          newEmp.net_salary = newEmp.gross_salary - newEmp.total_deductions;
          
          return newEmp;
        }
        return emp;
      });
      return updated;
    });
  };

  // Helper: update manual_override safely and recompute totals
  const updateManualOverride = (employeeId, key, rawValue) => {
    setEditedData(prev => prev.map(emp => {
      if (emp.employee_id !== employeeId) return emp;
      const value = (rawValue === '' || rawValue === undefined || rawValue === null) ? null : rawValue;
      const currentMO = emp.manual_override ? { ...emp.manual_override } : {};
      currentMO[key] = value;
      const newEmp = { ...emp, manual_override: currentMO };
      // If amounts provided, recompute attendance_deductions and totals
      const absAmt = (currentMO.absence_amount !== undefined && currentMO.absence_amount !== null) ? parseFloat(currentMO.absence_amount) || 0 : null;
      const lateAmt = (currentMO.late_amount !== undefined && currentMO.late_amount !== null) ? parseFloat(currentMO.late_amount) || 0 : null;
      if (absAmt !== null || lateAmt !== null) {
        const attendance = (absAmt !== null ? absAmt : (newEmp.attendance_deductions || 0)) + (lateAmt !== null ? lateAmt : 0);
        newEmp.attendance_deductions = attendance;
      }
      const gross = (newEmp.base_salary || 0) + (newEmp.allowances || 0);
      const total = (newEmp.manual_deductions || 0) + (newEmp.attendance_deductions || 0) + (newEmp.advance_deductions || 0);
      newEmp.gross_salary = gross;
      newEmp.total_deductions = total;
      newEmp.net_salary = gross - total;
      return newEmp;
    }));
  };

  const handleSaveChanges = async () => {
    if (!editedData || editedData.length === 0) {
      alert('لا توجد بيانات للحفظ');
      return;
    }

    try {
      setSaving(true);
      
      const payload = {
        employees: editedData.map(emp => ({
          employee_id: emp.employee_id,
          employee_name: emp.employee_name,
          base_salary: emp.base_salary,
          allowances: emp.allowances,
          manual_deductions: emp.manual_deductions,
          attendance_deductions: emp.attendance_deductions,
          advance_deductions: emp.advance_deductions,
          // Optional manual overrides for detailed breakdown
          manual_override: emp.manual_override || null,
        })),
        notes: `تم التعديل بواسطة Super Admin في ${new Date().toLocaleString('ar-AE')}`
      };

      console.log('💾 Saving payload:', payload);
      console.log('📊 Number of employees:', payload.employees.length);
      
      const response = await axios.put(`${API}/payroll/cycles/${id}/update-employees`, payload);
      
      console.log('✅ Save response:', response.data);
      alert('تم حفظ التعديلات بنجاح ✅\n' + (response.data.message || ''));
      setEditMode(false);
      setEditedData([]);
      fetchCycleData();
    } catch (err) {
      console.error('❌ Save error:', err);
      console.error('Error details:', err.response?.data);
      const errorMsg = err.response?.data?.detail || 'فشل حفظ التعديلات';
      alert('خطأ في الحفظ: ' + errorMsg);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mb-4">
          {error}
        </div>
        <a href="/payroll-cycles" className="inline-flex items-center text-blue-600 hover:underline">
          عودة إلى إدارة الدورات
        </a>
      </div>
    );
  }

  if (!cycle) return null;

  const displayData = editMode ? editedData : employeeSummaries;
  
  // Calculate totals
  const totals = displayData.reduce((acc, emp) => ({
    gross: acc.gross + (emp.gross_salary || emp.base_salary + (emp.allowances || emp.total_allowances || 0)),
    deductions: acc.deductions + (emp.total_deductions || 0),
    net: acc.net + (emp.net_salary || 0)
  }), { gross: 0, deductions: 0, net: 0 });

  return (
    <div className="max-w-[95%] mx-auto p-6" dir="rtl"> {/* ✅ FIXED: Increased from max-w-7xl to 95% for wider display */}
      {/* Header Card */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ملخص دورة الرواتب</h1>
            <p className="text-gray-600 mt-1">
              {cycle.display_name} — الحالة: 
              <span className={`font-semibold mr-2 ${cycle.is_locked ? 'text-red-600' : 'text-green-600'}`}>
                {cycle.is_locked ? 'مقفولة' : 'مفتوحة'}
              </span>
            </p>
          </div>
          
          <div className="flex items-center gap-2 flex-wrap">
            {/* Edit/Save/Cancel Buttons */}
            {!editMode ? (
              !cycle.is_locked && (
                <button 
                  onClick={handleStartEdit}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 inline-flex items-center"
                >
                  <PencilIcon className="w-5 h-5 ml-2" /> تعديل الرواتب
                </button>
              )
            ) : (
              <>
                <button 
                  onClick={handleSaveChanges}
                  disabled={saving}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 inline-flex items-center disabled:opacity-50"
                >
                  <CheckIcon className="w-5 h-5 ml-2" /> {saving ? 'جاري الحفظ...' : 'حفظ التعديلات'}
                </button>
                <button 
                  onClick={handleCancelEdit}
                  disabled={saving}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 inline-flex items-center disabled:opacity-50"
                >
                  <XMarkIcon className="w-5 h-5 ml-2" /> إلغاء
                </button>
              </>
            )}
            
            {/* Export Buttons */}
            {!editMode && (
              <>
                <button 
                  onClick={() => handleExportCycle('pdf')} 
                  className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 inline-flex items-center"
                >
                  <DocumentArrowDownIcon className="w-5 h-5 ml-2" /> PDF
                </button>
                <button 
                  onClick={() => handleExportCycle('excel')} 
                  className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 inline-flex items-center"
                >
                  <DocumentArrowDownIcon className="w-5 h-5 ml-2" /> Excel
                </button>
              </>
            )}
            
            {/* Calculate/Export/Lock/Unlock Buttons */}
            {!editMode && !cycle.is_locked && (
              <>
                <button 
                  onClick={handleCalculate} 
                  className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 inline-flex items-center"
                >
                  <CalculatorIcon className="w-5 h-5 ml-2" /> حساب الرواتب
                </button>
                
                {/* Export Buttons */}
                <button 
                  onClick={() => handleExportCycle('pdf')}
                  className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 inline-flex items-center"
                >
                  <DocumentArrowDownIcon className="w-5 h-5 ml-2" /> تصدير PDF
                </button>
                
                <button 
                  onClick={() => handleExportCycle('excel')}
                  className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 inline-flex items-center"
                >
                  <DocumentArrowDownIcon className="w-5 h-5 ml-2" /> تصدير Excel
                </button>
                
                <button 
                  onClick={handleLock} 
                  className="px-3 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 inline-flex items-center"
                >
                  <LockClosedIcon className="w-5 h-5 ml-2" /> قفل الدورة
                </button>
              </>
            )}
            
            {!editMode && cycle.is_locked && (
              <>
                {/* Export Buttons for locked cycle */}
                <button 
                  onClick={() => handleExportCycle('pdf')}
                  className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 inline-flex items-center"
                >
                  <DocumentArrowDownIcon className="w-5 h-5 ml-2" /> تصدير PDF
                </button>
                
                <button 
                  onClick={() => handleExportCycle('excel')}
                  className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 inline-flex items-center"
                >
                  <DocumentArrowDownIcon className="w-5 h-5 ml-2" /> تصدير Excel
                </button>
                
                <button 
                  onClick={handleUnlock} 
                  className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 inline-flex items-center"
                >
                  <LockOpenIcon className="w-5 h-5 ml-2" /> فتح الدورة
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Totals Summary Card */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">الإجماليات</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6">
          <div>
            <p className="text-sm text-gray-500">عدد الموظفين</p>
            <p className="text-2xl font-bold">{displayData.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">إجمالي الرواتب</p>
            <p className="text-2xl font-bold text-green-600">{totals.gross.toFixed(2)} درهم</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">إجمالي الخصومات</p>
            <p className="text-2xl font-bold text-red-600">{totals.deductions.toFixed(2)} درهم</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">الصافي</p>
            <p className="text-2xl font-bold text-blue-600">{totals.net.toFixed(2)} درهم</p>
          </div>
        </div>
      </div>

      {/* Employee Details Table */}
      {displayData && displayData.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              {editMode ? 'تعديل رواتب الموظفين' : 'تفاصيل الموظفين'}
            </h2>
            {editMode && (
              <span className="text-sm text-orange-600 font-medium">
                ⚠️ وضع التعديل - تأكد من حفظ التغييرات
              </span>
            )}
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase">الموظف</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase">الراتب الأساسي</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase">البدلات</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase">إجمالي الراتب</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase">خصم يدوي</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase" title="خصم الحضور والتأخير">
                    خصم حضور
                    <div className="text-xs font-normal text-gray-500 mt-1">(غياب + تأخير)</div>
                  </th>
                  {/* Manual overrides editable columns */}
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase" title="أيام الغياب (تعديل يدوي)">🔴 أيام غياب (يدوي)</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase" title="مبلغ خصم الغياب (تعديل يدوي)">مبلغ غياب (يدوي)</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase" title="دقائق التأخير (تعديل يدوي)">🟠 دقائق تأخير (يدوي)</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase" title="مبلغ خصم التأخير (تعديل يدوي)">مبلغ تأخير (يدوي)</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase">خصم سلف</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase">إجمالي الخصومات</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase bg-blue-50">صافي الراتب</th>
                  <th className="px-4 py-4 text-right text-sm font-bold text-gray-700 uppercase">رسالة الراتب</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {displayData.map((emp) => {
                  const baseSalary = editMode ? emp.base_salary : (emp.base_salary || 0);
                  const allowances = editMode ? emp.allowances : (emp.total_allowances || 0);
                  const manualDed = editMode ? emp.manual_deductions : (emp.manual_deductions || 0);
                  const attendDed = emp.attendance_deductions || 0;
                  const advanceDed = emp.advance_deductions || 0;
                  const grossSalary = editMode ? emp.gross_salary : (emp.gross_salary || baseSalary + allowances);
                  const totalDed = editMode ? emp.total_deductions : (emp.total_deductions || manualDed + attendDed + advanceDed);
                  const netSalary = editMode ? emp.net_salary : (emp.net_salary || grossSalary - totalDed);
                  
                  // ✅ NEW: Get detailed deduction breakdown from unified engine
                  const absentDays = (emp.manual_override && emp.manual_override.absent_days !== undefined && emp.manual_override.absent_days !== null)
                    ? emp.manual_override.absent_days
                    : (emp.absent_days || 0);
                  const absenceAmount = (emp.manual_override && emp.manual_override.absence_amount !== undefined && emp.manual_override.absence_amount !== null)
                    ? emp.manual_override.absence_amount
                    : (emp.absence_amount || 0);
                  const lateDays = emp.late_days || 0; // not overridden
                  const lateMinutes = (emp.manual_override && emp.manual_override.late_minutes !== undefined && emp.manual_override.late_minutes !== null)
                    ? emp.manual_override.late_minutes
                    : (emp.late_minutes || 0);
                  const lateAmount = (emp.manual_override && emp.manual_override.late_amount !== undefined && emp.manual_override.late_amount !== null)
                    ? emp.manual_override.late_amount
                    : (emp.late_amount || 0);

                  return (
                    <tr key={emp.employee_id} className={editMode ? 'hover:bg-blue-50' : 'hover:bg-gray-50'}>
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {emp.employee_name}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm">
                        {editMode ? (
                          <input
                            type="number"
                            step="0.01"
                            value={baseSalary}
                            onChange={(e) => handleFieldChange(emp.employee_id, 'base_salary', e.target.value)}
                            className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          />
                        ) : (
                          <span className="text-base font-medium">{baseSalary.toFixed(2)}</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm">
                        {editMode ? (
                          <input
                            type="number"
                            step="0.01"
                            value={allowances}
                            onChange={(e) => handleFieldChange(emp.employee_id, 'allowances', e.target.value)}
                            className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          />
                        ) : (
                          <span className="text-base font-medium">{allowances.toFixed(2)}</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                        <span className="text-base">{grossSalary.toFixed(2)}</span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm">
                        {editMode ? (
                          <input
                            type="number"
                            step="0.01"
                            value={manualDed}
                            onChange={(e) => handleFieldChange(emp.employee_id, 'manual_deductions', e.target.value)}
                            className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-red-500"
                          />
                        ) : (
                          <span className="text-red-600 text-base font-medium">{manualDed.toFixed(2)}</span>
                        )}
                      </td>
                      {/* Manual override inputs */}
                      {editMode && (
                        <>
                          <td className="px-4 py-4 whitespace-nowrap text-sm">
                            <input
                              type="number"
                              step="1"
                              value={(emp.manual_override && emp.manual_override.absent_days !== undefined && emp.manual_override.absent_days !== null) ? emp.manual_override.absent_days : ''}
                              onChange={(e) => updateManualOverride(emp.employee_id, 'absent_days', e.target.value === '' ? null : parseInt(e.target.value, 10))}
                              className="w-24 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              placeholder="—"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm">
                            <input
                              type="number"
                              step="0.01"
                              value={(emp.manual_override && emp.manual_override.absence_amount !== undefined && emp.manual_override.absence_amount !== null) ? emp.manual_override.absence_amount : ''}
                              onChange={(e) => updateManualOverride(emp.employee_id, 'absence_amount', e.target.value === '' ? null : parseFloat(e.target.value))}
                              className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              placeholder="—"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm">
                            <input
                              type="number"
                              step="1"
                              value={(emp.manual_override && emp.manual_override.late_minutes !== undefined && emp.manual_override.late_minutes !== null) ? emp.manual_override.late_minutes : ''}
                              onChange={(e) => updateManualOverride(emp.employee_id, 'late_minutes', e.target.value === '' ? null : parseInt(e.target.value, 10))}
                              className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              placeholder="—"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm">
                            <input
                              type="number"
                              step="0.01"
                              value={(emp.manual_override && emp.manual_override.late_amount !== undefined && emp.manual_override.late_amount !== null) ? emp.manual_override.late_amount : ''}
                              onChange={(e) => updateManualOverride(emp.employee_id, 'late_amount', e.target.value === '' ? null : parseFloat(e.target.value))}
                              className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              placeholder="—"
                            />
                          </td>
                        </>
                      )}

                      {!editMode && (
                        <>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-center">{absentDays > 0 ? absentDays : <span className="text-gray-400">-</span>}</td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-center">{absenceAmount > 0 ? absenceAmount.toFixed(2) : <span className="text-gray-400">0.00</span>}</td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-center">{lateMinutes > 0 ? `${lateMinutes}` : <span className="text-gray-400">-</span>}</td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-center">{lateAmount > 0 ? lateAmount.toFixed(2) : <span className="text-gray-400">0.00</span>}</td>
                        </>
                      )}
                      {/* Manual override inputs */}
                      {editMode && (
                        <>
                          <td className="px-4 py-4 whitespace-nowrap text-sm">
                            <input
                              type="number"
                              step="1"
                              value={(emp.manual_override && emp.manual_override.absent_days !== undefined && emp.manual_override.absent_days !== null) ? emp.manual_override.absent_days : ''}
                              onChange={(e) => updateManualOverride(emp.employee_id, 'absent_days', e.target.value === '' ? null : parseInt(e.target.value, 10))}
                              className="w-24 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              placeholder="—"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm">
                            <input
                              type="number"
                              step="0.01"
                              value={(emp.manual_override && emp.manual_override.absence_amount !== undefined && emp.manual_override.absence_amount !== null) ? emp.manual_override.absence_amount : ''}
                              onChange={(e) => updateManualOverride(emp.employee_id, 'absence_amount', e.target.value === '' ? null : parseFloat(e.target.value))}
                              className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              placeholder="—"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm">
                            <input
                              type="number"
                              step="1"
                              value={(emp.manual_override && emp.manual_override.late_minutes !== undefined && emp.manual_override.late_minutes !== null) ? emp.manual_override.late_minutes : ''}
                              onChange={(e) => updateManualOverride(emp.employee_id, 'late_minutes', e.target.value === '' ? null : parseInt(e.target.value, 10))}
                              className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              placeholder="—"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm">
                            <input
                              type="number"
                              step="0.01"
                              value={(emp.manual_override && emp.manual_override.late_amount !== undefined && emp.manual_override.late_amount !== null) ? emp.manual_override.late_amount : ''}
                              onChange={(e) => updateManualOverride(emp.employee_id, 'late_amount', e.target.value === '' ? null : parseFloat(e.target.value))}
                              className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              placeholder="—"
                            />
                          </td>
                        </>
                      )}

                      {!editMode && (
                        <>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-center">{absentDays > 0 ? absentDays : <span className="text-gray-400">-</span>}</td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-center">{absenceAmount > 0 ? absenceAmount.toFixed(2) : <span className="text-gray-400">0.00</span>}</td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-center">{lateMinutes > 0 ? `${lateMinutes}` : <span className="text-gray-400">-</span>}</td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-center">{lateAmount > 0 ? lateAmount.toFixed(2) : <span className="text-gray-400">0.00</span>}</td>
                        </>
                      )}

                            value={manualDed}
                            onChange={(e) => handleFieldChange(emp.employee_id, 'manual_deductions', e.target.value)}
                            className="w-28 px-3 py-2 text-base border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-red-500"
                          />
                        ) : (
                          <span className="text-red-600 text-base font-medium">{manualDed.toFixed(2)}</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm">
                        {editMode ? (
                          <input
                            type="number"
                            step="0.01"
                            value={attendDed}
                            onChange={(e) => handleFieldChange(emp.employee_id, 'attendance_deductions', e.target.value)}
                            className="w-28 px-3 py-2 text-base border border-orange-300 rounded focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                          />
                        ) : (
                          <span className="text-red-600 font-semibold text-base">{attendDed.toFixed(2)}</span>
                        )}
                      </td>
                      
                      {/* ✅ NEW: Detailed absence breakdown */}
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                        {absentDays > 0 ? (
                          <span className="inline-flex items-center px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-bold">
                            🔴 {absentDays}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                        {absenceAmount > 0 ? (
                          <span className="text-red-700 font-semibold">{absenceAmount.toFixed(2)}</span>
                        ) : (
                          <span className="text-gray-400">0.00</span>
                        )}
                      </td>
                      
                      {/* ✅ NEW: Detailed late breakdown */}
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                        {lateMinutes > 0 ? (
                          <span className="inline-flex items-center px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-bold">
                            🟠 {lateMinutes} min ({lateDays} days)
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-center">
                        {lateAmount > 0 ? (
                          <span className="text-orange-700 font-semibold">{lateAmount.toFixed(2)}</span>
                        ) : (
                          <span className="text-gray-400">0.00</span>
                        )}
                      </td>
                      
                      <td className="px-4 py-4 whitespace-nowrap text-sm">
                        {editMode ? (
                          <input
                            type="number"
                            step="0.01"
                            value={advanceDed}
                            onChange={(e) => handleFieldChange(emp.employee_id, 'advance_deductions', e.target.value)}
                            className="w-28 px-3 py-2 text-base border border-purple-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                          />
                        ) : (
                          <span className="text-red-600 text-base font-medium">{advanceDed.toFixed(2)}</span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-red-600">
                        <span className="text-base">{totalDed.toFixed(2)}</span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-bold text-blue-600">
                        <span className="text-lg">{netSalary.toFixed(2)}</span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm">
                        <div className="flex flex-col gap-2">
                          <button
                            onClick={() => handleViewSalaryLetter(emp.employee_id, 'html')}
                            className="inline-flex items-center justify-center px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors text-xs"
                          >
                            <DocumentArrowDownIcon className="h-4 w-4 ml-1" />
                            عرض الرسالة
                          </button>
                          <button
                            onClick={() => handleDownloadSalaryLetter(emp.employee_id, 'pdf')}
                            className="inline-flex items-center justify-center px-3 py-1 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors text-xs"
                          >
                            <DocumentArrowDownIcon className="h-4 w-4 ml-1" />
                            تحميل PDF
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot className="bg-gray-100">
                <tr>
                  <td className="px-4 py-4 text-sm font-bold text-gray-900" colSpan="3">الإجمالي:</td>
                  <td className="px-4 py-4 text-sm font-bold text-green-600">{totals.gross.toFixed(2)}</td>
                  <td className="px-4 py-4 text-sm" colSpan="6"></td>
                  <td className="px-4 py-4 text-sm font-bold text-red-600">{totals.deductions.toFixed(2)}</td>
                  <td className="px-4 py-4 text-sm font-bold text-blue-600">{totals.net.toFixed(2)}</td>
                  <td className="px-4 py-4 text-sm"></td>
                </tr>
              </tfoot>
            </table>
          </div>
          
          {editMode && (
            <div className="px-6 py-4 bg-blue-50 border-t border-blue-200">
              <p className="text-sm text-blue-800">
                ℹ️ <strong>ملاحظة:</strong> يمكنك الآن تعديل:
              </p>
              <ul className="text-sm text-blue-700 mt-2 mr-6 list-disc">
                <li><strong>الراتب الأساسي والبدلات</strong> - يؤثر على إجمالي الراتب</li>
                <li><strong>الخصم اليدوي</strong> - خصومات يدوية إضافية</li>
                <li><strong>خصم الحضور</strong> - خصومات التأخير والغياب <span className="text-orange-600 font-bold">✨ جديد!</span></li>
                <li><strong>خصم السلف</strong> - أقساط السلف الشهرية <span className="text-purple-600 font-bold">✨ جديد!</span></li>
              </ul>
              <p className="text-sm text-blue-700 mt-2">
                سيتم حساب الإجماليات وصافي الراتب تلقائياً عند أي تغيير.
              </p>
            </div>
          )}
        </div>
      )}

      {(!displayData || displayData.length === 0) && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <p className="text-gray-500 text-lg">لا توجد بيانات موظفين لهذه الدورة</p>
          <p className="text-gray-400 text-sm mt-2">اضغط على "حساب الرواتب" لإنشاء كشف الرواتب</p>
        </div>
      )}
    </div>
  );
};

export default PayrollSummary;
