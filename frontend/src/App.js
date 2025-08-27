import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import jwt_decode from 'jwt-decode';
import { 
  UserIcon, 
  ClockIcon, 
  CalendarDaysIcon as CalendarIcon, 
  DocumentTextIcon, 
  DocumentIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ArrowRightOnRectangleIcon as LogoutIcon,
  Bars3Icon as MenuIcon,
  XMarkIcon as XIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  UserGroupIcon,
  ExclamationCircleIcon,
  DocumentArrowDownIcon,
  DocumentArrowUpIcon,
  MagnifyingGlassIcon,
  Cog6ToothIcon,
  BellIcon,
  ChevronDownIcon,
  XMarkIcon,
  ShieldCheckIcon,
  FolderIcon,
  ServerIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  InformationCircleIcon,
  CalculatorIcon
} from '@heroicons/react/24/outline';
import './App.css';

// Import Work Reports Components
import WorkReportsDashboard from './WorkReports/WorkReportsDashboard';
import ClientManagement from './WorkReports/ClientManagement';
import WorkLogManagement from './WorkReports/WorkLogManagement';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      try {
        const decoded = jwt_decode(token);
        if (decoded.exp * 1000 > Date.now()) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          fetchUser();
        } else {
          logout();
        }
      } catch (error) {
        logout();
      }
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setLoading(false);
    } catch (error) {
      logout();
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setLoading(false);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Language Context
const LanguageContext = createContext();

const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState('ar');
  const [isRTL, setIsRTL] = useState(true);

  const toggleLanguage = () => {
    const newLang = language === 'ar' ? 'en' : 'ar';
    setLanguage(newLang);
    setIsRTL(newLang === 'ar');
  };

  const t = (key) => {
    const translations = {
      ar: {
        // Auth
        login: 'تسجيل الدخول',
        email: 'البريد الإلكتروني',
        password: 'كلمة المرور',
        logout: 'تسجيل الخروج',
        
        // Navigation
        dashboard: 'الرئيسية',
        employees: 'الموظفين',
        attendance: 'الحضور',
        leaves: 'الإجازات',
        field_exits: 'الزيارات الخارجية',
        reports: 'التقارير',
        payroll: 'كشف المرتبات',
        activity_logs: 'سجل الأنشطة',
        
        // Dashboard
        total_users: 'إجمالي الموظفين',
        present_today: 'الحاضرين اليوم',
        pending_leaves: 'الإجازات المعلقة',
        pending_field_exits: 'الزيارات المعلقة',
        
        // Attendance
        check_in: 'تسجيل الحضور',
        check_out: 'تسجيل الانصراف',
        checked_in: 'تم تسجيل الحضور',
        checked_out: 'تم تسجيل الانصراف',
        working_hours: 'ساعات العمل',
        late: 'متأخر',
        
        // Common
        name: 'الاسم',
        role: 'الدور',
        position: 'المنصب',
        status: 'الحالة',
        date: 'التاريخ',
        time: 'الوقت',
        actions: 'الإجراءات',
        save: 'حفظ',
        cancel: 'إلغاء',
        approve: 'موافق',
        reject: 'رفض',
        pending: 'معلق',
        approved: 'مقبول',
        rejected: 'مرفوض',
        
        // Roles
        super_admin: 'مدير عام',
        admin: 'مدير',
        user: 'موظف'
      },
      en: {
        // Auth
        login: 'Login',
        email: 'Email',
        password: 'Password',
        logout: 'Logout',
        
        // Navigation
        dashboard: 'Dashboard',
        employees: 'Employees',
        attendance: 'Attendance',
        leaves: 'Leaves',
        field_exits: 'Field Exits',
        reports: 'Reports',
        payroll: 'Payroll',
        activity_logs: 'Activity Logs',
        
        // Dashboard
        total_users: 'Total Users',
        present_today: 'Present Today',
        pending_leaves: 'Pending Leaves',
        pending_field_exits: 'Pending Field Exits',
        
        // Attendance
        check_in: 'Check In',
        check_out: 'Check Out',
        checked_in: 'Checked In',
        checked_out: 'Checked Out',
        working_hours: 'Working Hours',
        late: 'Late',
        
        // Common
        name: 'Name',
        role: 'Role',
        position: 'Position',
        status: 'Status',
        date: 'Date',
        time: 'Time',
        actions: 'Actions',
        save: 'Save',
        cancel: 'Cancel',
        approve: 'Approve',
        reject: 'Reject',
        pending: 'Pending',
        approved: 'Approved',
        rejected: 'Rejected',
        
        // Roles
        super_admin: 'Super Admin',
        admin: 'Admin',
        user: 'User'
      }
    };
    
    return translations[language][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, isRTL, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

// Login Component
const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { t, isRTL } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(email, password);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center px-4 ${isRTL ? 'rtl' : 'ltr'}`}>
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-white">
            TANSEEQ
          </h2>
          <p className="mt-2 text-sm text-blue-200">
            Tax Consultancy
          </p>
        </div>
        
        <form className="mt-8 space-y-6 bg-white p-8 rounded-lg shadow-lg" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                {t('email')}
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                {t('password')}
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? '...' : t('login')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Layout Component
const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const { t, isRTL, toggleLanguage } = useLanguage();
  const navigate = useNavigate();

  const navigation = [
    { name: t('dashboard'), href: '/dashboard', icon: ChartBarIcon },
    ...(user?.role === 'user' ? [
      { name: t('attendance'), href: '/attendance', icon: ClockIcon },
      { name: t('leaves'), href: '/leaves', icon: CalendarIcon },
      { name: t('field_exits'), href: '/field-exits', icon: DocumentTextIcon },
    ] : []),
    ...(user?.role === 'admin' || user?.role === 'super_admin' ? [
      { name: t('employees'), href: '/employees', icon: UserGroupIcon },
      { name: t('attendance'), href: '/attendance-management', icon: ClockIcon },
      { name: t('leaves'), href: '/leave-management', icon: CalendarIcon },
      { name: t('field_exits'), href: '/field-exit-management', icon: DocumentTextIcon },
      { name: t('reports'), href: '/reports', icon: DocumentTextIcon },
      { name: 'تقرير العمل الإضافي', href: '/overtime-report', icon: ClockIcon },
      { name: t('payroll'), href: '/payroll', icon: CurrencyDollarIcon },
      { name: 'إدارة النسخ الاحتياطية', href: '/backup-management', icon: ServerIcon },
      { name: 'عرض المرفقات', href: '/attachment-viewer', icon: FolderIcon },
    ] : []),
    ...(user?.role === 'super_admin' ? [
      { name: t('activity_logs'), href: '/activity-logs', icon: DocumentTextIcon },
      { name: 'إنشاء طلبات للموظفين', href: '/admin-request-creation', icon: PlusIcon },
    ] : []),
    // Work Reports Module (Isolated)
    { name: 'لوحة التقارير', href: '/work-reports', icon: ChartBarIcon },
    { name: 'إدارة العملاء', href: '/work-reports/clients', icon: UserGroupIcon },
    { name: 'سجلات العمل اليومية', href: '/work-reports/logs', icon: ClockIcon },
  ];

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      logout();
    }
  };

  return (
    <div className={`min-h-screen bg-gray-100 ${isRTL ? 'rtl' : 'ltr'}`}>
      {/* Sidebar */}
      <div className={`fixed inset-y-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out ${isRTL ? 'right-0' : 'left-0'} ${sidebarOpen ? 'translate-x-0' : isRTL ? 'translate-x-full' : '-translate-x-full'} lg:translate-x-0`}>
        <div className="flex items-center justify-between p-4 border-b">
          <h1 className="text-xl font-bold text-gray-800">TANSEEQ</h1>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden"
          >
            <XIcon className="h-6 w-6" />
          </button>
        </div>
        
        <nav className="mt-8">
          <div className="px-4 space-y-2">
            {navigation.map((item) => (
              <button
                key={item.name}
                onClick={() => navigate(item.href)}
                className="w-full flex items-center px-4 py-3 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors duration-200"
              >
                <item.icon className={`h-5 w-5 ${isRTL ? 'ml-3' : 'mr-3'}`} />
                {item.name}
              </button>
            ))}
          </div>
        </nav>
      </div>

      {/* Main content */}
      <div className={`${isRTL ? 'lg:mr-64' : 'lg:ml-64'} min-h-screen`}>
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="flex items-center justify-between px-4 py-4">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden"
              >
                <MenuIcon className="h-6 w-6" />
              </button>
              <h2 className="text-lg font-semibold text-gray-800 ml-4">
                TANSEEQ Tax Consultancy
              </h2>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleLanguage}
                className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
              >
                {isRTL ? 'EN' : 'عربي'}
              </button>
              
              <div className="flex items-center space-x-2">
                <UserIcon className="h-5 w-5 text-gray-600" />
                <span className="text-sm text-gray-700">{user?.name}</span>
                <span className="text-xs text-gray-500">({t(user?.role)})</span>
              </div>
              
              <button
                onClick={handleLogout}
                className="flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors"
              >
                <LogoutIcon className="h-4 w-4 mr-1" />
                {t('logout')}
              </button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

// Dashboard Component - Enhanced Professional Design
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

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await axios.get(`${API}/messages/unread-count`);
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  const markAsRead = async (messageId) => {
    try {
      await axios.post(`${API}/messages/${messageId}/read`);
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

  // Penalty functions (Super Admin only)
  const calculateLatePenalties = async () => {
    if (user?.name !== "Hatem Mohamed Ahmed") return;
    
    setPenaltyLoading(true);
    try {
      const response = await axios.get(`${API}/penalties/late/${selectedMonth}`);
      setPenalties(response.data);
      setShowPenaltySection(true);
    } catch (error) {
      console.error('Error calculating penalties:', error);
      alert('حدث خطأ في حساب الخصومات');
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
      const response = await axios.post(`${API}/penalties/apply/${selectedMonth}`);
      alert(`تم تطبيق خصومات التأخير بنجاح!\nعدد الموظفين: ${response.data.total_employees}\nإجمالي الخصم: ${response.data.total_penalty_amount} درهم`);
      calculateLatePenalties(); // Refresh data
    } catch (error) {
      console.error('Error applying penalties:', error);
      alert('حدث خطأ في تطبيق الخصومات');
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
                <input
                  type="month"
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
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
                  <div className="text-sm text-gray-600">
                    إجمالي الموظفين المتأخرين: <strong>{penalties.length}</strong>
                  </div>
                </div>
                
                <div className="overflow-x-auto max-h-96">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">الموظف</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">مرات التأخير</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">إجمالي الدقائق</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">دقائق مجانية</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">دقائق خصم</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">نوع الخصم</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">مبلغ الخصم</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {penalties.map((penalty, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-4 py-4 text-sm font-medium text-gray-900">
                            {penalty.user_name}
                          </td>
                          <td className="px-4 py-4 text-sm text-center">
                            <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs">
                              {penalty.late_incidents}
                            </span>
                          </td>
                          <td className="px-4 py-4 text-sm text-center text-red-600 font-medium">
                            {penalty.total_late_minutes} دقيقة
                          </td>
                          <td className="px-4 py-4 text-sm text-center text-green-600 font-medium">
                            {penalty.free_late_minutes} دقيقة
                          </td>
                          <td className="px-4 py-4 text-sm text-center text-red-600 font-bold">
                            {penalty.penalty_minutes} دقيقة
                          </td>
                          <td className="px-4 py-4 text-sm text-center">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              penalty.penalty_type === 'minutes' ? 'bg-blue-100 text-blue-800' :
                              penalty.penalty_type === 'actual_time' ? 'bg-orange-100 text-orange-800' :
                              penalty.penalty_type === 'half_day' ? 'bg-red-100 text-red-800' :
                              penalty.penalty_type === 'full_day' ? 'bg-red-200 text-red-900' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {penalty.penalty_type === 'minutes' ? 'دقائق' :
                               penalty.penalty_type === 'actual_time' ? 'وقت فعلي' :
                               penalty.penalty_type === 'half_day' ? 'نصف يوم' :
                               penalty.penalty_type === 'full_day' ? 'يوم كامل' : 'لا يوجد'}
                            </span>
                          </td>
                          <td className="px-4 py-4 text-sm text-center font-bold text-red-600">
                            {penalty.penalty_amount > 0 ? `${penalty.penalty_amount.toFixed(2)} درهم` : '-'}
                          </td>
                        </tr>
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('date')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحضور
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الانصراف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ساعات العمل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('status')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {attendance.map((record) => (
                <tr key={record.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {record.date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {record.check_in || '--'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {record.check_out || '--'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {record.working_hours ? `${record.working_hours.toFixed(1)} ساعة` : '--'}
                  </td>
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

// Employees Component (Admin only)
const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'user',
    position: '',
    monthly_salary: '',
    working_hours_start: '09:00',
    working_hours_end: '18:00',
    phone: '',
    has_flexible_schedule: false,
    flexible_hours_per_day: 8,
    flexible_start_range: '07:00-10:00',
    flexible_end_range: '16:00-19:00',
    flexible_core_hours: '10:00-15:00',
    flexible_days_per_week: 5
  });
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!selectedEmployee || !newPassword) return;
    
    try {
      await axios.post(`${API}/users/${selectedEmployee.id}/change-password`, {
        new_password: newPassword
      });
      setShowPasswordModal(false);
      setNewPassword('');
      setSelectedEmployee(null);
      alert('Password changed successfully');
    } catch (error) {
      console.error('Error changing password:', error);
      alert('Error changing password');
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    
    try {
      await axios.post(`${API}/users`, {
        ...formData,
        monthly_salary: parseFloat(formData.monthly_salary),
        hire_date: new Date().toISOString()
      });
      setShowAddModal(false);
      setFormData({
        name: '',
        email: '',
        password: '',
        role: 'user',
        position: '',
        monthly_salary: '',
        working_hours_start: '09:00',
        working_hours_end: '18:00',
        phone: ''
      });
      fetchEmployees();
      alert('Employee added successfully');
    } catch (error) {
      console.error('Error adding employee:', error);
      alert('Error adding employee: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const handleEditEmployee = async (e) => {
    e.preventDefault();
    
    try {
      await axios.put(`${API}/users/${selectedEmployee.id}`, {
        ...formData,
        monthly_salary: parseFloat(formData.monthly_salary)
      });
      setShowEditModal(false);
      setSelectedEmployee(null);
      setFormData({
        name: '',
        email: '',
        password: '',
        role: 'user',
        position: '',
        monthly_salary: '',
        working_hours_start: '09:00',
        working_hours_end: '18:00',
        phone: ''
      });
      fetchEmployees();
      alert('Employee updated successfully');
    } catch (error) {
      console.error('Error updating employee:', error);
      alert('Error updating employee: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const handleDeleteEmployee = async (employee) => {
    if (window.confirm(`Are you sure you want to delete ${employee.name}?`)) {
      try {
        await axios.delete(`${API}/users/${employee.id}`);
        fetchEmployees();
        alert('Employee deleted successfully');
      } catch (error) {
        console.error('Error deleting employee:', error);
        alert('Error deleting employee: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    }
  };

  const openPasswordModal = (employee) => {
    setSelectedEmployee(employee);
    setShowPasswordModal(true);
  };

  const openAddModal = () => {
    setFormData({
      name: '',
      email: '',
      password: '',
      role: 'user',
      position: '',
      monthly_salary: '',
      working_hours_start: '09:00',
      working_hours_end: '18:00',
      phone: '',
      has_flexible_schedule: false,
      flexible_hours_per_day: 8,
      flexible_start_range: '07:00-10:00',
      flexible_end_range: '16:00-19:00',
      flexible_core_hours: '10:00-15:00',
      flexible_days_per_week: 5
    });
    setShowAddModal(true);
  };

  const openEditModal = (employee) => {
    setSelectedEmployee(employee);
    setFormData({
      name: employee.name,
      email: employee.email,
      password: '',
      role: employee.role,
      position: employee.position,
      monthly_salary: employee.monthly_salary.toString(),
      working_hours_start: employee.working_hours_start,
      working_hours_end: employee.working_hours_end,
      phone: employee.phone,
      has_flexible_schedule: employee.has_flexible_schedule || false,
      flexible_hours_per_day: employee.flexible_hours_per_day || 8,
      flexible_start_range: employee.flexible_start_range || '07:00-10:00',
      flexible_end_range: employee.flexible_end_range || '16:00-19:00',
      flexible_core_hours: employee.flexible_core_hours || '10:00-15:00',
      flexible_days_per_week: employee.flexible_days_per_week || 5
    });
    setShowEditModal(true);
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">TANSEEQ Tax Consultancy - {t('employees')}</h2>
          <div className="flex items-center space-x-2">
            <div className="text-sm text-gray-600">
              Total: {employees.length} employees
            </div>
            {(user?.role === 'admin' || user?.role === 'super_admin') && (
              <button
                onClick={openAddModal}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                إضافة موظف
              </button>
            )}
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('name')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  البريد الإلكتروني
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('role')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('position')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الراتب الشهري
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  المعدل اليومي
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ساعات العمل
                </th>
                {user?.name === "Hatem Mohamed Ahmed" && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('actions')}
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {employees.map((employee) => (
                <tr key={employee.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <UserIcon className="h-8 w-8 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">{employee.name}</div>
                        <div className="text-sm text-gray-500">{employee.phone}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {employee.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      employee.role === 'super_admin' ? 'bg-purple-100 text-purple-800' :
                      employee.role === 'admin' ? 'bg-blue-100 text-blue-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {t(employee.role)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {employee.position}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="font-medium">AED {employee.monthly_salary.toLocaleString()}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>AED {employee.daily_rate.toFixed(2)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>{employee.working_hours_start} - {employee.working_hours_end}</div>
                    {employee.has_custom_schedule && (
                      <div className="text-xs text-blue-600">Custom Schedule</div>
                    )}
                    {employee.has_flexible_schedule && (
                      <div className="text-xs text-green-600">دوام مرن</div>
                    )}
                  </td>
                  {user?.name === "Hatem Mohamed Ahmed" && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => openEditModal(employee)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Edit Employee"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => openPasswordModal(employee)}
                          className="text-green-600 hover:text-green-900"
                          title="Change Password"
                        >
                          <ExclamationCircleIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteEmployee(employee)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete Employee"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Employee Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                إضافة موظف جديد
              </h3>
              <form onSubmit={handleAddEmployee} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الاسم</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">البريد الإلكتروني</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">كلمة المرور</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الدور</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="user">موظف</option>
                    <option value="admin">مدير</option>
                    <option value="super_admin">مدير عام</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">المنصب</label>
                  <input
                    type="text"
                    value={formData.position}
                    onChange={(e) => setFormData({...formData, position: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الراتب الشهري (AED)</label>
                  <input
                    type="number"
                    value={formData.monthly_salary}
                    onChange={(e) => setFormData({...formData, monthly_salary: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">بداية الدوام</label>
                    <input
                      type="time"
                      value={formData.working_hours_start}
                      onChange={(e) => setFormData({...formData, working_hours_start: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">نهاية الدوام</label>
                    <input
                      type="time"
                      value={formData.working_hours_end}
                      onChange={(e) => setFormData({...formData, working_hours_end: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                <div className="border-t pt-4">
                  <label className="flex items-center space-x-2 mb-4">
                    <input
                      type="checkbox"
                      checked={formData.has_flexible_schedule}
                      onChange={(e) => setFormData({...formData, has_flexible_schedule: e.target.checked})}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium text-gray-700">تفعيل الدوام المرن</span>
                  </label>

                  {formData.has_flexible_schedule && (
                    <div className="space-y-4 bg-blue-50 p-4 rounded-md">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">ساعات العمل اليومية</label>
                          <input
                            type="number"
                            value={formData.flexible_hours_per_day}
                            onChange={(e) => setFormData({...formData, flexible_hours_per_day: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="1"
                            max="12"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">أيام العمل الأسبوعية</label>
                          <input
                            type="number"
                            value={formData.flexible_days_per_week}
                            onChange={(e) => setFormData({...formData, flexible_days_per_week: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="1"
                            max="7"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">نطاق بداية الدوام (مثال: 07:00-10:00)</label>
                        <input
                          type="text"
                          value={formData.flexible_start_range}
                          onChange={(e) => setFormData({...formData, flexible_start_range: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="07:00-10:00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">نطاق نهاية الدوام (مثال: 16:00-19:00)</label>
                        <input
                          type="text"
                          value={formData.flexible_end_range}
                          onChange={(e) => setFormData({...formData, flexible_end_range: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="16:00-19:00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">ساعات الحضور الأساسية (مثال: 10:00-15:00)</label>
                        <input
                          type="text"
                          value={formData.flexible_core_hours}
                          onChange={(e) => setFormData({...formData, flexible_core_hours: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="10:00-15:00"
                        />
                        <p className="text-xs text-gray-500 mt-1">الساعات التي يجب على الموظف التواجد فيها</p>
                      </div>
                    </div>
                  )}
                </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">رقم الهاتف</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex space-x-2">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  >
                    إضافة الموظف
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    إلغاء
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Employee Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                تعديل بيانات الموظف - {selectedEmployee?.name}
              </h3>
              <form onSubmit={handleEditEmployee} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الاسم</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">البريد الإلكتروني</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الدور</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="user">موظف</option>
                    <option value="admin">مدير</option>
                    <option value="super_admin">مدير عام</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">المنصب</label>
                  <input
                    type="text"
                    value={formData.position}
                    onChange={(e) => setFormData({...formData, position: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الراتب الشهري (AED)</label>
                  <input
                    type="number"
                    value={formData.monthly_salary}
                    onChange={(e) => setFormData({...formData, monthly_salary: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">بداية الدوام</label>
                    <input
                      type="time"
                      value={formData.working_hours_start}
                      onChange={(e) => setFormData({...formData, working_hours_start: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">نهاية الدوام</label>
                    <input
                      type="time"
                      value={formData.working_hours_end}
                      onChange={(e) => setFormData({...formData, working_hours_end: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">رقم الهاتف</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex space-x-2">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  >
                    حفظ التعديلات
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    إلغاء
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Change Password - {selectedEmployee?.name}
              </h3>
              <div className="mt-2 px-7 py-3">
                <input
                  type="password"
                  placeholder="New Password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleChangePassword}
                  className="px-4 py-2 bg-blue-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                >
                  Change Password
                </button>
                <button
                  onClick={() => {
                    setShowPasswordModal(false);
                    setNewPassword('');
                    setSelectedEmployee(null);
                  }}
                  className="mt-3 px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Field Exit Component
const FieldExits = () => {
  const [fieldExits, setFieldExits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    visit_type: 'client_visit',
    client_name: '',
    expected_start_time: '',
    expected_end_time: '',
    report: ''
  });
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchFieldExits();
  }, []);

  const fetchFieldExits = async () => {
    try {
      const response = await axios.get(`${API}/field-exits`);
      setFieldExits(response.data);
    } catch (error) {
      console.error('Error fetching field exits:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('visit_type', formData.visit_type);
      formDataToSend.append('client_name', formData.client_name);
      formDataToSend.append('expected_start_time', formData.expected_start_time);
      formDataToSend.append('expected_end_time', formData.expected_end_time);
      formDataToSend.append('report', formData.report);
      
      await axios.post(`${API}/field-exits`, formDataToSend);
      
      setShowModal(false);
      setFormData({
        visit_type: 'client_visit',
        client_name: '',
        expected_start_time: '',
        expected_end_time: '',
        report: ''
      });
      fetchFieldExits();
      alert('تم إنشاء طلب الخروج بنجاح');
    } catch (error) {
      console.error('Error creating field exit:', error);
      alert('حدث خطأ في إنشاء طلب الخروج');
    }
  };

  const handleDepartureTime = async (id) => {
    try {
      await axios.post(`${API}/field-exits/${id}/start`);
      fetchFieldExits();
      alert('تم تسجيل وقت الذهاب بنجاح');
    } catch (error) {
      console.error('Error recording departure time:', error);
      alert('حدث خطأ في تسجيل وقت الذهاب');
    }
  };

  const handleReturnTime = async (id) => {
    try {
      await axios.post(`${API}/field-exits/${id}/end`);
      fetchFieldExits();
      alert('تم تسجيل وقت العودة بنجاح');
    } catch (error) {
      console.error('Error recording return time:', error);
      alert('حدث خطأ في تسجيل وقت العودة');
    }
  };

  const handleApprove = async (id) => {
    try {
      await axios.post(`${API}/field-exits/${id}/approve`);
      fetchFieldExits();
    } catch (error) {
      console.error('Error approving field exit:', error);
    }
  };

  const handleReject = async (id) => {
    try {
      await axios.post(`${API}/field-exits/${id}/reject`);
      fetchFieldExits();
    } catch (error) {
      console.error('Error rejecting field exit:', error);
    }
  };

  const visitTypeOptions = {
    client_visit: 'زيارة عميل',
    collection: 'تحصيل',
    bank_visit: 'زيارة بنك',
    personal: 'شخصي',
    admin_errand: 'مهمة إدارية'
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">خروج أثناء الدوام</h2>
          {user?.role === 'user' && (
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <PlusIcon className="h-4 w-4 inline mr-2" />
              طلب خروج
            </button>
          )}
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الموظف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  نوع الزيارة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  اسم العميل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الوقت المتوقع
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الوقت الفعلي
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحالة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الإجراءات
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {fieldExits.map((exit) => (
                <tr key={exit.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {exit.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {visitTypeOptions[exit.visit_type]}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {exit.client_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="text-xs">
                      <div>من: {exit.expected_start_time || exit.start_time}</div>
                      <div>إلى: {exit.expected_end_time || exit.end_time}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="text-xs">
                      <div>ذهب: {exit.actual_start_time || '-'}</div>
                      <div>عاد: {exit.actual_end_time || '-'}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      exit.status === 'approved' ? 'bg-green-100 text-green-800' :
                      exit.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {exit.status === 'approved' ? 'موافق عليه' : 
                       exit.status === 'rejected' ? 'مرفوض' : 'معلق'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex flex-col space-y-2">
                      {/* User Actions */}
                      {user?.role === 'user' && exit.user_id === user.id && exit.status === 'approved' && (
                        <div className="flex space-x-2">
                          {!exit.actual_start_time && (
                            <button
                              onClick={() => handleDepartureTime(exit.id)}
                              className="px-3 py-1 bg-blue-500 text-white text-xs rounded-md hover:bg-blue-600"
                            >
                              تسجيل الذهاب
                            </button>
                          )}
                          {exit.actual_start_time && !exit.actual_end_time && (
                            <button
                              onClick={() => handleReturnTime(exit.id)}
                              className="px-3 py-1 bg-green-500 text-white text-xs rounded-md hover:bg-green-600"
                            >
                              تسجيل العودة
                            </button>
                          )}
                        </div>
                      )}
                      
                      {/* Admin Actions */}
                      {user?.role !== 'user' && exit.status === 'pending' && (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleApprove(exit.id)}
                            className="text-green-600 hover:text-green-900"
                            title="Approve"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleReject(exit.id)}
                            className="text-red-600 hover:text-red-900"
                            title="Reject"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Field Exit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                طلب خروج أثناء الدوام
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    نوع الزيارة
                  </label>
                  <select
                    value={formData.visit_type}
                    onChange={(e) => setFormData({...formData, visit_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {Object.entries(visitTypeOptions).map(([key, value]) => (
                      <option key={key} value={key}>{value}</option>
                    ))}
                  </select>
                </div>

                {formData.visit_type === 'client_visit' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      اسم العميل
                    </label>
                    <input
                      type="text"
                      value={formData.client_name}
                      onChange={(e) => setFormData({...formData, client_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    وقت البداية المتوقع
                  </label>
                  <input
                    type="time"
                    value={formData.expected_start_time}
                    onChange={(e) => setFormData({...formData, expected_start_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    وقت النهاية المتوقع
                  </label>
                  <input
                    type="time"
                    value={formData.expected_end_time}
                    onChange={(e) => setFormData({...formData, expected_end_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    تقرير الزيارة
                  </label>
                  <textarea
                    value={formData.report}
                    onChange={(e) => setFormData({...formData, report: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="اكتب تفاصيل الزيارة..."
                  />
                </div>

                <div className="flex space-x-2">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    إنشاء الطلب
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    إلغاء
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

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (requiredRole && user.role !== requiredRole && user.role !== 'super_admin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/attendance" element={
              <ProtectedRoute>
                <Layout>
                  <Attendance />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/employees" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <Employees />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/field-exits" element={
              <ProtectedRoute>
                <Layout>
                  <FieldExits />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/leaves" element={
              <ProtectedRoute>
                <Layout>
                  <Leaves />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/attendance-management" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <AttendanceManagement />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/leave-management" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <LeaveManagement />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/field-exit-management" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <FieldExitManagement />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <Reports />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/overtime-report" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <OvertimeReport />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/activity-logs" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout>
                  <ActivityLogs />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/payroll" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <Payroll />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/backup-management" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <BackupManagement />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/overtime-report" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <OvertimeReport />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/admin-request-creation" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout>
                  <AdminRequestCreation />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/attachment-viewer" element={
              <ProtectedRoute requiredRole="admin">
                <Layout>
                  <AttachmentViewer />
                </Layout>
              </ProtectedRoute>
            } />
            {/* Work Reports Module Routes */}
            <Route path="/work-reports" element={
              <ProtectedRoute>
                <Layout>
                  <WorkReportsDashboard />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/work-reports/clients" element={
              <ProtectedRoute>
                <Layout>
                  <ClientManagement />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/work-reports/logs" element={
              <ProtectedRoute>
                <Layout>
                  <WorkLogManagement />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </LanguageProvider>
    </AuthProvider>
  );
}

// Payroll Management Component
const Payroll = () => {
  const [payrollData, setPayrollData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchPayrollData();
  }, [selectedMonth]);

  const fetchPayrollData = async () => {
    try {
      const response = await axios.get(`${API}/payroll/calculate/${selectedMonth}`);
      setPayrollData(response.data);
    } catch (error) {
      console.error('Error fetching payroll data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(`${API}/payroll/export/${selectedMonth}?format=${format}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `payroll_${selectedMonth}.${format === 'excel' ? 'xlsx' : 'pdf'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting payroll:', error);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  const totalSalary = payrollData.reduce((sum, employee) => sum + employee.final_salary, 0);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">كشف المرتبات - TANSEEQ Tax Consultancy</h2>
          <div className="flex space-x-2">
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Array.from({length: 12}, (_, i) => {
                const date = new Date();
                date.setMonth(date.getMonth() - i);
                const monthStr = date.toISOString().slice(0, 7);
                return (
                  <option key={monthStr} value={monthStr}>
                    {date.toLocaleDateString('ar', { year: 'numeric', month: 'long' })}
                  </option>
                );
              })}
            </select>
            <button
              onClick={() => handleExport('excel')}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              تصدير Excel
            </button>
            <button
              onClick={() => handleExport('pdf')}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              تصدير PDF
            </button>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الموظف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  المنصب
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الراتب الشهري
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  المعدل اليومي
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  أيام العمل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ساعات العمل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  أيام التأخير
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الراتب النهائي
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {payrollData.map((employee) => (
                <tr key={employee.user_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <UserIcon className="h-8 w-8 text-gray-400 mr-3" />
                      <div className="text-sm font-medium text-gray-900">{employee.name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {employee.position}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="font-medium">AED {employee.monthly_salary.toLocaleString()}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    AED {employee.daily_rate.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <span className="font-medium">{employee.working_days}</span>
                      <span className="text-gray-500 ml-1">/ 22</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {employee.total_hours.toFixed(1)} ساعة
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      employee.late_days > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {employee.late_days} يوم
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="font-bold text-green-600">
                      AED {employee.final_salary.toLocaleString()}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr>
                <td colSpan="7" className="px-6 py-4 text-right text-sm font-medium text-gray-900">
                  الإجمالي:
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">
                  AED {totalSalary.toLocaleString()}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
        
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900">إجمالي الموظفين</h3>
            <p className="text-2xl font-bold text-blue-600">{payrollData.length}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-green-900">متوسط الراتب</h3>
            <p className="text-2xl font-bold text-green-600">
              AED {payrollData.length > 0 ? (totalSalary / payrollData.length).toFixed(2) : 0}
            </p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-purple-900">إجمالي الرواتب</h3>
            <p className="text-2xl font-bold text-purple-600">AED {totalSalary.toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Attendance Management Component (Admin)
const AttendanceManagement = () => {
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingRecord, setEditingRecord] = useState(null);
  const [editData, setEditData] = useState({});
  const [showAbsenceModal, setShowAbsenceModal] = useState(false);
  const [absenceData, setAbsenceData] = useState({});
  const [missingEmployees, setMissingEmployees] = useState([]);
  const [showMissingModal, setShowMissingModal] = useState(false);
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchAllAttendance();
  }, []);

  const fetchAllAttendance = async () => {
    try {
      // Use the enhanced endpoint that shows absences
      const response = await axios.get(`${API}/attendance/with-absences`);
      setAttendance(response.data);
    } catch (error) {
      console.error('Error fetching attendance:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (record) => {
    setEditingRecord(record.id);
    
    // Convert display status to backend format
    let backendStatus = record.status;
    if (record.status === 'Present') backendStatus = 'present';
    else if (record.status === 'Late') backendStatus = 'late';  
    else if (record.status === 'Absent') backendStatus = 'absent';
    
    setEditData({
      check_in: record.check_in || '',
      check_out: record.check_out || '',
      status: backendStatus,
      reason: record.absence_reason || ''
    });
  };

  const handleSave = async (id) => {
    try {
      // Always use the regular attendance update endpoint
      // It will handle all status changes properly
      const updateData = {
        check_in: editData.check_in || null,
        check_out: editData.check_out || null,
        status: editData.status,
        reason: editData.reason || null
      };

      await axios.put(`${API}/attendance/${id}`, updateData);
      
      setEditingRecord(null);
      setEditData({});
      fetchAllAttendance();
      
      // Show success message
      alert('تم تحديث سجل الحضور بنجاح');
    } catch (error) {
      console.error('Error updating attendance:', error);
      alert('حدث خطأ في تحديث سجل الحضور: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCancel = () => {
    setEditingRecord(null);
    setEditData({});
  };

  const handleCreateAbsence = async () => {
    try {
      await axios.post(`${API}/attendance/create-absence`, absenceData);
      setShowAbsenceModal(false);
      setAbsenceData({});
      fetchAllAttendance();
      alert('تم إنشاء سجل الغياب بنجاح');
    } catch (error) {
      console.error('Error creating absence:', error);
      alert('حدث خطأ في إنشاء سجل الغياب');
    }
  };

  const handleCheckMissingEmployees = async () => {
    try {
      const response = await axios.get(`${API}/attendance/missing-today`);
      setMissingEmployees(response.data.missing_employees);
      setShowMissingModal(true);
    } catch (error) {
      console.error('Error fetching missing employees:', error);
      alert('حدث خطأ في جلب بيانات الموظفين الغائبين');
    }
  };

  const handleProcessDailyAbsences = async (date = null) => {
    const targetDate = date || new Date().toISOString().split('T')[0];
    if (window.confirm(`هل أنت متأكد من معالجة الغياب التلقائي لتاريخ ${targetDate}؟`)) {
      try {
        const response = await axios.post(`${API}/attendance/process-daily-absences`, { date: targetDate });
        alert(`تم إنشاء ${response.data.absences_created} سجل غياب تلقائي من أصل ${response.data.total_employees} موظف`);
        fetchAllAttendance();
        setShowMissingModal(false);
      } catch (error) {
        console.error('Error processing daily absences:', error);
        alert('حدث خطأ في معالجة الغياب التلقائي');
      }
    }
  };

  const handleDeleteAbsence = async (id) => {
    if (window.confirm('هل أنت متأكد من حذف سجل الغياب؟')) {
      try {
        await axios.delete(`${API}/attendance/delete-absence/${id}`);
        fetchAllAttendance();
        alert('تم حذف سجل الغياب بنجاح');
      } catch (error) {
        console.error('Error deleting absence:', error);
        alert('حدث خطأ في حذف سجل الغياب');
      }
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">إدارة الحضور - TANSEEQ Tax Consultancy</h2>
          {user?.role === 'super_admin' && (
            <div className="flex space-x-2">
              <button
                onClick={handleCheckMissingEmployees}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
              >
                فحص الغائبين اليوم
              </button>
              <button
                onClick={() => setShowAbsenceModal(true)}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
              >
                إنشاء سجل غياب
              </button>
            </div>
          )}
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الموظف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  التاريخ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحضور
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الانصراف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ساعات العمل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحالة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  سبب الغياب
                </th>
                {(user?.role === 'super_admin' || user?.name === "Hatem Mohamed Ahmed") && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الإجراءات
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {attendance.map((record) => (
                <tr key={record.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {record.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {record.date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {editingRecord === record.id ? (
                      <input
                        type="time"
                        value={editData.check_in || ''}
                        onChange={(e) => setEditData({...editData, check_in: e.target.value})}
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      />
                    ) : (
                      record.check_in || (record.status === 'Absent' ? 'N/A' : '--')
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {editingRecord === record.id ? (
                      <input
                        type="time"
                        value={editData.check_out || ''}
                        onChange={(e) => setEditData({...editData, check_out: e.target.value})}
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      />
                    ) : (
                      record.check_out || (record.status === 'Absent' ? 'N/A' : '--')
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {record.working_hours ? `${record.working_hours.toFixed(1)} ساعة` : '--'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {editingRecord === record.id ? (
                      <select
                        value={editData.status}
                        onChange={(e) => setEditData({...editData, status: e.target.value})}
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      >
                        <option value="present">حاضر</option>
                        <option value="late">متأخر</option>
                        <option value="absent">غائب</option>
                      </select>
                    ) : (
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        record.status === 'Present' || record.status === 'present' ? 'bg-green-100 text-green-800' :
                        record.status === 'Late' || record.status === 'late' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {record.status === 'Present' || record.status === 'present' ? 'حاضر' : 
                         record.status === 'Late' || record.status === 'late' ? 'متأخر' : 'غائب'}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {editingRecord === record.id && editData.status === 'absent' ? (
                      <input
                        type="text"
                        value={editData.reason || ''}
                        onChange={(e) => setEditData({...editData, reason: e.target.value})}
                        placeholder="سبب الغياب"
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      />
                    ) : (
                      record.absence_reason || '--'
                    )}
                  </td>
                  {(user?.role === 'super_admin' || user?.name === "Hatem Mohamed Ahmed") && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {editingRecord === record.id ? (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleSave(record.id)}
                            className="text-green-600 hover:text-green-900"
                            title="حفظ"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={handleCancel}
                            className="text-red-600 hover:text-red-900"
                            title="إلغاء"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEdit(record)}
                            className="text-blue-600 hover:text-blue-900"
                            title="تعديل"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          {record.is_manual_entry && user?.role === 'super_admin' && (
                            <button
                              onClick={() => handleDeleteAbsence(record.id)}
                              className="text-red-600 hover:text-red-900"
                              title="حذف سجل الغياب"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Absence Modal */}
      {showAbsenceModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">إنشاء سجل غياب</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">ID الموظف</label>
                <input
                  type="text"
                  value={absenceData.user_id || ''}
                  onChange={(e) => setAbsenceData({...absenceData, user_id: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="أدخل ID الموظف"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">التاريخ</label>
                <input
                  type="date"
                  value={absenceData.date || ''}
                  onChange={(e) => setAbsenceData({...absenceData, date: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">سبب الغياب</label>
                <input
                  type="text"
                  value={absenceData.reason || ''}
                  onChange={(e) => setAbsenceData({...absenceData, reason: e.target.value})}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="مثال: مرض، ظروف شخصية"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => setShowAbsenceModal(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                إلغاء
              </button>
              <button
                onClick={handleCreateAbsence}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                إنشاء سجل غياب
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Missing Employees Modal */}
      {showMissingModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-2/3 max-w-4xl shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">الموظفون الغائبون اليوم</h3>
            
            {missingEmployees.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-green-600 text-lg">✅ جميع الموظفين سجلوا حضورهم اليوم!</p>
              </div>
            ) : (
              <div>
                <p className="text-red-600 mb-4">
                  عدد الموظفين الغائبين: {missingEmployees.length}
                </p>
                
                <div className="max-h-60 overflow-y-auto mb-4">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          اسم الموظف
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          البريد الإلكتروني
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          ID
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {missingEmployees.map((employee) => (
                        <tr key={employee.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {employee.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {employee.email}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {employee.id}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
                  <p className="text-yellow-800 text-sm">
                    💡 يمكنك إنشاء سجلات غياب تلقائية لجميع هؤلاء الموظفين بضغطة واحدة
                  </p>
                </div>
              </div>
            )}
            
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowMissingModal(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                إغلاق
              </button>
              {missingEmployees.length > 0 && (
                <button
                  onClick={() => handleProcessDailyAbsences()}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  إنشاء سجلات غياب تلقائية ({missingEmployees.length})
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Leave Management Component (Admin)
const LeaveManagement = () => {
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showImageModal, setShowImageModal] = useState(false);
  const [selectedImage, setSelectedImage] = useState('');
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [selectedLeave, setSelectedLeave] = useState(null);
  const [actionType, setActionType] = useState(''); // 'approve' or 'reject'
  const [notes, setNotes] = useState('');
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchAllLeaves();
  }, []);

  const fetchAllLeaves = async () => {
    try {
      const response = await axios.get(`${API}/leaves/all`);
      setLeaves(response.data);
    } catch (error) {
      console.error('Error fetching leaves:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (leave) => {
    setSelectedLeave(leave);
    setActionType('approve');
    setShowNotesModal(true);
  };

  const handleReject = async (leave) => {
    setSelectedLeave(leave);
    setActionType('reject');
    setShowNotesModal(true);
  };

  const submitAction = async () => {
    if (!selectedLeave) return;

    try {
      const endpoint = actionType === 'approve' ? 'approve' : 'reject';
      const requestData = notes ? { notes } : {};
      
      await axios.post(`${API}/leaves/${selectedLeave.id}/${endpoint}`, requestData);
      
      setShowNotesModal(false);
      setSelectedLeave(null);
      setNotes('');
      setActionType('');
      fetchAllLeaves();
      
      alert(`Leave request ${actionType === 'approve' ? 'approved' : 'rejected'} successfully`);
    } catch (error) {
      console.error(`Error ${actionType}ing leave:`, error);
      alert(`Error ${actionType}ing leave request`);
    }
  };

  const handleImageClick = (imageUrl) => {
    setSelectedImage(imageUrl);
    setShowImageModal(true);
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4 text-gray-800">إدارة الإجازات - TANSEEQ Tax Consultancy</h2>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الموظف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  تاريخ البداية
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  تاريخ النهاية
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  عدد الأيام
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  السبب
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  المرفق
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحالة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  تم الموافقة/الرفض من قبل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الملاحظات
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الإجراءات
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {leaves.map((leave) => (
                <tr key={leave.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {leave.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.start_date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.end_date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.days_count} يوم
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="max-w-xs overflow-hidden text-ellipsis">
                      {leave.reason}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.attachment_url ? (
                      <button
                        onClick={() => handleImageClick(`${BACKEND_URL}${leave.attachment_url}`)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      leave.status === 'approved' ? 'bg-green-100 text-green-800' :
                      leave.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {leave.status === 'approved' ? 'موافق عليه' : 
                       leave.status === 'rejected' ? 'مرفوض' : 'معلق'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.approved_by || leave.rejected_by || '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="max-w-xs overflow-hidden text-ellipsis">
                      {leave.admin_notes || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {leave.status === 'pending' && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleApprove(leave)}
                          className="text-green-600 hover:text-green-900"
                          title="Approve"
                        >
                          <CheckCircleIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleReject(leave)}
                          className="text-red-600 hover:text-red-900"
                          title="Reject"
                        >
                          <XCircleIcon className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action Modal with Notes */}
      {showNotesModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                {actionType === 'approve' ? 'موافقة على الإجازة' : 'رفض الإجازة'}
              </h3>
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  الموظف: {selectedLeave?.user_name}
                </p>
                <p className="text-sm text-gray-600 mb-2">
                  من {selectedLeave?.start_date} إلى {selectedLeave?.end_date}
                </p>
                <p className="text-sm text-gray-600 mb-4">
                  السبب: {selectedLeave?.reason}
                </p>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  الملاحظات (اختياري)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="أدخل أي ملاحظات..."
                />
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={submitAction}
                  className={`flex-1 px-4 py-2 ${
                    actionType === 'approve' ? 'bg-green-500 hover:bg-green-700' : 'bg-red-500 hover:bg-red-700'
                  } text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-300`}
                >
                  {actionType === 'approve' ? 'موافقة' : 'رفض'}
                </button>
                <button
                  onClick={() => {
                    setShowNotesModal(false);
                    setSelectedLeave(null);
                    setNotes('');
                    setActionType('');
                  }}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  إلغاء
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Image Modal */}
      {showImageModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setShowImageModal(false)}
              className="absolute top-4 right-4 text-white bg-black bg-opacity-50 rounded-full p-2"
            >
              <XIcon className="h-6 w-6" />
            </button>
            <img
              src={selectedImage}
              alt="Leave attachment"
              className="max-w-full max-h-full object-contain"
            />
          </div>
        </div>
      )}
    </div>
  );
};

// Field Exit Management Component (Admin)
const FieldExitManagement = () => {
  const [fieldExits, setFieldExits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [selectedFieldExit, setSelectedFieldExit] = useState(null);
  const [actionType, setActionType] = useState(''); // 'approve' or 'reject'
  const [notes, setNotes] = useState('');
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchAllFieldExits();
  }, []);

  const fetchAllFieldExits = async () => {
    try {
      const response = await axios.get(`${API}/field-exits/all`);
      setFieldExits(response.data);
    } catch (error) {
      console.error('Error fetching field exits:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (fieldExit) => {
    setSelectedFieldExit(fieldExit);
    setActionType('approve');
    setShowNotesModal(true);
  };

  const handleReject = async (fieldExit) => {
    setSelectedFieldExit(fieldExit);
    setActionType('reject');
    setShowNotesModal(true);
  };

  const submitAction = async () => {
    if (!selectedFieldExit) return;

    try {
      const endpoint = actionType === 'approve' ? 'approve' : 'reject';
      const requestData = notes ? { notes } : {};
      
      await axios.post(`${API}/field-exits/${selectedFieldExit.id}/${endpoint}`, requestData);
      
      setShowNotesModal(false);
      setSelectedFieldExit(null);
      setNotes('');
      setActionType('');
      fetchAllFieldExits();
      
      alert(`Field exit request ${actionType === 'approve' ? 'approved' : 'rejected'} successfully`);
    } catch (error) {
      console.error(`Error ${actionType}ing field exit:`, error);
      alert(`Error ${actionType}ing field exit request`);
    }
  };

  const visitTypeOptions = {
    client_visit: 'زيارة عميل',
    collection: 'تحصيل',
    bank_visit: 'زيارة بنك',
    personal: 'شخصي',
    admin_errand: 'مهمة إدارية'
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4 text-gray-800">إدارة الزيارات الخارجية - TANSEEQ Tax Consultancy</h2>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الموظف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  التاريخ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  نوع الزيارة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  اسم العميل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الوقت المتوقع
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الوقت الفعلي
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  تقرير الزيارة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحالة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  تم الموافقة/الرفض من قبل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الملاحظات
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الإجراءات
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {fieldExits.map((exit) => (
                <tr key={exit.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {exit.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {exit.date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {visitTypeOptions[exit.visit_type]}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {exit.client_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="text-xs">
                      <div>من: {exit.expected_start_time || exit.start_time}</div>
                      <div>إلى: {exit.expected_end_time || exit.end_time}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="text-xs">
                      <div>ذهب: {exit.actual_start_time || '-'}</div>
                      <div>عاد: {exit.actual_end_time || '-'}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="max-w-xs overflow-hidden text-ellipsis">
                      {exit.report || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      exit.status === 'approved' ? 'bg-green-100 text-green-800' :
                      exit.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {exit.status === 'approved' ? 'موافق عليه' : 
                       exit.status === 'rejected' ? 'مرفوض' : 'معلق'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {exit.approved_by || exit.rejected_by || '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="max-w-xs overflow-hidden text-ellipsis">
                      {exit.admin_notes || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {exit.status === 'pending' && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleApprove(exit)}
                          className="text-green-600 hover:text-green-900"
                          title="Approve"
                        >
                          <CheckCircleIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleReject(exit)}
                          className="text-red-600 hover:text-red-900"
                          title="Reject"
                        >
                          <XCircleIcon className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action Modal with Notes */}
      {showNotesModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                {actionType === 'approve' ? 'موافقة على الزيارة الخارجية' : 'رفض الزيارة الخارجية'}
              </h3>
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  الموظف: {selectedFieldExit?.user_name}
                </p>
                <p className="text-sm text-gray-600 mb-2">
                  نوع الزيارة: {visitTypeOptions[selectedFieldExit?.visit_type]}
                </p>
                <p className="text-sm text-gray-600 mb-2">
                  التاريخ: {selectedFieldExit?.date}
                </p>
                <p className="text-sm text-gray-600 mb-4">
                  العميل: {selectedFieldExit?.client_name || 'غير محدد'}
                </p>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  الملاحظات (اختياري)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="أدخل أي ملاحظات..."
                />
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={submitAction}
                  className={`flex-1 px-4 py-2 ${
                    actionType === 'approve' ? 'bg-green-500 hover:bg-green-700' : 'bg-red-500 hover:bg-red-700'
                  } text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-300`}
                >
                  {actionType === 'approve' ? 'موافقة' : 'رفض'}
                </button>
                <button
                  onClick={() => {
                    setShowNotesModal(false);
                    setSelectedFieldExit(null);
                    setNotes('');
                    setActionType('');
                  }}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-300"
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

// Reports Component
const Reports = () => {
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
            <button
              onClick={() => handleExport('excel')}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              تصدير Excel
            </button>
            <button
              onClick={() => handleExport('pdf')}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              تصدير PDF
            </button>
          </div>
        </div>

        {/* Date Range Selection */}
        <div className="mb-6 bg-gray-50 p-4 rounded-lg">
          <h3 className="text-md font-medium text-gray-700 mb-3">اختيار الفترة</h3>
          
          {/* Quick Date Range Buttons */}
          <div className="flex flex-wrap gap-2 mb-4">
            <button
              onClick={() => handleQuickDateRange(7)}
              className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm"
            >
              آخر 7 أيام
            </button>
            <button
              onClick={() => handleQuickDateRange(30)}
              className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm"
            >
              آخر 30 يوم
            </button>
            <button
              onClick={() => handleQuickDateRange(90)}
              className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm"
            >
              آخر 3 أشهر
            </button>
            <button
              onClick={() => {
                const today = new Date();
                const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                setStartDate(firstDay.toISOString().slice(0, 10));
                setEndDate(today.toISOString().slice(0, 10));
              }}
              className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm"
            >
              هذا الشهر
            </button>
          </div>

          {/* Custom Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">من تاريخ</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">إلى تاريخ</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <div className="mt-3 flex justify-center">
            <button
              onClick={fetchReport}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
            >
              <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
              عرض التقرير
            </button>
          </div>
        </div>

        {/* Report Summary */}
        <div className="mb-4 bg-blue-50 p-3 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-blue-800">
              {reportType === 'attendance' ? 'تقرير الحضور' : 
               reportType === 'leaves' ? 'تقرير الإجازات' : 'تقرير الزيارات الخارجية'}
            </span>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-blue-700">الفترة: {startDate} إلى {endDate}</span>
              <span className="text-sm text-blue-700">عدد السجلات: {reportData.length}</span>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الموظف
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    التاريخ
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    التفاصيل
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الحالة
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reportData.map((item, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.user_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.date}
                    </td>
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
                         item.status === 'absent' ? 'غائب' :
                         'معلق'}
                      </span>
                      {reportType === 'attendance' && item.is_late && (
                        <span className="ml-2 px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-800">
                          متأخر
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {!loading && reportData.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">لا توجد بيانات في هذه الفترة</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Activity Logs Component (Super Admin only)
const ActivityLogs = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().slice(0, 10));
  const [error, setError] = useState('');
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchActivities();
  }, [selectedDate]);

  const fetchActivities = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(`${API}/activity-logs?date=${selectedDate}`);
      setActivities(response.data || []);
    } catch (error) {
      console.error('Error fetching activities:', error);
      setError(error.response?.data?.detail || 'حدث خطأ في تحميل سجل الأنشطة');
      setActivities([]);
    } finally {
      setLoading(false);
    }
  };

  // Check if user is super admin
  if (user?.name !== "Hatem Mohamed Ahmed") {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-800 mb-2">وصول مقيد</h2>
          <p className="text-gray-600">هذه الصفحة مخصصة للسوبر آدمن فقط</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">جاري تحميل سجل الأنشطة...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-800 mb-2">خطأ في التحميل</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchActivities}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            إعادة المحاولة
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center">
            <DocumentTextIcon className="h-6 w-6 text-blue-600 ml-2" />
            <h2 className="text-xl font-bold text-gray-800">سجل الأنشطة - TANSEEQ Tax Consultancy</h2>
          </div>
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">اختر التاريخ</label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            <div className="text-sm text-gray-600 mt-6">
              إجمالي الأنشطة: <strong className="text-blue-600">{activities.length}</strong>
            </div>
          </div>
        </div>
        
        {activities.length === 0 ? (
          <div className="text-center py-16">
            <DocumentTextIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-800 mb-2">لا توجد أنشطة</h3>
            <p className="text-gray-600 mb-4">لم يتم العثور على أنشطة في التاريخ المحدد: {selectedDate}</p>
            <button
              onClick={() => setSelectedDate(new Date().toISOString().slice(0, 10))}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
            >
              العودة لتاريخ اليوم
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الوقت
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    المستخدم
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    النشاط
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    التفاصيل
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {activities.map((activity, index) => (
                  <tr key={activity.id || index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex flex-col">
                        <span className="font-medium">
                          {new Date(activity.timestamp).toLocaleTimeString('ar-AE', {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit'
                          })}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(activity.timestamp).toLocaleDateString('ar-AE')}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center">
                        <UserIcon className="h-4 w-4 text-gray-400 ml-2" />
                        <span className="text-gray-900">{activity.user_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        activity.action.includes('login') ? 'bg-green-100 text-green-800' :
                        activity.action.includes('logout') ? 'bg-red-100 text-red-800' :
                        activity.action.includes('check') ? 'bg-blue-100 text-blue-800' :
                        activity.action.includes('approved') ? 'bg-green-100 text-green-800' :
                        activity.action.includes('rejected') ? 'bg-red-100 text-red-800' :
                        activity.action.includes('created') ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {activity.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      <div className="max-w-xs">
                        <p className="truncate" title={activity.details}>
                          {activity.details}
                        </p>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Export Options */}
        <div className="mt-6 flex justify-between items-center border-t pt-4">
          <div className="text-sm text-gray-600">
            آخر تحديث: {new Date().toLocaleString('ar-AE')}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={fetchActivities}
              className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 text-sm flex items-center"
            >
              <ArrowPathIcon className="h-4 w-4 ml-2" />
              تحديث
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Leaves Management Component
const Leaves = () => {
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showImageModal, setShowImageModal] = useState(false);
  const [selectedImage, setSelectedImage] = useState('');
  const [formData, setFormData] = useState({
    start_date: '',
    end_date: '',
    reason: '',
    days_count: 1,
    file: null
  });
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchLeaves();
  }, []);

  const fetchLeaves = async () => {
    try {
      const response = await axios.get(`${API}/leaves`);
      setLeaves(response.data);
    } catch (error) {
      console.error('Error fetching leaves:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const formDataToSend = new FormData();
    formDataToSend.append('user_id', user.id);
    formDataToSend.append('user_name', user.name);
    formDataToSend.append('start_date', formData.start_date);
    formDataToSend.append('end_date', formData.end_date);
    formDataToSend.append('reason', formData.reason);
    formDataToSend.append('days_count', formData.days_count);
    
    if (formData.file) {
      formDataToSend.append('file', formData.file);
    }
    
    try {
      await axios.post(`${API}/leaves`, formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setShowModal(false);
      setFormData({
        start_date: '',
        end_date: '',
        reason: '',
        days_count: 1,
        file: null
      });
      fetchLeaves();
    } catch (error) {
      console.error('Error creating leave request:', error);
    }
  };

  const handleApprove = async (id) => {
    try {
      await axios.post(`${API}/leaves/${id}/approve`);
      fetchLeaves();
    } catch (error) {
      console.error('Error approving leave:', error);
    }
  };

  const handleReject = async (id) => {
    try {
      await axios.post(`${API}/leaves/${id}/reject`);
      fetchLeaves();
    } catch (error) {
      console.error('Error rejecting leave:', error);
    }
  };

  const handleImageClick = (imageUrl) => {
    setSelectedImage(imageUrl);
    setShowImageModal(true);
  };

  const calculateDays = () => {
    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      const timeDiff = end.getTime() - start.getTime();
      const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24)) + 1;
      setFormData({...formData, days_count: daysDiff > 0 ? daysDiff : 1});
    }
  };

  useEffect(() => {
    calculateDays();
  }, [formData.start_date, formData.end_date]);

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">طلبات الإجازات</h2>
          {user?.role === 'user' && (
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <PlusIcon className="h-4 w-4 inline mr-2" />
              طلب إجازة
            </button>
          )}
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الموظف
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  تاريخ البداية
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  تاريخ النهاية
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  عدد الأيام
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  السبب
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  المرفق
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحالة
                </th>
                {user?.role !== 'user' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الإجراءات
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {leaves.map((leave) => (
                <tr key={leave.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {leave.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.start_date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.end_date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.days_count} يوم
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.reason}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {leave.attachment_url ? (
                      <button
                        onClick={() => handleImageClick(`${BACKEND_URL}${leave.attachment_url}`)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      leave.status === 'approved' ? 'bg-green-100 text-green-800' :
                      leave.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {leave.status === 'approved' ? 'موافق عليه' : 
                       leave.status === 'rejected' ? 'مرفوض' : 'معلق'}
                    </span>
                  </td>
                  {user?.role !== 'user' && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {leave.status === 'pending' && (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleApprove(leave.id)}
                            className="text-green-600 hover:text-green-900"
                            title="Approve"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleReject(leave.id)}
                            className="text-red-600 hover:text-red-900"
                            title="Reject"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Leave Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                طلب إجازة
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    تاريخ البداية
                  </label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    تاريخ النهاية
                  </label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    عدد الأيام: {formData.days_count}
                  </label>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    السبب
                  </label>
                  <textarea
                    value={formData.reason}
                    onChange={(e) => setFormData({...formData, reason: e.target.value})}
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="اكتب سبب الإجازة..."
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    المرفق (شهادة طبية/عذر رسمي)
                  </label>
                  <input
                    type="file"
                    accept="image/*,.pdf"
                    onChange={(e) => setFormData({...formData, file: e.target.files[0]})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex space-x-2">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  >
                    إرسال الطلب
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  >
                    إلغاء
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Image Modal */}
      {showImageModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-3/4 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  المرفق
                </h3>
                <button
                  onClick={() => setShowImageModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XIcon className="h-6 w-6" />
                </button>
              </div>
              <div className="text-center">
                <img
                  src={selectedImage}
                  alt="Leave attachment"
                  className="max-w-full max-h-96 object-contain mx-auto"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ============ SUPER ADMIN: CREATE REQUESTS ON BEHALF OF EMPLOYEES ============

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

// ============ ADMIN: ATTACHMENT VIEWING CAPABILITY ============

const AttachmentViewer = () => {
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAttachment, setSelectedAttachment] = useState(null);
  const [viewerModal, setViewerModal] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    fetchAttachments();
  }, []);

  const fetchAttachments = async () => {
    try {
      const response = await axios.get(`${API}/admin/attachments-list`);
      setAttachments(response.data.attachments);
    } catch (error) {
      console.error('Error fetching attachments:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewAttachment = async (requestType, requestId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/view-attachment/${requestType}/${requestId}`);
      setSelectedAttachment(response.data);
      setViewerModal(true);
    } catch (error) {
      console.error('Error viewing attachment:', error);
      alert('حدث خطأ في عرض المرفق');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'غير محدد';
    return new Date(dateString).toLocaleDateString('ar-SA');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'approved': return 'موافق عليه';
      case 'rejected': return 'مرفوض';
      case 'pending': return 'في الانتظار';
      default: return status;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">جاري التحميل...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-gray-800">عرض مرفقات الطلبات</h2>
          <div className="bg-purple-50 px-3 py-1 rounded-lg">
            <span className="text-sm text-purple-700 font-medium">Admin/Super Admin</span>
          </div>
        </div>

        {attachments.length === 0 ? (
          <div className="text-center py-8">
            <FolderIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">لا توجد طلبات بمرفقات</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    نوع الطلب
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الموظف
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    التواريخ
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    السبب/الغرض
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الحالة
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    تاريخ الطلب
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الإجراءات
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {attachments.map((attachment) => (
                  <tr key={`${attachment.request_type}-${attachment.request_id}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        attachment.request_type === 'leave' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {attachment.request_type === 'leave' ? 'إجازة' : 'زيارة خارجية'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {attachment.employee_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {attachment.date_range}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {attachment.reason}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(attachment.status)}`}>
                        {getStatusText(attachment.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(attachment.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => viewAttachment(attachment.request_type, attachment.request_id)}
                        className="text-blue-600 hover:text-blue-900 flex items-center"
                      >
                        <EyeIcon className="h-4 w-4 mr-1" />
                        عرض المرفق
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Attachment Viewer Modal */}
      {viewerModal && selectedAttachment && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-4xl max-h-screen overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                عرض مرفق - {selectedAttachment.employee_name}
              </h3>
              <button
                onClick={() => setViewerModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="mb-4 text-sm text-gray-600">
              <p><strong>نوع الطلب:</strong> {selectedAttachment.request_type === 'leave' ? 'إجازة' : 'زيارة خارجية'}</p>
              <p><strong>اسم الملف:</strong> {selectedAttachment.file_name}</p>
              <p><strong>حجم الملف:</strong> {Math.round(selectedAttachment.file_size / 1024)} KB</p>
              <p><strong>تاريخ الإنشاء:</strong> {formatDate(selectedAttachment.created_at)}</p>
            </div>

            <div className="border rounded-lg p-4 bg-gray-50">
              {selectedAttachment.mime_type.startsWith('image/') ? (
                <img
                  src={selectedAttachment.file_data}
                  alt={selectedAttachment.file_name}
                  className="max-w-full max-h-96 object-contain mx-auto"
                />
              ) : (
                <div className="text-center py-8">
                  <DocumentTextIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">معاينة غير متاحة لهذا النوع من الملفات</p>
                  <a
                    href={selectedAttachment.file_data}
                    download={selectedAttachment.file_name}
                    className="mt-2 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                    تحميل الملف
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Enhanced Backup Management Component for Admin/Super Admin
const BackupManagement = () => {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      fetchBackups();
    }
  }, [user]);

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/backup/list-files`);
      setBackups(response.data.backup_files || []);
    } catch (error) {
      console.error('Error fetching backups:', error);
      setMessage({ type: 'error', text: 'حدث خطأ في تحميل قائمة النسخ الاحتياطية' });
    } finally {
      setLoading(false);
    }
  };

  const createBackup = async () => {
    try {
      setLoading(true);
      setMessage('');
      const response = await axios.post(`${API}/backup/create-download`);
      
      setMessage({ 
        type: 'success', 
        text: `تم إنشاء النسخة الاحتياطية وحفظها على الخادم بنجاح: ${response.data.filename}` 
      });
      
      // Refresh backup list to show new backup
      await fetchBackups();
      
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في إنشاء النسخة الاحتياطية' 
      });
    } finally {
      setLoading(false);
    }
  };

  const downloadBackup = async (filename) => {
    try {
      const response = await axios.get(`${API}/backup/download/${filename}`, {
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data]);
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(link.href);
      
      setMessage({ type: 'success', text: `تم تحميل ${filename} بنجاح` });
      
    } catch (error) {
      console.error('Download error:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في تحميل الملف' 
      });
    }
  };

  const deleteBackup = async (filename) => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      `هل أنت متأكد من حذف النسخة الاحتياطية؟\n\n${filename}\n\nلا يمكن التراجع عن هذا الإجراء!`
    );

    if (!confirmed) return;

    try {
      await axios.delete(`${API}/backup/delete/${filename}`);
      
      setMessage({ 
        type: 'success', 
        text: `تم حذف ${filename} بنجاح` 
      });
      
      // Refresh backup list
      fetchBackups();
      
    } catch (error) {
      console.error('Delete error:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في حذف الملف' 
      });
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Show confirmation dialog
    const confirmed = window.confirm(
      `⚠️ تحذير مهم!\n\nسيتم حذف جميع البيانات الموجودة حالياً واستبدالها بالبيانات من الملف:\n${file.name}\n\nهل أنت متأكد من المتابعة؟\n\nهذا الإجراء لا يمكن التراجع عنه!`
    );

    if (!confirmed) {
      event.target.value = ''; // Reset file input
      return;
    }

    try {
      setUploadLoading(true);
      setMessage('');

      const formData = new FormData();
      formData.append('backup_file', file);

      const response = await axios.post(`${API}/backup/restore`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setMessage({ 
        type: 'success', 
        text: `تم استعادة النسخة الاحتياطية بنجاح من ${file.name}` 
      });

      // Refresh backup list
      await fetchBackups();

    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في استعادة النسخة الاحتياطية' 
      });
    } finally {
      setUploadLoading(false);
      event.target.value = ''; // Reset file input
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ar-SA', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (user?.role !== 'admin' && user?.role !== 'super_admin') {
    return (
      <div className="text-center py-8">
        <ExclamationCircleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
        <p className="text-gray-500">هذه الصفحة متاحة للإدارة فقط</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-gray-800">إدارة النسخ الاحتياطية</h2>
          <div className="bg-purple-50 px-3 py-1 rounded-lg">
            <span className="text-sm text-purple-700 font-medium">Admin/Super Admin</span>
          </div>
        </div>

        {message && (
          <div className={`p-4 mb-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {message.text}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 mb-6">
          <button
            onClick={createBackup}
            disabled={loading || uploadLoading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center"
          >
            {loading ? (
              <ArrowPathIcon className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            )}
            📥 إنشاء نسخة احتياطية
          </button>

          <label className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 cursor-pointer flex items-center">
            {uploadLoading ? (
              <ArrowPathIcon className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
            )}
            📤 استعادة من نسخة احتياطية
            <input
              type="file"
              accept=".json,.zip"
              onChange={handleFileUpload}
              disabled={loading || uploadLoading}
              className="hidden"
            />
          </label>

          <button
            onClick={fetchBackups}
            disabled={loading || uploadLoading}
            className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 disabled:bg-gray-400 flex items-center"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            تحديث القائمة
          </button>
        </div>

        {/* Warning Box */}
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700">
                <strong>تحذير:</strong> عملية استعادة النسخة الاحتياطية ستحذف جميع البيانات الموجودة حالياً وتستبدلها بالبيانات من الملف المرفوع. تأكد من إنشاء نسخة احتياطية قبل الاستعادة.
              </p>
            </div>
          </div>
        </div>

        {/* Backups List */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-md font-medium text-gray-800 mb-4">النسخ الاحتياطية المتاحة</h3>
          
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-600">جاري التحميل...</span>
            </div>
          ) : backups.length === 0 ? (
            <div className="text-center py-8">
              <FolderIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">لا توجد نسخ احتياطية متاحة</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      اسم الملف
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      الحجم
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      تاريخ الإنشاء
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      الحالة
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      الإجراءات
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {backups.map((backup, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <DocumentIcon className="h-5 w-5 text-blue-500 mr-2" />
                          {backup.filename}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatFileSize(backup.size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(backup.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          متاح
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-3">
                          <button
                            onClick={() => downloadBackup(backup.filename)}
                            className="text-blue-600 hover:text-blue-900 flex items-center"
                          >
                            <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
                            تحميل JSON
                          </button>
                          <button
                            onClick={() => downloadBackup(backup.filename.replace('.json', '.zip'))}
                            className="text-green-600 hover:text-green-900 flex items-center"
                          >
                            <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
                            تحميل ZIP
                          </button>
                          <button
                            onClick={() => deleteBackup(backup.filename)}
                            className="text-red-600 hover:text-red-900 flex items-center"
                          >
                            <TrashIcon className="h-4 w-4 mr-1" />
                            حذف
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Statistics */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <FolderIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">إجمالي النسخ</p>
                <p className="text-2xl font-bold text-gray-900">{backups.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <ServerIcon className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">إجمالي الحجم</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatFileSize(backups.reduce((total, backup) => total + backup.size, 0))}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">آخر نسخة</p>
                <p className="text-lg font-bold text-gray-900">
                  {backups.length > 0 ? formatDate(backups[0].created_at) : 'لا يوجد'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Overtime Report Component for Admin/Super Admin
const OvertimeReport = () => {
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [overtimeData, setOvertimeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { user } = useAuth();

  const fetchOvertimeReport = async () => {
    try {
      setLoading(true);
      setMessage('');
      const response = await axios.get(`${API}/overtime-reports/${selectedMonth}`);
      setOvertimeData(response.data);
      
      if (response.data.total_records === 0) {
        setMessage({ 
          type: 'info', 
          text: 'لا توجد ساعات عمل إضافية مسجلة في هذا الشهر' 
        });
      }
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في تحميل تقرير العمل الإضافي' 
      });
      setOvertimeData(null);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async (format) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/overtime-reports/export/${selectedMonth}?format=${format}`, {
        responseType: 'blob'
      });

      const blob = new Blob([response.data]);
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `TANSEEQ_overtime_report_${selectedMonth}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setMessage({ type: 'success', text: `تم تصدير التقرير بصيغة ${format.toUpperCase()} بنجاح` });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في تصدير التقرير' 
      });
    } finally {
      setLoading(false);
    }
  };

  const getOvertimeTypeColor = (type) => {
    switch (type) {
      case 'Early Start': return 'bg-blue-100 text-blue-800';
      case 'Late Finish': return 'bg-orange-100 text-orange-800';
      case 'Mixed': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getOvertimeTypeText = (type) => {
    switch (type) {
      case 'Early Start': return 'بداية مبكرة';
      case 'Late Finish': return 'انتهاء متأخر';
      case 'Mixed': return 'مختلط';
      default: return type;
    }
  };

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      fetchOvertimeReport();
    }
  }, [selectedMonth, user]);

  if (user?.role !== 'admin' && user?.role !== 'super_admin') {
    return (
      <div className="text-center py-8">
        <ExclamationCircleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
        <p className="text-gray-500">هذه الصفحة متاحة للإدارة فقط</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-gray-800">⏰ تقرير العمل الإضافي (Overtime Report)</h2>
          <div className="bg-green-50 px-3 py-1 rounded-lg">
            <span className="text-sm text-green-700 font-medium">Admin/Super Admin</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">الشهر</label>
            <input
              type="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex space-x-2">
            <button
              onClick={fetchOvertimeReport}
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex items-center"
            >
              {loading ? <ArrowPathIcon className="h-4 w-4 animate-spin mr-2" /> : <MagnifyingGlassIcon className="h-4 w-4 mr-2" />}
              عرض التقرير
            </button>

            <button
              onClick={() => exportReport('excel')}
              disabled={loading || !overtimeData}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400 flex items-center"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Excel
            </button>

            <button
              onClick={() => exportReport('pdf')}
              disabled={loading || !overtimeData}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:bg-gray-400 flex items-center"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              PDF
            </button>
          </div>
        </div>

        {message && (
          <div className={`p-4 mb-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 
            message.type === 'error' ? 'bg-red-50 text-red-700' : 
            'bg-blue-50 text-blue-700'
          }`}>
            {message.text}
          </div>
        )}

        {/* Statistics */}
        {overtimeData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center">
                <ClockIcon className="h-8 w-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-blue-600">إجمالي السجلات</p>
                  <p className="text-2xl font-bold text-blue-900">{overtimeData.total_records}</p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center">
                <UserGroupIcon className="h-8 w-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-green-600">عدد الموظفين</p>
                  <p className="text-2xl font-bold text-green-900">{overtimeData.total_employees}</p>
                </div>
              </div>
            </div>

            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="flex items-center">
                <ClockIcon className="h-8 w-8 text-orange-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-orange-600">إجمالي الساعات الإضافية</p>
                  <p className="text-2xl font-bold text-orange-900">{overtimeData.total_overtime_hours}h</p>
                </div>
              </div>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center">
                <CalculatorIcon className="h-8 w-8 text-purple-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-purple-600">المتوسط/موظف</p>
                  <p className="text-2xl font-bold text-purple-900">
                    {overtimeData.total_employees > 0 ? (overtimeData.total_overtime_hours / overtimeData.total_employees).toFixed(1) : '0'}h
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Overtime Records Table */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-500" />
            <span className="ml-2 text-gray-600">جاري تحميل التقرير...</span>
          </div>
        ) : overtimeData && overtimeData.overtime_records.length > 0 ? (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-md font-medium text-gray-800 mb-4">تفاصيل العمل الإضافي</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الموظف</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">التاريخ</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الحضور</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الانصراف</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">إجمالي الساعات</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">ساعات مبكرة</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">ساعات متأخرة</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">إجمالي إضافي</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">النوع</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {overtimeData.overtime_records.map((record, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {record.employee_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {record.date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {record.check_in_time}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {record.check_out_time}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span className="font-medium">{record.total_working_hours}h</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-medium">
                        {record.early_overtime_hours}h
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-600 font-medium">
                        {record.late_overtime_hours}h
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-bold">
                        {record.total_overtime_hours}h
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getOvertimeTypeColor(record.overtime_type)}`}>
                          {getOvertimeTypeText(record.overtime_type)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {/* Info Box */}
        <div className="mt-6 bg-blue-50 border-l-4 border-blue-400 p-4">
          <div className="flex">
            <InformationCircleIcon className="h-5 w-5 text-blue-400" />
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                <strong>ملاحظة:</strong> يتم حساب العمل الإضافي بناءً على ساعات العمل الرسمية (9:00 صباحاً - 6:00 مساءً). 
                أي وقت قبل 9:00 صباحاً أو بعد 6:00 مساءً يُحسب كساعات إضافية، حتى للموظفين ذوي العمل المرن.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;