import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UserIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API } from '../../config';

const Payroll = () => {
  const [payrollData, setPayrollData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchPayrollData();
  }, [selectedMonth]);

  const fetchPayrollData = async () => {
    try {
      const response = await axios.get(`${API}/payroll/calculate/${selectedMonth}`);
      setPayrollData(response.data);
    } catch (error) {
      console.error('Error fetching payroll data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(`${API}/payroll/export/${selectedMonth}?format=${format}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `payroll_${selectedMonth}.${format === 'excel' ? 'xlsx' : 'pdf'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting payroll:', error);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  const totalSalary = payrollData.reduce((sum, employee) => sum + employee.final_salary, 0);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">كشف المرتبات - TANSEEQ Tax Consultancy</h2>
          <div className="flex space-x-2">
            <div className="flex flex-col">
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Array.from({length: 12}, (_, i) => {
                const date = new Date();
                date.setMonth(date.getMonth() - i);
                const monthStr = date.toISOString().slice(0, 7);
                return (
                  <option key={monthStr} value={monthStr}>
                    {date.toLocaleDateString('ar', { year: 'numeric', month: 'long' })}
                  </option>
                );
              })}
            </select>
            <div className="text-xs text-gray-500 mt-1">
              Cycle: 29th prev month - 28th current month
            </div>
          </div>
        </div>
          
          <div className="sticky top-0 z-10 bg-white border-b border-gray-200 pb-3 flex gap-3">
            <button
              onClick={() => handleExport('excel')}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 shadow-md flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              تصدير Excel
            </button>
            <button
              onClick={() => handleExport('pdf')}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 shadow-md flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              تصدير PDF
            </button>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">الموظف</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">المنصب</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">الراتب الشهري</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">المعدل اليومي</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">أيام العمل</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ساعات العمل</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">أيام التأخير</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">الراتب النهائي</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {payrollData.map((employee) => (
                <tr key={employee.user_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <UserIcon className="h-8 w-8 text-gray-400 mr-3" />
                      <div className="text-sm font-medium text-gray-900">{employee.name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{employee.position}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="font-medium">AED {employee.monthly_salary.toLocaleString()}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">AED {employee.daily_rate.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <span className="font-medium">{employee.working_days}</span>
                      <span className="text-gray-500 ml-1">/ 22</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{employee.total_hours.toFixed(1)} ساعة</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      employee.late_days > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {employee.late_days} يوم
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="font-bold text-green-600">AED {employee.final_salary.toLocaleString()}</div>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr>
                <td colSpan="7" className="px-6 py-4 text-right text-sm font-medium text-gray-900">الإجمالي:</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">AED {totalSalary.toLocaleString()}</td>
              </tr>
            </tfoot>
          </table>
        </div>
        
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900">إجمالي الموظفين</h3>
            <p className="text-2xl font-bold text-blue-600">{payrollData.length}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-green-900">متوسط الراتب</h3>
            <p className="text-2xl font-bold text-green-600">
              AED {payrollData.length > 0 ? (totalSalary / payrollData.length).toFixed(2) : 0}
            </p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-purple-900">إجمالي الرواتب</h3>
            <p className="text-2xl font-bold text-purple-600">AED {totalSalary.toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Payroll;
