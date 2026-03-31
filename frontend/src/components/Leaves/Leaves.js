import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  PlusIcon, CheckCircleIcon, XCircleIcon, XMarkIcon, EyeIcon,
  ArrowDownTrayIcon, DocumentTextIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API, BACKEND_URL } from '../../config';

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

      {/* Enhanced Attachment Modal */}
      {showImageModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-3/4 max-w-4xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  عرض مرفق الإجازة
                </h3>
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
                  <div className="space-y-4">
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
                  </div>
                ) : (
                  <img
                    src={selectedImage}
                    alt="Leave attachment"
                    className="max-w-full max-h-96 object-contain mx-auto rounded-lg shadow-md"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextElementSibling.style.display = 'block';
                    }}
                  />
                )}
                <div className="hidden bg-gray-50 p-6 rounded-lg">
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
        </div>
      )}
    </div>
  );
};


export default Leaves;
