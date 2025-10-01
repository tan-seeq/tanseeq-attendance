import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  PlusIcon, 
  EyeIcon,
  EyeSlashIcon,
  PencilIcon,
  TrashIcon,
  KeyIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ClipboardDocumentIcon
} from '@heroicons/react/24/outline';

const ClientCredentialsManager = ({ client, isOpen, onClose }) => {
  const [credentials, setCredentials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [selectedCredential, setSelectedCredential] = useState(null);
  const [revealedPasswords, setRevealedPasswords] = useState({});
  const [formData, setFormData] = useState({
    credential_type: '',
    username: '',
    email: '',
    password: '',
    portal_url: '',
    description: ''
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  const credentialTypes = [
    { value: 'fta_portal', label: 'بوابة الهيئة الاتحادية للضرائب - FTA Portal', icon: '🏛️' },
    { value: 'ministry_portal', label: 'بوابة وزارة الاقتصاد - Ministry Portal', icon: '🏢' },
    { value: 'bank_portal', label: 'البوابة المصرفية - Banking Portal', icon: '🏦' },
    { value: 'chamber_commerce', label: 'غرفة التجارة - Chamber of Commerce', icon: '🏛️' },
    { value: 'municipality', label: 'البلدية - Municipality', icon: '🏘️' },
    { value: 'labor_ministry', label: 'وزارة العمل - Ministry of Labor', icon: '👷' },
    { value: 'customs_authority', label: 'الهيئة الاتحادية للجمارك - Customs Authority', icon: '📦' },
    { value: 'securities_authority', label: 'هيئة الأوراق المالية - Securities Authority', icon: '📈' },
    { value: 'other', label: 'أخرى - Other', icon: '🔧' }
  ];

  useEffect(() => {
    if (isOpen && client) {
      fetchCredentials();
    }
  }, [isOpen, client]);

  const fetchCredentials = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/work-reports/clients/${client.id}/credentials`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCredentials(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching credentials:', err);
      setError('فشل في تحميل بيانات الاعتماد');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      
      await axios.post(`${backendUrl}/api/work-reports/clients/${client.id}/credentials`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      setShowAddModal(false);
      resetFormData();
      fetchCredentials();
      alert('تم حفظ بيانات الاعتماد بنجاح مع التشفير');
    } catch (err) {
      console.error('Error saving credential:', err);
      const errorMessage = err.response?.data?.detail || 'فشل في حفظ بيانات الاعتماد';
      setError(`فشل في حفظ بيانات الاعتماد: ${errorMessage}`);
      alert(`فشل في حفظ بيانات الاعتماد: ${errorMessage}`);
    }
  };

  const resetFormData = () => {
    setFormData({
      credential_type: '',
      username: '',
      email: '',
      password: '',
      portal_url: '',
      description: ''
    });
  };

  const handleRevealPassword = async (credentialId) => {
    if (revealedPasswords[credentialId]) {
      // Hide password
      setRevealedPasswords(prev => ({...prev, [credentialId]: null}));
      return;
    }

    if (!window.confirm('هل أنت متأكد من أنك تريد كشف كلمة المرور؟ سيتم تسجيل هذا الإجراء في سجل التدقيق.')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/work-reports/credentials/${credentialId}/password`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setRevealedPasswords(prev => ({
        ...prev, 
        [credentialId]: response.data.password
      }));

      // Auto-hide after 30 seconds
      setTimeout(() => {
        setRevealedPasswords(prev => ({...prev, [credentialId]: null}));
      }, 30000);

    } catch (err) {
      console.error('Error revealing password:', err);
      const errorMessage = err.response?.data?.detail || 'خطأ غير معروف';
      const statusCode = err.response?.status || 'غير معروف';
      
      if (statusCode === 403) {
        alert(`فشل في كشف كلمة المرور: ${errorMessage}\n\nتأكد من صلاحياتك أو تحقق من إدارة الصلاحيات.`);
      } else if (statusCode === 404) {
        alert('لم يتم العثور على كلمة المرور أو بيانات الاعتماد.');
      } else {
        alert(`فشل في كشف كلمة المرور (${statusCode}): ${errorMessage}`);
      }
    }
  };

  const handleCopyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    alert(`تم نسخ ${type} إلى الحافظة`);
  };

  const handleDeleteCredential = async (credentialId) => {
    if (!window.confirm('هل أنت متأكد من حذف بيانات الاعتماد هذه؟ لا يمكن التراجع عن هذا الإجراء.')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${backendUrl}/api/work-reports/credentials/${credentialId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchCredentials();
      alert('تم حذف بيانات الاعتماد بنجاح');
    } catch (err) {
      console.error('Error deleting credential:', err);
      setError('فشل في حذف بيانات الاعتماد');
    }
  };

  const getCredentialTypeLabel = (type) => {
    const found = credentialTypes.find(ct => ct.value === type);
    return found ? found.label : type;
  };

  const getCredentialTypeIcon = (type) => {
    const found = credentialTypes.find(ct => ct.value === type);
    return found ? found.icon : '🔐';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-4/5 lg:w-3/4 max-h-screen overflow-y-auto shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h3 className="text-2xl font-bold text-gray-900 flex items-center">
              <KeyIcon className="h-8 w-8 text-blue-600 mr-3" />
              إدارة بيانات الاعتماد
            </h3>
            <p className="text-gray-600 mt-2">
              <strong>العميل:</strong> {client?.company_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Security Warning */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
            <div className="mr-3">
              <p className="text-sm text-yellow-700">
                <strong>تحذير أمني:</strong> جميع كلمات المرور مشفرة بتقنية AES-256-GCM. 
                الوصول لكلمات المرور يتم تسجيله في سجل التدقيق الأمني.
              </p>
            </div>
          </div>
        </div>

        {/* Add New Credential Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            إضافة بيانات اعتماد جديدة
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Credentials List */}
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          </div>
        ) : credentials.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {credentials.map((credential) => (
              <div key={credential.id} className="border rounded-lg p-6 bg-gray-50 hover:bg-gray-100 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">
                      {getCredentialTypeIcon(credential.credential_type)}
                    </span>
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900">
                        {getCredentialTypeLabel(credential.credential_type)}
                      </h4>
                      <p className="text-sm text-gray-500">{credential.description}</p>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleDeleteCredential(credential.id)}
                      className="text-red-600 hover:text-red-800"
                      title="حذف"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                <div className="space-y-3">
                  {credential.username && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">اسم المستخدم:</span>
                      <div className="flex items-center">
                        <span className="text-sm text-gray-900 font-mono bg-white px-2 py-1 rounded">
                          {credential.username}
                        </span>
                        <button
                          onClick={() => handleCopyToClipboard(credential.username, 'اسم المستخدم')}
                          className="mr-2 text-gray-500 hover:text-gray-700"
                          title="نسخ"
                        >
                          <ClipboardDocumentIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  )}

                  {credential.email && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">البريد الإلكتروني:</span>
                      <div className="flex items-center">
                        <span className="text-sm text-gray-900 font-mono bg-white px-2 py-1 rounded">
                          {credential.email}
                        </span>
                        <button
                          onClick={() => handleCopyToClipboard(credential.email, 'البريد الإلكتروني')}
                          className="mr-2 text-gray-500 hover:text-gray-700"
                          title="نسخ"
                        >
                          <ClipboardDocumentIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">كلمة المرور:</span>
                    <div className="flex items-center">
                      <span className="text-sm text-gray-900 font-mono bg-white px-2 py-1 rounded">
                        {revealedPasswords[credential.id] || '••••••••'}
                      </span>
                      <button
                        onClick={() => handleRevealPassword(credential.id)}
                        className="mr-2 text-gray-500 hover:text-gray-700"
                        title={revealedPasswords[credential.id] ? 'إخفاء' : 'كشف'}
                      >
                        {revealedPasswords[credential.id] ? 
                          <EyeSlashIcon className="h-4 w-4" /> : 
                          <EyeIcon className="h-4 w-4" />
                        }
                      </button>
                      {revealedPasswords[credential.id] && (
                        <button
                          onClick={() => handleCopyToClipboard(revealedPasswords[credential.id], 'كلمة المرور')}
                          className="mr-2 text-gray-500 hover:text-gray-700"
                          title="نسخ"
                        >
                          <ClipboardDocumentIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  {credential.portal_url && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">رابط البوابة:</span>
                      <div className="flex items-center">
                        <a
                          href={credential.portal_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:text-blue-800 underline"
                        >
                          فتح البوابة
                        </a>
                        <button
                          onClick={() => handleCopyToClipboard(credential.portal_url, 'الرابط')}
                          className="mr-2 text-gray-500 hover:text-gray-700"
                          title="نسخ"
                        >
                          <ClipboardDocumentIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="pt-2 border-t text-xs text-gray-500">
                    آخر استخدام: {credential.last_used ? 
                      new Date(credential.last_used).toLocaleDateString('ar-SA') : 
                      'لم يتم الاستخدام بعد'
                    }
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <ShieldCheckIcon className="mx-auto h-16 w-16 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">لا توجد بيانات اعتماد</h3>
            <p className="mt-2 text-gray-500">
              ابدأ بإضافة بيانات الاعتماد الخاصة بالهيئات والبوابات الحكومية
            </p>
          </div>
        )}

        {/* Add Credential Modal */}
        {showAddModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-60">
            <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-1/2 shadow-lg rounded-md bg-white">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                إضافة بيانات اعتماد جديدة
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">نوع البوابة/الهيئة *</label>
                  <select
                    required
                    value={formData.credential_type}
                    onChange={(e) => setFormData({...formData, credential_type: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">اختر نوع البوابة</option>
                    {credentialTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.icon} {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">اسم المستخدم</label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">البريد الإلكتروني</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">كلمة المرور</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="سيتم تشفيرها تلقائياً"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">رابط البوابة</label>
                  <input
                    type="url"
                    value={formData.portal_url}
                    onChange={(e) => setFormData({...formData, portal_url: e.target.value})}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">وصف/ملاحظات</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    rows={3}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="معلومات إضافية عن هذه البيانات"
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddModal(false);
                      resetFormData();
                    }}
                    className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors"
                  >
                    إلغاء
                  </button>
                  <button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                  >
                    حفظ مع التشفير
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClientCredentialsManager;