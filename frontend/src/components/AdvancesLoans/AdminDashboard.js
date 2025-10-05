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
  ArrowDownIcon
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
    users: []
  });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTransactionModal, setShowTransactionModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [approving, setApproving] = useState(false);

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

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch all data in parallel
      const [pendingRes, balancesRes, usersRes] = await Promise.all([
        axios.get(`${API}/advances/admin/pending-approvals`),
        axios.get(`${API}/advances/admin/all-balances`),
        axios.get(`${API}/users`)
      ]);

      setData({
        pendingApprovals: pendingRes.data.pending_transactions || [],
        allBalances: balancesRes.data.employee_balances || [],
        users: usersRes.data || []
      });
    } catch (error) {
      console.error('Error fetching admin dashboard data:', error);
    } finally {
      setLoading(false);
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

  const formatCurrency = (amount) => {
    return `${amount?.toFixed(2) || '0.00'} درهم`;
  };

  const getTransactionTypeColor = (type) => {
    switch (type) {
      case 'advance': return 'bg-blue-100 text-blue-800';
      case 'custody': return 'bg-green-100 text-green-800';
      case 'expense': return 'bg-red-100 text-red-800';
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