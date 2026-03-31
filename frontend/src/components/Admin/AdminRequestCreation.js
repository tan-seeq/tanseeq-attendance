import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowPathIcon, PlusIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../config';

const AdminRequestCreation = () => {
  const [activeTab, setActiveTab] = useState('leave');
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { user } = useAuth();

  // Leave Form State
  const [leaveForm, setLeaveForm] = useState({
    user_id: '',
    start_date: '',
    end_date: '',
    reason: '',
    leave_type: 'annual',
    days_count: 1,
    notes: '',
    file: null
  });

  // Field Exit Form State  
  const [fieldExitForm, setFieldExitForm] = useState({
    user_id: '',
    date: '',
    visit_type: 'client_visit',
    client_name: '',
    expected_start_time: '09:00',
    expected_end_time: '17:00',
    report: '',
    notes: ''
  });

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setEmployees(response.data.filter(emp => emp.is_active));
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  const calculateDaysCount = (startDate, endDate) => {
    if (!startDate || !endDate) return 1;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
  };

  const handleLeaveSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const formData = new FormData();
      Object.keys(leaveForm).forEach(key => {
        if (key === 'file' && leaveForm[key]) {
          formData.append(key, leaveForm[key]);
        } else if (key !== 'file') {
          formData.append(key, leaveForm[key]);
        }
      });

      const response = await axios.post(`${API}/admin/create-leave-request`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setMessage({ type: 'success', text: 'تم إنشاء طلب الإجازة بنجاح!' });
      setLeaveForm({
        user_id: '',
        start_date: '',
        end_date: '',
        reason: '',
        leave_type: 'annual',
        days_count: 1,
        notes: '',
        file: null
      });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في إنشاء طلب الإجازة' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFieldExitSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const formData = new FormData();
      Object.keys(fieldExitForm).forEach(key => {
        formData.append(key, fieldExitForm[key]);
      });

      const response = await axios.post(`${API}/admin/create-field-exit-request`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setMessage({ type: 'success', text: 'تم إنشاء طلب الزيارة الخارجية بنجاح!' });
      setFieldExitForm({
        user_id: '',
        date: '',
        visit_type: 'client_visit',
        client_name: '',
        expected_start_time: '09:00',
        expected_end_time: '17:00',
        report: '',
        notes: ''
      });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في إنشاء طلب الزيارة الخارجية' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-gray-800">إنشاء طلبات نيابة عن الموظفين</h2>
          <div className="bg-blue-50 px-3 py-1 rounded-lg">
            <span className="text-sm text-blue-700 font-medium">Super Admin فقط</span>
          </div>
        </div>

        {message && (
          <div className={`p-4 mb-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {message.text}
          </div>
        )}

        {/* Tabs */}
        <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('leave')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'leave'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            طلب إجازة
          </button>
          <button
            onClick={() => setActiveTab('field-exit')}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'field-exit'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            زيارة خارجية
          </button>
        </div>

        {/* Leave Request Tab */}
        {activeTab === 'leave' && (
          <form onSubmit={handleLeaveSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الموظف *</label>
                <select
                  value={leaveForm.user_id}
                  onChange={(e) => setLeaveForm({...leaveForm, user_id: e.target.value})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">اختر الموظف</option>
                  {employees.map(emp => (
                    <option key={emp.id} value={emp.id}>{emp.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">نوع الإجازة</label>
                <select
                  value={leaveForm.leave_type}
                  onChange={(e) => setLeaveForm({...leaveForm, leave_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="annual">إجازة سنوية</option>
                  <option value="sick">إجازة مرضية</option>
                  <option value="emergency">إجازة طارئة</option>
                  <option value="personal">إجازة شخصية</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">تاريخ البداية *</label>
                <input
                  type="date"
                  value={leaveForm.start_date}
                  onChange={(e) => {
                    const newStartDate = e.target.value;
                    const days = calculateDaysCount(newStartDate, leaveForm.end_date);
                    setLeaveForm({
                      ...leaveForm, 
                      start_date: newStartDate,
                      days_count: days
                    });
                  }}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">تاريخ النهاية *</label>
                <input
                  type="date"
                  value={leaveForm.end_date}
                  onChange={(e) => {
                    const newEndDate = e.target.value;
                    const days = calculateDaysCount(leaveForm.start_date, newEndDate);
                    setLeaveForm({
                      ...leaveForm, 
                      end_date: newEndDate,
                      days_count: days
                    });
                  }}
                  required
                  min={leaveForm.start_date}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">عدد الأيام</label>
                <input
                  type="number"
                  value={leaveForm.days_count}
                  onChange={(e) => setLeaveForm({...leaveForm, days_count: parseInt(e.target.value)})}
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-100"
                  readOnly
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">المرفقات</label>
                <input
                  type="file"
                  accept="image/*,.pdf"
                  onChange={(e) => setLeaveForm({...leaveForm, file: e.target.files[0]})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">السبب *</label>
              <textarea
                value={leaveForm.reason}
                onChange={(e) => setLeaveForm({...leaveForm, reason: e.target.value})}
                required
                rows="3"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="اكتب سبب الإجازة..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ملاحظات إضافية</label>
              <textarea
                value={leaveForm.notes}
                onChange={(e) => setLeaveForm({...leaveForm, notes: e.target.value})}
                rows="2"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="ملاحظات للموظف..."
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center"
            >
              {loading ? <ArrowPathIcon className="h-4 w-4 animate-spin mr-2" /> : <PlusIcon className="h-4 w-4 mr-2" />}
              إنشاء طلب الإجازة
            </button>
          </form>
        )}

        {/* Field Exit Request Tab */}
        {activeTab === 'field-exit' && (
          <form onSubmit={handleFieldExitSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الموظف *</label>
                <select
                  value={fieldExitForm.user_id}
                  onChange={(e) => setFieldExitForm({...fieldExitForm, user_id: e.target.value})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">اختر الموظف</option>
                  {employees.map(emp => (
                    <option key={emp.id} value={emp.id}>{emp.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">التاريخ *</label>
                <input
                  type="date"
                  value={fieldExitForm.date}
                  onChange={(e) => setFieldExitForm({...fieldExitForm, date: e.target.value})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">نوع الزيارة *</label>
                <select
                  value={fieldExitForm.visit_type}
                  onChange={(e) => setFieldExitForm({...fieldExitForm, visit_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="client_visit">زيارة عميل</option>
                  <option value="collection">تحصيل</option>
                  <option value="bank_visit">زيارة بنك</option>
                  <option value="admin_errand">مهمة إدارية</option>
                  <option value="personal">شخصية</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">اسم العميل</label>
                <input
                  type="text"
                  value={fieldExitForm.client_name}
                  onChange={(e) => setFieldExitForm({...fieldExitForm, client_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="اسم العميل (اختياري)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الوقت المتوقع للخروج *</label>
                <input
                  type="time"
                  value={fieldExitForm.expected_start_time}
                  onChange={(e) => setFieldExitForm({...fieldExitForm, expected_start_time: e.target.value})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الوقت المتوقع للعودة *</label>
                <input
                  type="time"
                  value={fieldExitForm.expected_end_time}
                  onChange={(e) => setFieldExitForm({...fieldExitForm, expected_end_time: e.target.value})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">الغرض من الزيارة *</label>
              <textarea
                value={fieldExitForm.report}
                onChange={(e) => setFieldExitForm({...fieldExitForm, report: e.target.value})}
                required
                rows="3"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="اكتب الغرض من الزيارة..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ملاحظات إضافية</label>
              <textarea
                value={fieldExitForm.notes}
                onChange={(e) => setFieldExitForm({...fieldExitForm, notes: e.target.value})}
                rows="2"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="ملاحظات للموظف..."
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400 flex items-center justify-center"
            >
              {loading ? <ArrowPathIcon className="h-4 w-4 animate-spin mr-2" /> : <PlusIcon className="h-4 w-4 mr-2" />}
              إنشاء طلب الزيارة الخارجية
            </button>
          </form>
        )}
      </div>
    </div>
  );
};


export default AdminRequestCreation;
