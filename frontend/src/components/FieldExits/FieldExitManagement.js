import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API } from '../../config';

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


export default FieldExitManagement;
