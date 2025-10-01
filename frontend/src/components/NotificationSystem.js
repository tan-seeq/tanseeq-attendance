import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  BellIcon, 
  PaperAirplaneIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

// API Configuration
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NotificationSystem = () => {
  const [notifications, setNotifications] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [showSendModal, setShowSendModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
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
  const [apiLoading, setApiLoading] = useState(false);

  useEffect(() => {
    fetchNotifications();
    fetchAllUsers();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');
      
      console.log('Fetching notifications from:', `${API}/notifications`);
      
      const response = await axios.get(`${API}/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('Notifications response:', response.data);
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      setError(`فشل في تحميل الإشعارات: ${error.message}`);
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      
      console.log('Fetching users from:', `${API}/users`);
      
      const response = await axios.get(`${API}/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('Users response:', response.data);
      setAllUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      if (!error) {
        setError(`فشل في تحميل قائمة الموظفين: ${error.message}`);
      }
    }
  };

  const handleSendNotification = async (e) => {
    e.preventDefault();
    setApiLoading(true);

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
      setApiLoading(false);
    }
  };

  // Handle sending warning/notice notifications
  const handleSendWarning = async (e) => {
    e.preventDefault();
    setApiLoading(true);

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/notifications/send-warning`, warningNotification, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      alert('تم إرسال الإنذار/الإشعار بنجاح');
      setShowWarningModal(false);
      setWarningNotification({
        recipient_id: '',
        title: '',
        message: '',
        notification_type: 'warning',
        required_action: '',
        additional_notes: ''
      });
      fetchNotifications();
    } catch (error) {
      console.error('Error sending warning:', error);
      alert('فشل في إرسال الإنذار');
    } finally {
      setApiLoading(false);
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

  // Debug info
  console.log('NotificationSystem rendered');
  console.log('BACKEND_URL:', BACKEND_URL);
  console.log('API:', API);

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex justify-center items-center min-h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">جاري تحميل نظام الإشعارات...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <ExclamationCircleIcon className="h-6 w-6 text-red-400 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-red-800">خطأ في تحميل النظام</h3>
              <p className="text-red-600 mt-1">{error}</p>
              <button 
                onClick={() => {
                  fetchNotifications();
                  fetchAllUsers();
                }}
                className="mt-3 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                إعادة المحاولة
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
        <div className="flex space-x-3">
          <button
            onClick={() => setShowSendModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center"
          >
            <PaperAirplaneIcon className="h-5 w-5 mr-2" />
            إرسال إشعار جديد
          </button>
          <button
            onClick={() => setShowWarningModal(true)}
            className="bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center"
          >
            <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            إرسال إنذار/لفت نظر
          </button>
        </div>
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
                  disabled={apiLoading}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-md transition-colors disabled:opacity-50"
                >
                  {apiLoading ? 'جاري الإرسال...' : 'إرسال الإشعار'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Warning/Notice Modal */}
      {showWarningModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-6 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl leading-6 font-medium text-gray-900 flex items-center">
                  <ExclamationTriangleIcon className="h-6 w-6 text-red-500 mr-2" />
                  إرسال إنذار أو لفت نظر للموظف
                </h3>
                <button
                  onClick={() => setShowWarningModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <form onSubmit={handleSendWarning} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      اختر الموظف *
                    </label>
                    <select
                      value={warningNotification.recipient_id}
                      onChange={(e) => setWarningNotification({...warningNotification, recipient_id: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                      required
                    >
                      <option value="">-- اختر الموظف --</option>
                      {allUsers.filter(user => user.role === 'user').map(user => (
                        <option key={user.id} value={user.id}>
                          {user.name} - {user.position}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      نوع الإشعار *
                    </label>
                    <select
                      value={warningNotification.notification_type}
                      onChange={(e) => setWarningNotification({...warningNotification, notification_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                      required
                    >
                      <option value="warning">⚠️ إنذار رسمي</option>
                      <option value="notice">📋 لفت نظر</option>
                      <option value="reminder">🔔 تذكير</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    عنوان الإشعار *
                  </label>
                  <input
                    type="text"
                    value={warningNotification.title}
                    onChange={(e) => setWarningNotification({...warningNotification, title: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    placeholder="مثال: إنذار بخصوص التأخير المتكرر"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    محتوى الإشعار *
                  </label>
                  <textarea
                    value={warningNotification.message}
                    onChange={(e) => setWarningNotification({...warningNotification, message: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    rows="4"
                    placeholder="اكتب محتوى الإشعار بالتفصيل..."
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    الإجراء المطلوب (اختياري)
                  </label>
                  <input
                    type="text"
                    value={warningNotification.required_action}
                    onChange={(e) => setWarningNotification({...warningNotification, required_action: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    placeholder="مثال: الالتزام بمواعيد العمل الرسمية"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ملاحظات إضافية (اختياري)
                  </label>
                  <textarea
                    value={warningNotification.additional_notes}
                    onChange={(e) => setWarningNotification({...warningNotification, additional_notes: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    rows="2"
                    placeholder="ملاحظات إضافية أو توجيهات..."
                  />
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowWarningModal(false)}
                    className="px-6 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    إلغاء
                  </button>
                  <button
                    type="submit"
                    disabled={apiLoading}
                    className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:bg-gray-300"
                  >
                    {loading ? 'جاري الإرسال...' : 'إرسال الإنذار'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationSystem;