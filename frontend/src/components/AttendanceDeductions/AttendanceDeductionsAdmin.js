import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ExclamationTriangleIcon as AlertTriangle,
  PlusIcon as Plus,
  PencilIcon as Edit,
  TrashIcon as Trash2,
  EyeIcon as Eye,
  ArrowDownTrayIcon as Download,
  FunnelIcon as Filter,
  MagnifyingGlassIcon as Search,
  CheckCircleIcon as CheckCircle,
  XCircleIcon as XCircle,
  InformationCircleIcon as Info,
  InformationCircleIcon as AlertCircle,
  CalendarIcon as Calendar,
  ClockIcon as Clock,
  CurrencyDollarIcon as DollarSign,
  UserGroupIcon as Users
} from '@heroicons/react/24/outline';

const AttendanceDeductionsAdmin = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [employees, setEmployees] = useState([]);
  const [deductions, setDeductions] = useState([]);
  const [attendanceStats, setAttendanceStats] = useState({});
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingDeduction, setEditingDeduction] = useState(null);

  // Form states
  const [newDeduction, setNewDeduction] = useState({
    employee_id: '',
    deduction_type: 'manual',
    category: 'minutes',
    date: new Date().toISOString().slice(0, 10),
    minutes: '',
    amount: '',
    reason: '',
    attachments: []
  });

  useEffect(() => {
    fetchEmployees();
    fetchDeductions();
    fetchAttendanceStats();
  }, [selectedMonth, selectedEmployee]);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees/list`);
      setEmployees(response.data.employees || []);
    } catch (error) {
      console.error('Error fetching employees:', error);
      // Fallback إلى API القديم إذا فشل الجديد
      try {
        const fallbackResponse = await axios.get(`${API}/users`);
        setEmployees(fallbackResponse.data.filter(emp => emp.role !== 'super_admin'));
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
      }
    }
  };

  const fetchDeductions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedMonth) params.append('month', selectedMonth);
      if (selectedEmployee) params.append('employee_id', selectedEmployee);
      if (selectedType) params.append('deduction_type', selectedType);

      const response = await axios.get(`${API}/deductions?${params}`);
      setDeductions(response.data || []);
    } catch (error) {
      console.error('Error fetching deductions:', error);
      alert('خطأ في جلب الخصومات');
    } finally {
      setLoading(false);
    }
  };

  const fetchAttendanceStats = async () => {
    if (!selectedEmployee || !selectedMonth) return;
    
    try {
      const response = await fetch(`/api/attendance/stats/${selectedEmployee}/${selectedMonth}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setAttendanceStats(data);
    } catch (error) {
      console.error('Error fetching attendance stats:', error);
    }
  };

  const handleCreateDeduction = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/deductions/manual`, {
        employee_id: formData.employee_id,
        amount: parseFloat(formData.amount),
        reason: formData.reason,
        date: formData.date
      });
      
      alert('تم إنشاء الخصم اليدوي بنجاح');
      setShowModal(false);
      setFormData({ employee_id: '', amount: '', reason: '', date: new Date().toISOString().split('T')[0] });
      fetchDeductions();
    } catch (error) {
      console.error('Error creating deduction:', error);
      alert(error.response?.data?.detail || 'خطأ في إنشاء الخصم اليدوي');
    } finally {
      setLoading(false);
    }
  };

  // إزالة الكود القديم
  const oldHandleCreateDeduction = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/deductions/manual', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newDeduction)
      });

      if (response.ok) {
        alert('تم إنشاء الخصم بنجاح');
        setShowCreateModal(false);
        setNewDeduction({
          employee_id: '',
          deduction_type: 'manual',
          category: 'minutes',
          date: new Date().toISOString().slice(0, 10),
          minutes: '',
          amount: '',
          reason: '',
          attachments: []
        });
        fetchDeductions();
      } else {
        const error = await response.json();
        alert(`خطأ: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error creating deduction:', error);
      alert('حدث خطأ في إنشاء الخصم');
    } finally {
      setLoading(false);
    }
  };

  const handleEditDeduction = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`/api/deductions/${editingDeduction.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          minutes: editingDeduction.minutes,
          amount: editingDeduction.amount,
          reason: editingDeduction.reason
        })
      });

      if (response.ok) {
        alert('تم تحديث الخصم بنجاح');
        setShowEditModal(false);
        setEditingDeduction(null);
        fetchDeductions();
      } else {
        const error = await response.json();
        alert(`خطأ: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error updating deduction:', error);
      alert('حدث خطأ في تحديث الخصم');
    } finally {
      setLoading(false);
    }
  };

  const handleVoidDeduction = async (deductionId) => {
    if (!confirm('هل أنت متأكد من إلغاء هذا الخصم؟')) return;

    const reason = prompt('سبب الإلغاء:');
    if (!reason) return;

    try {
      const response = await fetch(`/api/deductions/${deductionId}/void`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ void_reason: reason })
      });

      if (response.ok) {
        alert('تم إلغاء الخصم بنجاح');
        fetchDeductions();
      } else {
        const error = await response.json();
        alert(`خطأ: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error voiding deduction:', error);
      alert('حدث خطأ في إلغاء الخصم');
    }
  };

  const getDeductionTypeColor = (type) => {
    const colors = {
      lateness: 'bg-yellow-100 text-yellow-800',
      early_leave: 'bg-orange-100 text-orange-800',
      missing_checkout: 'bg-red-100 text-red-800',
      manual: 'bg-blue-100 text-blue-800',
      absence: 'bg-gray-100 text-gray-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getCategoryColor = (category) => {
    const colors = {
      minutes: 'bg-green-100 text-green-800',
      half_day: 'bg-yellow-100 text-yellow-800',
      full_day: 'bg-red-100 text-red-800',
      custom: 'bg-purple-100 text-purple-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const totalDeductions = deductions.reduce((sum, d) => sum + (d.is_voided ? 0 : d.amount), 0);
  const totalMinutes = deductions.reduce((sum, d) => sum + (d.is_voided ? 0 : d.minutes), 0);

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Clock className="w-8 h-8 text-blue-600" />
                نظام الحضور والخصومات المتقدم
              </h1>
              <p className="text-gray-600 mt-1">إدارة خصومات التأخير والخروج المبكر - قواعد أكتوبر 2025</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              خصم يدوي جديد
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">الشهر</label>
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">الموظف</label>
              <select
                value={selectedEmployee}
                onChange={(e) => setSelectedEmployee(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="">جميع الموظفين</option>
                {employees.map(emp => (
                  <option key={emp.id} value={emp.id}>{emp.name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={fetchDeductions}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-gray-700"
              >
                <Filter className="w-4 h-4" />
                تطبيق الفلتر
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">إجمالي الخصومات</p>
                <p className="text-2xl font-bold text-red-600">{totalDeductions.toFixed(2)} درهم</p>
              </div>
              <DollarSign className="w-8 h-8 text-red-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">إجمالي الدقائق</p>
                <p className="text-2xl font-bold text-orange-600">{totalMinutes} دقيقة</p>
              </div>
              <Clock className="w-8 h-8 text-orange-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">عدد الخصومات</p>
                <p className="text-2xl font-bold text-blue-600">{deductions.filter(d => !d.is_voided).length}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">الموظفين المتأثرين</p>
                <p className="text-2xl font-bold text-green-600">
                  {new Set(deductions.filter(d => !d.is_voided).map(d => d.employee_id)).size}
                </p>
              </div>
              <Users className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        {/* Attendance Stats for Selected Employee */}
        {selectedEmployee && attendanceStats.employee_id && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              إحصائيات الحضور - {attendanceStats.employee_name}
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{attendanceStats.present_days}</p>
                <p className="text-sm text-gray-600">أيام الحضور</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">{attendanceStats.late_days}</p>
                <p className="text-sm text-gray-600">أيام التأخير</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{attendanceStats.absent_days}</p>
                <p className="text-sm text-gray-600">أيام الغياب</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{attendanceStats.free_occurrences_remaining}</p>
                <p className="text-sm text-gray-600">المرات المجانية المتبقية</p>
              </div>
            </div>
          </div>
        )}

        {/* Deductions Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">سجل الخصومات</h3>
          </div>
          
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">جاري التحميل...</p>
            </div>
          ) : deductions.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>لا توجد خصومات للفترة المحددة</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الموظف</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">التاريخ</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">النوع</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الفئة</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الدقائق</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">المبلغ</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">السبب</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الحالة</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الإجراءات</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {deductions.map((deduction) => (
                    <tr key={deduction.id} className={deduction.is_voided ? 'bg-gray-50 opacity-60' : ''}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {deduction.employee_name || deduction.user_name || deduction.name || 'غير محدد'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(deduction.date).toLocaleDateString('ar-AE')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getDeductionTypeColor(deduction.deduction_type)}`}>
                          {deduction.deduction_type_ar}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(deduction.category)}`}>
                          {deduction.category_ar}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {deduction.minutes}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-red-600">
                        {deduction.amount.toFixed(2)} درهم
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                        {deduction.reason}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {deduction.is_voided ? (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                            <XCircle className="w-3 h-3 mr-1" />
                            ملغي
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            فعال
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center gap-2">
                          {!deduction.is_voided && (
                            <>
                              <button
                                onClick={() => {
                                  setEditingDeduction(deduction);
                                  setShowEditModal(true);
                                }}
                                className="text-blue-600 hover:text-blue-900"
                                title="تعديل"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleVoidDeduction(deduction.id)}
                                className="text-red-600 hover:text-red-900"
                                title="إلغاء"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => alert('تفاصيل الخصم:\n' + JSON.stringify(deduction, null, 2))}
                            className="text-gray-600 hover:text-gray-900"
                            title="عرض التفاصيل"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Create Deduction Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">إنشاء خصم يدوي جديد</h3>
            
            <form onSubmit={handleCreateDeduction} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الموظف</label>
                <select
                  value={newDeduction.employee_id}
                  onChange={(e) => setNewDeduction({...newDeduction, employee_id: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                >
                  <option value="">اختر الموظف</option>
                  {employees.map(emp => (
                    <option key={emp.id} value={emp.id}>{emp.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">فئة الخصم</label>
                <select
                  value={newDeduction.category}
                  onChange={(e) => setNewDeduction({...newDeduction, category: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                >
                  <option value="minutes">خصم دقائق</option>
                  <option value="half_day">نصف يوم</option>
                  <option value="full_day">يوم كامل</option>
                  <option value="custom">مخصص</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">التاريخ</label>
                <input
                  type="date"
                  value={newDeduction.date}
                  onChange={(e) => setNewDeduction({...newDeduction, date: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>

              {newDeduction.category === 'minutes' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الدقائق</label>
                  <input
                    type="number"
                    value={newDeduction.minutes}
                    onChange={(e) => setNewDeduction({...newDeduction, minutes: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    min="1"
                  />
                </div>
              )}

              {newDeduction.category === 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">المبلغ (درهم)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newDeduction.amount}
                    onChange={(e) => setNewDeduction({...newDeduction, amount: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    min="0"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">السبب</label>
                <textarea
                  value={newDeduction.reason}
                  onChange={(e) => setNewDeduction({...newDeduction, reason: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  rows="3"
                  required
                  minLength="5"
                  placeholder="اكتب سبب الخصم..."
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'جاري الإنشاء...' : 'إنشاء الخصم'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400"
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Deduction Modal */}
      {showEditModal && editingDeduction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">تعديل الخصم</h3>
            
            <form onSubmit={handleEditDeduction} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الدقائق</label>
                <input
                  type="number"
                  value={editingDeduction.minutes}
                  onChange={(e) => setEditingDeduction({...editingDeduction, minutes: parseInt(e.target.value)})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">المبلغ (درهم)</label>
                <input
                  type="number"
                  step="0.01"
                  value={editingDeduction.amount}
                  onChange={(e) => setEditingDeduction({...editingDeduction, amount: parseFloat(e.target.value)})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">السبب</label>
                <textarea
                  value={editingDeduction.reason}
                  onChange={(e) => setEditingDeduction({...editingDeduction, reason: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  rows="3"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'جاري التحديث...' : 'تحديث الخصم'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingDeduction(null);
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400"
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendanceDeductionsAdmin;