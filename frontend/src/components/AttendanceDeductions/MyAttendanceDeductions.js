import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../../App';
import {
  CalendarIcon as Calendar,
  ClockIcon as Clock,
  ExclamationTriangleIcon as AlertTriangle,
  CurrencyDollarIcon as DollarSign,
  EyeIcon as Eye,
  ArrowDownTrayIcon as Download,
  InformationCircleIcon as Info,
  CheckCircleIcon as CheckCircle,
  XCircleIcon as XCircle,
  ArrowTrendingUpIcon as TrendingUp,
  ArrowTrendingDownIcon as TrendingDown,
  MinusIcon as Minus
} from '@heroicons/react/24/outline';

const MyAttendanceDeductions = () => {
  const { user: currentUser } = useContext(AuthContext);
  const [deductions, setDeductions] = useState([]);
  const [attendanceStats, setAttendanceStats] = useState({});
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [loading, setLoading] = useState(false);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    fetchMyDeductions();
    fetchMyAttendanceStats();
    fetchMyNotifications();
  }, [selectedMonth]);

  const fetchMyDeductions = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/deductions?employee_id=${currentUser.id}&month=${selectedMonth}`);
      setDeductions(response.data || []);
    } catch (error) {
      console.error('Error fetching my deductions:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMyAttendanceStats = async () => {
    try {
      const response = await axios.get(`${API}/attendance/stats/${currentUser.id}?month=${selectedMonth}`);
      setAttendanceStats(response.data);
    } catch (error) {
      console.error('Error fetching attendance stats:', error);
    }
  };

  const fetchMyNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications?category=deduction&limit=10`);
      setNotifications(response.data || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const acknowledgeNotification = async (notificationId) => {
    try {
      await fetch(`/api/notifications/${notificationId}/acknowledge`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      fetchMyNotifications();
    } catch (error) {
      console.error('Error acknowledging notification:', error);
    }
  };

  const getDeductionTypeColor = (type) => {
    const colors = {
      lateness: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      early_leave: 'bg-orange-100 text-orange-800 border-orange-200',
      missing_checkout: 'bg-red-100 text-red-800 border-red-200',
      manual: 'bg-blue-100 text-blue-800 border-blue-200',
      absence: 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[type] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getCategoryIcon = (category) => {
    const icons = {
      minutes: Clock,
      half_day: TrendingDown,
      full_day: Minus,
      custom: Info
    };
    return icons[category] || Info;
  };

  const totalDeductions = deductions.reduce((sum, d) => sum + (d.is_voided ? 0 : d.amount), 0);
  const totalMinutes = deductions.reduce((sum, d) => sum + (d.is_voided ? 0 : d.minutes), 0);
  const activeDeductions = deductions.filter(d => !d.is_voided);

  // Calculate trends (compare with previous month)
  const currentMonthDeductions = totalDeductions;
  const previousMonth = new Date(selectedMonth + '-01');
  previousMonth.setMonth(previousMonth.getMonth() - 1);
  const previousMonthStr = previousMonth.toISOString().slice(0, 7);

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Clock className="w-8 h-8 text-blue-600" />
                سجل الحضور والخصومات الخاص بي
              </h1>
              <p className="text-gray-600 mt-1">عرض تفصيلي لحضورك وخصوماتك الشهرية</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">الموظف</p>
              <p className="text-lg font-semibold text-gray-900">{currentUser.name}</p>
            </div>
          </div>
        </div>

        {/* Month Selector */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700">اختر الشهر:</label>
            <input
              type="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-sm p-6 border-r-4 border-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">إجمالي الخصومات</p>
                <p className="text-2xl font-bold text-red-600">{totalDeductions.toFixed(2)} درهم</p>
                <p className="text-xs text-gray-500 mt-1">{activeDeductions.length} خصم فعال</p>
              </div>
              <DollarSign className="w-8 h-8 text-red-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border-r-4 border-orange-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">إجمالي الدقائق</p>
                <p className="text-2xl font-bold text-orange-600">{totalMinutes} دقيقة</p>
                <p className="text-xs text-gray-500 mt-1">{Math.round(totalMinutes / 60 * 10) / 10} ساعة</p>
              </div>
              <Clock className="w-8 h-8 text-orange-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border-r-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">أيام الحضور</p>
                <p className="text-2xl font-bold text-green-600">{attendanceStats.present_days || 0}</p>
                <p className="text-xs text-gray-500 mt-1">من {attendanceStats.total_days || 0} يوم</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border-r-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">المرات المجانية المتبقية</p>
                <p className="text-2xl font-bold text-blue-600">{attendanceStats.free_occurrences_remaining || 0}</p>
                <p className="text-xs text-gray-500 mt-1">من 4 مرات شهرياً</p>
              </div>
              <Info className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>

        {/* Attendance Summary */}
        {attendanceStats.employee_id && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">ملخص الحضور الشهري</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">{attendanceStats.present_days}</p>
                <p className="text-sm text-gray-600">أيام الحضور</p>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <p className="text-2xl font-bold text-yellow-600">{attendanceStats.late_days}</p>
                <p className="text-sm text-gray-600">أيام التأخير</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-2xl font-bold text-red-600">{attendanceStats.absent_days}</p>
                <p className="text-sm text-gray-600">أيام الغياب</p>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-2xl font-bold text-blue-600">{attendanceStats.total_late_minutes}</p>
                <p className="text-sm text-gray-600">دقائق التأخير الإجمالية</p>
              </div>
            </div>
          </div>
        )}

        {/* Recent Notifications */}
        {notifications.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">الإشعارات الأخيرة</h3>
            <div className="space-y-3">
              {notifications.slice(0, 3).map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 rounded-lg border-r-4 ${
                    notification.severity === 'warning' ? 'bg-yellow-50 border-yellow-400' :
                    notification.severity === 'important' ? 'bg-red-50 border-red-400' :
                    'bg-blue-50 border-blue-400'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{notification.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        {new Date(notification.created_at).toLocaleString('ar-AE')}
                      </p>
                    </div>
                    {notification.must_acknowledge && !notification.acknowledged_at && (
                      <button
                        onClick={() => acknowledgeNotification(notification.id)}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        إقرار
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Deductions List */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">تفاصيل الخصومات</h3>
          </div>
          
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">جاري التحميل...</p>
            </div>
          ) : deductions.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-400" />
              <p className="text-lg font-medium text-gray-900">ممتاز! لا توجد خصومات</p>
              <p className="text-sm text-gray-600 mt-1">لم يتم تسجيل أي خصومات لهذا الشهر</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {deductions.map((deduction) => {
                const CategoryIcon = getCategoryIcon(deduction.category);
                return (
                  <div
                    key={deduction.id}
                    className={`p-6 ${deduction.is_voided ? 'bg-gray-50 opacity-60' : 'hover:bg-gray-50'}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-lg ${getDeductionTypeColor(deduction.deduction_type)}`}>
                          <CategoryIcon className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="font-medium text-gray-900">
                              {deduction.deduction_type_ar}
                            </h4>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getDeductionTypeColor(deduction.deduction_type)}`}>
                              {deduction.category_ar}
                            </span>
                            {deduction.is_voided && (
                              <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                                <XCircle className="w-3 h-3 mr-1" />
                                ملغي
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{deduction.reason}</p>
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-4 h-4" />
                              {new Date(deduction.date).toLocaleDateString('ar-AE')}
                            </span>
                            {deduction.minutes > 0 && (
                              <span className="flex items-center gap-1">
                                <Clock className="w-4 h-4" />
                                {deduction.minutes} دقيقة
                              </span>
                            )}
                            {deduction.source === 'manual' && (
                              <span className="text-blue-600">خصم يدوي</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="text-left">
                        <p className={`text-lg font-bold ${deduction.is_voided ? 'text-gray-400 line-through' : 'text-red-600'}`}>
                          {deduction.amount.toFixed(2)} درهم
                        </p>
                        {deduction.daily_rate > 0 && (
                          <p className="text-xs text-gray-500">
                            الأجر اليومي: {deduction.daily_rate.toFixed(2)} درهم
                          </p>
                        )}
                      </div>
                    </div>
                    
                    {/* Additional Details */}
                    {(deduction.created_by_name || deduction.voided_by_name) && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          {deduction.created_by_name && (
                            <span>أنشأ بواسطة: {deduction.created_by_name}</span>
                          )}
                          {deduction.voided_by_name && (
                            <span>ألغي بواسطة: {deduction.voided_by_name}</span>
                          )}
                          <span>
                            {new Date(deduction.created_at).toLocaleString('ar-AE')}
                          </span>
                        </div>
                        {deduction.void_reason && (
                          <p className="text-xs text-red-600 mt-1">
                            سبب الإلغاء: {deduction.void_reason}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Rules Information */}
        <div className="bg-blue-50 rounded-lg p-6 mt-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4 flex items-center gap-2">
            <Info className="w-5 h-5" />
            قواعد نظام الخصومات - أكتوبر 2025
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <h4 className="font-medium mb-2">المرات المجانية:</h4>
              <ul className="space-y-1 text-blue-700">
                <li>• أول 15 دقيقة تأخير × 4 مرات = مجاناً شهرياً</li>
                <li>• بعد استنزاف المرات المجانية: خصم بالدقائق الفعلية</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">فئات الخصومات:</h4>
              <ul className="space-y-1 text-blue-700">
                <li>• أكثر من 20 دقيقة: خصم مباشر</li>
                <li>• 60-120 دقيقة: خصم نصف يوم</li>
                <li>• أكثر من 120 دقيقة: خصم يوم كامل</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MyAttendanceDeductions;