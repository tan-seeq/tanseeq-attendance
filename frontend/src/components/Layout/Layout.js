import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  UserIcon, ClockIcon, CalendarDaysIcon as CalendarIcon, DocumentTextIcon,
  DocumentIcon, CurrencyDollarIcon, ChartBarIcon,
  ArrowRightOnRectangleIcon as LogoutIcon,
  Bars3Icon as MenuIcon, XMarkIcon as XIcon,
  UserGroupIcon, ExclamationTriangleIcon, BellIcon,
  Cog6ToothIcon, ServerIcon, ShieldCheckIcon,
  CalculatorIcon, BuildingOfficeIcon, BanknotesIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API } from '../../config';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [openSections, setOpenSections] = useState({});
  const { user, logout } = useAuth();
  const { t, isRTL, toggleLanguage } = useLanguage();
  const navigate = useNavigate();

  // القوائم الرئيسية والفرعية المنظمة
  const navigation = [
    { name: 'الرئيسية', href: '/dashboard', icon: ChartBarIcon },
    
    // قسم الموظفين - للجميع
    { name: 'الحضور', href: '/attendance', icon: ClockIcon },
    { name: 'الإجازات', href: '/leaves', icon: CalendarIcon },
    { name: 'الزيارات الخارجية', href: '/field-exits', icon: DocumentTextIcon },
    { name: 'الزيارات التسويقية', href: '/marketing-visits', icon: BuildingOfficeIcon },
    { name: 'السُلف والعُهد', href: '/advances', icon: BanknotesIcon }, // NEW: للموظفين
    { name: 'خصوماتي', href: '/my-deductions', icon: CalculatorIcon },
    
    // قسم الإدارة - للمديرين والسوبر أدمن
    ...(user?.role === 'admin' || user?.role === 'super_admin' ? [
      { name: 'الموظفين', href: '/employees', icon: UserGroupIcon },
      { name: 'إدارة الحضور', href: '/attendance-management', icon: ClockIcon },
      { name: 'إدارة الإجازات', href: '/leave-management', icon: CalendarIcon },
      { name: 'إدارة الزيارات الخارجية', href: '/field-exit-management', icon: DocumentTextIcon },
      { name: 'إدارة العملاء', href: '/work-reports/clients', icon: UserGroupIcon },
    ] : []),
    
    // قسم الرواتب والخصومات - Super Admin فقط
    ...(user?.role === 'super_admin' ? [
      { 
        name: '💰 الرواتب والخصومات', 
        isSection: true,
        icon: CurrencyDollarIcon,
        children: [
          { name: 'إدارة دورات الرواتب', href: '/payroll-cycles', icon: CurrencyDollarIcon },
          { name: 'كشف الرواتب', href: '/payroll', icon: BanknotesIcon },
          { name: 'سجل قيود الرواتب', href: '/payroll-ledger', icon: DocumentTextIcon },
          { name: 'نظام الخصومات المتقدم', href: '/attendance-deductions', icon: ExclamationTriangleIcon },
          { name: 'إدارة السُلف والعُهد', href: '/advances/admin', icon: BanknotesIcon },
          { name: 'جدولة الأقساط', href: '/installment-schedules', icon: CalendarIcon },
        ]
      },
    ] : []),
    
    // قسم التقارير - Super Admin فقط
    ...(user?.role === 'super_admin' ? [
      { 
        name: '📊 التقارير', 
        isSection: true,
        icon: ChartBarIcon,
        children: [
          { name: 'لوحة التحكم التحليلية', href: '/hr-dashboard', icon: ChartBarIcon },
          { name: 'تقرير الحضور والإنصراف', href: '/reports/attendance', icon: ClockIcon },
          { name: 'تقارير الخصومات الشهرية', href: '/reports/deductions', icon: ExclamationTriangleIcon },
          { name: 'نظام الخصومات المتقدم', href: '/reports/advanced-deductions', icon: ExclamationTriangleIcon },
          { name: 'تقارير السُلف والأقساط', href: '/reports/advances', icon: BanknotesIcon },
          { name: 'تقارير الرواتب', href: '/reports', icon: DocumentTextIcon },
          { name: 'تقارير الإجازات', href: '/leave-management', icon: CalendarIcon },
        ]
      },
    ] : []),
    
    // قسم النظام - Super Admin فقط
    ...(user?.role === 'super_admin' ? [
      { name: 'نظام الإشعارات', href: '/notifications', icon: BellIcon },
      { name: 'قسائم الرواتب والبريد', href: '/salary-slips', icon: DocumentIcon },
      { name: 'إدارة النسخ الاحتياطية', href: '/backup-management', icon: ServerIcon },
      { name: 'إعدادات النظام', href: '/admin/config', icon: Cog6ToothIcon },
      { name: 'المراقبة المباشرة', href: '/admin/live', icon: ChartBarIcon },
      { name: 'صحة النظام', href: '/system-health', icon: ShieldCheckIcon },
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

  const location = useLocation();
  const isActive = (href) => location.pathname === href;

  return (
    <div className={`min-h-screen bg-gray-100 ${isRTL ? 'rtl' : 'ltr'}`}>
      {/* Sidebar */}
      <div className={`fixed inset-y-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out ${isRTL ? 'right-0' : 'left-0'} ${sidebarOpen ? 'translate-x-0' : isRTL ? 'translate-x-full' : '-translate-x-full'} lg:translate-x-0 flex flex-col`}>
        <div className="flex items-center justify-between p-4 border-b flex-shrink-0">
          <h1 className="text-xl font-bold text-gray-800">TANSEEQ</h1>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden"
          >
            <XIcon className="h-6 w-6" />
          </button>
        </div>
        
        <nav className="flex-1 overflow-y-auto overflow-x-hidden py-4" style={{scrollbarWidth: 'thin', scrollbarColor: '#CBD5E0 transparent'}}>
          <div className="px-4 space-y-1">
            {navigation.map((item) => {
              // قائمة فرعية (section مع children)
              if (item.isSection && item.children) {
                const isOpen = openSections[item.name];
                return (
                  <div key={item.name} className="space-y-1">
                    <button
                      onClick={() => setOpenSections(prev => ({ ...prev, [item.name]: !prev[item.name] }))}
                      className="w-full flex items-center justify-between px-4 py-3 text-sm font-bold rounded-lg transition-colors duration-200 text-right bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800"
                    >
                      <div className="flex items-center">
                        <item.icon className={`h-5 w-5 ${isRTL ? 'ml-3' : 'mr-3'} flex-shrink-0`} />
                        <span className="truncate">{item.name}</span>
                      </div>
                      <svg
                        className={`h-4 w-4 transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {isOpen && (
                      <div className="mr-4 space-y-1 border-r-2 border-blue-200 pr-2">
                        {item.children.map((child) => (
                          <button
                            key={child.name}
                            onClick={() => navigate(child.href)}
                            className={`w-full flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200 text-right ${isActive(child.href) ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}`}
                            data-testid={`nav-${child.href}`}
                          >
                            <child.icon className={`h-4 w-4 ${isRTL ? 'ml-2' : 'mr-2'} flex-shrink-0`} />
                            <span className="truncate text-xs">{child.name}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              }
              
              // قائمة عادية (بدون children)
              return (
                <button
                  key={item.name}
                  onClick={() => navigate(item.href)}
                  className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors duration-200 text-right ${isActive(item.href) ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'}`}
                  data-testid={`nav-${item.href}`}
                >
                  <item.icon className={`h-5 w-5 ${isRTL ? 'ml-3' : 'mr-3'} flex-shrink-0`} />
                  <span className="truncate">{item.name}</span>
                </button>
              );
            })}
          </div>
          {/* مساحة فارغة كبيرة في الأسفل لضمان ظهور جميع القوائم */}
          <div className="h-20 flex-shrink-0"></div>
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

export default Layout;
