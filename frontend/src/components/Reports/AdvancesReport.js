import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BanknotesIcon,
  CalendarIcon,
  UserGroupIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdvancesReport = () => {
  const [advances, setAdvances] = useState([]);
  const [filteredAdvances, setFilteredAdvances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
    totalAmount: 0,
    paidAmount: 0,
    remainingAmount: 0
  });

  useEffect(() => {
    fetchAdvances();
  }, []);

  useEffect(() => {
    filterAdvances();
  }, [statusFilter, advances]);

  const fetchAdvances = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/advances/admin/all-transactions`);
      const data = response.data.transactions || [];
      setAdvances(data);
      calculateStats(data);
    } catch (err) {
      console.error('Error fetching advances:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (data) => {
    const advancesOnly = data.filter(t => t.transaction_type === 'advance');
    
    const stats = {
      total: advancesOnly.length,
      pending: advancesOnly.filter(a => a.status === 'pending').length,
      approved: advancesOnly.filter(a => a.status === 'approved').length,
      rejected: advancesOnly.filter(a => a.status === 'rejected').length,
      totalAmount: advancesOnly.reduce((sum, a) => sum + (a.amount || 0), 0),
      approvedAmount: advancesOnly.filter(a => a.status === 'approved').reduce((sum, a) => sum + (a.amount || 0), 0)
    };
    
    setStats(stats);
  };

  const filterAdvances = () => {
    let filtered = advances.filter(a => a.transaction_type === 'advance');
    
    if (statusFilter !== 'all') {
      filtered = filtered.filter(a => a.status === statusFilter);
    }
    
    setFilteredAdvances(filtered);
  };

  const getStatusBadge = (status) => {
    const badges = {
      'pending': { color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon, label: 'معلق' },
      'approved': { color: 'bg-green-100 text-green-800', icon: CheckCircleIcon, label: 'موافق' },
      'rejected': { color: 'bg-red-100 text-red-800', icon: ExclamationTriangleIcon, label: 'مرفوض' }
    };
    
    const badge = badges[status] || badges['pending'];
    const Icon = badge.icon;
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${badge.color}`}>
        <Icon className="h-3 w-3 ml-1" />
        {badge.label}
      </span>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-800 text-white p-6 rounded-lg shadow-lg mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">💰 تقرير السلف الشامل</h1>
            <p className="text-green-100">تقرير تفصيلي عن السلف المستحقة، المسددة، والمعلقة</p>
          </div>
          <BanknotesIcon className="h-16 w-16 text-green-200" />
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-r from-blue-100 to-blue-200 p-5 rounded-xl shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-700 font-medium">إجمالي السلف</p>
              <p className="text-2xl font-bold text-blue-900">{stats.total}</p>
            </div>
            <BanknotesIcon className="h-10 w-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-yellow-100 to-yellow-200 p-5 rounded-xl shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-yellow-700 font-medium">معلقة</p>
              <p className="text-2xl font-bold text-yellow-900">{stats.pending}</p>
            </div>
            <ClockIcon className="h-10 w-10 text-yellow-500" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-100 to-green-200 p-5 rounded-xl shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-700 font-medium">موافق عليها</p>
              <p className="text-2xl font-bold text-green-900">{stats.approved}</p>
            </div>
            <CheckCircleIcon className="h-10 w-10 text-green-500" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-red-100 to-red-200 p-5 rounded-xl shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-red-700 font-medium">مرفوضة</p>
              <p className="text-2xl font-bold text-red-900">{stats.rejected}</p>
            </div>
            <ExclamationTriangleIcon className="h-10 w-10 text-red-500" />
          </div>
        </div>
      </div>

      {/* Amount Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">إجماليات المبالغ</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">إجمالي المبالغ المطلوبة:</span>
              <span className="text-xl font-bold text-blue-600">{(stats.totalAmount || 0).toFixed(2)} درهم</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">المبالغ الموافق عليها:</span>
              <span className="text-xl font-bold text-green-600">{(stats.approvedAmount || 0).toFixed(2)} درهم</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">الفلاتر</h3>
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">تصفية حسب الحالة:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
            >
              <option value="all">جميع الحالات</option>
              <option value="pending">معلق</option>
              <option value="approved">موافق عليه</option>
              <option value="rejected">مرفوض</option>
            </select>
          </div>
        </div>
      </div>

      {/* Advances Table */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">
            تفاصيل السلف ({filteredAdvances.length})
          </h2>
          <button
            onClick={() => window.print()}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center gap-2"
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            تصدير PDF
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الموظف</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">المبلغ</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">التاريخ</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الوصف</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الحالة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الموافق/الرافض</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
                  </td>
                </tr>
              ) : filteredAdvances.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                    لا توجد سلف مطابقة للفلتر المحدد
                  </td>
                </tr>
              ) : (
                filteredAdvances.map((advance, index) => (
                  <tr key={advance.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {advance.employee_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">
                      {(advance.amount || 0).toFixed(2)} درهم
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {new Date(advance.created_at).toLocaleDateString('ar-EG')}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                      {advance.description || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {getStatusBadge(advance.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {advance.approved_by || advance.rejected_by || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            {filteredAdvances.length > 0 && (
              <tfoot className="bg-gray-100">
                <tr>
                  <td className="px-6 py-4 text-sm font-bold text-gray-900">الإجمالي:</td>
                  <td className="px-6 py-4 text-sm font-bold text-green-700">
                    {filteredAdvances.reduce((sum, a) => sum + (a.amount || 0), 0).toFixed(2)} درهم
                  </td>
                  <td colSpan="4"></td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdvancesReport;