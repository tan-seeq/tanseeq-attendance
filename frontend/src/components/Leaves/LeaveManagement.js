import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  CheckCircleIcon, XCircleIcon, XMarkIcon, EyeIcon,
  ArrowDownTrayIcon, DocumentTextIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API, BACKEND_URL } from '../../config';

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
                    {leave.attachment_url || leave.file_path ? (
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleImageClick(`${BACKEND_URL}${leave.attachment_url || leave.file_path}`)}
                          className="text-blue-600 hover:text-blue-900 flex items-center"
                          title="عرض المرفق"
                        >
                          <EyeIcon className="h-4 w-4 mr-1" />
                          عرض
                        </button>
                        <a
                          href={`${BACKEND_URL}${leave.attachment_url || leave.file_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-900 flex items-center"
                          title="تحميل المرفق"
                        >
                          <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                          تحميل
                        </a>
                      </div>
                    ) : (
                      <span className="text-gray-400">لا يوجد مرفق</span>
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

      {/* Enhanced Attachment Modal */}
      {showImageModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="relative max-w-4xl max-h-full bg-white rounded-lg p-6 m-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">عرض مرفق الإجازة</h3>
              <div className="flex items-center space-x-2">
                <a
                  href={selectedImage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 flex items-center"
                >
                  <ArrowDownTrayIcon className="h-5 w-5 mr-1" />
                  تحميل
                </a>
                <button
                  onClick={() => setShowImageModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </div>
            <div className="text-center">
              {selectedImage && selectedImage.toLowerCase().includes('.pdf') ? (
                <div className="bg-gray-50 p-6 rounded-lg">
                  <DocumentTextIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">ملف PDF - انقر للفتح في نافذة جديدة</p>
                  <a
                    href={selectedImage}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                  >
                    <DocumentTextIcon className="h-4 w-4 mr-2" />
                    فتح PDF
                  </a>
                </div>
              ) : (
                <img
                  src={selectedImage}
                  alt="Leave attachment"
                  className="max-w-full max-h-96 object-contain rounded-lg shadow-md"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextElementSibling.style.display = 'block';
                  }}
                />
              )}
              <div className="hidden bg-gray-50 p-6 rounded-lg mt-4">
                <DocumentTextIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">خطأ في تحميل المرفق</p>
                <a
                  href={selectedImage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                  تحميل مباشرة
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


export default LeaveManagement;
