import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  UserIcon, ClockIcon, CalendarDaysIcon as CalendarIcon, DocumentTextIcon,
  CheckCircleIcon, XMarkIcon, BellIcon, ChevronDownIcon,
  ServerIcon, ShieldCheckIcon, FolderIcon, ExclamationTriangleIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API } from '../../config';

const Dashboard = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalEmployees: 0,
    presentToday: 0,
    pendingLeaves: 0,
    pendingFieldExits: 0,
    todayAttendance: []
  });
  const [loading, setLoading] = useState(true);
  
  // Messages state
  const [messages, setMessages] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showMessages, setShowMessages] = useState(false);
  const [showMessageModal, setShowMessageModal] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(null);

  // Custom message state (Admin & Super Admin)
  const [showCustomMessageModal, setShowCustomMessageModal] = useState(false);
  const [customMessage, setCustomMessage] = useState({
    title: '',
    content: '',
    priority: 'normal'
  });
  const [sendingMessage, setSendingMessage] = useState(false);

  // Backup state (Super Admin only)
  const [backupStats, setBackupStats] = useState(null);
  const [showBackupSection, setShowBackupSection] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);

  // Penalty system state (Super Admin only)
  const [penalties, setPenalties] = useState([]);
  const [showPenaltySection, setShowPenaltySection] = useState(false);
  const [penaltyLoading, setPenaltyLoading] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [expandedPenalties, setExpandedPenalties] = useState({});

  useEffect(() => {
    fetchDashboardStats();
    fetchMessages();
    fetchUnreadCount();
    
    // Refresh messages every 30 seconds
    const interval = setInterval(() => {
      fetchMessages();
      fetchUnreadCount();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Helper function to calculate time ago
  const calculateTimeAgo = (date) => {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'منذ لحظات';
    if (diffInSeconds < 3600) return `منذ ${Math.floor(diffInSeconds / 60)} دقيقة`;
    if (diffInSeconds < 86400) return `منذ ${Math.floor(diffInSeconds / 3600)} ساعة`;
    return `منذ ${Math.floor(diffInSeconds / 86400)} يوم`;
  };

  const fetchMessages = async () => {
    try {
      // Fetch both messages and notifications
      const [messagesRes, notificationsRes] = await Promise.all([
        axios.get(`${API}/messages`),
        axios.get(`${API}/notifications/my`).catch(() => ({ data: [] })) // Handle error if endpoint doesn't exist
      ]);
      
      // Convert notifications to message format for unified display
      const notifArray = Array.isArray(notificationsRes.data) ? notificationsRes.data : (notificationsRes.data.notifications || []);
      const notifications = notifArray.map(notification => ({
        id: `notification_${notification.id}`,
        title: notification.subject,
        content: notification.message,
        message_type: 'notification',
        priority: notification.priority || 'normal',
        created_at: notification.sent_at,
        is_read: notification.is_read || false,
        time_ago: calculateTimeAgo(new Date(notification.sent_at)),
        sender: notification.sender_name || 'الإدارة'
      }));
      
      // Combine and sort by creation date
      const allMessages = [...messagesRes.data, ...notifications]
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      
      setMessages(allMessages);
    } catch (error) {
      console.error('Error fetching messages:', error);
      // Fallback to messages only if notifications fail
      try {
        const response = await axios.get(`${API}/messages`);
        setMessages(response.data);
      } catch (fallbackError) {
        console.error('Error fetching messages (fallback):', fallbackError);
      }
    }
  };

  const fetchUnreadCount = async () => {
    try {
      // Get unread count from both messages and notifications
      const [messagesRes, notificationsRes] = await Promise.all([
        axios.get(`${API}/messages/unread-count`),
        axios.get(`${API}/notifications/my`).catch(() => ({ data: [] }))
      ]);
      
      const notifData = Array.isArray(notificationsRes.data) ? notificationsRes.data : (notificationsRes.data.notifications || []);
      const unreadNotifications = notifData.filter(n => !n.is_read).length;
      const totalUnread = messagesRes.data.unread_count + unreadNotifications;
      
      setUnreadCount(totalUnread);
    } catch (error) {
      console.error('Error fetching unread count:', error);
      // Fallback to messages only
      try {
        const response = await axios.get(`${API}/messages/unread-count`);
        setUnreadCount(response.data.unread_count);
      } catch (fallbackError) {
        console.error('Error fetching unread count (fallback):', fallbackError);
      }
    }
  };

  const markAsRead = async (messageId) => {
    try {
      // Check if it's a notification or message
      if (messageId.startsWith('notification_')) {
        const notificationId = messageId.replace('notification_', '');
        await axios.post(`${API}/notifications/${notificationId}/read`);
      } else {
        await axios.post(`${API}/messages/${messageId}/read`);
      }
      fetchMessages();
      fetchUnreadCount();
    } catch (error) {
      console.error('Error marking message as read:', error);
    }
  };

  const handleMessageClick = (message) => {
    setSelectedMessage(message);
    setShowMessageModal(true);
    if (!message.is_read) {
      markAsRead(message.id);
    }
  };

  const sendFridayWorkMessage = async () => {
    try {
      const response = await axios.post(`${API}/messages/friday-work`);
      alert(`تم إرسال إعلان دوام الجمعة بنجاح!\nالتاريخ: ${response.data.friday_date}\nتم الإرسال لجميع الموظفين`);
      fetchMessages();
      fetchUnreadCount();
    } catch (error) {
      console.error('Error sending Friday work message:', error);
      alert('حدث خطأ في إرسال الإعلان');
    }
  };

  // Custom message functions
  const sendCustomMessage = async () => {
    if (!customMessage.title.trim() || !customMessage.content.trim()) {
      alert('يرجى إدخال عنوان ونص الرسالة');
      return;
    }

    setSendingMessage(true);
    try {
      const response = await axios.post(`${API}/messages/custom`, {
        title: customMessage.title,
        content: customMessage.content,
        priority: customMessage.priority,
        to_user_ids: [] // Send to all employees
      });
      
      alert(`تم إرسال الرسالة بنجاح!\nالعنوان: ${response.data.title}\nتم الإرسال لعدد: ${response.data.recipients_count} موظف`);
      
      // Reset form
      setCustomMessage({
        title: '',
        content: '',
        priority: 'normal'
      });
      setShowCustomMessageModal(false);
      
      // Refresh messages
      fetchMessages();
      fetchUnreadCount();
      
    } catch (error) {
      console.error('Error sending custom message:', error);
      alert('حدث خطأ في إرسال الرسالة');
    } finally {
      setSendingMessage(false);
    }
  };

  // Automatic notification functions
  const sendLateWarnings = async () => {
    try {
      const response = await axios.post(`${API}/notifications/late-warning`);
      alert(`تم إرسال تنبيهات التأخير!\nعدد الموظفين المتأخرين: ${response.data.notifications_sent}\nالتاريخ: ${response.data.date}`);
      fetchMessages();
      fetchUnreadCount();
    } catch (error) {
      console.error('Error sending late warnings:', error);
      alert('حدث خطأ في إرسال تنبيهات التأخير');
    }
  };

  const sendAbsenceWarnings = async () => {
    try {
      const response = await axios.post(`${API}/notifications/absence-warning`);
      alert(`تم إرسال تنبيهات الغياب!\nعدد الموظفين الغائبين بدون إذن: ${response.data.notifications_sent}\nالتاريخ: ${response.data.date}`);
      fetchMessages();
      fetchUnreadCount();
    } catch (error) {
      console.error('Error sending absence warnings:', error);
      alert('حدث خطأ في إرسال تنبيهات الغياب');
    }
  };

  // Backup functions (Super Admin only)
  const fetchBackupStats = async () => {
    if (user?.name !== "Hatem Mohamed Ahmed") return;
    
    try {
      const response = await axios.get(`${API}/backup/stats`);
      setBackupStats(response.data);
    } catch (error) {
      console.error('Error fetching backup stats:', error);
    }
  };

  const createManualBackup = async () => {
    if (user?.name !== "Hatem Mohamed Ahmed") return;
    
    setBackupLoading(true);
    try {
      const response = await axios.post(`${API}/backup/manual`);
      alert(`تم إنشاء النسخة الاحتياطية بنجاح!\nالحجم: ${response.data.file_size_mb} MB\nالوقت: ${response.data.created_at}`);
      fetchBackupStats(); // Refresh stats
    } catch (error) {
      console.error('Error creating manual backup:', error);
      alert('حدث خطأ في إنشاء النسخة الاحتياطية');
    } finally {
      setBackupLoading(false);
    }
  };

  // Fetch backup stats if super admin
  useEffect(() => {
    if (user?.name === "Hatem Mohamed Ahmed") {
      fetchBackupStats();
    }
  }, [user]);


  // Export functions for home page penalties
  const exportEmployeeToExcel = (employee, month) => {
    let csvContent = `تقرير خصومات الموظف\nالموظف: ${employee.employee_name}\nالفترة: ${month}\n\n`;
    csvContent += 'الملخص\n';
    csvContent += 'المقياس,القيمة\n';
    csvContent += `أيام التأخير,${employee.late_count || 0}\n`;
    csvContent += `أيام الغياب,${employee.absence_count || 0}\n`;
    csvContent += `إجمالي الدقائق,${employee.total_late_minutes || 0}\n`;
    csvContent += `خصم التأخير,${(employee.late_deduction || 0).toFixed(2)} درهم\n`;
    csvContent += `خصم الغياب,${(employee.absence_deduction || 0).toFixed(2)} درهم\n`;
    csvContent += `إجمالي الخصم,${(employee.penalty_amount || 0).toFixed(2)} درهم\n\n`;
    
    // Daily breakdown
    if (employee.daily_records && employee.daily_records.length > 0) {
      csvContent += 'التفاصيل اليومية\n';
      csvContent += 'التاريخ,الحضور,الانصراف,التأخير (د),الخروج المبكر (د),النقص (د),الخصم (درهم),الحالة\n';
      employee.daily_records.forEach(record => {
        csvContent += `${record.date},${record.check_in || '-'},${record.check_out || '-'},${record.late_minutes || 0},${record.early_leave_minutes || 0},${record.deficit_minutes || 0},${(record.deduction_amount || 0).toFixed(2)},${record.is_absent ? 'غياب' : record.deficit_minutes > 0 ? 'خصم' : 'مكتمل'}\n`;
      });
    }

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${employee.employee_name}_deductions.csv`;
    link.click();
  };

  const exportEmployeeToPDF = (employee, month) => {
    // Simple PDF export using window.print
    const printWindow = window.open('', '', 'height=600,width=800');
    
    let dailyTable = '';
    if (employee.daily_records && employee.daily_records.length > 0) {
      dailyTable = `
        <h3>التفاصيل اليومية</h3>
        <table border="1" cellpadding="5" cellspacing="0" style="width:100%; border-collapse: collapse;">
          <thead style="background-color: #f0f0f0;">
            <tr>
              <th>التاريخ</th>
              <th>الحضور</th>
              <th>الانصراف</th>
              <th>التأخير (د)</th>
              <th>خروج مبكر (د)</th>
              <th>النقص (د)</th>
              <th>الخصم (درهم)</th>
              <th>الحالة</th>
            </tr>
          </thead>
          <tbody>
            ${employee.daily_records.map(record => `
              <tr style="${record.is_absent ? 'background-color: #fee' : ''}">
                <td>${record.date}</td>
                <td>${record.check_in || '-'}</td>
                <td>${record.check_out || '-'}</td>
                <td>${record.late_minutes || 0}</td>
                <td>${record.early_leave_minutes || 0}</td>
                <td>${record.deficit_minutes || 0}</td>
                <td>${(record.deduction_amount || 0).toFixed(2)}</td>
                <td>${record.is_absent ? 'غياب' : record.deficit_minutes > 0 ? 'خصم' : 'مكتمل'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }
    
    printWindow.document.write(`
      <html dir="rtl">
        <head>
          <title>تقرير الخصومات - ${employee.employee_name}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h2 { color: #333; }
            table { margin-top: 10px; }
            th { background-color: #4CAF50; color: white; }
          </style>
        </head>
        <body>
          <h2>تقرير الخصومات: ${employee.employee_name}</h2>
          <p><strong>الفترة:</strong> ${month}</p>
          <hr>
          <h3>الملخص</h3>
          <p>أيام التأخير: ${employee.late_count || 0}</p>
          <p>أيام الغياب: ${employee.absence_count || 0}</p>
          <p>إجمالي الدقائق: ${employee.total_late_minutes || 0}</p>
          <p>خصم التأخير: ${(employee.late_deduction || 0).toFixed(2)} درهم</p>
          <p>خصم الغياب: ${(employee.absence_deduction || 0).toFixed(2)} درهم</p>
          <p><strong>إجمالي الخصم: ${(employee.penalty_amount || 0).toFixed(2)} درهم</strong></p>
          ${dailyTable}
          <script>window.print(); window.close();</script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  // Penalty functions (Super Admin only)
  const calculateLatePenalties = async () => {
    if (user?.name !== "Hatem Mohamed Ahmed") return;
    
    setPenaltyLoading(true);
    try {
      // ✅ FIXED: Send month in YYYY-MM format as backend expects
      const response = await axios.post(`${API}/deductions/calculate-monthly?month=${selectedMonth}`);
      
      if (response.data.success && response.data.employees) {
        // Transform to old penalty format for display with daily records
        const transformedPenalties = response.data.employees.map(emp => ({
          employee_id: emp.employee_id,
          employee_name: emp.employee_name,
          late_count: emp.late_count || 0,
          absence_count: emp.absence_count || 0,
          total_late_minutes: emp.total_late_minutes || 0,
          penalty_amount: emp.total_deduction || 0,
          late_deduction: emp.late_deduction || 0,
          absence_deduction: emp.absence_deduction || 0,
          advance_deduction: emp.advance_deduction || 0,
          details: emp.deduction_details || emp.details || [],
          daily_records: emp.daily_records || []  // Add daily records
        }));
        
        setPenalties(transformedPenalties);
        setShowPenaltySection(true);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('Error calculating penalties:', error);
      const rawDetail = error.response?.data?.detail;
      const errorMsg = typeof rawDetail === 'string' ? rawDetail : (Array.isArray(rawDetail) ? rawDetail.map(e => e?.msg || '').join(', ') : error.message || 'حدث خطأ في حساب الخصومات');
      alert('حدث خطأ في حساب الخصومات: ' + errorMsg);
    } finally {
      setPenaltyLoading(false);
    }
  };

  const applyLatePenalties = async () => {
    if (user?.name !== "Hatem Mohamed Ahmed") return;
    
    const confirm = window.confirm(
      `هل أنت متأكد من تطبيق خصومات التأخير لشهر ${selectedMonth}؟\nسيتم خصم المبالغ من الرواتب تلقائياً.`
    );
    
    if (!confirm) return;
    
    try {
      // ✅ FIXED: Send request body with month and employees data
      const requestBody = {
        month: selectedMonth,  // YYYY-MM format
        employees: penalties || [],  // Current calculated penalties
        notes: `Applied from Dashboard on ${new Date().toISOString()}`
      };
      
      const response = await axios.post(`${API}/deductions/apply-monthly`, requestBody);
      
      const totalEmployees = response.data.employees_affected || response.data.total_employees || 0;
      const totalAmount = response.data.total_deduction_amount || response.data.total_penalty_amount || 0;
      
      alert(
        `تم تطبيق خصومات التأخير بنجاح!\n` +
        `عدد الموظفين: ${totalEmployees}\n` +
        `إجمالي الخصم: ${totalAmount.toFixed(2)} درهم`
      );
      
      calculateLatePenalties(); // Refresh data
    } catch (error) {
      console.error('Error applying penalties:', error);
      const rawDetail = error.response?.data?.detail;
      const errorMsg = typeof rawDetail === 'string' ? rawDetail : (Array.isArray(rawDetail) ? rawDetail.map(e => e?.msg || '').join(', ') : error.message || 'حدث خطأ في تطبيق الخصومات');
      alert('حدث خطأ في تطبيق الخصومات: ' + errorMsg);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const [employeesRes, attendanceRes, leavesRes, fieldExitsRes] = await Promise.all([
        axios.get(`${API}/users`),
        axios.get(`${API}/attendance`),
        axios.get(`${API}/leaves`),
        axios.get(`${API}/field-exits`)
      ]);

      const todayDate = new Date().toISOString().slice(0, 10);
      const todayAttendance = attendanceRes.data.filter(record => record.date === todayDate);
      
      setStats({
        totalEmployees: employeesRes.data.length,
        presentToday: todayAttendance.filter(record => record.status === 'present' || record.status === 'late').length,
        pendingLeaves: leavesRes.data.filter(leave => leave.status === 'pending').length,
        pendingFieldExits: fieldExitsRes.data.filter(exit => exit.status === 'pending').length,
        todayAttendance
      });
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'صباح الخير';
    if (hour < 17) return 'مساء الخير';
    return 'مساء الخير';
  };

  const StatCard = ({ title, value, icon: Icon, color, bgColor, textColor }) => (
    <div className={`${bgColor} rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1`}>
      <div className="flex items-center justify-between">
        <div>
          <p className={`${textColor} text-sm font-medium opacity-80`}>{title}</p>
          <p className={`${textColor} text-3xl font-bold mt-2`}>{value}</p>
        </div>
        <div className={`${color} p-3 rounded-full`}>
          <Icon className="h-8 w-8 text-white" />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-8 px-6 rounded-lg mb-8 shadow-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="bg-white/20 backdrop-blur-sm rounded-full p-3">
              <UserIcon className="h-12 w-12 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold mb-1">
                {getGreeting()}، {user.name}
              </h1>
              <p className="text-blue-100 text-lg">
                {user.role === 'super_admin' ? 'المدير العام' : 
                 user.role === 'admin' ? 'المدير' : 'الموظف'}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="bg-white/20 backdrop-blur-sm rounded-lg p-4">
              <h2 className="text-2xl font-bold mb-1">TANSEEQ</h2>
              <p className="text-blue-100">Tax Consultancy</p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Section */}
      <div className="mb-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center">
              <BellIcon className="h-5 w-5 ml-2 text-blue-600" />
              الرسائل والإعلانات
              {unreadCount > 0 && (
                <span className="bg-red-500 text-white text-xs rounded-full px-2 py-1 mr-2">
                  {unreadCount}
                </span>
              )}
            </h3>
            <div className="flex space-x-2">
              {user?.name === "Hatem Mohamed Ahmed" && (
                <button
                  onClick={sendFridayWorkMessage}
                  className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm flex items-center"
                >
                  🚨 دوام الجمعة الاستثنائي
                </button>
              )}
              {(user?.role === "admin" || user?.role === "super_admin") && (
                <button
                  onClick={() => setShowCustomMessageModal(true)}
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 text-sm flex items-center"
                >
                  ✉️ رسالة مخصصة
                </button>
              )}
              <button
                onClick={() => setShowMessages(!showMessages)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm flex items-center"
              >
                {showMessages ? 'إخفاء الرسائل' : 'عرض الرسائل'}
                <ChevronDownIcon className={`h-4 w-4 mr-1 transition-transform ${showMessages ? 'rotate-180' : ''}`} />
              </button>
            </div>
          </div>

          {showMessages && (
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {messages.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <BellIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>لا توجد رسائل حالياً</p>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    onClick={() => handleMessageClick(message)}
                    className={`border rounded-lg p-4 cursor-pointer hover:shadow-md transition-all ${
                      message.is_read ? 'bg-gray-50' : 'bg-blue-50 border-blue-200'
                    } ${message.priority === 'urgent' ? 'border-l-4 border-l-red-500' : ''}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className={`font-medium ${!message.is_read ? 'font-bold text-blue-800' : 'text-gray-800'}`}>
                        {message.message_type === 'friday_work' && '🚨 '}
                        {message.priority === 'urgent' && '⚠️ '}
                        {message.title}
                      </h4>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <span>{message.time_ago}</span>
                        {!message.is_read && <span className="w-2 h-2 bg-blue-600 rounded-full"></span>}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {message.content.substring(0, 100)}...
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-500">من: {message.from_user_name}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        message.message_type === 'friday_work' ? 'bg-red-100 text-red-700' :
                        message.message_type === 'urgent' ? 'bg-orange-100 text-orange-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {message.message_type === 'friday_work' ? 'دوام جمعة' :
                         message.message_type === 'urgent' ? 'عاجل' : 'عام'}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Automatic Notifications Section (Admin & Super Admin) */}
      {(user?.role === "admin" || user?.role === "super_admin") && (
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                <BellIcon className="h-5 w-5 ml-2 text-orange-600" />
                التنبيهات التلقائية
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <ClockIcon className="h-6 w-6 text-yellow-600 ml-2" />
                  <h4 className="font-semibold text-yellow-800">تنبيهات التأخير</h4>
                </div>
                <p className="text-sm text-yellow-700 mb-3">
                  إرسال تنبيهات للموظفين المتأخرين اليوم تلقائياً
                </p>
                <button
                  onClick={sendLateWarnings}
                  className="bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 text-sm flex items-center w-full justify-center"
                >
                  ⚠️ إرسال تنبيهات التأخير
                </button>
              </div>

              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <ExclamationTriangleIcon className="h-6 w-6 text-red-600 ml-2" />
                  <h4 className="font-semibold text-red-800">تنبيهات الغياب</h4>
                </div>
                <p className="text-sm text-red-700 mb-3">
                  إرسال تنبيهات للموظفين الغائبين بدون إذن اليوم
                </p>
                <button
                  onClick={sendAbsenceWarnings}
                  className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm flex items-center w-full justify-center"
                >
                  🚨 إرسال تنبيهات الغياب
                </button>
              </div>
            </div>

            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2">📋 ملاحظات هامة:</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• يتم إرسال تنبيه واحد فقط لكل موظف في اليوم الواحد</li>
                <li>• تنبيهات الغياب تتحقق من الإجازات المعتمدة أولاً</li>
                <li>• يتم إرسال التنبيهات للموظف مباشرة في صفحة الرسائل</li>
                <li>• التنبيهات تتضمن تفاصيل الخصم المحتمل حسب سياسة الشركة</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="إجمالي الموظفين"
          value={stats.totalEmployees}
          icon={UserIcon}
          color="bg-blue-600"
          bgColor="bg-gradient-to-r from-blue-100 to-blue-200"
          textColor="text-blue-800"
        />
        <StatCard
          title="الحضور اليوم"
          value={stats.presentToday}
          icon={ClockIcon}
          color="bg-green-600"
          bgColor="bg-gradient-to-r from-green-100 to-green-200"
          textColor="text-green-800"
        />
        <StatCard
          title="طلبات الإجازات المعلقة"
          value={stats.pendingLeaves}
          icon={CalendarIcon}
          color="bg-yellow-600"
          bgColor="bg-gradient-to-r from-yellow-100 to-yellow-200"
          textColor="text-yellow-800"
        />
        <StatCard
          title="طلبات الخروج المعلقة"
          value={stats.pendingFieldExits}
          icon={DocumentTextIcon}
          color="bg-purple-600"
          bgColor="bg-gradient-to-r from-purple-100 to-purple-200"
          textColor="text-purple-800"
        />
      </div>

      {/* Today's Attendance */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
          <ClockIcon className="h-6 w-6 mr-2 text-blue-600" />
          حضور اليوم
        </h3>
        
        {stats.todayAttendance.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">الموظف</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">الحضور</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">الانصراف</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">الحالة</th>
                </tr>
              </thead>
              <tbody>
                {stats.todayAttendance.map((record, index) => (
                  <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 font-medium text-gray-800">{record.user_name}</td>
                    <td className="py-3 px-4 text-gray-600">{record.check_in || '--'}</td>
                    <td className="py-3 px-4 text-gray-600">{record.check_out || '--'}</td>
                    <td className="py-3 px-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
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
        ) : (
          <div className="text-center py-12">
            <ClockIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500">لا يوجد سجلات حضور اليوم</p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
          <Cog6ToothIcon className="h-6 w-6 mr-2 text-blue-600" />
          الإجراءات السريعة
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <button 
            onClick={() => navigate('/attendance')}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 transform hover:-translate-y-1">
            <ClockIcon className="h-8 w-8 mx-auto mb-2" />
            <p className="font-semibold">تسجيل الحضور</p>
          </button>
          
          <button 
            onClick={() => navigate('/leaves')}
            className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 transform hover:-translate-y-1">
            <CalendarIcon className="h-8 w-8 mx-auto mb-2" />
            <p className="font-semibold">طلب إجازة</p>
          </button>
          
          <button 
            onClick={() => navigate('/field-exits')}
            className="bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 transform hover:-translate-y-1">
            <DocumentTextIcon className="h-8 w-8 mx-auto mb-2" />
            <p className="font-semibold">زيارة خارجية</p>
          </button>
        </div>
      </div>

      {/* Backup Section (Super Admin Only) */}
      {user?.name === "Hatem Mohamed Ahmed" && (
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                <ShieldCheckIcon className="h-5 w-5 ml-2 text-green-600" />
                النسخ الاحتياطي التلقائي
              </h3>
              <div className="flex space-x-2">
                <button
                  onClick={createManualBackup}
                  disabled={backupLoading}
                  className={`px-4 py-2 rounded-md text-sm text-white ${
                    backupLoading 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-green-600 hover:bg-green-700'
                  } flex items-center`}
                >
                  {backupLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      جاري الإنشاء...
                    </>
                  ) : (
                    '💾 نسخة احتياطية يدوية'
                  )}
                </button>
                <button
                  onClick={() => setShowBackupSection(!showBackupSection)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm flex items-center"
                >
                  {showBackupSection ? 'إخفاء التفاصيل' : 'عرض التفاصيل'}
                  <ChevronDownIcon className={`h-4 w-4 mr-1 transition-transform ${showBackupSection ? 'rotate-180' : ''}`} />
                </button>
              </div>
            </div>

            {/* Backup Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="bg-blue-100 rounded-lg p-2">
                    <FolderIcon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="mr-3">
                    <p className="text-sm text-gray-600">إجمالي النسخ</p>
                    <p className="text-xl font-bold text-blue-600">{backupStats?.total_backups || 0}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="bg-green-100 rounded-lg p-2">
                    <ServerIcon className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="mr-3">
                    <p className="text-sm text-gray-600">الحجم الكلي</p>
                    <p className="text-xl font-bold text-green-600">{backupStats?.total_size_mb || 0} MB</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="bg-purple-100 rounded-lg p-2">
                    <ClockIcon className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="mr-3">
                    <p className="text-sm text-gray-600">آخر نسخة</p>
                    <p className="text-sm font-bold text-purple-600">
                      {backupStats?.latest_backup_date || 'لا يوجد'}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="bg-orange-100 rounded-lg p-2">
                    <Cog6ToothIcon className="h-6 w-6 text-orange-600" />
                  </div>
                  <div className="mr-3">
                    <p className="text-sm text-gray-600">التشغيل التلقائي</p>
                    <p className="text-sm font-bold text-orange-600">2:00 ص يومياً</p>
                  </div>
                </div>
              </div>
            </div>

            {showBackupSection && backupStats && (
              <div className="border-t pt-4">
                <h4 className="font-semibold text-gray-800 mb-3">سجل النسخ الاحتياطي الأخير</h4>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {backupStats.recent_logs?.length > 0 ? (
                    backupStats.recent_logs.map((log, index) => (
                      <div key={index} className={`p-3 rounded-lg ${
                        log.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                      } border`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            {log.status === 'success' ? (
                              <CheckCircleIcon className="h-4 w-4 text-green-600 ml-2" />
                            ) : (
                              <ExclamationTriangleIcon className="h-4 w-4 text-red-600 ml-2" />
                            )}
                            <span className="text-sm font-medium">
                              {log.status === 'success' ? 'نجح' : 'فشل'}
                            </span>
                          </div>
                          <div className="text-xs text-gray-500">
                            {log.time_ago}
                          </div>
                        </div>
                        <div className="mt-1 text-xs text-gray-600">
                          {log.status === 'success' ? 
                            `الحجم: ${log.file_size_mb} MB` : 
                            `خطأ: ${log.error}`
                          }
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-sm">لا يوجد سجل للنسخ الاحتياطي</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Late Penalty System (Super Admin Only) */}
      {user?.name === "Hatem Mohamed Ahmed" && (
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                <ExclamationTriangleIcon className="h-5 w-5 ml-2 text-orange-600" />
                نظام خصومات التأخير المتقدم
              </h3>
              <div className="flex items-center space-x-2">
                <div className="flex flex-col">
                  <input
                    type="month"
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    📅 Cycle: 29th prev month → 28th current month
                  </div>
                </div>
                <button
                  onClick={calculateLatePenalties}
                  disabled={penaltyLoading}
                  className={`px-4 py-2 rounded-md text-sm text-white ${
                    penaltyLoading 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-orange-600 hover:bg-orange-700'
                  } flex items-center`}
                >
                  {penaltyLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      جاري الحساب...
                    </>
                  ) : (
                    '🧮 حساب الخصومات'
                  )}
                </button>
                {penalties.length > 0 && (
                  <button
                    onClick={applyLatePenalties}
                    className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm flex items-center"
                  >
                    ⚠️ تطبيق الخصومات
                  </button>
                )}
              </div>
            </div>

            {/* Penalty Rules Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <h4 className="font-semibold text-blue-800 mb-2">📋 قواعد نظام الخصومات:</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• أول 15 دقيقة تأخير × 4 مرات = <strong>مجاناً</strong></li>
                <li>• أكثر من 4 مرات: تُجمع الدقائق وتُخصم من الراتب</li>
                <li>• أكثر من 20 دقيقة: خصم بالوقت الفعلي</li>
                <li>• من ساعة إلى ساعتين: خصم <strong>نصف يوم</strong></li>
                <li>• أكثر من ساعتين: خصم <strong>يوم كامل</strong></li>
              </ul>
            </div>

            {showPenaltySection && penalties.length > 0 && (
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b pb-2">
                  <h4 className="font-semibold text-gray-800">نتائج حساب الخصومات - {selectedMonth}</h4>
                  <div className="flex items-center gap-3">
                    <div className="text-sm text-gray-600">
                      إجمالي الموظفين المتأخرين: <strong>{penalties.length}</strong>
                    </div>
                    <button
                      onClick={() => {
                        // Export to Excel
                        let csvContent = 'الموظف,مرات التأخير,إجمالي الدقائق,خصم التأخير,خصم الغياب,خصم السلف,إجمالي الخصم\n';
                        penalties.forEach(p => {
                          csvContent += `${p.employee_name || p.user_name},${p.late_count || 0},${p.total_late_minutes || 0},${(p.late_deduction || 0).toFixed(2)},${(p.absence_deduction || 0).toFixed(2)},${(p.advance_deduction || 0).toFixed(2)},${(p.penalty_amount || 0).toFixed(2)}\n`;
                        });
                        const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = `deductions_${selectedMonth}.csv`;
                        link.click();
                      }}
                      className="px-3 py-1.5 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm flex items-center gap-1"
                    >
                      📥 تحميل Excel
                    </button>
                  </div>
                </div>
                
                <div className="overflow-x-auto max-h-96">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">الموظف</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">مرات التأخير</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">أيام الغياب</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">إجمالي الدقائق</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">خصم التأخير</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">خصم الغياب</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">إجمالي الخصم</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">التفاصيل</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {penalties.map((penalty, index) => (
                        <React.Fragment key={index}>
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-4 text-sm font-medium text-gray-900">
                              {penalty.employee_name || penalty.user_name}
                            </td>
                            <td className="px-4 py-4 text-sm text-center">
                              <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs">
                                {penalty.late_count || 0}
                              </span>
                            </td>
                            <td className="px-4 py-4 text-sm text-center">
                              <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs">
                                {penalty.absence_count || 0}
                              </span>
                            </td>
                            <td className="px-4 py-4 text-sm text-center text-orange-600 font-medium">
                              {penalty.total_late_minutes || 0} دقيقة
                            </td>
                            <td className="px-4 py-4 text-sm text-center text-orange-600 font-medium">
                              {penalty.late_deduction ? `${penalty.late_deduction.toFixed(2)} درهم` : '-'}
                            </td>
                            <td className="px-4 py-4 text-sm text-center text-red-600 font-medium">
                              {penalty.absence_deduction ? `${penalty.absence_deduction.toFixed(2)} درهم` : '-'}
                            </td>
                            <td className="px-4 py-4 text-sm text-center font-bold text-red-700">
                              {penalty.penalty_amount ? `${penalty.penalty_amount.toFixed(2)} درهم` : '-'}
                            </td>
                            <td className="px-4 py-4 text-sm">
                              <div className="flex flex-col gap-2">
                                <button
                                  onClick={() => {
                                    const newExpanded = {...expandedPenalties};
                                    newExpanded[index] = !newExpanded[index];
                                    setExpandedPenalties(newExpanded);
                                  }}
                                  className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded text-sm font-semibold"
                                >
                                  {expandedPenalties[index] ? '▲ إخفاء' : '▼ عرض التفاصيل'}
                                </button>
                                <div className="flex gap-2">
                                  <button
                                    onClick={() => exportEmployeeToExcel(penalty, selectedMonth)}
                                    className="flex-1 bg-green-500 hover:bg-green-600 text-white px-2 py-1 rounded text-xs font-semibold"
                                    title="تحميل Excel"
                                  >
                                    📥 Excel
                                  </button>
                                  <button
                                    onClick={() => exportEmployeeToPDF(penalty, selectedMonth)}
                                    className="flex-1 bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-xs font-semibold"
                                    title="تحميل PDF"
                                  >
                                    📄 PDF
                                  </button>
                                </div>
                              </div>
                            </td>
                          </tr>
                          {expandedPenalties[index] && (
                            <tr>
                              <td colSpan="8" className="bg-gray-50 p-4">
                                <div className="bg-white rounded-lg p-4 border-2 border-blue-200">
                                  <h4 className="font-bold text-lg mb-3 text-gray-700 flex items-center justify-between">
                                    <span>📋 التفاصيل اليومية - {penalty.employee_name}</span>
                                    <span className="text-sm text-gray-500">
                                      الفترة: {selectedMonth}
                                    </span>
                                  </h4>
                                  
                                  {/* Daily Details Table */}
                                  {penalty.daily_records && penalty.daily_records.length > 0 ? (
                                    <div className="overflow-x-auto">
                                      <table className="min-w-full border border-gray-300">
                                        <thead className="bg-blue-100">
                                          <tr>
                                            <th className="border border-gray-300 px-3 py-2 text-sm">التاريخ</th>
                                            <th className="border border-gray-300 px-3 py-2 text-sm">الحضور</th>
                                            <th className="border border-gray-300 px-3 py-2 text-sm">الانصراف</th>
                                            <th className="border border-gray-300 px-3 py-2 text-sm">ساعات العمل</th>
                                            <th className="border border-gray-300 px-3 py-2 text-sm">التأخير (د)</th>
                                            <th className="border border-gray-300 px-3 py-2 text-sm">خروج مبكر (د)</th>
                                            <th className="border border-gray-300 px-3 py-2 text-sm">النقص (د)</th>
                                            <th className="border border-gray-300 px-3 py-2 text-sm">الخصم (درهم)</th>
                                            <th className="border border-gray-300 px-3 py-2 text-sm">الحالة</th>
                                          </tr>
                                        </thead>
                                        <tbody>
                                          {penalty.daily_records.map((record, idx) => (
                                            <tr key={idx} className={record.is_absent ? 'bg-red-50' : idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                              <td className="border border-gray-300 px-3 py-2 text-sm text-center">{record.date}</td>
                                              <td className="border border-gray-300 px-3 py-2 text-sm text-center">
                                                {record.check_in || '-'}
                                              </td>
                                              <td className="border border-gray-300 px-3 py-2 text-sm text-center">
                                                {record.check_out || '-'}
                                              </td>
                                              <td className="border border-gray-300 px-3 py-2 text-sm text-center">
                                                {record.total_work_minutes ? `${Math.floor(record.total_work_minutes / 60)}:${(record.total_work_minutes % 60).toString().padStart(2, '0')}` : '-'}
                                              </td>
                                              <td className="border border-gray-300 px-3 py-2 text-sm text-center text-orange-600 font-medium">
                                                {record.late_minutes || 0}
                                              </td>
                                              <td className="border border-gray-300 px-3 py-2 text-sm text-center text-orange-600 font-medium">
                                                {record.early_leave_minutes || 0}
                                              </td>
                                              <td className="border border-gray-300 px-3 py-2 text-sm text-center text-red-600 font-medium">
                                                {record.deficit_minutes || 0}
                                              </td>
                                              <td className="border border-gray-300 px-3 py-2 text-sm text-center text-red-700 font-bold">
                                                {(record.deduction_amount || 0).toFixed(2)}
                                              </td>
                                              <td className="border border-gray-300 px-3 py-2 text-sm text-center">
                                                {record.is_absent ? (
                                                  <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-semibold">غياب</span>
                                                ) : record.deficit_minutes > 0 ? (
                                                  <span className="bg-orange-100 text-orange-700 px-2 py-1 rounded text-xs font-semibold">خصم</span>
                                                ) : (
                                                  <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-semibold">مكتمل</span>
                                                )}
                                              </td>
                                            </tr>
                                          ))}
                                        </tbody>
                                      </table>
                                    </div>
                                  ) : (
                                    <div className="text-center py-4 text-gray-500">
                                      لا توجد سجلات يومية متاحة
                                    </div>
                                  )}
                                  
                                  {/* Summary at bottom */}
                                  {penalty.details && penalty.details.length > 0 && (
                                    <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200">
                                      <h5 className="font-semibold text-gray-700 mb-2">الملخص:</h5>
                                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                                        {penalty.details.map((detail, idx) => (
                                          <li key={idx}>{typeof detail === 'string' ? detail : (detail?.msg || detail?.message || JSON.stringify(detail))}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg border-t">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-gray-700">إجمالي الخصومات:</span>
                    <span className="text-xl font-bold text-red-600">
                      {penalties.reduce((sum, p) => sum + p.penalty_amount, 0).toFixed(2)} درهم
                    </span>
                  </div>
                </div>
              </div>
            )}

            {showPenaltySection && penalties.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>لا يوجد موظفين متأخرين في الشهر المحدد</p>
                <p className="text-sm mt-1">🎉 جميع الموظفين ملتزمون بالحضور في الوقت!</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-8 text-center text-gray-500">
        <p className="text-sm">
          نظام إدارة الموارد البشرية - TANSEEQ Tax Consultancy © 2025
        </p>
      </div>

      {/* Message Modal */}
      {showMessageModal && selectedMessage && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl leading-6 font-bold text-gray-900 flex items-center">
                  {selectedMessage.message_type === 'friday_work' && '🚨 '}
                  {selectedMessage.priority === 'urgent' && '⚠️ '}
                  {selectedMessage.title}
                </h3>
                <button
                  onClick={() => setShowMessageModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                  <span>من: {selectedMessage.from_user_name}</span>
                  <span>{selectedMessage.time_ago}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    selectedMessage.message_type === 'friday_work' ? 'bg-red-100 text-red-700' :
                    selectedMessage.message_type === 'urgent' ? 'bg-orange-100 text-orange-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {selectedMessage.message_type === 'friday_work' ? 'دوام جمعة' :
                     selectedMessage.message_type === 'urgent' ? 'عاجل' : 'عام'}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    selectedMessage.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                    selectedMessage.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {selectedMessage.priority === 'urgent' ? 'عاجل جداً' :
                     selectedMessage.priority === 'high' ? 'مهم' : 'عادي'}
                  </span>
                </div>
              </div>
              
              <div className="mb-6 bg-white border rounded-lg p-4 max-h-96 overflow-y-auto">
                <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                  {selectedMessage.content}
                </div>
              </div>
              
              <div className="flex justify-end">
                <button
                  onClick={() => setShowMessageModal(false)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                >
                  إغلاق
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Custom Message Modal */}
      {showCustomMessageModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl leading-6 font-bold text-gray-900">
                  ✉️ إرسال رسالة مخصصة لجميع الموظفين
                </h3>
                <button
                  onClick={() => setShowCustomMessageModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    عنوان الرسالة *
                  </label>
                  <input
                    type="text"
                    value={customMessage.title}
                    onChange={(e) => setCustomMessage({...customMessage, title: e.target.value})}
                    placeholder="أدخل عنوان الرسالة..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    maxLength={100}
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    {customMessage.title.length}/100 حرف
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    نص الرسالة *
                  </label>
                  <textarea
                    value={customMessage.content}
                    onChange={(e) => setCustomMessage({...customMessage, content: e.target.value})}
                    placeholder="اكتب نص الرسالة هنا..."
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    maxLength={1000}
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    {customMessage.content.length}/1000 حرف
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    أولوية الرسالة
                  </label>
                  <select
                    value={customMessage.priority}
                    onChange={(e) => setCustomMessage({...customMessage, priority: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="normal">عادية</option>
                    <option value="high">مهمة</option>
                    <option value="urgent">عاجلة جداً</option>
                  </select>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-center mb-2">
                    <BellIcon className="h-4 w-4 text-blue-600 ml-2" />
                    <span className="text-sm font-medium text-blue-800">معاينة الإرسال:</span>
                  </div>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• سيتم إرسال الرسالة لجميع الموظفين النشطين</li>
                    <li>• ستظهر الرسالة في صفحة الرسائل لكل موظف</li>
                    <li>• سيحصل كل موظف على تنبيه عند دخول النظام</li>
                    <li>• اسمك سيظهر كمرسل الرسالة: {user?.name}</li>
                  </ul>
                </div>
              </div>
              
              <div className="flex space-x-2 mt-6">
                <button
                  onClick={sendCustomMessage}
                  disabled={sendingMessage || !customMessage.title.trim() || !customMessage.content.trim()}
                  className={`flex-1 px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-300 ${
                    sendingMessage || !customMessage.title.trim() || !customMessage.content.trim()
                      ? 'bg-gray-400 cursor-not-allowed text-white'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  } flex items-center justify-center`}
                >
                  {sendingMessage ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      جاري الإرسال...
                    </>
                  ) : (
                    <>
                      <BellIcon className="h-4 w-4 mr-2" />
                      إرسال لجميع الموظفين
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    setShowCustomMessageModal(false);
                    setCustomMessage({
                      title: '',
                      content: '',
                      priority: 'normal'
                    });
                  }}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  إلغاء
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Attendance Component

export default Dashboard;
