import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ArrowPathIcon, DocumentArrowDownIcon, DocumentTextIcon,
  EyeIcon, FolderIcon, XMarkIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../config';

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


export default AttachmentViewer;
