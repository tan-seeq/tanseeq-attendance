import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API } from '../../config';

const Attendance = () => {
  const [attendance, setAttendance] = useState([]);
  const [todayAttendance, setTodayAttendance] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchAttendance();
  }, []);

  const fetchAttendance = async () => {
    try {
      const response = await axios.get(`${API}/attendance`);
      setAttendance(response.data);
      
      const today = new Date().toISOString().split('T')[0];
      const todayRecord = response.data.find(a => a.date === today && a.user_id === user?.id);
      setTodayAttendance(todayRecord);
    } catch (error) {
      console.error('Error fetching attendance:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckIn = async () => {
    try {
      await axios.post(`${API}/attendance/check-in`);
      fetchAttendance();
    } catch (error) {
      console.error('Error checking in:', error);
      alert(error.response?.data?.detail || 'Error checking in');
    }
  };

  const handleCheckOut = async () => {
    try {
      await axios.post(`${API}/attendance/check-out`);
      fetchAttendance();
    } catch (error) {
      console.error('Error checking out:', error);
      alert(error.response?.data?.detail || 'Error checking out');
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">{t('attendance')}</h2>
        
        <div className="flex space-x-4 mb-6">
          <button
            onClick={handleCheckIn}
            disabled={todayAttendance?.check_in}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t('check_in')}
          </button>
          
          <button
            onClick={handleCheckOut}
            disabled={!todayAttendance?.check_in || todayAttendance?.check_out}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t('check_out')}
          </button>
        </div>

        {todayAttendance && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium mb-2">الحضور اليوم</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">الحضور:</span>
                <span className="ml-2 font-medium">{todayAttendance.check_in || '--'}</span>
              </div>
              <div>
                <span className="text-gray-600">الانصراف:</span>
                <span className="ml-2 font-medium">{todayAttendance.check_out || '--'}</span>
              </div>
              <div>
                <span className="text-gray-600">ساعات العمل:</span>
                <span className="ml-2 font-medium">{todayAttendance.working_hours ? `${todayAttendance.working_hours.toFixed(1)} ساعة` : '--'}</span>
              </div>
              <div>
                <span className="text-gray-600">الحالة:</span>
                <span className={`ml-2 font-medium ${todayAttendance.is_late ? 'text-red-600' : 'text-green-600'}`}>
                  {todayAttendance.is_late ? t('late') : 'في الوقت'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">سجل الحضور</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('date')}</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">الحضور</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">الانصراف</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ساعات العمل</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('status')}</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {attendance.map((record) => (
                <tr key={record.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{record.date}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{record.check_in || '--'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{record.check_out || '--'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{record.working_hours ? `${record.working_hours.toFixed(1)} ساعة` : '--'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      record.status === 'present' ? 'bg-green-100 text-green-800' :
                      record.status === 'late' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {record.status === 'present' ? 'حاضر' : 
                       record.status === 'late' ? 'متأخر' : 'غائب'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Attendance;
