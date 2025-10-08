import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  DocumentTextIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  UserIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EmployeeLedger = () => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [ledgerData, setLedgerData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Filters
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    entry_type: ''
  });

  const entryTypes = [
    { value: '', label: 'جميع الأنواع' },
    { value: 'ATTENDANCE_DEDUCTION', label: 'خصم حضور/تأخير' },
    { value: 'LEAVE_ADJUSTMENT', label: 'تعديل إجازة' },
    { value: 'MANUAL_DEDUCTION', label: 'خصم يدوي' },
    { value: 'ADVANCE_INSTALLMENT', label: 'قسط سلفة' },
    { value: 'CUSTODY_ADJUSTMENT', label: 'تعديل عهدة' }
  ];

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees/list`);
      setEmployees(response.data.employees || []);
    } catch (err) {
      console.error('Error fetching employees:', err);
    }
  };

  const fetchLedger = async () => {
    if (!selectedEmployee) {
      alert('يرجى اختيار موظف');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const params = new URLSearchParams();
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.entry_type) params.append('entry_type', filters.entry_type);
      
      const response = await axios.get(
        `${API}/payroll/ledger/employee/${selectedEmployee}?${params.toString()}`
      );
      
      setLedgerData(response.data);
    } catch (err) {
      console.error('Error fetching ledger:', err);
      setError(err.response?.data?.detail || 'خطأ في جلب البيانات');
    } finally {
      setLoading(false);
    }
  };

  const getEntryTypeLabel = (type) => {
    const found = entryTypes.find(t => t.value === type);
    return found ? found.label : type;
  };

  const getEntryTypeColor = (type) => {
    const colors = {
      'ATTENDANCE_DEDUCTION': 'bg-yellow-100 text-yellow-800',
      'LEAVE_ADJUSTMENT': 'bg-blue-100 text-blue-800',
      'MANUAL_DEDUCTION': 'bg-red-100 text-red-800',
      'ADVANCE_INSTALLMENT': 'bg-purple-100 text-purple-800',
      'CUSTODY_ADJUSTMENT': 'bg-green-100 text-green-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="p-6 max-w-7xl mx-auto" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 text-white p-6 rounded-lg shadow-lg mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">📋 سجل قيود الرواتب (Payroll Ledger)</h1>
            <p className="text-indigo-100">عرض جميع القيود المحاسبية لرواتب الموظفين</p>
          </div>
          <DocumentTextIcon className="h-16 w-16 text-indigo-200" />
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <FunnelIcon className="h-5 w-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">الفلاتر</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Employee Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <UserIcon className="h-4 w-4 inline ml-1" />
              الموظف *
            </label>
            <select
              value={selectedEmployee}
              onChange={(e) => setSelectedEmployee(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">اختر موظف...</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.name}
                </option>
              ))}
            </select>
          </div>

          {/* Entry Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              نوع القيد
            </label>
            <select
              value={filters.entry_type}
              onChange={(e) => setFilters({...filters, entry_type: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
            >
              {entryTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <CalendarIcon className="h-4 w-4 inline ml-1" />
              من تاريخ
            </label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => setFilters({...filters, start_date: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <CalendarIcon className="h-4 w-4 inline ml-1" />
              إلى تاريخ
            </label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => setFilters({...filters, end_date: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="mt-4 flex gap-3">
          <button
            onClick={fetchLedger}
            disabled={loading || !selectedEmployee}
            className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                جاري التحميل...
              </>
            ) : (
              <>
                <FunnelIcon className="h-4 w-4" />
                عرض القيود
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Results */}
      {ledgerData && (
        <>
          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gradient-to-r from-blue-100 to-blue-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-700 font-medium">الموظف</p>
                  <p className="text-xl font-bold text-blue-900 mt-1">{ledgerData.employee_name}</p>
                </div>
                <UserIcon className="h-10 w-10 text-blue-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-100 to-purple-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-700 font-medium">إجمالي القيود</p>
                  <p className="text-2xl font-bold text-purple-900">{ledgerData.total_entries}</p>
                </div>
                <DocumentTextIcon className="h-10 w-10 text-purple-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-orange-100 to-orange-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-700 font-medium">أنواع القيود</p>
                  <p className="text-2xl font-bold text-orange-900">
                    {Object.keys(ledgerData.totals_by_type || {}).length}
                  </p>
                </div>
                <FunnelIcon className="h-10 w-10 text-orange-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-green-100 to-green-200 p-5 rounded-xl shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-700 font-medium">إجمالي المبالغ</p>
                  <p className="text-xl font-bold text-green-900">
                    {Object.values(ledgerData.totals_by_type || {})
                      .reduce((sum, t) => sum + t.total_amount, 0)
                      .toFixed(2)} درهم
                  </p>
                </div>
                <CurrencyDollarIcon className="h-10 w-10 text-green-500" />
              </div>
            </div>
          </div>

          {/* Totals by Type */}
          {Object.keys(ledgerData.totals_by_type || {}).length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">الإجماليات حسب النوع</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(ledgerData.totals_by_type).map(([type, data]) => (
                  <div key={type} className="border border-gray-200 rounded-lg p-4">
                    <div className={`inline-block px-3 py-1 rounded-full text-xs font-semibold mb-2 ${getEntryTypeColor(type)}`}>
                      {getEntryTypeLabel(type)}
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-sm text-gray-600">العدد:</span>
                      <span className="text-lg font-bold text-gray-900">{data.count}</span>
                    </div>
                    <div className="flex justify-between items-center mt-1">
                      <span className="text-sm text-gray-600">المبلغ:</span>
                      <span className="text-lg font-bold text-red-600">{data.total_amount.toFixed(2)} درهم</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Entries Table */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">تفاصيل القيود</h2>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">التاريخ</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">النوع</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الوصف</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">المبلغ</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">دورة الراتب</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">المرجع</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {ledgerData.entries.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                        لا توجد قيود مطابقة للفلاتر المحددة
                      </td>
                    </tr>
                  ) : (
                    ledgerData.entries.map((entry, index) => (
                      <tr key={entry.id || index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center">
                            <ClockIcon className="h-4 w-4 text-gray-400 ml-2" />
                            {new Date(entry.created_at).toLocaleDateString('ar-EG', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric'
                            })}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${getEntryTypeColor(entry.entry_type)}`}>
                            {getEntryTypeLabel(entry.entry_type)}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                          {entry.description || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600">
                          {entry.amount.toFixed(2)} درهم
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {entry.payroll_cycle_id ? entry.payroll_cycle_id.slice(0, 8) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {entry.reference_id ? entry.reference_id.slice(0, 8) : '-'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!ledgerData && !loading && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <DocumentTextIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            ابدأ بعرض قيود الموظفين
          </h3>
          <p className="text-gray-500">
            اختر موظف وحدد الفلاتر ثم اضغط على "عرض القيود"
          </p>
        </div>
      )}
    </div>
  );
};

export default EmployeeLedger;