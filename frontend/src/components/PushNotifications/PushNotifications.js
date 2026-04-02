import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../../config';
import { useAuth } from '../../contexts/AuthContext';
import {
  BellIcon,
  BellSlashIcon,
  DevicePhoneMobileIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

const PushNotifications = () => {
  const { user } = useAuth();
  const [permission, setPermission] = useState('default');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState({
    late_notifications: true,
    absence_notifications: true,
    notify_employee: true,
    notify_admin: true,
  });
  const [testSending, setTestSending] = useState(false);
  const [stats, setStats] = useState({ total_subscriptions: 0, active_users: 0 });
  const isAdmin = user?.role === 'super_admin' || user?.role === 'admin';

  const checkSubscription = useCallback(async () => {
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        setLoading(false);
        return;
      }
      setPermission(Notification.permission);

      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      setIsSubscribed(!!sub);

      if (isAdmin) {
        const [settingsRes, statsRes] = await Promise.all([
          axios.get(`${API}/push/settings`).catch(() => ({ data: {} })),
          axios.get(`${API}/push/stats`).catch(() => ({ data: { total_subscriptions: 0, active_users: 0 } })),
        ]);
        if (settingsRes.data) setSettings(s => ({ ...s, ...settingsRes.data }));
        if (statsRes.data) setStats(statsRes.data);
      }
    } catch (e) {
      console.error('Check subscription error:', e);
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => { checkSubscription(); }, [checkSubscription]);

  const subscribe = async () => {
    try {
      const perm = await Notification.requestPermission();
      setPermission(perm);
      if (perm !== 'granted') return;

      const vapidRes = await axios.get(`${API}/push/vapid-key`);
      const vapidKey = vapidRes.data.public_key;

      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey),
      });

      await axios.post(`${API}/push/subscribe`, {
        subscription: sub.toJSON(),
      });

      setIsSubscribed(true);
    } catch (e) {
      console.error('Subscribe error:', e);
      alert('فشل تفعيل الإشعارات. تأكد من السماح بالإشعارات في المتصفح.');
    }
  };

  const unsubscribe = async () => {
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await sub.unsubscribe();
        await axios.post(`${API}/push/unsubscribe`, {
          endpoint: sub.endpoint,
        });
      }
      setIsSubscribed(false);
    } catch (e) {
      console.error('Unsubscribe error:', e);
    }
  };

  const saveSettings = async () => {
    try {
      await axios.post(`${API}/push/settings`, settings);
      alert('تم حفظ الإعدادات بنجاح');
    } catch (e) {
      console.error('Save settings error:', e);
    }
  };

  const sendTestNotification = async () => {
    setTestSending(true);
    try {
      const res = await axios.post(`${API}/push/test`);
      alert(res.data.message || 'تم إرسال إشعار تجريبي');
    } catch (e) {
      alert('فشل إرسال الإشعار التجريبي');
    } finally {
      setTestSending(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const isSupported = 'serviceWorker' in navigator && 'PushManager' in window;

  return (
    <div className="max-w-4xl mx-auto space-y-6" data-testid="push-notifications-page">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-blue-100 rounded-lg">
            <BellIcon className="h-6 w-6 text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">إشعارات الهاتف</h1>
        </div>
        <p className="text-gray-500 text-sm mr-11">
          تفعيل إشعارات فورية على هاتفك عند تسجيل تأخير أو غياب
        </p>
      </div>

      {/* Browser Support Check */}
      {!isSupported && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-5">
          <div className="flex items-center gap-3">
            <XCircleIcon className="h-6 w-6 text-red-500 flex-shrink-0" />
            <div>
              <p className="font-semibold text-red-900">المتصفح لا يدعم الإشعارات</p>
              <p className="text-sm text-red-700 mt-1">
                استخدم Chrome أو Edge أو Firefox. على iPhone، ثبّت التطبيق من Safari أولاً.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Subscription Status Card */}
      {isSupported && (
        <div className={`rounded-xl border-2 p-6 transition-all ${
          isSubscribed ? 'bg-green-50 border-green-300' : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-full ${isSubscribed ? 'bg-green-200' : 'bg-gray-200'}`}>
                <DevicePhoneMobileIcon className={`h-8 w-8 ${isSubscribed ? 'text-green-700' : 'text-gray-500'}`} />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {isSubscribed ? 'الإشعارات مفعّلة' : 'الإشعارات غير مفعّلة'}
                </h3>
                <p className="text-sm text-gray-600">
                  {isSubscribed
                    ? 'ستصلك إشعارات فورية عند تسجيل تأخير أو غياب'
                    : 'فعّل الإشعارات لتصلك تنبيهات على هاتفك'}
                </p>
              </div>
            </div>
            <button
              onClick={isSubscribed ? unsubscribe : subscribe}
              data-testid={isSubscribed ? 'unsubscribe-btn' : 'subscribe-btn'}
              className={`px-6 py-3 rounded-lg font-medium text-white transition-all ${
                isSubscribed
                  ? 'bg-red-500 hover:bg-red-600'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isSubscribed ? (
                <span className="flex items-center gap-2">
                  <BellSlashIcon className="h-5 w-5" />
                  إيقاف
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <BellIcon className="h-5 w-5" />
                  تفعيل الإشعارات
                </span>
              )}
            </button>
          </div>

          {/* Test Notification */}
          {isSubscribed && (
            <div className="mt-4 pt-4 border-t border-green-200">
              <button
                onClick={sendTestNotification}
                disabled={testSending}
                data-testid="test-notification-btn"
                className="px-4 py-2 bg-white border border-green-400 rounded-lg text-green-800 hover:bg-green-100 text-sm font-medium disabled:opacity-50"
              >
                {testSending ? 'جاري الإرسال...' : 'إرسال إشعار تجريبي'}
              </button>
            </div>
          )}

          {/* Permission denied warning */}
          {permission === 'denied' && (
            <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <ExclamationTriangleIcon className="h-5 w-5 text-amber-600" />
                <p className="text-sm text-amber-800">
                  تم حظر الإشعارات في المتصفح. افتح إعدادات الموقع وفعّل الإشعارات.
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* How It Works */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">كيف تعمل الإشعارات؟</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <ClockIcon className="h-8 w-8 text-blue-600 mx-auto mb-2" />
            <p className="font-medium text-gray-900">تسجيل التأخير</p>
            <p className="text-sm text-gray-600 mt-1">إشعار فوري عند تسجيل حضور متأخر</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <XCircleIcon className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="font-medium text-gray-900">تسجيل الغياب</p>
            <p className="text-sm text-gray-600 mt-1">إشعار عند عدم تسجيل الحضور</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <CheckCircleIcon className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p className="font-medium text-gray-900">إشعار المدير</p>
            <p className="text-sm text-gray-600 mt-1">المديرون يستلمون إشعارات أيضاً</p>
          </div>
        </div>
      </div>

      {/* Admin Settings */}
      {isAdmin && (
        <div className="bg-white rounded-xl shadow-sm border p-6" data-testid="admin-push-settings">
          <h3 className="font-semibold text-gray-900 mb-4">إعدادات الإشعارات (المدير)</h3>
          
          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-blue-700">{stats.total_subscriptions}</p>
              <p className="text-sm text-blue-600">أجهزة مسجّلة</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-green-700">{stats.active_users}</p>
              <p className="text-sm text-green-600">موظفين مفعّلين</p>
            </div>
          </div>

          {/* Toggle Settings */}
          <div className="space-y-4">
            {[
              { key: 'late_notifications', label: 'إشعارات التأخير', desc: 'إرسال إشعار عند تسجيل حضور متأخر' },
              { key: 'absence_notifications', label: 'إشعارات الغياب', desc: 'إرسال إشعار عند تسجيل غياب' },
              { key: 'notify_employee', label: 'إشعار الموظف', desc: 'الموظف يستلم إشعار على هاتفه' },
              { key: 'notify_admin', label: 'إشعار المدير', desc: 'المدير يستلم إشعار على هاتفه' },
            ].map(({ key, label, desc }) => (
              <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{label}</p>
                  <p className="text-sm text-gray-500">{desc}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings[key]}
                    onChange={(e) => setSettings({ ...settings, [key]: e.target.checked })}
                    className="sr-only peer"
                    data-testid={`toggle-${key}`}
                  />
                  <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            ))}
          </div>

          <button
            onClick={saveSettings}
            data-testid="save-push-settings-btn"
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            حفظ الإعدادات
          </button>
        </div>
      )}

      {/* iPhone Instructions */}
      <div className="bg-gray-50 border rounded-xl p-5">
        <h4 className="font-semibold text-gray-900 mb-2">ملاحظات لمستخدمي iPhone</h4>
        <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
          <li>افتح التطبيق في <strong>Safari</strong></li>
          <li>اضغط على زر المشاركة ↑ ثم <strong>"Add to Home Screen"</strong></li>
          <li>افتح التطبيق من الشاشة الرئيسية</li>
          <li>اضغط "تفعيل الإشعارات" وقبل الإذن</li>
        </ol>
      </div>
    </div>
  );
};

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export default PushNotifications;
