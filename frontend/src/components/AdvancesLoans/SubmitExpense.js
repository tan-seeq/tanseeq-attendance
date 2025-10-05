import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  DocumentTextIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  PaperClipIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SubmitExpense = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [balance, setBalance] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    amount: '',
    category: 'transportation',
    description: '',
    expense_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  
  // File handling
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [fileErrors, setFileErrors] = useState([]);

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
    fetchBalance();
  }, []);

  const fetchBalance = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/advances/my-balance`);
      setBalance(response.data);
    } catch (error) {
      console.error('Error fetching balance:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    const newFiles = [];
    const errors = [];

    files.forEach((file, index) => {
      // Check file type
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
      if (!allowedTypes.includes(file.type)) {
        errors.push(`ملف ${file.name}: نوع الملف غير مدعوم. يُسمح بـ: JPEG, PNG, PDF فقط`);
        return;
      }

      // Check file size (10MB max)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        errors.push(`ملف ${file.name}: حجم الملف كبير جداً. الحد الأقصى 10 ميجابايت`);
        return;
      }

      newFiles.push({
        file,
        id: Date.now() + index,
        name: file.name,
        size: file.size,
        type: file.type
      });
    });

    setSelectedFiles(prev => [...prev, ...newFiles]);
    setFileErrors(errors);

    // Clear the input
    event.target.value = '';
  };

  const removeFile = (fileId) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const validateForm = () => {
    const errors = [];

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      errors.push('يجب إدخال مبلغ صحيح');
    }

    if (!formData.description || formData.description.trim().length < 5) {
      errors.push('يجب إدخال وصف لا يقل عن 5 أحرف');
    }

    if (!formData.expense_date) {
      errors.push('يجب تحديد تاريخ المصروف');
    }

    if (selectedFiles.length === 0) {
      errors.push('يجب رفع فاتورة واحدة على الأقل');
    }

    // Check available balance
    const amount = parseFloat(formData.amount);
    const availableBalance = (balance?.total_available || 0);
    if (amount > availableBalance) {
      errors.push(`المبلغ المطلوب يتجاوز الرصيد المتاح (${availableBalance.toFixed(2)} درهم)`);
    }

    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const errors = validateForm();
    if (errors.length > 0) {
      alert('يرجى تصحيح الأخطاء التالية:\n' + errors.join('\n'));
      return;
    }

    try {
      setSubmitting(true);

      // Prepare form data for file upload
      const submitData = new FormData();
      submitData.append('amount', formData.amount);
      submitData.append('category', formData.category);
      submitData.append('description', formData.description);
      submitData.append('expense_date', formData.expense_date);
      if (formData.notes) {
        submitData.append('notes', formData.notes);
      }

      // Add files
      selectedFiles.forEach(fileObj => {
        submitData.append('invoice_files', fileObj.file);
      });

      const response = await axios.post(`${API}/advances/expense`, submitData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        alert('تم تقديم المصروف بنجاح! سيتم إرساله للموافقة.');
        navigate('/advances/my-transactions');
      }
    } catch (error) {
      console.error('Error submitting expense:', error);
      const errorMessage = error.response?.data?.detail || 'حدث خطأ في تقديم المصروف';
      alert(`خطأ: ${errorMessage}`);
    } finally {
      setSubmitting(false);
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
    <div className="p-6 max-w-4xl mx-auto">
      {/* Page Header */}
      <div className="mb-8">
        <div className="bg-gradient-to-r from-green-600 to-green-800 text-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">📋 تقديم مصروف جديد</h1>
              <p className="text-green-100">رفع فاتورة وطلب خصم من الرصيد المتاح</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-full p-4">
              <DocumentTextIcon className="h-12 w-12 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Balance Information */}
      {balance && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <CurrencyDollarIcon className="h-5 w-5 text-green-600 ml-2" />
            الرصيد المتاح
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-700">السُلف المتبقية</p>
              <p className="text-xl font-bold text-blue-800">{balance.remaining_advance?.toFixed(2)} درهم</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-green-700">العُهد المتبقية</p>
              <p className="text-xl font-bold text-green-800">{balance.remaining_custody?.toFixed(2)} درهم</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm text-purple-700">المجموع المتاح</p>
              <p className="text-2xl font-bold text-purple-800">{balance.total_available?.toFixed(2)} درهم</p>
            </div>
          </div>
        </div>
      )}

      {/* Expense Form */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Amount and Category */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                المبلغ (بالدرهم) *
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={formData.amount}
                  onChange={(e) => setFormData({...formData, amount: e.target.value})}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="0.00"
                  required
                />
                <CurrencyDollarIcon className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" />
              </div>
              {formData.amount && balance && parseFloat(formData.amount) > balance.total_available && (
                <p className="text-red-500 text-sm mt-1">
                  ⚠️ المبلغ يتجاوز الرصيد المتاح
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                تصنيف المصروف *
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              >
                {Object.entries(expenseCategories).map(([key, value]) => (
                  <option key={key} value={key}>{value}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              تاريخ المصروف *
            </label>
            <div className="relative">
              <input
                type="date"
                value={formData.expense_date}
                onChange={(e) => setFormData({...formData, expense_date: e.target.value})}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
              <CalendarIcon className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              وصف المصروف *
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              rows={3}
              placeholder="اكتب تفاصيل المصروف هنا..."
              required
              minLength={5}
            />
            <div className="text-xs text-gray-500 mt-1">
              {formData.description.length}/200 حرف (الحد الأدنى: 5 أحرف)
            </div>
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              رفع الفواتير والإيصالات *
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-green-400 transition-colors">
              <div className="space-y-1 text-center">
                <PaperClipIcon className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-green-600 hover:text-green-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-green-500">
                    <span>اختر الملفات</span>
                    <input
                      id="file-upload"
                      name="file-upload"
                      type="file"
                      className="sr-only"
                      multiple
                      accept=".jpg,.jpeg,.png,.pdf"
                      onChange={handleFileSelect}
                    />
                  </label>
                  <p className="pr-1">أو اسحب الملفات هنا</p>
                </div>
                <p className="text-xs text-gray-500">
                  يُسمح بـ: JPEG, PNG, PDF حتى 10 ميجابايت لكل ملف
                </p>
              </div>
            </div>
          </div>

          {/* File Errors */}
          {fileErrors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                <div className="mr-3">
                  <h3 className="text-sm font-medium text-red-800">
                    أخطاء في الملفات:
                  </h3>
                  <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                    {fileErrors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                الملفات المحددة ({selectedFiles.length}):
              </h4>
              <div className="space-y-2">
                {selectedFiles.map((fileObj) => (
                  <div key={fileObj.id} className="flex items-center justify-between bg-white p-3 rounded border">
                    <div className="flex items-center">
                      <div className="bg-blue-100 p-1 rounded ml-3">
                        {fileObj.type === 'application/pdf' ? (
                          <DocumentTextIcon className="h-4 w-4 text-red-600" />
                        ) : (
                          <EyeIcon className="h-4 w-4 text-blue-600" />
                        )}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-800">{fileObj.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(fileObj.size)}</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(fileObj.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ملاحظات إضافية
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              rows={2}
              placeholder="ملاحظات اختيارية..."
            />
          </div>

          {/* Important Notice */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <CheckCircleIcon className="h-5 w-5 text-blue-400" />
              <div className="mr-3">
                <h3 className="text-sm font-medium text-blue-800">
                  معلومات مهمة:
                </h3>
                <ul className="mt-2 text-sm text-blue-700 space-y-1">
                  <li>• سيتم إرسال طلبك للإدارة للموافقة</li>
                  <li>• ستحصل على إشعار عند الموافقة أو الرفض</li>
                  <li>• تأكد من وضوح الفواتير وصحة البيانات</li>
                  <li>• سيتم خصم المبلغ من رصيدك عند الموافقة</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end space-x-3 pt-6 border-t">
            <button
              type="button"
              onClick={() => navigate('/advances')}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              إلغاء
            </button>
            <button
              type="submit"
              disabled={submitting || selectedFiles.length === 0}
              className={`px-6 py-2 rounded-md text-white font-medium ${
                submitting || selectedFiles.length === 0
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              {submitting ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-2"></div>
                  جاري الإرسال...
                </div>
              ) : (
                'تقديم المصروف'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SubmitExpense;