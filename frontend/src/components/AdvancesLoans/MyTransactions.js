import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  DocumentTextIcon,
  CurrencyDollarIcon,
  EyeIcon,
  CalendarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  FunnelIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';
import AttachmentViewer from '../AttachmentViewer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MyTransactions = () => {
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  const [balance, setBalance] = useState(null);
  
  // Filter states
  const [filters, setFilters] = useState({
    type: 'all',
    status: 'all',
    category: 'all',
    dateFrom: '',
    dateTo: ''
  });

  // Modal states
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  // Categories with Arabic translations
  const expenseCategories = {
    transportation: 'مواصلات',
    meals: 'وجبات',
    accommodation: 'إقامة',
    supplies: 'لوازم مكتبية',
    fuel: 'وقود',
    maintenance: 'صيانة',
    client_entertainment: 'ضيافة عملاء',
    travel: 'سفر',
    communications: 'اتصالات',
    other: 'أخرى'
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [transactions, filters]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch transactions and balance
      const [transactionsRes, balanceRes] = await Promise.all([
        axios.get(`${API}/advances/my-transactions?limit=100`),
        axios.get(`${API}/advances/my-balance`)
      ]);

      setTransactions(transactionsRes.data.transactions || []);
      setBalance(balanceRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...transactions];

    // Filter by type
    if (filters.type !== 'all') {
      filtered = filtered.filter(t => t.transaction_type === filters.type);
    }

    // Filter by status
    if (filters.status !== 'all') {
      filtered = filtered.filter(t => t.status === filters.status);
    }

    // Filter by category
    if (filters.category !== 'all') {
      filtered = filtered.filter(t => t.category === filters.category);
    }

    // Filter by date range
    if (filters.dateFrom) {
      filtered = filtered.filter(t => {
        const transactionDate = new Date(t.created_at).toISOString().split('T')[0];
        return transactionDate >= filters.dateFrom;
      });
    }

    if (filters.dateTo) {
      filtered = filtered.filter(t => {
        const transactionDate = new Date(t.created_at).toISOString().split('T')[0];
        return transactionDate <= filters.dateTo;
      });
    }

    setFilteredTransactions(filtered);
  };

  const resetFilters = () => {
    setFilters({
      type: 'all',
      status: 'all',
      category: 'all',
      dateFrom: '',
      dateTo: ''
    });
  };

  const viewTransactionDetails = (transaction) => {
    setSelectedTransaction(transaction);
    setShowDetailsModal(true);
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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved': return CheckCircleIcon;
      case 'pending': return ClockIcon;
      case 'rejected': return XCircleIcon;
      default: return ExclamationTriangleIcon;
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
        <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 text-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">📊 سجل المعاملات</h1>
              <p className="text-indigo-100">عرض تفصيلي لجميع السلف والمصروفات</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-full p-4">
              <DocumentTextIcon className="h-12 w-12 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Balance Summary */}
      {balance && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-r from-blue-100 to-blue-200 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700 font-medium">إجمالي السُلف</p>
                <p className="text-xl font-bold text-blue-800">
                  {formatCurrency(balance.total_advances)}
                </p>
              </div>
              <div className="bg-blue-600 p-3 rounded-full">
                <ArrowUpIcon className="h-5 w-5 text-white" />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-green-100 to-green-200 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700 font-medium">إجمالي العُهد</p>
                <p className="text-xl font-bold text-green-800">
                  {formatCurrency(balance.total_custody)}
                </p>
              </div>
              <div className="bg-green-600 p-3 rounded-full">
                <ArrowUpIcon className="h-5 w-5 text-white" />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-red-100 to-red-200 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-700 font-medium">إجمالي المصروفات</p>
                <p className="text-xl font-bold text-red-800">
                  {formatCurrency(balance.total_expenses)}
                </p>
              </div>
              <div className="bg-red-600 p-3 rounded-full">
                <ArrowDownIcon className="h-5 w-5 text-white" />
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-purple-100 to-purple-200 p-6 rounded-xl shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-700 font-medium">الرصيد المتاح</p>
                <p className="text-xl font-bold text-purple-800">
                  {formatCurrency(balance.total_available)}
                </p>
              </div>
              <div className="bg-purple-600 p-3 rounded-full">
                <CurrencyDollarIcon className="h-5 w-5 text-white" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters Section */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center">
            <FunnelIcon className="h-5 w-5 text-gray-600 ml-2" />
            تصفية المعاملات
          </h3>
          <div className="flex space-x-2">
            <button
              onClick={resetFilters}
              className="text-gray-600 hover:text-gray-800 text-sm"
            >
              إعادة تعيين
            </button>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-md hover:bg-indigo-200 text-sm"
            >
              {showFilters ? 'إخفاء الفلاتر' : 'إظهار الفلاتر'}
            </button>
          </div>
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">نوع المعاملة</label>
              <select
                value={filters.type}
                onChange={(e) => setFilters({...filters, type: e.target.value})}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="all">جميع الأنواع</option>
                <option value="advance">سُلفة</option>
                <option value="custody">عُهدة</option>
                <option value="expense">مصروف</option>
                <option value="return">إرجاع</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">الحالة</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({...filters, status: e.target.value})}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="all">جميع الحالات</option>
                <option value="pending">معلق</option>
                <option value="approved">معتمد</option>
                <option value="rejected">مرفوض</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">التصنيف</label>
              <select
                value={filters.category}
                onChange={(e) => setFilters({...filters, category: e.target.value})}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="all">جميع التصنيفات</option>
                {Object.entries(expenseCategories).map(([key, value]) => (
                  <option key={key} value={key}>{value}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">من تاريخ</label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => setFilters({...filters, dateFrom: e.target.value})}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">إلى تاريخ</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => setFilters({...filters, dateTo: e.target.value})}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>
        )}

        {/* Results Summary */}
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm text-gray-600">
            عرض <span className="font-semibold">{filteredTransactions.length}</span> من أصل <span className="font-semibold">{transactions.length}</span> معاملة
          </p>
        </div>
      </div>

      {/* Transactions List */}
      <div className="bg-white rounded-xl shadow-lg">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">المعاملات</h3>
        </div>

        <div className="p-6">
          {filteredTransactions.length > 0 ? (
            <div className="space-y-4">
              {filteredTransactions.map((transaction) => {
                const StatusIcon = getStatusIcon(transaction.status);
                return (
                  <div key={transaction.id} className="border border-gray-200 rounded-lg p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0">
                          <div className={`p-3 rounded-full ${
                            transaction.transaction_type === 'expense' ? 'bg-red-100' : 'bg-green-100'
                          }`}>
                            {transaction.transaction_type === 'expense' ? (
                              <ArrowDownIcon className="h-6 w-6 text-red-600" />
                            ) : (
                              <ArrowUpIcon className="h-6 w-6 text-green-600" />
                            )}
                          </div>
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTransactionTypeColor(transaction.transaction_type)}`}>
                              {transaction.transaction_type_ar}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(transaction.status)}`}>
                              <div className="flex items-center space-x-1">
                                <StatusIcon className="h-4 w-4" />
                                <span>{transaction.status_ar}</span>
                              </div>
                            </span>
                            {transaction.category_ar && (
                              <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                                {transaction.category_ar}
                              </span>
                            )}
                          </div>
                          <h3 className="text-lg font-semibold text-gray-800 mb-1">{transaction.description}</h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <div className="flex items-center">
                              <CalendarIcon className="h-4 w-4 ml-1" />
                              <span>{transaction.created_at_display}</span>
                            </div>
                            {transaction.expense_date && (
                              <div className="flex items-center">
                                <span>تاريخ المصروف: {transaction.expense_date}</span>
                              </div>
                            )}
                            {transaction.attachments && transaction.attachments.length > 0 && (
                              <div className="flex items-center text-blue-600">
                                <DocumentTextIcon className="h-4 w-4 ml-1" />
                                <span>{transaction.attachments.length} مرفق(ات)</span>
                              </div>
                            )}
                          </div>
                          {transaction.notes && (
                            <p className="text-sm text-gray-500 mt-2">
                              ملاحظات: {transaction.notes}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-left">
                          <p className={`text-2xl font-bold ${
                            transaction.transaction_type === 'expense' ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {transaction.transaction_type === 'expense' ? '-' : '+'}{formatCurrency(transaction.amount)}
                          </p>
                        </div>
                        <button
                          onClick={() => viewTransactionDetails(transaction)}
                          className="bg-indigo-100 text-indigo-700 px-4 py-2 rounded-md hover:bg-indigo-200 transition-colors flex items-center space-x-1"
                        >
                          <EyeIcon className="h-4 w-4" />
                          <span>التفاصيل</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12">
              <DocumentTextIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-600 mb-2">لا توجد معاملات</h3>
              <p className="text-gray-500">
                {transactions.length === 0 ? 
                  'لم تقم بأي معاملات حتى الآن' : 
                  'لا توجد معاملات تطابق الفلاتر المحددة'
                }
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Transaction Details Modal */}
      {showDetailsModal && selectedTransaction && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-full max-w-3xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900">تفاصيل المعاملة</h3>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {/* Transaction Info */}
              <div className="bg-gray-50 p-6 rounded-lg mb-6">
                <div className="grid grid-cols-2 gap-6 text-sm">
                  <div><span className="font-medium">نوع المعاملة:</span> {selectedTransaction.transaction_type_ar}</div>
                  <div><span className="font-medium">الحالة:</span> {selectedTransaction.status_ar}</div>
                  <div><span className="font-medium">المبلغ:</span> {formatCurrency(selectedTransaction.amount)}</div>
                  <div><span className="font-medium">التاريخ:</span> {selectedTransaction.created_at_display}</div>
                  {selectedTransaction.category_ar && (
                    <div><span className="font-medium">التصنيف:</span> {selectedTransaction.category_ar}</div>
                  )}
                  {selectedTransaction.expense_date && (
                    <div><span className="font-medium">تاريخ المصروف:</span> {selectedTransaction.expense_date}</div>
                  )}
                </div>
                
                <div className="mt-4">
                  <span className="font-medium">الوصف:</span>
                  <p className="text-gray-600 mt-1">{selectedTransaction.description}</p>
                </div>
                
                {selectedTransaction.notes && (
                  <div className="mt-4">
                    <span className="font-medium">الملاحظات:</span>
                    <p className="text-gray-600 mt-1">{selectedTransaction.notes}</p>
                  </div>
                )}
              </div>

              {/* Attachments */}
              {selectedTransaction.attachments && selectedTransaction.attachments.length > 0 && (
                <div className="bg-blue-50 p-6 rounded-lg mb-6">
                  <h4 className="font-semibold text-gray-800 mb-4 flex items-center">
                    <DocumentTextIcon className="h-5 w-5 text-blue-600 ml-2" />
                    المرفقات ({selectedTransaction.attachments.length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedTransaction.attachments.map((attachment, index) => (
                      <div key={index} className="flex items-center justify-between bg-white p-4 rounded border">
                        <div className="flex items-center">
                          <div className="bg-blue-100 p-2 rounded ml-3">
                            <DocumentTextIcon className="h-5 w-5 text-blue-600" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-800">{attachment.original_filename}</p>
                            <p className="text-xs text-gray-500">
                              {(attachment.file_size / 1024).toFixed(1)} KB
                            </p>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => window.open(`${API}/advances/attachment/${selectedTransaction.id}/${attachment.id}`, '_blank')}
                            className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                          >
                            <EyeIcon className="h-4 w-4 ml-1" />
                            عرض
                          </button>
                          <button
                            onClick={() => {
                              const link = document.createElement('a');
                              link.href = `${API}/advances/attachment/${selectedTransaction.id}/${attachment.id}`;
                              link.download = attachment.original_filename;
                              link.click();
                            }}
                            className="text-green-600 hover:text-green-800 text-sm flex items-center"
                          >
                            <ArrowDownTrayIcon className="h-4 w-4 ml-1" />
                            تحميل
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Close Button */}
              <div className="flex justify-end">
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  إغلاق
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyTransactions;