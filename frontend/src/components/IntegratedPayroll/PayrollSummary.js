import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { EyeIcon, PencilIcon, DocumentArrowDownIcon, CalculatorIcon, LockClosedIcon, LockOpenIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PayrollSummary = () => {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const isEdit = searchParams.get('edit') === 'true';
  const [cycle, setCycle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchCycle = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/payroll/cycles/${id}`);
      setCycle(res.data);
      setError('');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'تعذر تحميل بيانات دورة الرواتب');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCycle();
  }, [id]);

  const handleCalculate = async () => {
    try {
      const res = await axios.get(`${API}/payroll/cycles/${id}/calculate`);
      alert(res.data?.message || 'تم حساب الرواتب');
      fetchCycle();
    } catch (err) {
      alert(err.response?.data?.detail || 'فشل حساب الرواتب');
    }
  };

  const handleLock = async () => {
    const lock_reason = prompt('سبب القفل:');
    if (!lock_reason) return;
    try {
      await axios.post(`${API}/payroll/cycles/${id}/lock`, { lock_reason });
      alert('تم قفل الدورة');
      fetchCycle();
    } catch (err) {
      alert(err.response?.data?.detail || 'فشل قفل الدورة');
    }
  };

  const handleUnlock = async () => {
    const reason = prompt('سبب فتح الدورة:');
    if (!reason) return;
    try {
      await axios.post(`${API}/payroll/cycles/${id}/unlock`, { reason });
      alert('تم فتح الدورة');
      fetchCycle();
    } catch (err) {
      alert(err.response?.data?.detail || 'فشل فتح الدورة');
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
          <ArrowLeftIcon className="w-4 h-4 ml-1" /> عودة إلى إدارة الدورات
        </a>
      </div>
    );
  }

  if (!cycle) return null;

  const exportPdfUrl = `${API}/payroll/cycles/${cycle.id}/export/pdf`;
  const exportExcelUrl = `${API}/payroll/cycles/${cycle.id}/export/excel`;

  return (
    <div className="max-w-6xl mx-auto p-6" dir="rtl">
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ملخص دورة الرواتب</h1>
            <p className="text-gray-600 mt-1">{cycle.display_name} — الحالة: {cycle.is_locked ? 'مقفولة' : 'مفتوحة'}</p>
          </div>
          <div className="flex items-center gap-2">
            <a href={exportPdfUrl} className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 inline-flex items-center" target="_blank" rel="noreferrer">
              <DocumentArrowDownIcon className="w-5 h-5 ml-2" /> PDF
            </a>
            <a href={exportExcelUrl} className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 inline-flex items-center" target="_blank" rel="noreferrer">
              <DocumentArrowDownIcon className="w-5 h-5 ml-2" /> Excel
            </a>
            {!cycle.is_locked ? (
              <>
                <button onClick={handleCalculate} className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 inline-flex items-center">
                  <CalculatorIcon className="w-5 h-5 ml-2" /> حساب الرواتب
                </button>
                <button onClick={handleLock} className="px-3 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 inline-flex items-center">
                  <LockClosedIcon className="w-5 h-5 ml-2" /> قفل الدورة
                </button>
              </>
            ) : (
              <button onClick={handleUnlock} className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 inline-flex items-center">
                <LockOpenIcon className="w-5 h-5 ml-2" /> فتح الدورة
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">تفاصيل</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6">
          <div>
            <p className="text-sm text-gray-500">عدد الموظفين</p>
            <p className="text-xl font-bold">{cycle.total_employees || 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">إجمالي الرواتب</p>
            <p className="text-xl font-bold text-green-600">{(cycle.total_gross_salary || 0).toFixed(2)} درهم</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">إجمالي الخصومات</p>
            <p className="text-xl font-bold text-red-600">{(cycle.total_deductions || 0).toFixed(2)} درهم</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">الصافي</p>
            <p className="text-xl font-bold text-blue-600">{(cycle.total_net_salary || 0).toFixed(2)} درهم</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">تاريخ الإنشاء</p>
            <p className="text-xl font-bold">{new Date(cycle.created_at).toLocaleString('ar-AE')}</p>
          </div>
        </div>
      </div>

      {Array.isArray(cycle.lines) && cycle.lines.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden mt-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">تفاصيل الموظفين</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الموظف</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الراتب</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الخصومات</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الصافي</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {cycle.lines.map((line) => (
                  <tr key={line.employee_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{line.employee_name || line.name || 'غير محدد'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{(line.gross || 0).toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">{(line.deductions || 0).toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">{(line.net || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default PayrollSummary;
