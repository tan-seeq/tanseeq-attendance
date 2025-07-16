import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import jwt_decode from 'jwt-decode';
import { 
  UserIcon, 
  ClockIcon, 
  CalendarDaysIcon as CalendarIcon, 
  DocumentTextIcon, 
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
  MagnifyingGlassIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import './App.css';

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
      { name: t('payroll'), href: '/payroll', icon: CurrencyDollarIcon },
    ] : []),
    ...(user?.role === 'super_admin' ? [
      { name: t('activity_logs'), href: '/activity-logs', icon: DocumentTextIcon },
    ] : []),
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
  const [stats, setStats] = useState({
    totalEmployees: 0,
    presentToday: 0,
    pendingLeaves: 0,
    pendingFieldExits: 0,
    todayAttendance: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

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
          <button className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 transform hover:-translate-y-1">
            <ClockIcon className="h-8 w-8 mx-auto mb-2" />
            <p className="font-semibold">تسجيل الحضور</p>
          </button>
          
          <button className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 transform hover:-translate-y-1">
            <CalendarIcon className="h-8 w-8 mx-auto mb-2" />
            <p className="font-semibold">طلب إجازة</p>
          </button>
          
          <button className="bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white p-4 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 transform hover:-translate-y-1">
            <DocumentTextIcon className="h-8 w-8 mx-auto mb-2" />
            <p className="font-semibold">زيارة خارجية</p>
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 text-center text-gray-500">
        <p className="text-sm">
          نظام إدارة الموارد البشرية - TANSEEQ Tax Consultancy © 2025
        </p>
      </div>
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
    start_time: '',
    end_time: '',
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
      await axios.post(`${API}/field-exits`, {
        ...formData,
        user_id: user.id,
        user_name: user.name
      });
      
      setShowModal(false);
      setFormData({
        visit_type: 'client_visit',
        client_name: '',
        start_time: '',
        end_time: '',
        report: ''
      });
      fetchFieldExits();
    } catch (error) {
      console.error('Error creating field exit:', error);
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
                  وقت البداية
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  وقت النهاية
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
                    {exit.start_time}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {exit.end_time}
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
                  {user?.role !== 'user' && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {exit.status === 'pending' && (
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
                    </td>
                  )}
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
                    وقت البداية
                  </label>
                  <input
                    type="time"
                    value={formData.start_time}
                    onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    وقت النهاية
                  </label>
                  <input
                    type="time"
                    value={formData.end_time}
                    onChange={(e) => setFormData({...formData, end_time: e.target.value})}
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
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="اكتب تفاصيل الزيارة..."
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
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
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
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchAllAttendance();
  }, []);

  const fetchAllAttendance = async () => {
    try {
      const response = await axios.get(`${API}/attendance/all`);
      setAttendance(response.data);
    } catch (error) {
      console.error('Error fetching attendance:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (record) => {
    setEditingRecord(record.id);
    setEditData({
      check_in: record.check_in,
      check_out: record.check_out,
      status: record.status
    });
  };

  const handleSave = async (id) => {
    try {
      await axios.put(`${API}/attendance/${id}`, editData);
      setEditingRecord(null);
      fetchAllAttendance();
    } catch (error) {
      console.error('Error updating attendance:', error);
    }
  };

  const handleCancel = () => {
    setEditingRecord(null);
    setEditData({});
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4 text-gray-800">إدارة الحضور - TANSEEQ Tax Consultancy</h2>
        
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
                {user?.name === "Hatem Mohamed Ahmed" && (
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
                      record.check_in || '--'
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
                      record.check_out || '--'
                    )}
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
                  {user?.name === "Hatem Mohamed Ahmed" && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {editingRecord === record.id ? (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleSave(record.id)}
                            className="text-green-600 hover:text-green-900"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={handleCancel}
                            className="text-red-600 hover:text-red-900"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleEdit(record)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Leave Management Component (Admin)
const LeaveManagement = () => {
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showImageModal, setShowImageModal] = useState(false);
  const [selectedImage, setSelectedImage] = useState('');
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

  const handleApprove = async (id) => {
    try {
      await axios.post(`${API}/leaves/${id}/approve`);
      fetchAllLeaves();
    } catch (error) {
      console.error('Error approving leave:', error);
    }
  };

  const handleReject = async (id) => {
    try {
      await axios.post(`${API}/leaves/${id}/reject`);
      fetchAllLeaves();
    } catch (error) {
      console.error('Error rejecting leave:', error);
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

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

  const handleApprove = async (id) => {
    try {
      await axios.post(`${API}/field-exits/${id}/approve`);
      fetchAllFieldExits();
    } catch (error) {
      console.error('Error approving field exit:', error);
    }
  };

  const handleReject = async (id) => {
    try {
      await axios.post(`${API}/field-exits/${id}/reject`);
      fetchAllFieldExits();
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
                  وقت البداية
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  وقت النهاية
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  تقرير الزيارة
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
                    {exit.date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {visitTypeOptions[exit.visit_type]}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {exit.client_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {exit.start_time}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {exit.end_time}
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
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {exit.status === 'pending' && (
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
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchActivities();
  }, [selectedDate]);

  const fetchActivities = async () => {
    try {
      const response = await axios.get(`${API}/activity-logs?date=${selectedDate}`);
      setActivities(response.data);
    } catch (error) {
      console.error('Error fetching activities:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">سجل الأنشطة - TANSEEQ Tax Consultancy</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">التاريخ</label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        
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
              {activities.map((activity) => (
                <tr key={activity.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(activity.timestamp).toLocaleTimeString('ar')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {activity.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {activity.action}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {activity.details}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {activities.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">لا توجد أنشطة في هذا التاريخ</p>
          </div>
        )}
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

export default App;