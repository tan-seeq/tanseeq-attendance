import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  CurrencyDollarIcon,
  DocumentTextIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  EyeIcon,
  UserIcon,
  CalendarIcon,
  BanknotesIcon,
  ArrowUpIcon,
  ArrowDownIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdvancesDashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    myBalance: null,
    recentTransactions: [],
    pendingApprovals: []
  });
  const [userRole, setUserRole] = useState('user');

  useEffect(() => {
    // Get user role from token or user object
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUserRole(payload.role || 'user');
      } catch (error) {
        console.error('Error parsing token:', error);
      }
    }
    
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch user's balance
      const balanceRes = await axios.get(`${API}/advances/my-balance`);
      
      // Fetch recent transactions
      const transactionsRes = await axios.get(`${API}/advances/my-transactions?limit=5`);
      
      let pendingApprovals = [];
      // Fetch pending approvals if super admin
      if (userRole === 'super_admin') {
        try {
          const pendingRes = await axios.get(`${API}/advances/admin/pending-approvals`);
          pendingApprovals = pendingRes.data.pending_transactions || [];
        } catch (error) {
          console.error('Error fetching pending approvals:', error);
        }
      }

      setStats({
        myBalance: balanceRes.data,
        recentTransactions: transactionsRes.data.transactions || [],
        pendingApprovals
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return `${amount?.toFixed(2) || '0.00'} درهم`;
  };

  const getTransactionTypeColor = (type) => {
    switch (type) {
      case 'advance': return 'bg-blue-100 text-blue-800';
      case 'custody': return 'bg-green-100 text-green-800';
      case 'expense': return 'bg-red-100 text-red-800';
      case 'return': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="mb-8">
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">💰 إدارة السُلف والعُهد</h1>
              <p className="text-blue-100">نظام إدارة السلف والمصروفات للموظفين</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-full p-4">
              <BanknotesIcon className="h-12 w-12 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Balance Summary */}
      {stats.myBalance && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-r from-blue-100 to-blue-200 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700 font-medium">إجمالي السُلف</p>
                <p className="text-2xl font-bold text-blue-800">
                  {formatCurrency(stats.myBalance.total_advances)}
                </p>
              </div>
              <div className="bg-blue-600 p-3 rounded-full">
                <ArrowUpIcon className="h-6 w-6 text-white" />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-green-100 to-green-200 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700 font-medium">إجمالي العُهد</p>
                <p className="text-2xl font-bold text-green-800">
                  {formatCurrency(stats.myBalance.total_custody)}
                </p>
              </div>
              <div className="bg-green-600 p-3 rounded-full">
                <BanknotesIcon className="h-6 w-6 text-white" />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-red-100 to-red-200 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-700 font-medium">إجمالي المصروفات</p>
                <p className="text-2xl font-bold text-red-800">
                  {formatCurrency(stats.myBalance.total_expenses)}
                </p>
              </div>
              <div className="bg-red-600 p-3 rounded-full">
                <ArrowDownIcon className="h-6 w-6 text-white" />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-purple-100 to-purple-200 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-700 font-medium">الرصيد المتاح</p>
                <p className="text-2xl font-bold text-purple-800">
                  {formatCurrency(stats.myBalance.total_available)}
                </p>
              </div>
              <div className="bg-purple-600 p-3 rounded-full">
                <CurrencyDollarIcon className="h-6 w-6 text-white" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions - Row 1: Request Actions */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">📝 طلبات جديدة</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <button
            onClick={() => setShowRequestAdvanceModal(true)}
            className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border-2 border-transparent hover:border-blue-200"
          >
            <div className="text-center">
              <div className="bg-blue-100 p-4 rounded-full inline-block mb-3">
                <ArrowUpIcon className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">طلب سلفة</h3>
              <p className="text-sm text-gray-600">طلب سلفة جديدة من الإدارة</p>
            </div>
          </button>

          <button
            onClick={() => setShowRequestCustodyModal(true)}
            className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border-2 border-transparent hover:border-green-200"
          >
            <div className="text-center">
              <div className="bg-green-100 p-4 rounded-full inline-block mb-3">
                <BanknotesIcon className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">طلب عهدة</h3>
              <p className="text-sm text-gray-600">طلب عهدة جديدة من الإدارة</p>
            </div>
          </button>

          <button
            onClick={() => setShowSettleCustodyModal(true)}
            disabled={!stats.myBalance || stats.myBalance.remaining_custody <= 0}
            className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border-2 border-transparent hover:border-purple-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="text-center">
              <div className="bg-purple-100 p-4 rounded-full inline-block mb-3">
                <CheckCircleIcon className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">تسوية عهدة</h3>
              <p className="text-sm text-gray-600">رد العهدة المستلمة</p>
            </div>
          </button>
        </div>
      </div>

      {/* Quick Actions - Row 2: View Actions */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">📊 عرض البيانات</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <button
            onClick={() => navigate('/advances/submit-expense')}
            className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border-2 border-transparent hover:border-red-200"
          >
            <div className="text-center">
              <div className="bg-red-100 p-4 rounded-full inline-block mb-3">
                <DocumentTextIcon className="h-8 w-8 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">تقديم مصروف</h3>
              <p className="text-sm text-gray-600">رفع فاتورة وطلب خصم من الرصيد</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/advances/my-transactions')}
            className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border-2 border-transparent hover:border-indigo-200"
          >
            <div className="text-center">
              <div className="bg-indigo-100 p-4 rounded-full inline-block mb-3">
                <ChartBarIcon className="h-8 w-8 text-indigo-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">سجل المعاملات</h3>
              <p className="text-sm text-gray-600">عرض جميع السلف والمصروفات</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/advances/balance-details')}
            className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border-2 border-transparent hover:border-teal-200"
          >
            <div className="text-center">
              <div className="bg-teal-100 p-4 rounded-full inline-block mb-3">
                <CurrencyDollarIcon className="h-8 w-8 text-teal-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">تفاصيل الرصيد</h3>
              <p className="text-sm text-gray-600">عرض تفصيلي للأرصدة المتاحة</p>
            </div>
          </button>

          {userRole === 'super_admin' && (
            <button
              onClick={() => navigate('/advances/admin')}
              className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border-2 border-transparent hover:border-orange-200"
            >
              <div className="text-center">
                <div className="bg-orange-100 p-4 rounded-full inline-block mb-3">
                  <UserIcon className="h-8 w-8 text-orange-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">لوحة الإدارة</h3>
                <p className="text-sm text-gray-600">إدارة السلف والموافقات</p>
              </div>
            </button>
          )}
        </div>
      </div>

      {/* Pending Approvals (Super Admin Only) */}
      {userRole === 'super_admin' && stats.pendingApprovals.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-800 flex items-center">
              <ExclamationTriangleIcon className="h-6 w-6 text-orange-600 ml-2" />
              طلبات الموافقة المعلقة ({stats.pendingApprovals.length})
            </h3>
            <button
              onClick={() => navigate('/advances/admin')}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              عرض الكل ←
            </button>
          </div>
          
          <div className="space-y-4">
            {stats.pendingApprovals.slice(0, 3).map((transaction) => (
              <div key={transaction.id} className="border border-orange-200 rounded-lg p-4 bg-orange-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="bg-orange-100 p-2 rounded-full">
                      <DocumentTextIcon className="h-5 w-5 text-orange-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">{transaction.employee_name}</p>
                      <p className="text-sm text-gray-600">{transaction.description}</p>
                      <p className="text-xs text-gray-500">{transaction.created_at_display}</p>
                    </div>
                  </div>
                  <div className="text-left">
                    <p className="text-lg font-bold text-orange-600">
                      {formatCurrency(transaction.amount)}
                    </p>
                    <p className="text-sm text-gray-600">{transaction.category_ar}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Transactions */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-800 flex items-center">
            <ClockIcon className="h-6 w-6 text-blue-600 ml-2" />
            المعاملات الأخيرة
          </h3>
          <button
            onClick={() => navigate('/advances/my-transactions')}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            عرض الكل ←
          </button>
        </div>

        {stats.recentTransactions.length > 0 ? (
          <div className="space-y-4">
            {stats.recentTransactions.map((transaction) => (
              <div key={transaction.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {transaction.transaction_type === 'expense' ? (
                        <ArrowDownIcon className="h-6 w-6 text-red-600" />
                      ) : (
                        <ArrowUpIcon className="h-6 w-6 text-green-600" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTransactionTypeColor(transaction.transaction_type)}`}>
                          {transaction.transaction_type_ar}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(transaction.status)}`}>
                          {transaction.status_ar}
                        </span>
                      </div>
                      <p className="font-semibold text-gray-800">{transaction.description}</p>
                      <p className="text-sm text-gray-600">{transaction.created_at_display}</p>
                      {transaction.category_ar && (
                        <p className="text-xs text-gray-500">{transaction.category_ar}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-left">
                    <p className={`text-lg font-bold ${
                      transaction.transaction_type === 'expense' ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {transaction.transaction_type === 'expense' ? '-' : '+'}{formatCurrency(transaction.amount)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <DocumentTextIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">لا توجد معاملات حتى الآن</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancesDashboard;