import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  CurrencyDollarIcon,
  UserIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  PlusIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  BanknotesIcon,
  ChartBarIcon,
  CalendarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import AttachmentViewer from '../AttachmentViewer';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pending');
  const [data, setData] = useState({
    pendingApprovals: [],
    allBalances: [],
    allTransactions: [],
    users: []
  });
  const [employeesWithBalances, setEmployeesWithBalances] = useState([]); // NEW: للموظفين الذين لديهم رصيد نشط
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTransactionModal, setShowTransactionModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [approving, setApproving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showRepayModal, setShowRepayModal] = useState(false);
  const [repayForm, setRepayForm] = useState({ employee_id: '', amount: '', repayment_date: new Date().toISOString().split('T')[0], method: 'cash', reference: '', notes: '', salary_month: '' });


  // Create advance/custody form
  const [createForm, setCreateForm] = useState({
    employee_id: '',
    transaction_type: 'advance',
    amount: '',
    description: '',
    category: '',
    notes: ''
  });

  // Approval form
  const [approvalForm, setApprovalForm] = useState({
    status: 'approved',
    notes: ''
  });

  // Edit form
  const [editForm, setEditForm] = useState({
    amount: '',
    description: '',
    notes: ''
  });

  useEffect(() => {
    fetchDashboardData();
    fetchEmployeesWithBalances(); // NEW: جلب الموظفين الذين لديهم رصيد نشط
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch all data in parallel
      const [pendingRes, balancesRes, transactionsRes, usersRes] = await Promise.all([
        axios.get(`${API}/advances/admin/pending-approvals`),
        axios.get(`${API}/advances/admin/all-balances`),
        axios.get(`${API}/advances/admin/all-transactions`),
        axios.get(`${API}/users`)
      ]);

      setData({
        pendingApprovals: pendingRes.data.pending_transactions || [],
        allBalances: balancesRes.data.employee_balances || [],
        allTransactions: transactionsRes.data.transactions || [],
        users: usersRes.data || []
      });
    } catch (error) {
      console.error('Error fetching admin dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // NEW: جلب الموظفين الذين لديهم رصيد سلف/عهد نشط
  const fetchEmployeesWithBalances = async () => {
    try {
      const response = await axios.get(`${API}/advances/admin/employees-with-balances`);
      setEmployeesWithBalances(response.data.employees || []);
    } catch (error) {
      console.error('Error fetching employees with balances:', error);
    }
  };

  const handleCreateAdvance = async (e) => {
    e.preventDefault();
    
    // Comprehensive validation
    if (!createForm.employee_id || createForm.employee_id === '') {
      alert('يرجى اختيار الموظف');
      return;
    }
    
    if (!createForm.transaction_type || createForm.transaction_type === '') {
      alert('يرجى اختيار نوع المعاملة');
      return;
    }
    
    if (!createForm.amount || parseFloat(createForm.amount) <= 0) {
      alert('يرجى إدخال مبلغ صحيح');
      return;
    }
    
    if (!createForm.description || createForm.description.trim().length < 5) {
      alert('يرجى إدخال وصف لا يقل عن 5 أحرف');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const requestData = {
        employee_id: createForm.employee_id,
        transaction_type: createForm.transaction_type,
        amount: parseFloat(createForm.amount),
        description: createForm.description,
        notes: createForm.notes
      };
      
      console.log('Sending advance create request:', requestData);
      
      const response = await axios.post(`${API}/advances/create`, requestData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('Create advance response:', response.data);
      
      // Check if the response indicates success
      if (response.data && response.data.success === true) {
        alert('تم إنشاء السلفة/العهدة بنجاح!');
        setShowCreateModal(false);
        setCreateForm({
          employee_id: '',
          transaction_type: 'advance',
          amount: '',
          description: '',
          category: '',
          notes: ''
        });
        fetchDashboardData();
      } else {
        // If success is not true, show the error message from the response
        const message = response.data?.message || 'حدث خطأ غير متوقع';
        alert(`خطأ في إنشاء السلفة/العهدة: ${message}`);
      }
    } catch (error) {
      console.error('Error creating advance:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || 'خطأ غير معروف';
      alert(`حدث خطأ في إنشاء السلفة/العهدة: ${errorMessage}`);
    }
  };

  const handleApproval = async (transactionId, decision) => {
    try {
      setApproving(true);
      
      await axios.post(`${API}/advances/${transactionId}/approve`, {
        status: decision,
        notes: approvalForm.notes
      });

      alert(`تم ${decision === 'approved' ? 'قبول' : 'رفض'} الطلب بنجاح!`);
      setShowTransactionModal(false);
      setSelectedTransaction(null);
      setApprovalForm({ status: 'approved', notes: '' });
      fetchDashboardData();
    } catch (error) {
      console.error('Error processing approval:', error);
      alert('حدث خطأ في معالجة الطلب');
    } finally {
      setApproving(false);
    }
  };

  const viewTransactionDetails = (transaction) => {
    setSelectedTransaction(transaction);
    setShowTransactionModal(true);
  };

  const openEditModal = (transaction) => {
    setSelectedTransaction(transaction);
    setEditForm({
      amount: transaction.amount,
      description: transaction.description,
      notes: transaction.notes || ''
    });
    setShowEditModal(true);
  };

  const handleEditTransaction = async (e) => {
    e.preventDefault();
    
    if (!editForm.amount || parseFloat(editForm.amount) <= 0) {
      alert('يرجى إدخال مبلغ صحيح');
      return;
    }
    
    if (!editForm.description || editForm.description.trim().length < 5) {
      alert('يرجى إدخال وصف لا يقل عن 5 أحرف');
      return;
    }

    try {
      setEditing(true);
      
      await axios.put(`${API}/advances/${selectedTransaction.id}/edit`, {
        amount: parseFloat(editForm.amount),
        description: editForm.description,
        notes: editForm.notes
      });

      alert('تم تعديل المعاملة بنجاح!');
      setShowEditModal(false);
      setSelectedTransaction(null);
      setEditForm({ amount: '', description: '', notes: '' });
      fetchDashboardData();
    } catch (error) {
      console.error('Error editing transaction:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || 'خطأ غير معروف';
      alert(`حدث خطأ في تعديل المعاملة: ${errorMessage}`);
    } finally {
      setEditing(false);
    }
  };

  const handleDeleteTransaction = async (transactionId, transactionName) => {
    const confirmDelete = window.confirm(
      `هل أنت متأكد من حذف هذه المعاملة؟\n${transactionName}\n\nلا يمكن التراجع عن هذا الإجراء.`
    );
    
    if (!confirmDelete) {
      return;
    }

    try {
      setDeleting(true);
      
      await axios.delete(`${API}/advances/${transactionId}`);

      alert('تم حذف المعاملة بنجاح!');
      fetchDashboardData();
    } catch (error) {
      console.error('Error deleting transaction:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || 'خطأ غير معروف';
      alert(`حدث خطأ في حذف المعاملة: ${errorMessage}`);
    } finally {
      setDeleting(false);
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
      case 'advance_settlement': return 'bg-indigo-100 text-indigo-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
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
        <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">👑 لوحة إدارة السُلف والعُهد</h1>
              <p className="text-purple-100">إدارة شاملة لسلف الموظفين والموافقات</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-full p-4">
              <UserIcon className="h-12 w-12 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-r from-orange-100 to-orange-200 p-6 rounded-xl shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-orange-700 font-medium">طلبات معلقة</p>
              <p className="text-2xl font-bold text-orange-800">
                {data.pendingApprovals.length}
              </p>
            </div>
            <div className="bg-orange-600 p-3 rounded-full">
              <ExclamationTriangleIcon className="h-6 w-6 text-white" />
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-100 to-blue-200 p-6 rounded-xl shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-700 font-medium">إجمالي الموظفين</p>
              <p className="text-2xl font-bold text-blue-800">
                {data.allBalances.length}
              </p>
            </div>
            <div className="bg-blue-600 p-3 rounded-full">
              <UserIcon className="h-6 w-6 text-white" />
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-100 to-green-200 p-6 rounded-xl shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-700 font-medium">إجمالي السُلف النشطة</p>
              <p className="text-2xl font-bold text-green-800">
                {formatCurrency(
                  data.allBalances.reduce((sum, emp) => sum + (emp.remaining_advance || 0), 0)
                )}
              </p>
            </div>
            <div className="bg-green-600 p-3 rounded-full">
              <ArrowUpIcon className="h-6 w-6 text-white" />
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-100 to-purple-200 p-6 rounded-xl shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-700 font-medium">إجمالي العُهد النشطة</p>
              <p className="text-2xl font-bold text-purple-800">
                {formatCurrency(
                  data.allBalances.reduce((sum, emp) => sum + (emp.remaining_custody || 0), 0)
                )}
              </p>
            </div>
            <div className="bg-purple-600 p-3 rounded-full">
              <BanknotesIcon className="h-6 w-6 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      {/* Repay Button Modal Trigger */}
      <button
        onClick={() => {
          if (employeesWithBalances.length === 0) {
            return alert('لا يوجد موظفون لديهم أرصدة نشطة');
          }
          const firstEmployee = employeesWithBalances[0];
          setSelectedTransaction({ 
            employee_id: firstEmployee.employee_id, 
            employee_name: firstEmployee.employee_name 
          });
          setRepayForm({ 
            employee_id: firstEmployee.employee_id, 
            amount: '', 
            repayment_date: new Date().toISOString().split('T')[0], 
            method: 'cash', 
            reference: '', 
            notes: '', 
            salary_month: '' 
          });
          setShowRepayModal(true);
        }}
        className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2"
      >
        <span>تسجيل سداد</span>
      </button>

      <div className="flex flex-wrap gap-4 mb-8">
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>إنشاء سُلفة/عُهدة جديدة</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-lg">
        <div className="border-b border-gray-200">
          <nav className="flex">
            <button
              onClick={() => setActiveTab('pending')}
              className={`px-6 py-4 text-sm font-medium border-b-2 ${
                activeTab === 'pending'
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              طلبات الموافقة ({data.pendingApprovals.length})
            </button>
            <button
              onClick={() => setActiveTab('balances')}
              className={`px-6 py-4 text-sm font-medium border-b-2 ${
                activeTab === 'balances'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              أرصدة الموظفين ({data.allBalances.length})
            </button>
            <button
              onClick={() => setActiveTab('transactions')}
              className={`px-6 py-4 text-sm font-medium border-b-2 ${
                activeTab === 'transactions'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              جميع المعاملات ({data.allTransactions.length})
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* Pending Approvals Tab */}
          {activeTab === 'pending' && (
            <div>
              {data.pendingApprovals.length > 0 ? (
                <div className="space-y-4">
                  {data.pendingApprovals.map((transaction) => (
                    <div key={transaction.id} className="border border-orange-200 rounded-lg p-6 bg-orange-50 hover:bg-orange-100 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="bg-orange-100 p-3 rounded-full">
                            <DocumentTextIcon className="h-6 w-6 text-orange-600" />
                          </div>
                          <div>
                            <div className="flex items-center space-x-2 mb-2">
                              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTransactionTypeColor(transaction.transaction_type)}`}>
                                {transaction.transaction_type_ar}
                              </span>
                              {transaction.category_ar && (
                                <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                                  {transaction.category_ar}
                                </span>
                              )}
                            </div>
                            <h3 className="text-lg font-semibold text-gray-800">{transaction.employee_name}</h3>
                            <p className="text-gray-600 mb-1">{transaction.description}</p>
                            <p className="text-sm text-gray-500">{transaction.created_at_display}</p>
                            {transaction.attachments && transaction.attachments.length > 0 && (
                              <p className="text-xs text-blue-600 mt-1">
                                📎 {transaction.attachments.length} مرفق(ات)
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-center">
                            <p className="text-2xl font-bold text-orange-600">
                              {formatCurrency(transaction.amount)}
                            </p>
                          </div>
                          <div className="flex flex-col space-y-2">
                            <button
                              onClick={() => viewTransactionDetails(transaction)}
                              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-1"
                            >
                              <EyeIcon className="h-4 w-4" />
                              <span>عرض التفاصيل</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <CheckCircleIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-600 mb-2">لا توجد طلبات معلقة</h3>
                  <p className="text-gray-500">جميع الطلبات تم معالجتها بنجاح!</p>
                </div>
              )}
            </div>
          )}

          {/* Employee Balances Tab */}
          {activeTab === 'balances' && (
            <div>
              {data.allBalances.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          الموظف
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          إجمالي السُلف
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          إجمالي العُهد
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          المصروفات
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          السُلف المتبقية
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          العُهد المتبقية
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          آخر معاملة
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {data.allBalances.map((employee) => (
                        <tr key={employee.employee_id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="bg-blue-100 p-2 rounded-full ml-3">
                                <UserIcon className="h-5 w-5 text-blue-600" />
                              </div>
                              <div>
                                <div className="text-sm font-medium text-gray-900">
                                  {employee.employee_name}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                            {formatCurrency(employee.total_advances)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                            {formatCurrency(employee.total_custody)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-medium">
                            {formatCurrency(employee.total_expenses)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-bold">
                            {formatCurrency(employee.remaining_advance)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-bold">
                            {formatCurrency(employee.remaining_custody)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {employee.last_transaction_date ? 
                              new Date(employee.last_transaction_date).toLocaleDateString('ar-SA') : 
                              'لا يوجد'
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12">
                  <UserIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">لا توجد أرصدة للموظفين</p>
                </div>
              )}
            </div>
          )}

          {/* All Transactions Tab */}
          {activeTab === 'transactions' && (
            <div>
              {data.allTransactions.length > 0 ? (
                <div className="space-y-4">
                  {data.allTransactions.map((transaction) => (
                    <div key={transaction.id} className="border border-gray-200 rounded-lg p-6 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="flex-shrink-0">
                            <div className={`p-3 rounded-full ${
                              transaction.transaction_type === 'expense' ? 'bg-red-100' : 
                              transaction.transaction_type === 'advance_settlement' ? 'bg-purple-100' : 'bg-green-100'
                            }`}>
                              {transaction.transaction_type === 'expense' ? (
                                <ArrowDownIcon className="h-6 w-6 text-red-600" />
                              ) : transaction.transaction_type === 'advance_settlement' ? (
                                <CalendarIcon className="h-6 w-6 text-purple-600" />
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
                                {transaction.status_ar}
                              </span>
                              {transaction.category_ar && (
                                <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                                  {transaction.category_ar}
                                </span>
                              )}
                            </div>
                            <h3 className="text-lg font-semibold text-gray-800 mb-1">
                              {transaction.employee_name}
                            </h3>
                            <p className="text-gray-600 mb-1">{transaction.description}</p>
                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                              <div className="flex items-center">
                                <CalendarIcon className="h-4 w-4 ml-1" />
                                <span>{transaction.created_at_display}</span>
                              </div>
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
                              transaction.transaction_type === 'expense' ? 'text-red-600' : 
                              transaction.transaction_type === 'advance_settlement' ? 'text-purple-600' : 'text-green-600'
                            }`}>
                              {transaction.transaction_type === 'expense' || transaction.transaction_type === 'advance_settlement' ? '-' : '+'}{formatCurrency(transaction.amount)}
                            </p>
                          </div>
                          <div className="flex flex-col space-y-2">
                            <button
                              onClick={() => viewTransactionDetails(transaction)}
                              className="bg-blue-100 text-blue-700 px-4 py-2 rounded-md hover:bg-blue-200 transition-colors flex items-center space-x-1"
                            >
                              <EyeIcon className="h-4 w-4" />
                              <span>التفاصيل</span>
                            </button>
                            {/* Edit button - Available for ALL transactions (حتى بعد الموافقة) */}
                            <button
                              onClick={() => openEditModal(transaction)}
                              className="bg-yellow-100 text-yellow-700 px-4 py-2 rounded-md hover:bg-yellow-200 transition-colors flex items-center space-x-1"
                              title="تعديل المعاملة"
                            >
                              <PencilIcon className="h-4 w-4" />
                              <span>تعديل</span>
                            </button>
                            {/* Delete button - Available for ALL transactions (حتى بعد الموافقة) */}
                            <button
                              onClick={() => handleDeleteTransaction(transaction.id, `${transaction.transaction_type_ar} - ${transaction.employee_name}`)}
                              disabled={deleting}
                              className="bg-red-100 text-red-700 px-4 py-2 rounded-md hover:bg-red-200 transition-colors flex items-center space-x-1 disabled:opacity-50"
                              title="حذف المعاملة"
                            >
                              <TrashIcon className="h-4 w-4" />
                              <span>حذف</span>
                            </button>
                            {/* Add installment schedule button for approved advances/custody */}
                            {transaction.status === 'approved' && 
                             ['advance', 'custody'].includes(transaction.transaction_type) && (
                              <button
                                onClick={() => window.location.href = '/installment-schedules'}
                                className="bg-green-100 text-green-700 px-4 py-2 rounded-md hover:bg-green-200 transition-colors flex items-center space-x-1"
                                title="إنشاء جدولة أقساط"
                              >
                                <CalendarIcon className="h-4 w-4" />
                                <span>جدولة أقساط</span>
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <DocumentTextIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-600 mb-2">لا توجد معاملات</h3>
                  <p className="text-gray-500">لم يتم العثور على أي معاملات في النظام</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create Advance Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">إنشاء سُلفة أو عُهدة جديدة</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateAdvance} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    الموظف *
                  </label>
                  <select
                    value={createForm.employee_id}
                    onChange={(e) => setCreateForm({...createForm, employee_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">اختر الموظف</option>
                    {data.users.map(user => (
                      <option key={user.id} value={user.id}>{user.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    نوع المعاملة *
                  </label>
                  <select
                    value={createForm.transaction_type}
                    onChange={(e) => setCreateForm({...createForm, transaction_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="advance">سُلفة</option>
                    <option value="custody">عُهدة</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    المبلغ (بالدرهم) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={createForm.amount}
                    onChange={(e) => setCreateForm({...createForm, amount: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    الوصف *
                  </label>
                  <textarea
                    value={createForm.description}
                    onChange={(e) => setCreateForm({...createForm, description: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="اكتب وصف المعاملة..."
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ملاحظات إضافية
                  </label>
                  <textarea
                    value={createForm.notes}
                    onChange={(e) => setCreateForm({...createForm, notes: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={2}
                    placeholder="ملاحظات اختيارية..."
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    إلغاء
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    إنشاء
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
      {/* Repay Modal */}
      {showRepayModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">تسجيل سداد سُلفة/عُهدة</h3>
                <button onClick={() => setShowRepayModal(false)} className="text-gray-400 hover:text-gray-600">✕</button>
              </div>
              
              <form onSubmit={async (e) => {
                e.preventDefault();
                try {
                  const token = localStorage.getItem('token');
                  const payload = {
                    employee_id: repayForm.employee_id,
                    amount: parseFloat(repayForm.amount),
                    repayment_date: repayForm.repayment_date,
                    method: repayForm.method || undefined,
                    reference: repayForm.reference || undefined,
                    notes: repayForm.notes || undefined
                  };
                  if (!payload.employee_id) return alert('يرجى اختيار الموظف');
                  if (!payload.amount || payload.amount <= 0) return alert('يرجى إدخال مبلغ صحيح');
                  if (!payload.repayment_date) return alert('يرجى تحديد تاريخ السداد');

                  const res = await axios.post(`${API}/advances/repay`, payload, {
                    headers: { Authorization: `Bearer ${token}` }
                  });
                  if (res.data?.success) {
                    alert('✅ تم تسجيل السداد بنجاح');
                    setShowRepayModal(false);
                    setRepayForm({ 
                      employee_id: '',
                      amount: '', 
                      repayment_date: new Date().toISOString().split('T')[0], 
                      method: 'cash', 
                      reference: '', 
                      notes: '' 
                    });
                    fetchDashboardData();
                    fetchEmployeesWithBalances(); // تحديث قائمة الموظفين
                  } else {
                    alert(res.data?.message || 'حدث خطأ في تسجيل السداد');
                  }
                } catch (err) {
                  console.error('Repay error', err);
                  alert(err.response?.data?.detail || 'حدث خطأ في تسجيل السداد');
                }
              }} className="space-y-4">
                
                {/* NEW: Dropdown لاختيار الموظف */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الموظف *</label>
                  <select 
                    value={repayForm.employee_id} 
                    onChange={(e) => {
                      const selectedEmp = employeesWithBalances.find(emp => emp.employee_id === e.target.value);
                      setRepayForm({...repayForm, employee_id: e.target.value});
                      setSelectedTransaction({
                        employee_id: e.target.value,
                        employee_name: selectedEmp?.employee_name || ''
                      });
                    }}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  >
                    <option value="">-- اختر الموظف --</option>
                    {employeesWithBalances.map(emp => (
                      <option key={emp.employee_id} value={emp.employee_id}>
                        {emp.employee_name} (رصيد: {(emp.total_remaining || 0).toFixed(2)} درهم)
                      </option>
                    ))}
                  </select>
                </div>
                
                {/* عرض تفاصيل الرصيد للموظف المختار */}
                {repayForm.employee_id && (() => {
                  const selectedEmp = employeesWithBalances.find(emp => emp.employee_id === repayForm.employee_id);
                  return selectedEmp ? (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">رصيد السُلف:</span>
                          <span className="font-bold text-blue-600 mr-2">{(selectedEmp.remaining_advance || 0).toFixed(2)} درهم</span>
                        </div>
                        <div>
                          <span className="text-gray-600">رصيد العُهد:</span>
                          <span className="font-bold text-green-600 mr-2">{(selectedEmp.remaining_custody || 0).toFixed(2)} درهم</span>
                        </div>
                      </div>
                    </div>
                  ) : null;
                })()}
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">المبلغ *</label>
                  <input type="number" step="0.01" value={repayForm.amount} onChange={(e) => setRepayForm({...repayForm, amount: e.target.value})} className="w-full px-3 py-2 border rounded-md" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">تاريخ السداد *</label>
                  <input type="date" value={repayForm.repayment_date} onChange={(e) => setRepayForm({...repayForm, repayment_date: e.target.value})} className="w-full px-3 py-2 border rounded-md" required />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">طريقة السداد</label>
                    <select value={repayForm.method} onChange={(e) => setRepayForm({...repayForm, method: e.target.value})} className="w-full px-3 py-2 border rounded-md">
                      <option value="cash">نقدي</option>
                      <option value="bank">تحويل بنكي</option>
                      <option value="salary">خصم من الراتب</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">رقم مرجع</label>
                    <input type="text" value={repayForm.reference} onChange={(e) => setRepayForm({...repayForm, reference: e.target.value})} className="w-full px-3 py-2 border rounded-md" placeholder="اختياري" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ملاحظات</label>
                  <textarea value={repayForm.notes} onChange={(e) => setRepayForm({...repayForm, notes: e.target.value})} className="w-full px-3 py-2 border rounded-md" rows={2} placeholder="اختياري"></textarea>
                </div>
                <div className="flex justify-end space-x-3 space-x-reverse">
                  <button type="button" onClick={() => setShowRepayModal(false)} className="px-4 py-2 border rounded-md">إلغاء</button>
                  <button type="submit" className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700">تسجيل السداد</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Transaction Modal */}
      {showEditModal && selectedTransaction && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">تعديل المعاملة</h3>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg mb-4">
                <p className="text-sm text-gray-600">
                  <strong>الموظف:</strong> {selectedTransaction.employee_name}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>النوع:</strong> {selectedTransaction.transaction_type_ar}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>الحالة:</strong> {selectedTransaction.status_ar}
                </p>
              </div>

              <form onSubmit={handleEditTransaction} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    المبلغ (بالدرهم) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={editForm.amount}
                    onChange={(e) => setEditForm({...editForm, amount: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    الوصف *
                  </label>
                  <textarea
                    value={editForm.description}
                    onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="اكتب وصف المعاملة..."
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ملاحظات إضافية
                  </label>
                  <textarea
                    value={editForm.notes}
                    onChange={(e) => setEditForm({...editForm, notes: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={2}
                    placeholder="ملاحظات اختيارية..."
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    disabled={editing}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    إلغاء
                  </button>
                  <button
                    type="submit"
                    disabled={editing}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
                  >
                    {editing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-2"></div>
                        جاري الحفظ...
                      </>
                    ) : (
                      <>
                        <PencilIcon className="h-4 w-4 ml-2" />
                        حفظ التعديلات
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Transaction Details Modal */}
      {showTransactionModal && selectedTransaction && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-full max-w-3xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-gray-900">تفاصيل الطلب والموافقة</h3>
                <button
                  onClick={() => setShowTransactionModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {/* Transaction Details */}
              <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <h4 className="font-semibold text-gray-800 mb-3">تفاصيل المعاملة</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="font-medium">الموظف:</span> {selectedTransaction.employee_name}</div>
                  <div><span className="font-medium">المبلغ:</span> {formatCurrency(selectedTransaction.amount)}</div>
                  <div><span className="font-medium">النوع:</span> {selectedTransaction.transaction_type_ar}</div>
                  <div><span className="font-medium">التاريخ:</span> {selectedTransaction.created_at_display}</div>
                  {selectedTransaction.category_ar && (
                    <div><span className="font-medium">التصنيف:</span> {selectedTransaction.category_ar}</div>
                  )}
                </div>
                <div className="mt-3">
                  <span className="font-medium">الوصف:</span>
                  <p className="text-gray-600 mt-1">{selectedTransaction.description}</p>
                </div>
              </div>

              {/* Attachments */}
              {selectedTransaction.attachments && selectedTransaction.attachments.length > 0 && (
                <div className="bg-blue-50 p-4 rounded-lg mb-6">
                  <h4 className="font-semibold text-gray-800 mb-3">المرفقات ({selectedTransaction.attachments.length})</h4>
                  <AttachmentViewer 
                    attachments={selectedTransaction.attachments.map(attachment => ({
                      ...attachment,
                      url: `${API}/advances/attachment/${selectedTransaction.id}/${attachment.id}`
                    }))}
                  />
                </div>
              )}

              {/* Approval Form */}
              <div className="bg-white border rounded-lg p-4">
                <h4 className="font-semibold text-gray-800 mb-4">قرار الموافقة</h4>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ملاحظات الإدارة
                    </label>
                    <textarea
                      value={approvalForm.notes}
                      onChange={(e) => setApprovalForm({...approvalForm, notes: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                      placeholder="ملاحظات أو تعليقات (اختياري)..."
                    />
                  </div>

                  <div className="flex justify-end space-x-3 pt-4 border-t">
                    <button
                      onClick={() => setShowTransactionModal(false)}
                      className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                      disabled={approving}
                    >
                      إلغاء
                    </button>
                    <button
                      onClick={() => handleApproval(selectedTransaction.id, 'rejected')}
                      className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center"
                      disabled={approving}
                    >
                      <XCircleIcon className="h-4 w-4 ml-1" />
                      رفض
                    </button>
                    <button
                      onClick={() => handleApproval(selectedTransaction.id, 'approved')}
                      className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center"
                      disabled={approving}
                    >
                      {approving ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-1"></div>
                      ) : (
                        <CheckCircleIcon className="h-4 w-4 ml-1" />
                      )}
                      موافقة
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;