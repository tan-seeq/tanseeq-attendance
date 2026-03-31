import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ArrowPathIcon, ClockIcon, DocumentArrowDownIcon, DocumentArrowUpIcon,
  DocumentIcon, ExclamationCircleIcon, ExclamationTriangleIcon,
  FolderIcon, ServerIcon, TrashIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { API } from '../../config';

const BackupManagement = () => {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'super_admin') {
      fetchBackups();
    }
  }, [user]);

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/backup/list-files`);
      setBackups(response.data.backup_files || []);
    } catch (error) {
      console.error('Error fetching backups:', error);
      setMessage({ type: 'error', text: 'حدث خطأ في تحميل قائمة النسخ الاحتياطية' });
    } finally {
      setLoading(false);
    }
  };

  const createBackup = async () => {
    try {
      setLoading(true);
      setMessage('');
      const response = await axios.post(`${API}/backup/create-download`);
      
      setMessage({ 
        type: 'success', 
        text: `تم إنشاء النسخة الاحتياطية وحفظها على الخادم بنجاح: ${response.data.filename}` 
      });
      
      // Refresh backup list to show new backup
      await fetchBackups();
      
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في إنشاء النسخة الاحتياطية' 
      });
    } finally {
      setLoading(false);
    }
  };

  const downloadBackup = async (filename) => {
    try {
      const response = await axios.get(`${API}/backup/download/${filename}`, {
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data]);
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(link.href);
      
      setMessage({ type: 'success', text: `تم تحميل ${filename} بنجاح` });
      
    } catch (error) {
      console.error('Download error:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في تحميل الملف' 
      });
    }
  };

  const deleteBackup = async (filename) => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      `هل أنت متأكد من حذف النسخة الاحتياطية؟\n\n${filename}\n\nلا يمكن التراجع عن هذا الإجراء!`
    );

    if (!confirmed) return;

    try {
      await axios.delete(`${API}/backup/delete/${filename}`);
      
      setMessage({ 
        type: 'success', 
        text: `تم حذف ${filename} بنجاح` 
      });
      
      // Refresh backup list
      fetchBackups();
      
    } catch (error) {
      console.error('Delete error:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في حذف الملف' 
      });
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Show confirmation dialog
    const confirmed = window.confirm(
      `⚠️ تحذير مهم!\n\nسيتم حذف جميع البيانات الموجودة حالياً واستبدالها بالبيانات من الملف:\n${file.name}\n\nهل أنت متأكد من المتابعة؟\n\nهذا الإجراء لا يمكن التراجع عنه!`
    );

    if (!confirmed) {
      event.target.value = ''; // Reset file input
      return;
    }

    try {
      setUploadLoading(true);
      setMessage('');

      const formData = new FormData();
      formData.append('backup_file', file);

      const response = await axios.post(`${API}/backup/restore`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setMessage({ 
        type: 'success', 
        text: `تم استعادة النسخة الاحتياطية بنجاح من ${file.name}` 
      });

      // Refresh backup list
      await fetchBackups();

    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'حدث خطأ في استعادة النسخة الاحتياطية' 
      });
    } finally {
      setUploadLoading(false);
      event.target.value = ''; // Reset file input
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ar-SA', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (user?.role !== 'admin' && user?.role !== 'super_admin') {
    return (
      <div className="text-center py-8">
        <ExclamationCircleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
        <p className="text-gray-500">هذه الصفحة متاحة للإدارة فقط</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-gray-800">إدارة النسخ الاحتياطية</h2>
          <div className="bg-purple-50 px-3 py-1 rounded-lg">
            <span className="text-sm text-purple-700 font-medium">Admin/Super Admin</span>
          </div>
        </div>

        {message && (
          <div className={`p-4 mb-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {message.text}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 mb-6">
          <button
            onClick={createBackup}
            disabled={loading || uploadLoading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center"
          >
            {loading ? (
              <ArrowPathIcon className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            )}
            📥 إنشاء نسخة احتياطية
          </button>

          <label className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 cursor-pointer flex items-center">
            {uploadLoading ? (
              <ArrowPathIcon className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
            )}
            📤 استعادة من نسخة احتياطية
            <input
              type="file"
              accept=".json,.zip"
              onChange={handleFileUpload}
              disabled={loading || uploadLoading}
              className="hidden"
            />
          </label>

          <button
            onClick={fetchBackups}
            disabled={loading || uploadLoading}
            className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 disabled:bg-gray-400 flex items-center"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            تحديث القائمة
          </button>
        </div>

        {/* Warning Box */}
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700">
                <strong>تحذير:</strong> عملية استعادة النسخة الاحتياطية ستحذف جميع البيانات الموجودة حالياً وتستبدلها بالبيانات من الملف المرفوع. تأكد من إنشاء نسخة احتياطية قبل الاستعادة.
              </p>
            </div>
          </div>
        </div>

        {/* Backups List */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-md font-medium text-gray-800 mb-4">النسخ الاحتياطية المتاحة</h3>
          
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-600">جاري التحميل...</span>
            </div>
          ) : backups.length === 0 ? (
            <div className="text-center py-8">
              <FolderIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">لا توجد نسخ احتياطية متاحة</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      اسم الملف
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      الحجم
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      تاريخ الإنشاء
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      الحالة
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      الإجراءات
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {backups.map((backup, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <DocumentIcon className="h-5 w-5 text-blue-500 mr-2" />
                          {backup.filename}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatFileSize(backup.size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(backup.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          متاح
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-3">
                          <button
                            onClick={() => downloadBackup(backup.filename)}
                            className="text-blue-600 hover:text-blue-900 flex items-center"
                          >
                            <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
                            تحميل JSON
                          </button>
                          <button
                            onClick={() => downloadBackup(backup.filename.replace('.json', '.zip'))}
                            className="text-green-600 hover:text-green-900 flex items-center"
                          >
                            <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
                            تحميل ZIP
                          </button>
                          <button
                            onClick={() => deleteBackup(backup.filename)}
                            className="text-red-600 hover:text-red-900 flex items-center"
                          >
                            <TrashIcon className="h-4 w-4 mr-1" />
                            حذف
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Statistics */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <FolderIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">إجمالي النسخ</p>
                <p className="text-2xl font-bold text-gray-900">{backups.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <ServerIcon className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">إجمالي الحجم</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatFileSize(backups.reduce((total, backup) => total + backup.size, 0))}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg border">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">آخر نسخة</p>
                <p className="text-lg font-bold text-gray-900">
                  {backups.length > 0 ? formatDate(backups[0].created_at) : 'لا يوجد'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


export default BackupManagement;
