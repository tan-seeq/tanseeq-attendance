import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  DocumentArrowDownIcon,
  XMarkIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API } from '../../config';

const AttendanceManagement = () => {
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingRecord, setEditingRecord] = useState(null);
  const [editData, setEditData] = useState({});
  const [showAbsenceModal, setShowAbsenceModal] = useState(false);
  const [absenceData, setAbsenceData] = useState({});
  const [missingEmployees, setMissingEmployees] = useState([]);
  const [showMissingModal, setShowMissingModal] = useState(false);
  
  // NEW: Manual Attendance State
  const [showManualAttendanceModal, setShowManualAttendanceModal] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [manualAttendanceForm, setManualAttendanceForm] = useState({
    employee_id: '',
    start_date: '',
    end_date: '',
    check_in_time: '09:00',
    check_out_time: '18:00'
  });
  const [missingDays, setMissingDays] = useState([]);
  const [selectedMissingDays, setSelectedMissingDays] = useState([]);
  const [loadingMissingDays, setLoadingMissingDays] = useState(false);
  const [addingManualRecords, setAddingManualRecords] = useState(false);
  
  // NEW: Manual Absence State
  const [showManualAbsenceModal, setShowManualAbsenceModal] = useState(false);
  const [manualAbsenceForm, setManualAbsenceForm] = useState({
    employee_id: '',
    start_date: '',
    end_date: '',
    absence_type: 'full_day',
    reason: ''
  });
  const [missingDaysForAbsence, setMissingDaysForAbsence] = useState([]);
  const [selectedAbsenceDays, setSelectedAbsenceDays] = useState([]);
  const [loadingMissingDaysAbsence, setLoadingMissingDaysAbsence] = useState(false);
  const [addingAbsenceRecords, setAddingAbsenceRecords] = useState(false);
  
  // NEW: Custom Report State
  const [showCustomReportModal, setShowCustomReportModal] = useState(false);
  const [customReportForm, setCustomReportForm] = useState({
    employee_ids: [],
    start_date: '',
    end_date: '',
    format: 'excel'
  });
  const [generatingReport, setGeneratingReport] = useState(false);
  
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchAllAttendance();
    if (user?.role === 'super_admin') {
      fetchEmployees();
    }
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setEmployees(response.data || []);
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  const fetchAllAttendance = async () => {
    try {
      // Use the enhanced endpoint that shows absences
      const response = await axios.get(`${API}/attendance/with-absences`);
      setAttendance(response.data);
    } catch (error) {
      console.error('Error fetching attendance:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (record) => {
    setEditingRecord(record.id);
    
    // Convert display status to backend format
    let backendStatus = record.status;
    if (record.status === 'Present') backendStatus = 'present';
    else if (record.status === 'Late') backendStatus = 'late';  
    else if (record.status === 'Absent') backendStatus = 'absent';
    
    setEditData({
      check_in: record.check_in || '',
      check_out: record.check_out || '',
      status: backendStatus,
      reason: record.absence_reason || '',
      leave_type: record.leave_type || ''
    });
  };

  const handleSave = async (id) => {
    try {
      // Always use the regular attendance update endpoint
      // It will handle all status changes properly
      const updateData = {
        check_in: editData.check_in || null,
        check_out: editData.check_out || null,
        status: editData.status,
        reason: editData.reason || null,
        leave_type: editData.leave_type || null
      };

      await axios.put(`${API}/attendance/${id}`, updateData);
      
      setEditingRecord(null);
      setEditData({});
      fetchAllAttendance();
      
      // Show success message
      alert('تم تحديث سجل الحضور بنجاح');
    } catch (error) {
      console.error('Error updating attendance:', error);
      alert('حدث خطأ في تحديث سجل الحضور: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCancel = () => {
    setEditingRecord(null);
    setEditData({});
  };

  const handleCreateAbsence = async () => {
    try {
      await axios.post(`${API}/attendance/create-absence`, absenceData);
      setShowAbsenceModal(false);
      setAbsenceData({});
      fetchAllAttendance();
      alert('تم إنشاء سجل الغياب بنجاح');
    } catch (error) {
      console.error('Error creating absence:', error);
      alert('حدث خطأ في إنشاء سجل الغياب');
    }
  };

  const handleCheckMissingEmployees = async () => {
    try {
      const response = await axios.get(`${API}/attendance/missing-today`);
      setMissingEmployees(response.data.missing_employees);
      setShowMissingModal(true);
    } catch (error) {
      console.error('Error fetching missing employees:', error);
      alert('حدث خطأ في جلب بيانات الموظفين الغائبين');
    }
  };

  const handleProcessDailyAbsences = async (date = null) => {
    const targetDate = date || new Date().toISOString().split('T')[0];
    if (window.confirm(`هل أنت متأكد من معالجة الغياب التلقائي لتاريخ ${targetDate}؟`)) {
      try {
        const response = await axios.post(`${API}/attendance/process-daily-absences`, { date: targetDate });
        alert(`تم إنشاء ${response.data.absences_created} سجل غياب تلقائي من أصل ${response.data.total_employees} موظف`);
        fetchAllAttendance();
        setShowMissingModal(false);
      } catch (error) {
        console.error('Error processing daily absences:', error);
        alert('حدث خطأ في معالجة الغياب التلقائي');
      }
    }
  };

  const handleDeleteAbsence = async (id) => {
    if (window.confirm('هل أنت متأكد من حذف سجل الغياب؟')) {
      try {
        await axios.delete(`${API}/attendance/delete-absence/${id}`);
        fetchAllAttendance();
        alert('تم حذف سجل الغياب بنجاح');
      } catch (error) {
        console.error('Error deleting absence:', error);
        alert('حدث خطأ في حذف سجل الغياب');
      }
    }
  };

  const handleDeleteAttendance = async (id, record) => {
    const employeeName = record.user_name || 'غير محدد';
    const date = record.date || 'غير محدد';
    const status = record.status || 'غير محدد';
    
    const confirmMessage = `هل أنت متأكد من حذف سجل الحضور؟\n\nالموظف: ${employeeName}\nالتاريخ: ${date}\nالحالة: ${status}`;
    
    if (window.confirm(confirmMessage)) {
      try {
        await axios.delete(`${API}/attendance/${id}`);
        fetchAllAttendance();
        alert('تم حذف سجل الحضور بنجاح');
      } catch (error) {
        console.error('Error deleting attendance:', error);
        const errorMessage = error.response?.data?.detail || 'حدث خطأ في حذف سجل الحضور';
        alert(errorMessage);
      }
    }
  };

  // NEW: Manual Attendance Handlers
  const handleFetchMissingDays = async () => {
    if (!manualAttendanceForm.employee_id || !manualAttendanceForm.start_date || !manualAttendanceForm.end_date) {
      alert('الرجاء اختيار الموظف والفترة');
      return;
    }

    try {
      setLoadingMissingDays(true);
      const response = await axios.get(
        `${API}/attendance/missing-days/${manualAttendanceForm.employee_id}?start_date=${manualAttendanceForm.start_date}&end_date=${manualAttendanceForm.end_date}`
      );
      
      setMissingDays(response.data.missing_days || []);
      setSelectedMissingDays(response.data.missing_days.map(d => d.date) || []);
      
      if (response.data.missing_days.length === 0) {
        alert('لا توجد أيام مفقودة في هذه الفترة ✅');
      }
    } catch (error) {
      console.error('Error fetching missing days:', error);
      alert('حدث خطأ في جلب الأيام المفقودة');
    } finally {
      setLoadingMissingDays(false);
    }
  };

  const handleAddManualAttendance = async () => {
    if (selectedMissingDays.length === 0) {
      alert('الرجاء اختيار الأيام المراد إضافتها');
      return;
    }

    if (!manualAttendanceForm.check_in_time || !manualAttendanceForm.check_out_time) {
      alert('الرجاء تحديد وقت الحضور والانصراف');
      return;
    }

    try {
      setAddingManualRecords(true);
      const response = await axios.post(`${API}/attendance/bulk-add-manual`, {
        employee_id: manualAttendanceForm.employee_id,
        missing_days: selectedMissingDays,
        check_in_time: `${manualAttendanceForm.check_in_time}:00`,
        check_out_time: `${manualAttendanceForm.check_out_time}:00`
      });

      alert(response.data.message);
      
      // Reset and close
      setShowManualAttendanceModal(false);
      setManualAttendanceForm({
        employee_id: '',
        start_date: '',
        end_date: '',
        check_in_time: '09:00',
        check_out_time: '18:00'
      });
      setMissingDays([]);
      setSelectedMissingDays([]);
      
      // Refresh attendance data
      fetchAllAttendance();
    } catch (error) {
      console.error('Error adding manual attendance:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في إضافة السجلات');
    } finally {
      setAddingManualRecords(false);
    }
  };

  const toggleDaySelection = (date) => {
    if (selectedMissingDays.includes(date)) {
      setSelectedMissingDays(selectedMissingDays.filter(d => d !== date));
    } else {
      setSelectedMissingDays([...selectedMissingDays, date]);
    }
  };

  // NEW: Custom Report Handler
  const handleGenerateCustomReport = async () => {
    if (customReportForm.employee_ids.length === 0) {
      alert('الرجاء اختيار موظف واحد على الأقل');
      return;
    }
    
    if (!customReportForm.start_date || !customReportForm.end_date) {
      alert('الرجاء تحديد الفترة');
      return;
    }

    try {
      setGeneratingReport(true);
      const response = await axios.post(`${API}/attendance/custom-report`, customReportForm);
      
      // تحويل base64 إلى blob وتحميل الملف
      const byteCharacters = atob(response.data.file_content);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: response.data.content_type });
      
      // إنشاء رابط تحميل
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = response.data.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      alert(`✅ تم تصدير التقرير بنجاح\nعدد السجلات: ${response.data.records_count}\nعدد الموظفين: ${response.data.employees_count}`);
      
      // Reset form
      setShowCustomReportModal(false);
      setCustomReportForm({
        employee_ids: [],
        start_date: '',
        end_date: '',
        format: 'excel'
      });
      
    } catch (error) {
      console.error('Error generating report:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في إنشاء التقرير');
    } finally {
      setGeneratingReport(false);
    }
  };

  const toggleEmployeeSelection = (employeeId) => {
    if (customReportForm.employee_ids.includes(employeeId)) {
      setCustomReportForm({
        ...customReportForm,
        employee_ids: customReportForm.employee_ids.filter(id => id !== employeeId)
      });
    } else {
      setCustomReportForm({
        ...customReportForm,
        employee_ids: [...customReportForm.employee_ids, employeeId]
      });
    }
  };

  // NEW: Manual Absence Handlers (نفس منطق الحضور اليدوي)
  const handleFetchMissingDaysForAbsence = async () => {
    if (!manualAbsenceForm.employee_id || !manualAbsenceForm.start_date || !manualAbsenceForm.end_date) {
      alert('الرجاء اختيار الموظف والفترة');
      return;
    }

    try {
      setLoadingMissingDaysAbsence(true);
      const response = await axios.get(
        `${API}/attendance/missing-days/${manualAbsenceForm.employee_id}?start_date=${manualAbsenceForm.start_date}&end_date=${manualAbsenceForm.end_date}`
      );
      
      setMissingDaysForAbsence(response.data.missing_days || []);
      setSelectedAbsenceDays(response.data.missing_days.map(d => d.date) || []);
      
      if (response.data.missing_days.length === 0) {
        alert('لا توجد أيام مفقودة في هذه الفترة ✅');
      }
    } catch (error) {
      console.error('Error fetching missing days:', error);
      alert('حدث خطأ في جلب الأيام المفقودة');
    } finally {
      setLoadingMissingDaysAbsence(false);
    }
  };

  const handleAddManualAbsence = async () => {
    if (selectedAbsenceDays.length === 0) {
      alert('الرجاء اختيار الأيام المراد إضافتها');
      return;
    }

    try {
      setAddingAbsenceRecords(true);
      const response = await axios.post(`${API}/attendance/bulk-add-absence`, {
        employee_id: manualAbsenceForm.employee_id,
        missing_days: selectedAbsenceDays,
        absence_type: manualAbsenceForm.absence_type,
        reason: manualAbsenceForm.reason || 'غياب يدوي'
      });

      const noDeduction = ['annual_leave', 'sick_leave_paid'].includes(manualAbsenceForm.absence_type);
      const typeLabels = {
        'full_day': 'غياب يوم كامل',
        'half_day': 'غياب نصف يوم',
        'annual_leave': 'إجازة سنوية',
        'sick_leave_paid': 'إجازة مرضية (بدون خصم)',
        'sick_leave_unpaid': 'إجازة مرضية (مع خصم)'
      };
      const typeLabel = typeLabels[manualAbsenceForm.absence_type] || manualAbsenceForm.absence_type;
      
      if (noDeduction) {
        alert(`${response.data.message}\nالنوع: ${typeLabel}\nبدون خصم من الراتب`);
      } else {
        alert(`${response.data.message}\nالنوع: ${typeLabel}\nالخصم الكلي: ${response.data.total_deduction} درهم\nدورة الرواتب: ${response.data.cycle_month}`);
      }
      
      // Reset and close
      setShowManualAbsenceModal(false);
      setManualAbsenceForm({
        employee_id: '',
        start_date: '',
        end_date: '',
        absence_type: 'full_day',
        reason: ''
      });
      setMissingDaysForAbsence([]);
      setSelectedAbsenceDays([]);
      
      // Refresh attendance data
      fetchAllAttendance();
    } catch (error) {
      console.error('Error adding manual absence:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في إضافة سجلات الغياب');
    } finally {
      setAddingAbsenceRecords(false);
    }
  };

  const toggleAbsenceDaySelection = (date) => {
    if (selectedAbsenceDays.includes(date)) {
      setSelectedAbsenceDays(selectedAbsenceDays.filter(d => d !== date));
    } else {
      setSelectedAbsenceDays([...selectedAbsenceDays, date]);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">إدارة الحضور - TANSEEQ Tax Consultancy</h2>
          {user?.role === 'super_admin' && (
            <div className="flex space-x-2 space-x-reverse">
              <button
                onClick={() => setShowCustomReportModal(true)}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center space-x-2"
              >
                <DocumentArrowDownIcon className="h-5 w-5" />
                <span>تقرير مخصص</span>
              </button>
              <button
                onClick={() => setShowManualAbsenceModal(true)}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex items-center space-x-2"
              >
                <XMarkIcon className="h-5 w-5" />
                <span>إضافة غياب يدوي</span>
              </button>
              <button
                onClick={() => setShowManualAttendanceModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
              >
                <PlusIcon className="h-5 w-5" />
                <span>إضافة حضور يدوي</span>
              </button>
              <button
                onClick={handleCheckMissingEmployees}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
              >
                فحص الغائبين اليوم
              </button>
              <button
                onClick={() => setShowAbsenceModal(true)}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                إنشاء سجل غياب
              </button>
            </div>
          )}
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الموظف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  التاريخ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحضور
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الانصراف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ساعات العمل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحالة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  سبب الغياب
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  نوع الإجازة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ملاحظات
                </th>
                {(user?.role === 'super_admin' || user?.name === "Hatem Mohamed Ahmed") && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الإجراءات
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {attendance.map((record) => (
                <tr key={record.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {record.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {record.date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {editingRecord === record.id ? (
                      <input
                        type="time"
                        value={editData.check_in || ''}
                        onChange={(e) => setEditData({...editData, check_in: e.target.value})}
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      />
                    ) : (
                      record.check_in || (record.status === 'Absent' ? 'N/A' : '--')
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {editingRecord === record.id ? (
                      <input
                        type="time"
                        value={editData.check_out || ''}
                        onChange={(e) => setEditData({...editData, check_out: e.target.value})}
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      />
                    ) : (
                      record.check_out || (record.status === 'Absent' ? 'N/A' : '--')
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {record.working_hours ? `${record.working_hours.toFixed(1)} ساعة` : '--'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingRecord === record.id ? (
                      <select
                        value={editData.status}
                        onChange={(e) => setEditData({...editData, status: e.target.value})}
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      >
                        <option value="present">حاضر</option>
                        <option value="late">متأخر</option>
                        <option value="absent">غائب</option>
                      </select>
                    ) : (
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        record.status === 'Present' || record.status === 'present' ? 'bg-green-100 text-green-800' :
                        record.status === 'Late' || record.status === 'late' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {record.status === 'Present' || record.status === 'present' ? 'حاضر' : 
                         record.status === 'Late' || record.status === 'late' ? 'متأخر' : 'غائب'}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {editingRecord === record.id && editData.status === 'absent' ? (
                      <input
                        type="text"
                        value={editData.reason || ''}
                        onChange={(e) => setEditData({...editData, reason: e.target.value})}
                        placeholder="سبب الغياب"
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      />
                    ) : (
                      record.absence_reason || '--'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {editingRecord === record.id && editData.status === 'absent' ? (
                      <select
                        value={editData.leave_type || ''}
                        onChange={(e) => setEditData({...editData, leave_type: e.target.value})}
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      >
                        <option value="">-- اختر نوع الإجازة --</option>
                        <option value="annual">إجازة سنوية</option>
                        <option value="sick">إجازة مرضية</option>
                        <option value="personal">إجازة شخصية</option>
                        <option value="emergency">إجازة طارئة</option>
                        <option value="unpaid">إجازة بدون راتب</option>
                        <option value="maternity">إجازة أمومة</option>
                        <option value="study">إجازة دراسية</option>
                        <option value="other">أخرى</option>
                      </select>
                    ) : (
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        record.leave_type === 'annual' ? 'bg-blue-100 text-blue-800' :
                        record.leave_type === 'sick' ? 'bg-red-100 text-red-800' :
                        record.leave_type === 'personal' ? 'bg-purple-100 text-purple-800' :
                        record.leave_type === 'emergency' ? 'bg-orange-100 text-orange-800' :
                        record.leave_type === 'unpaid' ? 'bg-gray-100 text-gray-800' :
                        record.leave_type ? 'bg-indigo-100 text-indigo-800' : ''
                      }`}>
                        {record.leave_type === 'annual' ? '🏖️ إجازة سنوية' :
                         record.leave_type === 'sick' ? '🤒 إجازة مرضية' :
                         record.leave_type === 'personal' ? '👤 إجازة شخصية' :
                         record.leave_type === 'emergency' ? '🚨 إجازة طارئة' :
                         record.leave_type === 'unpaid' ? '💰 بدون راتب' :
                         record.leave_type === 'maternity' ? '👶 إجازة أمومة' :
                         record.leave_type === 'study' ? '📚 إجازة دراسية' :
                         record.leave_type === 'other' ? '📋 أخرى' :
                         record.status === 'Absent' || record.status === 'absent' ? '--' : ''}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {(record.manual_entry || record.manual_absence || record.is_manual_entry) ? (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-amber-100 text-amber-800">
                        إدخال يدوي
                      </span>
                    ) : '--'}
                  </td>
                  {(user?.role === 'super_admin' || user?.name === "Hatem Mohamed Ahmed") && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {editingRecord === record.id ? (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleSave(record.id)}
                            className="text-green-600 hover:text-green-900"
                            title="حفظ"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={handleCancel}
                            className="text-red-600 hover:text-red-900"
                            title="إلغاء"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEdit(record)}
                            className="text-blue-600 hover:text-blue-900"
                            title="تعديل"
                            data-testid={`edit-attendance-${record.id}`}
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          {user?.role === 'super_admin' && (
                            <button
                              onClick={() => handleDeleteAttendance(record.id, record)}
                              className="text-red-600 hover:text-red-900"
                              title="حذف سجل الحضور"
                              data-testid={`delete-attendance-${record.id}`}
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Absence Modal */}
      {showAbsenceModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">إنشاء سجل غياب</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">ID الموظف</label>
                <input
                  type="text"
                  value={absenceData.user_id || ''}
                  onChange={(e) => setAbsenceData({...absenceData, user_id: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="أدخل ID الموظف"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">التاريخ</label>
                <input
                  type="date"
                  value={absenceData.date || ''}
                  onChange={(e) => setAbsenceData({...absenceData, date: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">سبب الغياب</label>
                <input
                  type="text"
                  value={absenceData.reason || ''}
                  onChange={(e) => setAbsenceData({...absenceData, reason: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="مثال: مرض، ظروف شخصية"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">نوع الإجازة</label>
                <select
                  value={absenceData.leave_type || ''}
                  onChange={(e) => setAbsenceData({...absenceData, leave_type: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="">-- اختر نوع الإجازة --</option>
                  <option value="annual">🏖️ إجازة سنوية</option>
                  <option value="sick">🤒 إجازة مرضية</option>
                  <option value="personal">👤 إجازة شخصية</option>
                  <option value="emergency">🚨 إجازة طارئة</option>
                  <option value="unpaid">💰 إجازة بدون راتب</option>
                  <option value="maternity">👶 إجازة أمومة</option>
                  <option value="study">📚 إجازة دراسية</option>
                  <option value="other">📋 أخرى</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => setShowAbsenceModal(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                إلغاء
              </button>
              <button
                onClick={handleCreateAbsence}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                إنشاء سجل غياب
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Missing Employees Modal */}
      {showMissingModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-2/3 max-w-4xl shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">الموظفون الغائبون اليوم</h3>
            
            {missingEmployees.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-green-600 text-lg">✅ جميع الموظفين سجلوا حضورهم اليوم!</p>
              </div>
            ) : (
              <div>
                <p className="text-red-600 mb-4">
                  عدد الموظفين الغائبين: {missingEmployees.length}
                </p>
                
                <div className="max-h-60 overflow-y-auto mb-4">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          اسم الموظف
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          البريد الإلكتروني
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          ID
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {missingEmployees.map((employee) => (
                        <tr key={employee.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {employee.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {employee.email}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {employee.id}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
                  <p className="text-yellow-800 text-sm">
                    💡 يمكنك إنشاء سجلات غياب تلقائية لجميع هؤلاء الموظفين بضغطة واحدة
                  </p>
                </div>
              </div>
            )}
            
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowMissingModal(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                إغلاق
              </button>
              {missingEmployees.length > 0 && (
                <button
                  onClick={() => handleProcessDailyAbsences()}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  إنشاء سجلات غياب تلقائية ({missingEmployees.length})
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* NEW: Manual Attendance Modal */}
      {showManualAttendanceModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-6 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-gray-900 mb-4">إضافة حضور يدوي للموظفين</h3>
            
            {/* Step 1: Select Employee and Date Range */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-blue-900 mb-3">الخطوة 1: اختر الموظف والفترة</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الموظف</label>
                  <select
                    value={manualAttendanceForm.employee_id}
                    onChange={(e) => setManualAttendanceForm({...manualAttendanceForm, employee_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">-- اختر الموظف --</option>
                    {employees.map(emp => (
                      <option key={emp.id} value={emp.id}>{emp.name}</option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">من تاريخ</label>
                    <input
                      type="date"
                      value={manualAttendanceForm.start_date}
                      onChange={(e) => setManualAttendanceForm({...manualAttendanceForm, start_date: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">إلى تاريخ</label>
                    <input
                      type="date"
                      value={manualAttendanceForm.end_date}
                      onChange={(e) => setManualAttendanceForm({...manualAttendanceForm, end_date: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              </div>
              <button
                onClick={handleFetchMissingDays}
                disabled={loadingMissingDays}
                className="mt-3 w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loadingMissingDays ? 'جاري البحث...' : 'عرض الأيام المفقودة'}
              </button>
            </div>

            {/* Step 2: Show Missing Days */}
            {missingDays.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <h4 className="font-semibold text-yellow-900 mb-3">
                  الخطوة 2: الأيام المفقودة ({missingDays.length} يوم)
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-60 overflow-y-auto">
                  {missingDays.map(day => (
                    <label key={day.date} className="flex items-center space-x-2 space-x-reverse bg-white p-2 rounded border hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedMissingDays.includes(day.date)}
                        onChange={() => toggleDaySelection(day.date)}
                        className="h-4 w-4"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium">{day.date}</div>
                        <div className="text-xs text-gray-600">{day.day_name_ar}</div>
                      </div>
                    </label>
                  ))}
                </div>
                <div className="mt-3 flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedMissingDays(missingDays.map(d => d.date))}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    اختيار الكل
                  </button>
                  <span className="text-gray-400">|</span>
                  <button
                    onClick={() => setSelectedMissingDays([])}
                    className="text-sm text-gray-600 hover:underline"
                  >
                    إلغاء الاختيار
                  </button>
                  <span className="flex-1 text-left text-sm text-gray-700">
                    محدد: {selectedMissingDays.length} يوم
                  </span>
                </div>
              </div>
            )}

            {/* Step 3: Set Times */}
            {selectedMissingDays.length > 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <h4 className="font-semibold text-green-900 mb-3">الخطوة 3: حدد أوقات الحضور والانصراف</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">وقت الحضور</label>
                    <input
                      type="time"
                      value={manualAttendanceForm.check_in_time}
                      onChange={(e) => setManualAttendanceForm({...manualAttendanceForm, check_in_time: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">وقت الانصراف</label>
                    <input
                      type="time"
                      value={manualAttendanceForm.check_out_time}
                      onChange={(e) => setManualAttendanceForm({...manualAttendanceForm, check_out_time: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 space-x-reverse pt-4 border-t">
              <button
                onClick={() => {
                  setShowManualAttendanceModal(false);
                  setManualAttendanceForm({
                    employee_id: '',
                    start_date: '',
                    end_date: '',
                    check_in_time: '09:00',
                    check_out_time: '18:00'
                  });
                  setMissingDays([]);
                  setSelectedMissingDays([]);
                }}
                className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
              >
                إلغاء
              </button>
              {selectedMissingDays.length > 0 && (
                <button
                  onClick={handleAddManualAttendance}
                  disabled={addingManualRecords}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {addingManualRecords ? 'جاري الإضافة...' : `إضافة ${selectedMissingDays.length} سجل`}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* NEW: Manual Absence Modal (نفس منطق الحضور اليدوي) */}
      {showManualAbsenceModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-6 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-gray-900 mb-4">إضافة غياب يدوي للموظفين</h3>
            
            {/* Step 1: Select Employee and Date Range */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-red-900 mb-3">الخطوة 1: اختر الموظف والفترة</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الموظف</label>
                  <select
                    value={manualAbsenceForm.employee_id}
                    onChange={(e) => setManualAbsenceForm({...manualAbsenceForm, employee_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">-- اختر الموظف --</option>
                    {employees.map(emp => (
                      <option key={emp.id} value={emp.id}>{emp.name}</option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">من تاريخ</label>
                    <input
                      type="date"
                      value={manualAbsenceForm.start_date}
                      onChange={(e) => setManualAbsenceForm({...manualAbsenceForm, start_date: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">إلى تاريخ</label>
                    <input
                      type="date"
                      value={manualAbsenceForm.end_date}
                      onChange={(e) => setManualAbsenceForm({...manualAbsenceForm, end_date: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              </div>
              <button
                onClick={handleFetchMissingDaysForAbsence}
                disabled={loadingMissingDaysAbsence}
                className="mt-3 w-full bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {loadingMissingDaysAbsence ? 'جاري البحث...' : 'عرض الأيام المتاحة لتسجيل الغياب'}
              </button>
            </div>

            {/* Step 2: Show Missing Days */}
            {missingDaysForAbsence.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <h4 className="font-semibold text-yellow-900 mb-3">
                  الخطوة 2: الأيام المتاحة ({missingDaysForAbsence.length} يوم)
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-60 overflow-y-auto">
                  {missingDaysForAbsence.map(day => (
                    <label key={day.date} className="flex items-center space-x-2 space-x-reverse bg-white p-2 rounded border hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedAbsenceDays.includes(day.date)}
                        onChange={() => toggleAbsenceDaySelection(day.date)}
                        className="h-4 w-4"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium">{day.date}</div>
                        <div className="text-xs text-gray-600">{day.day_name_ar}</div>
                      </div>
                    </label>
                  ))}
                </div>
                <div className="mt-3 flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedAbsenceDays(missingDaysForAbsence.map(d => d.date))}
                    className="text-sm text-red-600 hover:underline"
                  >
                    اختيار الكل
                  </button>
                  <span className="text-gray-400">|</span>
                  <button
                    onClick={() => setSelectedAbsenceDays([])}
                    className="text-sm text-gray-600 hover:underline"
                  >
                    إلغاء الاختيار
                  </button>
                  <span className="flex-1 text-left text-sm text-gray-700">
                    محدد: {selectedAbsenceDays.length} يوم
                  </span>
                </div>
              </div>
            )}

            {/* Step 3: Set Absence Type & Reason */}
            {selectedAbsenceDays.length > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
                <h4 className="font-semibold text-orange-900 mb-3">الخطوة 3: حدد نوع الغياب والسبب</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">نوع الغياب</label>
                    <select
                      value={manualAbsenceForm.absence_type}
                      onChange={(e) => setManualAbsenceForm({...manualAbsenceForm, absence_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      data-testid="absence-type-select"
                    >
                      <optgroup label="غياب مع خصم">
                        <option value="full_day">غياب - يوم كامل (خصم كامل)</option>
                        <option value="half_day">غياب - نصف يوم (خصم نصف)</option>
                      </optgroup>
                      <optgroup label="إجازات بدون خصم">
                        <option value="annual_leave">إجازة سنوية (مدفوعة - بدون خصم)</option>
                        <option value="sick_leave_paid">إجازة مرضية (بدون خصم)</option>
                      </optgroup>
                      <optgroup label="إجازات مع خصم">
                        <option value="sick_leave_unpaid">إجازة مرضية (مع خصم)</option>
                      </optgroup>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">سبب الغياب (اختياري)</label>
                    <input
                      type="text"
                      value={manualAbsenceForm.reason}
                      onChange={(e) => setManualAbsenceForm({...manualAbsenceForm, reason: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      placeholder="مثال: مرضي، شخصي، ..."
                      data-testid="absence-reason-input"
                    />
                  </div>
                </div>
                
                {/* Deduction Preview */}
                <div className={`mt-3 border rounded p-3 ${
                  ['annual_leave', 'sick_leave_paid'].includes(manualAbsenceForm.absence_type)
                    ? 'bg-green-50 border-green-300'
                    : 'bg-orange-50 border-orange-300'
                }`}>
                  {['annual_leave', 'sick_leave_paid'].includes(manualAbsenceForm.absence_type) ? (
                    <p className="text-sm text-green-900">
                      <strong>بدون خصم</strong> - {manualAbsenceForm.absence_type === 'annual_leave' 
                        ? 'الإجازة السنوية مدفوعة الأجر بالكامل' 
                        : 'الإجازة المرضية بدون خصم بقرار الإدارة'}
                    </p>
                  ) : (
                    <p className="text-sm text-orange-900">
                      <strong>مع خصم</strong> - سيتم احتساب {manualAbsenceForm.absence_type === 'half_day' ? 'نصف' : 'كامل'} خصم اليوم وإضافته إلى دورة الرواتب
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 space-x-reverse pt-4 border-t">
              <button
                onClick={() => {
                  setShowManualAbsenceModal(false);
                  setManualAbsenceForm({
                    employee_id: '',
                    start_date: '',
                    end_date: '',
                    absence_type: 'full_day',
                    reason: ''
                  });
                  setMissingDaysForAbsence([]);
                  setSelectedAbsenceDays([]);
                }}
                className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
              >
                إلغاء
              </button>
              {selectedAbsenceDays.length > 0 && (
                <button
                  onClick={handleAddManualAbsence}
                  disabled={addingAbsenceRecords}
                  className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  {addingAbsenceRecords ? 'جاري الإضافة...' : `إضافة ${selectedAbsenceDays.length} سجل غياب`}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Custom Report Modal */}
      {showCustomReportModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" data-testid="custom-report-modal">
          <div className="relative top-10 mx-auto p-6 border w-11/12 max-w-3xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-gray-900 mb-4">تقرير حضور مخصص</h3>
            
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-purple-900 mb-3">اختر الموظفين</h4>
              <div className="mb-2 flex space-x-2 space-x-reverse">
                <button
                  onClick={() => setCustomReportForm({...customReportForm, employee_ids: employees.map(e => e.id)})}
                  className="text-sm text-purple-600 hover:underline"
                  data-testid="select-all-employees-report"
                >
                  اختيار الكل
                </button>
                <span className="text-gray-400">|</span>
                <button
                  onClick={() => setCustomReportForm({...customReportForm, employee_ids: []})}
                  className="text-sm text-gray-600 hover:underline"
                >
                  إلغاء الاختيار
                </button>
                <span className="text-sm text-gray-500 mr-auto">محدد: {customReportForm.employee_ids.length} موظف</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
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
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">من تاريخ</label>
                <input
                  type="date"
                  value={customReportForm.start_date}
                  onChange={(e) => setCustomReportForm({...customReportForm, start_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="custom-report-start-date"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">إلى تاريخ</label>
                <input
                  type="date"
                  value={customReportForm.end_date}
                  onChange={(e) => setCustomReportForm({...customReportForm, end_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="custom-report-end-date"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">صيغة التصدير</label>
              <select
                value={customReportForm.format}
                onChange={(e) => setCustomReportForm({...customReportForm, format: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                data-testid="custom-report-format"
              >
                <option value="excel">Excel (.xlsx)</option>
                <option value="csv">CSV (.csv)</option>
              </select>
            </div>

            <div className="flex justify-end space-x-3 space-x-reverse">
              <button
                onClick={() => {
                  setShowCustomReportModal(false);
                  setCustomReportForm({ employee_ids: [], start_date: '', end_date: '', format: 'excel' });
                }}
                className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                data-testid="custom-report-cancel"
              >
                إلغاء
              </button>
              <button
                onClick={handleGenerateCustomReport}
                disabled={generatingReport || customReportForm.employee_ids.length === 0 || !customReportForm.start_date || !customReportForm.end_date}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                data-testid="custom-report-generate"
              >
                {generatingReport ? 'جاري إنشاء التقرير...' : 'تصدير التقرير'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendanceManagement;
