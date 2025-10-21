import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  CalculatorIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  DocumentTextIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MonthlyDeductionsCalculator = () => {
  // Mode: 'monthly' or 'custom'
  const [mode, setMode] = useState('monthly');
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [calculating, setCalculating] = useState(false);
  const [applying, setApplying] = useState(false);
  const [calculatedData, setCalculatedData] = useState(null);
  const [error, setError] = useState('');

  const handleCalculate = async () => {
    try {
      setCalculating(true);
      setError('');
      
      // Validation for custom mode
      if (mode === 'custom') {
        if (!fromDate || !toDate) {
          setError('يرجى تحديد الفترة كاملة (من وإلى)');
          setCalculating(false);
          return;
        }
        
        const diffDays = Math.floor((new Date(toDate) - new Date(fromDate)) / (1000 * 60 * 60 * 24));
        
        if (new Date(fromDate) > new Date(toDate)) {
          setError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية');
          setCalculating(false);
          return;
        }
        
        if (diffDays > 93) {
          setError('الفترة المحددة تتجاوز 93 يومًا، الرجاء تقليص النطاق');
          setCalculating(false);
          return;
        }
      }
      
      // Build API URL based on mode
      let apiUrl;
      if (mode === 'monthly') {
        apiUrl = `${API}/deductions/calculate-monthly?month=${selectedMonth}`;
      } else {
        apiUrl = `${API}/deductions/calculate?mode=custom&from_date=${fromDate}&to_date=${toDate}&preview=true`;
      }
      
      const response = await axios.post(apiUrl, {});
      
      // Handle response and transform to consistent format
      let transformedData = null;
      
      if (response.data.items) {
        // Custom API format - transform to match monthly format
        transformedData = {
          success: true,
          employee_count: response.data.employees_count || response.data.items.length,
          total_deductions: response.data.items.reduce((sum, emp) => sum + (emp.amount || 0), 0),
          employees: response.data.items.map(item => ({
            employee_id: item.employee_id,
            employee_name: item.employee_name,
            // Map custom API fields to monthly API structure
            late_deduction: 0, // Custom API doesn't provide breakdown
            absence_deduction: 0,
            advance_deduction: 0,
            total_deduction: item.amount || 0,
            late_count: 0,
            absence_count: 0,
            installment_count: 0,
            deduction_details: [`إجمالي الخصومات: ${(item.amount || 0).toFixed(2)} درهم`]
          }))
        };
      } else if (response.data.success && response.data.employees) {
        // Monthly API format - use as is
        transformedData = response.data;
        if (!transformedData.total_deductions) {
          transformedData.total_deductions = transformedData.employees.reduce((sum, emp) => sum + (emp.total_deduction || 0), 0);
        }
      } else {
        // Fallback: empty result
        transformedData = {
          success: true,
          employees: [],
          employee_count: 0,
          total_deductions: 0
        };
      }
      
      setCalculatedData(transformedData);
    } catch (err) {
      console.error('Error calculating deductions:', err);
      const errorMsg = typeof err.response?.data?.detail === 'string' 
        ? err.response.data.detail 
        : err.response?.data?.message || err.message || 'خطأ في حساب الخصومات';
      setError(errorMsg);
    } finally {
      setCalculating(false);
    }
  };

  const handleApply = async () => {
    if (!calculatedData || !calculatedData.employees) {
      alert('يرجى حساب الخصومات أولاً');
      return;
    }

    const confirmApply = window.confirm(
      `هل أنت متأكد من تطبيق الخصومات على ${calculatedData.employee_count} موظف؟\n` +
      `إجمالي الخصومات: ${(calculatedData.total_deductions || 0).toFixed(2)} درهم\n\n` +
      `سيتم:\n` +
      `• إضافة/تحديث دورة الرواتب لشهر ${selectedMonth}\n` +
      `• تطبيق جميع الخصومات (التأخير، الغياب، السلف)\n` +
      `• إرسال إشعارات للموظفين`
    );

    if (!confirmApply) {
      return;
    }

    try {
      setApplying(true);
      setError('');
      
      const response = await axios.post(`${API}/deductions/apply-monthly`, {
        month: selectedMonth,
        employees: calculatedData.employees
      });
      
      if (response.data.success) {
        alert(response.data.message);
        // Clear calculated data after successful application
        setCalculatedData(null);
      }
    } catch (err) {
      console.error('Error applying deductions:', err);
      const errorMsg = typeof err.response?.data?.detail === 'string' 
        ? err.response.data.detail 
        : err.response?.data?.message || err.message || 'خطأ في تطبيق الخصومات';
      setError(errorMsg);
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg shadow-lg mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">🧮 نظام خصومات التأخير المتقدم</h1>
            <p className="text-blue-100">حساب وتطبيق خصومات التأخير والغياب والسلف المستحقة</p>
          </div>
          <CalculatorIcon className="h-16 w-16 text-blue-200" />
        </div>
      </div>

      {/* Rules Box */}
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">📋 قواعد نظام الخصومات:</h3>
        <ul className="space-y-2 text-blue-800">
          <li className="flex items-start">
            <span className="ml-2">•</span>
            <span>أول 15 دقيقة تأخير × 4 مرات = مجاناً</span>
          </li>
          <li className="flex items-start">
            <span className="ml-2">•</span>
            <span>أكثر من 4 مرات: تُجمع الدقائق وتُخصم من الراتب</span>
          </li>
          <li className="flex items-start">
            <span className="ml-2">•</span>
            <span>أكثر من 20 دقيقة: خصم بالوقت الفعلي</span>
          </li>
          <li className="flex items-start">
            <span className="ml-2">•</span>
            <span>من ساعة إلى ساعتين: خصم نصف يوم</span>
          </li>
          <li className="flex items-start">
            <span className="ml-2">•</span>
            <span>أكثر من ساعتين: خصم يوم كامل</span>
          </li>
          <li className="flex items-start">
            <span className="ml-2">•</span>
            <span>الغياب: خصم يوم كامل من الراتب</span>
          </li>
          <li className="flex items-start">
            <span className="ml-2">•</span>
            <span>السلف: خصم الأقساط المستحقة حسب الجدولة</span>
          </li>
        </ul>
      </div>

      {/* Month Selection & Actions */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        {/* Mode Selector */}
        <div className="mb-6 pb-4 border-b-2 border-gray-300">
          <label className="block text-gray-800 font-bold mb-3 text-lg">📋 نوع الحساب</label>
          <div className="flex flex-wrap items-center gap-6">
            <label className="flex items-center gap-2 cursor-pointer bg-blue-50 px-4 py-3 rounded-lg border-2 border-blue-200 hover:bg-blue-100 transition">
              <input
                type="radio"
                name="mode"
                value="monthly"
                checked={mode === 'monthly'}
                onChange={() => {
                  setMode('monthly');
                  setCalculatedData(null);
                  setError('');
                }}
                className="w-5 h-5 text-blue-600"
              />
              <span className="text-gray-800 font-semibold text-base">🗓️ حساب شهري</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer bg-green-50 px-4 py-3 rounded-lg border-2 border-green-200 hover:bg-green-100 transition">
              <input
                type="radio"
                name="mode"
                value="custom"
                checked={mode === 'custom'}
                onChange={() => {
                  setMode('custom');
                  setCalculatedData(null);
                  setError('');
                }}
                className="w-5 h-5 text-green-600"
              />
              <span className="text-gray-800 font-semibold text-base">📅 فترة مخصصة</span>
            </label>
          </div>
        </div>

        {/* Custom Mode Info */}
        {mode === 'custom' && (
          <div className="mb-4 p-4 bg-blue-50 border-2 border-blue-400 rounded-lg">
            <p className="text-sm text-blue-800 font-semibold">
              ℹ️ <strong>ملاحظة:</strong> يمكنك حساب الخصومات لأي فترة زمنية مخصصة (الحد الأقصى: 93 يوم).
            </p>
          </div>
        )}

        <div className="flex items-center justify-between flex-wrap gap-4">
          {mode === 'monthly' ? (
            <div className="flex items-center gap-4">
              <CalendarIcon className="h-6 w-6 text-gray-500" />
              <label className="text-sm font-medium text-gray-700">اختر الشهر:</label>
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => {
                  setSelectedMonth(e.target.value);
                  setCalculatedData(null); // Clear previous calculations
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ) : (
            <div className="flex items-center gap-4 flex-wrap">
              <CalendarIcon className="h-6 w-6 text-gray-500" />
              <label className="text-sm font-medium text-gray-700">من تاريخ:</label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => {
                  setFromDate(e.target.value);
                  setCalculatedData(null);
                  setError('');
                }}
                className="px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <label className="text-sm font-medium text-gray-700">إلى تاريخ:</label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => {
                  setToDate(e.target.value);
                  setCalculatedData(null);
                  setError('');
                }}
                className="px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>
          )}
          
          <div className="flex gap-3">
            <button
              onClick={handleCalculate}
              disabled={calculating || (mode === 'custom' && (!fromDate || !toDate))}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-semibold shadow-md"
            >
              {calculating ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  جاري الحساب...
                </>
              ) : (
                <>
                  <CalculatorIcon className="h-5 w-5" />
                  🧮 حساب الخصومات
                </>
              )}
            </button>

            {calculatedData && (
              <button
                onClick={handleApply}
                disabled={applying}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-semibold shadow-md"
              >
                {applying ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    جاري التطبيق...
                  </>
                ) : (
                  <>
                    <CheckCircleIcon className="h-5 w-5" />
                    تطبيق الخصومات
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-lg">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-6 w-6 text-red-500 ml-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {calculatedData && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-gradient-to-r from-orange-100 to-orange-200 p-6 rounded-xl shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-700 font-medium">الموظفين المتأثرين</p>
                  <p className="text-3xl font-bold text-orange-800">{calculatedData.employee_count}</p>
                </div>
                <UserGroupIcon className="h-12 w-12 text-orange-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-red-100 to-red-200 p-6 rounded-xl shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-700 font-medium">إجمالي الخصومات</p>
                  <p className="text-3xl font-bold text-red-800">
                    {(calculatedData.total_deductions || 0).toFixed(2)} <span className="text-xl">درهم</span>
                  </p>
                </div>
                <CurrencyDollarIcon className="h-12 w-12 text-red-500" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-blue-100 to-blue-200 p-6 rounded-xl shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-700 font-medium">الشهر</p>
                  <p className="text-2xl font-bold text-blue-800">{calculatedData.month}</p>
                </div>
                <CalendarIcon className="h-12 w-12 text-blue-500" />
              </div>
            </div>
          </div>

          {/* Deductions Table */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                نتائج حساب الخصومات - {calculatedData.month}
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      الموظف
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      مرات التأخير
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      أيام الغياب
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      أقساط السلف
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      خصم التأخير
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      خصم الغياب
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      خصم السلف
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      إجمالي الخصم
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      التفاصيل
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {calculatedData.employees && calculatedData.employees.map((emp, index) => (
                    <tr key={emp.employee_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="text-sm font-medium text-gray-900">{emp.employee_name}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                        {emp.late_count > 0 ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800">
                            {emp.late_count}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                        {emp.absence_count > 0 ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                            {emp.absence_count}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                        {emp.installment_count > 0 ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
                            {emp.installment_count}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-yellow-600">
                        {(emp.late_deduction || 0) > 0 ? `${(emp.late_deduction || 0).toFixed(2)} درهم` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-red-600">
                        {(emp.absence_deduction || 0) > 0 ? `${(emp.absence_deduction || 0).toFixed(2)} درهم` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-purple-600">
                        {(emp.advance_deduction || 0) > 0 ? `${(emp.advance_deduction || 0).toFixed(2)} درهم` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-700">
                        {(emp.total_deduction || 0).toFixed(2)} درهم
                      </td>
                      <td className="px-6 py-4">
                        <div className="max-w-xs">
                          {emp.deduction_details && emp.deduction_details.length > 0 ? (
                            <ul className="text-xs text-gray-600 space-y-1">
                              {emp.deduction_details.map((detail, idx) => (
                                <li key={idx} className="flex items-start">
                                  <span className="ml-1">•</span>
                                  <span>{detail}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-100">
                  <tr>
                    <td colSpan="7" className="px-6 py-4 text-right text-sm font-bold text-gray-900">
                      إجمالي الخصومات:
                    </td>
                    <td colSpan="2" className="px-6 py-4 text-sm font-bold text-red-700">
                      {(calculatedData.total_deductions || 0).toFixed(2)} درهم
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!calculatedData && !calculating && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <CalculatorIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            ابدأ بحساب الخصومات
          </h3>
          <p className="text-gray-500 mb-6">
            اختر الشهر واضغط على "🧮 حساب الخصومات" لعرض التفاصيل
          </p>
        </div>
      )}
    </div>
  );
};

export default MonthlyDeductionsCalculator;