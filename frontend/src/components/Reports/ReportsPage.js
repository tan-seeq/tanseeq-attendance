import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DocumentArrowDownIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API } from '../../config';

const ReportsPage = () => {
  const [reportType, setReportType] = useState('attendance');
  const [startDate, setStartDate] = useState(new Date().toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [reportData, setReportData] = useState([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const { t } = useLanguage();

  const fetchReport = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/reports/${reportType}?start_date=${startDate}&end_date=${endDate}`);
      setReportData(response.data);
    } catch (error) {
      console.error('Error fetching report:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(`${API}/reports/${reportType}/export?start_date=${startDate}&end_date=${endDate}&format=${format}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `TANSEEQ_${reportType}_report_${startDate}_${endDate}.${format === 'excel' ? 'xlsx' : 'pdf'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting report:', error);
    }
  };

  const handleQuickDateRange = (days) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    setStartDate(start.toISOString().slice(0, 10));
    setEndDate(end.toISOString().slice(0, 10));
  };

  useEffect(() => {
    if (startDate && endDate) {
      fetchReport();
    }
  }, [reportType, startDate, endDate]);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">التقارير - TANSEEQ Tax Consultancy</h2>
          <div className="flex flex-wrap gap-2">
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="attendance">تقرير الحضور</option>
              <option value="leaves">تقرير الإجازات</option>
              <option value="field-exits">تقرير الزيارات الخارجية</option>
            </select>
            <button onClick={() => handleExport('excel')} className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center">
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />تصدير Excel
            </button>
            <button onClick={() => handleExport('pdf')} className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center">
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />تصدير PDF
            </button>
          </div>
        </div>

        <div className="mb-6 bg-gray-50 p-4 rounded-lg">
          <h3 className="text-md font-medium text-gray-700 mb-3">اختيار الفترة</h3>
          <div className="flex flex-wrap gap-2 mb-4">
            <button onClick={() => handleQuickDateRange(7)} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm">آخر 7 أيام</button>
            <button onClick={() => handleQuickDateRange(30)} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm">آخر 30 يوم</button>
            <button onClick={() => handleQuickDateRange(90)} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm">آخر 3 أشهر</button>
            <button onClick={() => {
              const today = new Date();
              const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
              setStartDate(firstDay.toISOString().slice(0, 10));
              setEndDate(today.toISOString().slice(0, 10));
            }} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm">هذا الشهر</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">من تاريخ</label>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">إلى تاريخ</label>
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div className="mt-3 flex justify-center">
            <button onClick={fetchReport} className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center">
              <MagnifyingGlassIcon className="h-4 w-4 mr-2" />عرض التقرير
            </button>
          </div>
        </div>

        <div className="mb-4 bg-blue-50 p-3 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-blue-800">
              {reportType === 'attendance' ? 'تقرير الحضور' : reportType === 'leaves' ? 'تقرير الإجازات' : 'تقرير الزيارات الخارجية'}
            </span>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-blue-700">الفترة: {startDate} إلى {endDate}</span>
              <span className="text-sm text-blue-700">عدد السجلات: {reportData.length}</span>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">الموظف</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">التاريخ</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">التفاصيل</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">الحالة</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reportData.map((item, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.user_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.date}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {reportType === 'attendance' && `${item.check_in || '--'} - ${item.check_out || '--'} (${item.working_hours ? item.working_hours.toFixed(1) : '0.0'}h)`}
                      {reportType === 'leaves' && `${item.start_date} إلى ${item.end_date} (${item.days_count} يوم) - ${item.reason}`}
                      {reportType === 'field-exits' && `${item.visit_type} - ${item.start_time} إلى ${item.end_time}${item.client_name ? ` - ${item.client_name}` : ''}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        item.status === 'approved' || item.status === 'present' ? 'bg-green-100 text-green-800' :
                        item.status === 'rejected' || item.status === 'absent' ? 'bg-red-100 text-red-800' :
                        item.status === 'late' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {item.status === 'approved' ? 'موافق عليه' : 
                         item.status === 'rejected' ? 'مرفوض' : 
                         item.status === 'present' ? 'حاضر' :
                         item.status === 'late' ? 'متأخر' :
                         item.status === 'absent' ? 'غائب' : 'معلق'}
                      </span>
                      {reportType === 'attendance' && item.is_late && (
                        <span className="ml-2 px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-800">متأخر</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {!loading && reportData.length === 0 && (
          <div className="text-center py-12"><p className="text-gray-500">لا توجد بيانات في هذه الفترة</p></div>
        )}
      </div>
    </div>
  );
};

export default ReportsPage;
