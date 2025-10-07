import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  CalendarIcon,
  LockClosedIcon,
  LockOpenIcon,
  PlusIcon,
  EyeIcon,
  CalculatorIcon,
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  PencilIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PayrollCycleManagement = () => {
  const [cycles, setCycles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showLockModal, setShowLockModal] = useState(false);
  const [selectedCycle, setSelectedCycle] = useState(null);
  const [exportDropdown, setExportDropdown] = useState(null);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [yearFilter, setYearFilter] = useState(new Date().getFullYear());
  
  // Form data
  const [createData, setCreateData] = useState({
    month: new Date().toISOString().slice(0, 7), // YYYY-MM
    notes: ''
  });
  
  const [lockData, setLockData] = useState({
    lock_reason: ''
  });

  useEffect(() => {
    fetchPayrollCycles();
  }, [statusFilter, yearFilter]);

  const fetchPayrollCycles = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (yearFilter) params.append('year', yearFilter);
      
      const response = await axios.get(`${API}/payroll/cycles?${params}`);
      setCycles(response.data);
    } catch (error) {
      console.error('Error fetching payroll cycles:', error);
      alert('خطأ في جلب دورات الرواتب');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCycle = async (e) => {
    e.preventDefault();
    
    if (!createData.month) {
      alert('يرجى تحديد الشهر');
      return;
    }

    try {
      await axios.post(`${API}/payroll/cycles`, createData);
      setShowCreateModal(false);
      setCreateData({
        month: new Date().toISOString().slice(0, 7),
        notes: ''
      });
      fetchPayrollCycles();
      alert('تم إنشاء دورة الراتب بنجاح');
    } catch (error) {
      console.error('Error creating payroll cycle:', error);
      const errorMsg = error.response?.data?.detail || 'خطأ في إنشاء دورة الراتب';
      alert(errorMsg);
    }
  };

  const handleLockCycle = async (e) => {
    e.preventDefault();
    
    if (!selectedCycle) return;

    try {
      await axios.post(`${API}/payroll/cycles/${selectedCycle.id}/lock`, lockData);
      setShowLockModal(false);
      setSelectedCycle(null);
      setLockData({ lock_reason: '' });
      fetchPayrollCycles();
      alert('تم قفل دورة الراتب بنجاح');
    } catch (error) {
      console.error('Error locking cycle:', error);
      const errorMsg = error.response?.data?.detail || 'خطأ في قفل دورة الراتب';
      alert(errorMsg);
    }
  };

  const handleUnlockCycle = async (cycle) => {
    const reason = prompt('سبب فتح دورة الراتب:');
    if (!reason) return;

    try {
      await axios.post(`${API}/payroll/cycles/${cycle.id}/unlock`, { reason });
      fetchPayrollCycles();
      alert('تم فتح دورة الراتب بنجاح');
    } catch (error) {
      console.error('Error unlocking cycle:', error);
      const errorMsg = error.response?.data?.detail || 'خطأ في فتح دورة الراتب';
      alert(errorMsg);
    }
  };

  const handleCalculatePayroll = async (cycle) => {
    if (!window.confirm(`هل أنت متأكد من حساب رواتب دورة ${cycle.display_name}؟`)) {
      return;
    }

    try {
      const response = await axios.get(`${API}/payroll/cycles/${cycle.id}/calculate`);
      alert(`تم حساب الرواتب بنجاح: ${response.data.message}`);
      fetchPayrollCycles();
    } catch (error) {
      console.error('Error calculating payroll:', error);
      const errorMsg = error.response?.data?.detail || 'خطأ في حساب الرواتب';
      alert(errorMsg);
    }
  };

  const handleEditCycle = (cycle) => {
    // توجيه لصفحة التفاصيل مع إمكانية التعديل
    window.location.href = `/payroll-summary/${cycle.id}?edit=true`;
  };

  const getStatusColor = (status) => {
    const colors = {
      'open': 'bg-green-100 text-green-800',
      'processing': 'bg-yellow-100 text-yellow-800',
      'closed': 'bg-gray-100 text-gray-800',
      'cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status) => {
    const texts = {
      'open': 'مفتوحة',
      'processing': 'قيد المعالجة',
      'closed': 'مقفولة',
      'cancelled': 'ملغاة'
    };
    return texts[status] || status;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      return new Date(dateString).toLocaleString('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <CalendarIcon className="h-8 w-8 text-blue-600 ml-3" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">إدارة دورات الرواتب</h1>
              <p className="text-gray-600">النظام المتكامل للرواتب والخصومات والسلف</p>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => window.location.href = '/installment-schedules'}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <CalendarIcon className="h-5 w-5 ml-2" />
              إدارة الأقساط
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <PlusIcon className="h-5 w-5 ml-2" />
              إنشاء دورة جديدة
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">الحالة</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">جميع الحالات</option>
              <option value="open">مفتوحة</option>
              <option value="processing">قيد المعالجة</option>
              <option value="closed">مقفولة</option>
              <option value="cancelled">ملغاة</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">السنة</label>
            <select
              value={yearFilter}
              onChange={(e) => setYearFilter(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              {[2025, 2024, 2023].map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={fetchPayrollCycles}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              تحديث
            </button>
          </div>
        </div>

        {/* Summary Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center">
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
              <div className="mr-3">
                <p className="text-sm text-green-600">دورات مفتوحة</p>
                <p className="text-2xl font-bold text-green-600">
                  {cycles.filter(c => c.status === 'open').length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-yellow-600" />
              <div className="mr-3">
                <p className="text-sm text-yellow-600">قيد المعالجة</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {cycles.filter(c => c.status === 'processing').length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center">
              <LockClosedIcon className="h-8 w-8 text-gray-600" />
              <div className="mr-3">
                <p className="text-sm text-gray-600">دورات مقفولة</p>
                <p className="text-2xl font-bold text-gray-600">
                  {cycles.filter(c => c.status === 'closed').length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center">
              <CalendarIcon className="h-8 w-8 text-blue-600" />
              <div className="mr-3">
                <p className="text-sm text-blue-600">إجمالي الدورات</p>
                <p className="text-2xl font-bold text-blue-600">{cycles.length}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Cycles Table */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">دورات الرواتب</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الدورة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الحالة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">عدد الموظفين</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">إجمالي الرواتب</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">إجمالي الخصومات</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الصافي</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">تاريخ الإنشاء</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {cycles.map((cycle) => (
                <tr key={cycle.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {cycle.display_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(cycle.status)}`}>
                      {getStatusText(cycle.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {cycle.total_employees || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="font-semibold text-green-600">
                      {(cycle.total_gross_salary || 0).toFixed(2)} درهم
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="font-semibold text-red-600">
                      {(cycle.total_deductions || 0).toFixed(2)} درهم
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="font-semibold text-blue-600">
                      {(cycle.total_net_salary || 0).toFixed(2)} درهم
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(cycle.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => window.location.href = `/payroll-summary/${cycle.id}`}
                        className="text-blue-600 hover:text-blue-900"
                        title="عرض التفاصيل"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                      {!cycle.is_locked && (
                        <>
                          <button
                            onClick={() => handleEditCycle(cycle)}
                            className="text-yellow-600 hover:text-yellow-900"
                            title="تعديل الدورة"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleCalculatePayroll(cycle)}
                            className="text-green-600 hover:text-green-900"
                            title="حساب الرواتب"
                          >
                            <CalculatorIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => {
                              setSelectedCycle(cycle);
                              setShowLockModal(true);
                            }}
                            className="text-orange-600 hover:text-orange-900"
                            title="قفل الدورة"
                          >
                            <LockClosedIcon className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      {cycle.is_locked && (
                        <button
                          onClick={() => handleUnlockCycle(cycle)}
                          className="text-purple-600 hover:text-purple-900"
                          title="فتح الدورة"
                        >
                          <LockOpenIcon className="h-4 w-4" />
                        </button>
                      )}
                      <div className="relative inline-block text-left">
                        <button
                          onClick={() => setExportDropdown(exportDropdown === cycle.id ? null : cycle.id)}
                          className="text-gray-700 hover:text-gray-900"
                          title="تصدير"
                        >
                          <DocumentArrowDownIcon className="h-5 w-5" />
                        </button>
                        {exportDropdown === cycle.id && (
                          <div className="origin-top-right absolute right-0 mt-2 w-44 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
                            <div className="py-1">
                              <a href={`${API}/payroll/cycles/${cycle.id}/export/pdf`} className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" target="_blank" rel="noreferrer">تحميل PDF</a>
                              <a href={`${API}/payroll/cycles/${cycle.id}/export/excel`} className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" target="_blank" rel="noreferrer">تحميل Excel</a>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Cycle Modal */}
      {showCreateModal && (
        <>
          <div className="fixed inset-0 z-40 bg-black bg-opacity-50" />
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4" role="dialog" aria-modal="true" data-testid="create-cycle-modal">

            <h3 className="text-lg font-semibold text-gray-900 mb-4">إنشاء دورة راتب جديدة</h3>
            <form onSubmit={handleCreateCycle} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الشهر</label>
                <input
                  type="month"
                  value={createData.month}
                  onChange={(e) => setCreateData({ ...createData, month: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ملاحظات</label>
                <textarea
                  value={createData.notes}
                  onChange={(e) => setCreateData({ ...createData, notes: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  rows="3"
                  placeholder="اكتب أي ملاحظات"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="submit" className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700">إنشاء</button>
                <button type="button" onClick={() => setShowCreateModal(false)} className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400">إلغاء</button>
              </div>
            </div>
          </div>
        </>

            </form>
          </div>
        </div>
      )}

      {/* Lock Cycle Modal */}
      {showLockModal && selectedCycle && (
        <>
          <div className="fixed inset-0 z-40 bg-black bg-opacity-50" />
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4" role="dialog" aria-modal="true" data-testid="lock-cycle-modal">

            <h3 className="text-lg font-semibold text-gray-900 mb-4">قفل دورة الراتب</h3>
            <form onSubmit={handleLockCycle} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">سبب القفل</label>
                <textarea
                  value={lockData.lock_reason}
                  onChange={(e) => setLockData({ lock_reason: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  rows="3"
                  required
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="submit" className="flex-1 bg-orange-600 text-white py-2 px-4 rounded-lg hover:bg-orange-700">قفل</button>
                <button type="button" onClick={() => setShowLockModal(false)} className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400">إلغاء</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PayrollCycleManagement;
