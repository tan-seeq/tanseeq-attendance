import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  UserGroupIcon,
  CurrencyDollarIcon,
  BanknotesIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CheckCircleIcon,
  ChartBarIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DEFAULT_KPIS = {
  totalEmployees: 0, activeEmployees: 0,
  totalSalaries: 0, avgSalary: 0,
  totalAdvances: 0, pendingAdvances: 0, approvedAdvances: 0, totalAdvancesAmount: 0,
  totalAttendance: 0, presentCount: 0, lateCount: 0, absentCount: 0, attendanceRate: 0,
  totalDeductions: 0, employeesWithDeductions: 0, month: ''
};

const HRDashboard = () => {
  const [kpis, setKpis] = useState(DEFAULT_KPIS);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));

  useEffect(() => {
    fetchKPIs();
  }, [selectedMonth]);

  const fetchKPIs = async () => {
    try {
      setLoading(true);
      
      // Fetch each source independently to avoid one failure breaking all
      let employees = [];
      let advances = [];
      let attendance = [];
      let deductions = {};

      const results = await Promise.allSettled([
        axios.get(`${API}/employees/list`),
        axios.get(`${API}/advances/admin/all-transactions`),
        axios.get(`${API}/attendance/with-absences?month=${selectedMonth}`),
        axios.post(`${API}/deductions/calculate-monthly?month=${selectedMonth}`, {})
      ]);

      if (results[0].status === 'fulfilled') employees = results[0].value?.data?.employees || [];
      if (results[1].status === 'fulfilled') advances = results[1].value?.data?.transactions?.filter(t => t.transaction_type === 'advance') || [];
      if (results[2].status === 'fulfilled') attendance = results[2].value?.data?.attendance || [];
      if (results[3].status === 'fulfilled') deductions = results[3].value?.data || {};

      setKpis({
        totalEmployees: employees.length,
        activeEmployees: employees.filter(e => e.is_active).length,
        totalSalaries: employees.reduce((sum, e) => sum + (e.monthly_salary || 0), 0),
        avgSalary: employees.length > 0 ? employees.reduce((sum, e) => sum + (e.monthly_salary || 0), 0) / employees.length : 0,
        totalAdvances: advances.length,
        pendingAdvances: advances.filter(a => a.status === 'pending').length,
        approvedAdvances: advances.filter(a => a.status === 'approved').length,
        totalAdvancesAmount: advances.filter(a => a.status === 'approved').reduce((sum, a) => sum + (a.amount || 0), 0),
        totalAttendance: attendance.length,
        presentCount: attendance.filter(r => r.status === 'present').length,
        lateCount: attendance.filter(r => r.status === 'late').length,
        absentCount: attendance.filter(r => r.status === 'absent').length,
        attendanceRate: attendance.length > 0 ? 
          ((attendance.filter(r => r.status === 'present' || r.status === 'late').length / attendance.length) * 100).toFixed(1) : 0,
        totalDeductions: deductions.total_deductions || 0,
        employeesWithDeductions: deductions.employee_count || 0,
        month: selectedMonth
      });
    } catch (err) {
      console.error('Error fetching KPIs:', err);
      setKpis({...DEFAULT_KPIS, month: selectedMonth});
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 text-white p-6 rounded-lg shadow-lg mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">📊 لوحة التحكم التحليلية</h1>
            <p className="text-indigo-100">مؤشرات الأداء الرئيسية (KPIs) للموارد البشرية</p>
          </div>
          <ChartBarIcon className="h-16 w-16 text-indigo-200" />
        </div>
      </div>

      {/* Month Selector */}
      <div className="bg-white rounded-lg shadow-lg p-4 mb-6">
        <div className="flex items-center gap-4">
          <CalendarIcon className="h-5 w-5 text-gray-500" />
          <label className="text-sm font-medium text-gray-700">اختر الشهر:</label>
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
          />
          <span className="text-sm text-gray-600">
            البيانات محدّثة حسب الشهر المختار
          </span>
        </div>
      </div>

      {/* Employee KPIs */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">👥 مؤشرات الموظفين</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gradient-to-r from-blue-100 to-blue-200 p-6 rounded-xl shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700 font-medium">إجمالي الموظفين</p>
                <p className="text-4xl font-bold text-blue-900">{kpis.totalEmployees}</p>
                <p className="text-xs text-blue-600 mt-1">نشط: {kpis.activeEmployees}</p>
              </div>
              <UserGroupIcon className="h-14 w-14 text-blue-500" />
            </div>
          </div>

          <div className="bg-gradient-to-r from-green-100 to-green-200 p-6 rounded-xl shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700 font-medium">معدل الحضور</p>
                <p className="text-4xl font-bold text-green-900">{kpis.attendanceRate}%</p>
                <p className="text-xs text-green-600 mt-1">للشهر الحالي</p>
              </div>
              <CheckCircleIcon className="h-14 w-14 text-green-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Payroll KPIs */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">💰 مؤشرات الرواتب</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-r from-purple-100 to-purple-200 p-6 rounded-xl shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-700 font-medium">إجمالي الرواتب</p>
                <p className="text-3xl font-bold text-purple-900">
                  {(kpis.totalSalaries || 0).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                </p>
                <p className="text-xs text-purple-600 mt-1">درهم شهرياً</p>
              </div>
              <CurrencyDollarIcon className="h-12 w-12 text-purple-500" />
            </div>
          </div>

          <div className="bg-gradient-to-r from-indigo-100 to-indigo-200 p-6 rounded-xl shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-indigo-700 font-medium">متوسط الراتب</p>
                <p className="text-3xl font-bold text-indigo-900">
                  {(kpis.avgSalary || 0).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                </p>
                <p className="text-xs text-indigo-600 mt-1">درهم</p>
              </div>
              <ChartBarIcon className="h-12 w-12 text-indigo-500" />
            </div>
          </div>

          <div className="bg-gradient-to-r from-red-100 to-red-200 p-6 rounded-xl shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-700 font-medium">إجمالي الخصومات</p>
                <p className="text-3xl font-bold text-red-900">
                  {(kpis.totalDeductions || 0).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                </p>
                <p className="text-xs text-red-600 mt-1">درهم ({kpis.month})</p>
              </div>
              <ExclamationTriangleIcon className="h-12 w-12 text-red-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Advances KPIs */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">💵 مؤشرات السلف</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500">
            <p className="text-sm text-gray-600 font-medium">إجمالي السلف</p>
            <p className="text-3xl font-bold text-gray-900">{kpis.totalAdvances}</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-yellow-500">
            <p className="text-sm text-gray-600 font-medium">معلقة</p>
            <p className="text-3xl font-bold text-yellow-600">{kpis.pendingAdvances}</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-green-500">
            <p className="text-sm text-gray-600 font-medium">موافق عليها</p>
            <p className="text-3xl font-bold text-green-600">{kpis.approvedAdvances}</p>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-purple-500">
            <p className="text-sm text-gray-600 font-medium">إجمالي المبالغ</p>
            <p className="text-2xl font-bold text-purple-600">
              {(kpis.totalAdvancesAmount || 0).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            </p>
            <p className="text-xs text-gray-500">درهم</p>
          </div>
        </div>
      </div>

      {/* Attendance Breakdown */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">⏰ تفصيل الحضور ({kpis.month})</h2>
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-3">
                <span className="text-2xl font-bold text-blue-600">{kpis.totalAttendance}</span>
              </div>
              <p className="text-sm text-gray-600">إجمالي السجلات</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-3">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              </div>
              <p className="text-2xl font-bold text-green-600">{kpis.presentCount}</p>
              <p className="text-sm text-gray-600">حضور</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-yellow-100 mb-3">
                <ClockIcon className="h-8 w-8 text-yellow-600" />
              </div>
              <p className="text-2xl font-bold text-yellow-600">{kpis.lateCount}</p>
              <p className="text-sm text-gray-600">تأخير</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-3">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />
              </div>
              <p className="text-2xl font-bold text-red-600">{kpis.absentCount}</p>
              <p className="text-sm text-gray-600">غياب</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">⚡ إجراءات سريعة</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/reports/deductions"
            className="block p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:shadow-md transition-all"
          >
            <ChartBarIcon className="h-8 w-8 text-indigo-600 mb-2" />
            <p className="font-semibold text-gray-900">تقرير الخصومات</p>
            <p className="text-sm text-gray-600">عرض تفاصيل الخصومات الشهرية</p>
          </a>

          <a
            href="/reports/advances"
            className="block p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:shadow-md transition-all"
          >
            <BanknotesIcon className="h-8 w-8 text-green-600 mb-2" />
            <p className="font-semibold text-gray-900">تقرير السلف</p>
            <p className="text-sm text-gray-600">متابعة السلف والأقساط</p>
          </a>

          <a
            href="/payroll-ledger"
            className="block p-4 border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:shadow-md transition-all"
          >
            <CurrencyDollarIcon className="h-8 w-8 text-purple-600 mb-2" />
            <p className="font-semibold text-gray-900">سجل قيود الرواتب</p>
            <p className="text-sm text-gray-600">عرض جميع القيود المحاسبية</p>
          </a>
        </div>
      </div>
    </div>
  );
};

export default HRDashboard;