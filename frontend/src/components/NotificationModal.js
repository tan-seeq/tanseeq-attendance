import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  XMarkIcon,
  ClockIcon,
  BellIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NotificationModal = ({ isOpen, onClose }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [acknowledging, setAcknowledging] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (isOpen) {
      fetchUnreadNotifications();
    }
  }, [isOpen]);

  const fetchUnreadNotifications = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/notifications/my?unread_only=true`);
      
      console.log('🔔 Fetched notifications:', response.data);
      
      // ✅ FIX: عرض جميع الإشعارات غير المقروءة (من الأدمن والنظام)
      const allUnreadNotifications = response.data.notifications || [];
      
      console.log(`📊 Total unread notifications: ${allUnreadNotifications.length}`);
      if (allUnreadNotifications.length > 0) {
        console.log('📧 First notification:', allUnreadNotifications[0]);
      }
      
      setNotifications(allUnreadNotifications);
      setCurrentIndex(0);
    } catch (error) {
      console.error('❌ Error fetching notifications:', error);
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'urgent':
        return <ExclamationCircleIcon className="h-8 w-8 text-red-600" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-8 w-8 text-yellow-600" />;
      case 'important':
        return <InformationCircleIcon className="h-8 w-8 text-blue-600" />;
      default:
        return <BellIcon className="h-8 w-8 text-gray-600" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'urgent':
        return 'bg-red-100 border-red-500 text-red-800';
      case 'warning':
        return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      case 'important':
        return 'bg-blue-100 border-blue-500 text-blue-800';
      default:
        return 'bg-gray-100 border-gray-500 text-gray-800';
    }
  };

  const getSeverityText = (severity) => {
    switch (severity) {
      case 'urgent': return 'عاجل';
      case 'warning': return 'تحذير';
      case 'important': return 'مهم';
      default: return 'إشعار';
    }
  };

  const acknowledgeNotification = async (notificationId) => {
    try {
      console.log('🔔 Attempting to acknowledge notification:', notificationId);
      setAcknowledging(true);
      
      const response = await axios.post(`${API}/notifications/${notificationId}/acknowledge`);
      console.log('✅ Acknowledge successful:', response.data);
      
      // إزالة الإشعار من القائمة
      const updatedNotifications = notifications.filter(n => n.id !== notificationId);
      setNotifications(updatedNotifications);
      
      // الانتقال للإشعار التالي أو إغلاق Modal
      if (updatedNotifications.length === 0) {
        onClose();
      } else if (currentIndex >= updatedNotifications.length) {
        setCurrentIndex(0);
      }
    } catch (error) {
      console.error('❌ Error acknowledging notification:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      alert(`حدث خطأ في تأكيد الإشعار: ${error.response?.data?.detail || error.message}`);
    } finally {
      setAcknowledging(false);
    }
  };

  const acknowledgeAll = async () => {
    try {
      setAcknowledging(true);
      
      // تأكيد جميع الإشعارات
      await Promise.all(
        notifications.map(notification => 
          axios.post(`${API}/notifications/${notification.id}/acknowledge`)
        )
      );
      
      setNotifications([]);
      onClose();
    } catch (error) {
      console.error('Error acknowledging all notifications:', error);
      alert('حدث خطأ في تأكيد الإشعارات');
    } finally {
      setAcknowledging(false);
    }
  };

  const nextNotification = () => {
    if (currentIndex < notifications.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const prevNotification = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  if (!isOpen || notifications.length === 0) {
    return null;
  }

  const currentNotification = notifications[currentIndex];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden relative">
        {/* Close Button - Always Visible */}
        <button
          onClick={onClose}
          className="absolute top-4 left-4 z-10 bg-gray-100 hover:bg-gray-200 rounded-full p-2 transition-colors"
          title="إغلاق"
        >
          <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">جاري تحميل الإشعارات...</p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className={`p-6 border-l-4 ${getSeverityColor(currentNotification.severity)}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getSeverityIcon(currentNotification.severity)}
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">
                      {getSeverityText(currentNotification.severity)}
                    </h3>
                    <p className="text-sm text-gray-600">
                      إشعار {currentIndex + 1} من {notifications.length}
                    </p>
                  </div>
                </div>
                
                {/* Counter Badge */}
                <div className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                  {notifications.length}
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              <div className="mb-4">
                <h4 className="text-lg font-semibold text-gray-800 mb-2">
                  {currentNotification.title}
                </h4>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-700 leading-relaxed">
                    {currentNotification.message}
                  </p>
                </div>
              </div>

              {/* Metadata */}
              <div className="bg-blue-50 p-3 rounded-lg mb-6">
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 ml-1" />
                    <span>
                      {new Date(currentNotification.sent_at || currentNotification.created_at).toLocaleString('ar-SA', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                  
                  {currentNotification.category && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                      {currentNotification.category}
                    </span>
                  )}
                </div>
              </div>

              {/* Action URL if available */}
              {currentNotification.action_url && (
                <div className="mb-6">
                  <a
                    href={currentNotification.action_url}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <InformationCircleIcon className="h-4 w-4 ml-2" />
                    عرض التفاصيل
                  </a>
                </div>
              )}
            </div>

            {/* Navigation & Actions */}
            <div className="bg-gray-50 px-6 py-4">
              <div className="flex items-center justify-between">
                {/* Navigation */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={prevNotification}
                    disabled={currentIndex === 0}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      currentIndex === 0
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                    }`}
                  >
                    ← السابق
                  </button>
                  
                  <span className="text-sm text-gray-600 px-3">
                    {currentIndex + 1} / {notifications.length}
                  </span>
                  
                  <button
                    onClick={nextNotification}
                    disabled={currentIndex === notifications.length - 1}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      currentIndex === notifications.length - 1
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                    }`}
                  >
                    التالي →
                  </button>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-3 space-x-reverse">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 text-sm font-medium"
                  >
                    تخطي الآن
                  </button>
                  
                  {notifications.length > 1 && (
                    <button
                      onClick={acknowledgeAll}
                      disabled={acknowledging}
                      className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 text-sm font-medium flex items-center"
                    >
                      {acknowledging ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-2"></div>
                      ) : (
                        <CheckCircleIcon className="h-4 w-4 ml-2" />
                      )}
                      تأكيد الكل ({notifications.length})
                    </button>
                  )}
                  
                  <button
                    onClick={() => acknowledgeNotification(currentNotification.id)}
                    disabled={acknowledging}
                    className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 font-medium flex items-center"
                  >
                    {acknowledging ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-2"></div>
                    ) : (
                      <CheckCircleIcon className="h-4 w-4 ml-2" />
                    )}
                    تم الاطلاع
                  </button>
                </div>
              </div>
            </div>

            {/* Urgent Notice */}
            {currentNotification.severity === 'urgent' && (
              <div className="bg-red-600 text-white p-3 text-center font-medium">
                <ExclamationCircleIcon className="h-5 w-5 inline ml-2" />
                هذا إشعار عاجل يتطلب اطلاعك الفوري
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default NotificationModal;