import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  BellIcon, 
  PaperAirplaneIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const NotificationSystem = () => {
  const [notifications, setNotifications] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [showSendModal, setShowSendModal] = useState(false);
  const [newNotification, setNewNotification] = useState({
    recipient_id: '',
    subject: '',
    message: '',
    priority: 'normal',
    type: 'info'
  });
  
  // Warning/Notice notification state
  const [showWarningModal, setShowWarningModal] = useState(false);
  const [warningNotification, setWarningNotification] = useState({
    recipient_id: '',
    title: '',
    message: '',
    notification_type: 'warning',
    required_action: '',
    additional_notes: ''
  });
  const [loading, setLoading] = useState(false);

  const API = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchNotifications();
    fetchAllUsers();
  }, []);

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const fetchAllUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAllUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const handleSendNotification = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/notifications/send`, newNotification, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      alert('تم إرسال الإشعار بنجاح');
      setShowSendModal(false);
      setNewNotification({
        recipient_id: '',
        subject: '',
        message: '',
        priority: 'normal',
        type: 'info'
      });
      fetchNotifications();
    } catch (error) {
      console.error('Error sending notification:', error);
      alert('فشل في إرسال الإشعار');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'normal': return 'bg-blue-100 text-blue-800';
      case 'low': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'warning': return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'info': return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
      case 'alert': return <BellIcon className="h-5 w-5 text-red-500" />;
      default: return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <BellIcon className="h-8 w-8 text-blue-600 mr-3" />
            نظام الإشعارات والرسائل
          </h1>
          <p className="text-gray-600 mt-2">إرسال إشعارات وتنبيهات للموظفين</p>
        </div>
        <button
          onClick={() => setShowSendModal(true)}
          className="bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center"
        >
          <PaperAirplaneIcon className="h-5 w-5 mr-2" />
          إرسال إشعار جديد
        </button>
      </div>

      {/* Notifications List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            الإشعارات المُرسلة ({notifications.length})
          </h2>
        </div>

        {notifications.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {notifications.map((notification) => (
              <div key={notification.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="mt-1">
                      {getTypeIcon(notification.type)}
                    </div>
                    <div className="flex-1 mr-3">
                      <div className="flex items-center mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 mr-3">
                          {notification.subject}
                        </h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(notification.priority)}`}>
                          {notification.priority === 'urgent' && 'عاجل'}
                          {notification.priority === 'high' && 'مهم'}
                          {notification.priority === 'normal' && 'عادي'}
                          {notification.priority === 'low' && 'منخفض'}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-3">{notification.message}</p>
                      <div className="flex items-center text-sm text-gray-500 space-x-4">
                        <span>إلى: {notification.recipient_name}</span>
                        <span>•</span>
                        <span>{new Date(notification.sent_at).toLocaleString('ar-SA')}</span>
                        <span>•</span>
                        <span className={notification.is_read ? 'text-green-600' : 'text-orange-600'}>
                          {notification.is_read ? 'تم القراءة' : 'غير مقروء'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <BellIcon className="mx-auto h-16 w-16 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">لا توجد إشعارات</h3>
            <p className="mt-2 text-gray-500">ابدأ بإرسال إشعار للموظفين</p>
          </div>
        )}
      </div>

      {/* Send Notification Modal */}
      {showSendModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-2/3 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900">إرسال إشعار جديد</h3>
              <button
                onClick={() => setShowSendModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <form onSubmit={handleSendNotification} className="space-y-6">
              {/* Recipient */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  المُستقبِل *
                </label>
                <select
                  required
                  value={newNotification.recipient_id}
                  onChange={(e) => setNewNotification({...newNotification, recipient_id: e.target.value})}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">اختر موظف</option>
                  {allUsers.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.name} - {user.email} ({user.position})
                    </option>
                  ))}
                </select>
              </div>

              {/* Type and Priority */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    نوع الإشعار
                  </label>
                  <select
                    value={newNotification.type}
                    onChange={(e) => setNewNotification({...newNotification, type: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="info">معلومات</option>
                    <option value="warning">تحذير</option>
                    <option value="alert">تنبيه</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    الأولوية
                  </label>
                  <select
                    value={newNotification.priority}
                    onChange={(e) => setNewNotification({...newNotification, priority: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">منخفض</option>
                    <option value="normal">عادي</option>
                    <option value="high">مهم</option>
                    <option value="urgent">عاجل</option>
                  </select>
                </div>
              </div>

              {/* Subject */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  الموضوع *
                </label>
                <input
                  type="text"
                  required
                  value={newNotification.subject}
                  onChange={(e) => setNewNotification({...newNotification, subject: e.target.value})}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="اكتب موضوع الإشعار..."
                />
              </div>

              {/* Message */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  الرسالة *
                </label>
                <textarea
                  required
                  rows={4}
                  value={newNotification.message}
                  onChange={(e) => setNewNotification({...newNotification, message: e.target.value})}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="اكتب نص الرسالة هنا..."
                />
              </div>

              {/* Buttons */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowSendModal(false)}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-6 rounded-md transition-colors"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-md transition-colors disabled:opacity-50"
                >
                  {loading ? 'جاري الإرسال...' : 'إرسال الإشعار'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationSystem;