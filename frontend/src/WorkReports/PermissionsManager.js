import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  UserGroupIcon,
  ShieldCheckIcon,
  KeyIcon,
  PlusIcon,
  PencilIcon,
  EyeIcon,
  LockClosedIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const PermissionsManager = () => {
  const [users, setUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]); // From TANSEEQ HR system
  const [permissionTemplates, setPermissionTemplates] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newUserData, setNewUserData] = useState({
    user_id: '',
    permission_level: 'user',
    notes: ''
  });
  const [editPermissions, setEditPermissions] = useState({});

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchUserPermissions();
    fetchPermissionTemplates();
    fetchAllSystemUsers();
  }, []);

  const fetchUserPermissions = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/work-reports/permissions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching permissions:', err);
      if (err.response?.status === 403) {
        setError('ليس لديك صلاحية لإدارة الصلاحيات - Access Denied');
      } else {
        setError('فشل في تحميل بيانات الصلاحيات');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchPermissionTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/work-reports/permission-templates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPermissionTemplates(response.data.templates);
    } catch (err) {
      console.error('Error fetching templates:', err);
    }
  };

  const fetchAllSystemUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAllUsers(response.data);
    } catch (err) {
      console.error('Error fetching system users:', err);
      // Mock data if API not available
      setAllUsers([
        { id: 'hatem-user-id', name: 'Hatem Mohamed Ahmed', email: 'hatem@tanseeq.com', role: 'super_admin' },
        { id: 'mahmoud-user-id', name: 'Mahmoud Al-Rashid', email: 'mahmoud@tanseeq.com', role: 'admin' },
        { id: 'jihad-user-id', name: 'Jihad Al-Mansouri', email: 'jihad@tanseeq.com', role: 'user' },
        { id: 'sara-user-id', name: 'Sara Abdullah', email: 'sara@tanseeq.com', role: 'user' },
        { id: 'omar-user-id', name: 'Omar Hassan', email: 'omar@tanseeq.com', role: 'user' }
      ]);
    }
  };

  const handleCreatePermission = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${backendUrl}/api/work-reports/permissions/${newUserData.user_id}`, {
        permission_level: newUserData.permission_level,
        notes: newUserData.notes
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      setShowAddModal(false);
      setNewUserData({ user_id: '', permission_level: 'user', notes: '' });
      fetchUserPermissions();
      alert('تم إنشاء صلاحيات المستخدم بنجاح');
    } catch (err) {
      console.error('Error creating permissions:', err);
      alert('فشل في إنشاء الصلاحيات');
    }
  };

  const handleUpdatePermissions = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${backendUrl}/api/work-reports/permissions/${selectedUser.user_id}`, editPermissions, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      setShowEditModal(false);
      setSelectedUser(null);
      setEditPermissions({});
      fetchUserPermissions();
      alert('تم تحديث صلاحيات المستخدم بنجاح');
    } catch (err) {
      console.error('Error updating permissions:', err);
      alert('فشل في تحديث الصلاحيات');
    }
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setEditPermissions({
      permission_level: user.permission_level,
      can_view_credentials: user.can_view_credentials,
      can_reveal_passwords: user.can_reveal_passwords,
      can_create_credentials: user.can_create_credentials,
      can_edit_credentials: user.can_edit_credentials,
      can_delete_credentials: user.can_delete_credentials,
      can_create_clients: user.can_create_clients,
      can_edit_clients: user.can_edit_clients,
      can_delete_clients: user.can_delete_clients,
      can_import_clients: user.can_import_clients,
      can_export_excel: user.can_export_excel,
      can_manage_permissions: user.can_manage_permissions
    });
    setShowEditModal(true);
  };

  const handleRevokePermissions = async (userId, userName) => {
    if (!window.confirm(`هل أنت متأكد من إلغاء صلاحيات المستخدم ${userName}؟\n\nسيفقد المستخدم جميع الصلاحيات في نظام تقارير العمل.`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${backendUrl}/api/work-reports/permissions/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchUserPermissions();
      alert('تم إلغاء صلاحيات المستخدم بنجاح');
    } catch (err) {
      console.error('Error revoking permissions:', err);
      alert('فشل في إلغاء الصلاحيات');
    }
  };

  const getPermissionLevelColor = (level) => {
    switch (level) {
      case 'user': return 'bg-blue-100 text-blue-800';
      case 'supervisor': return 'bg-green-100 text-green-800';
      case 'admin': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPermissionLevelIcon = (level) => {
    switch (level) {
      case 'user': return <UserGroupIcon className="h-4 w-4" />;
      case 'supervisor': return <ShieldCheckIcon className="h-4 w-4" />;
      case 'admin': return <KeyIcon className="h-4 w-4" />;
      default: return <UserGroupIcon className="h-4 w-4" />;
    }
  };

  const getUserInfo = (userId) => {
    return allUsers.find(u => u.id === userId) || { name: 'مستخدم غير معروف', email: '' };
  };

  const getAvailableUsers = () => {
    const existingUserIds = users.map(u => u.user_id);
    return allUsers.filter(u => !existingUserIds.includes(u.id));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <ShieldCheckIcon className="h-8 w-8 text-blue-600 mr-3" />
            إدارة صلاحيات الموظفين
          </h1>
          <p className="text-gray-600 mt-2">تحديد صلاحيات الوصول لنظام تقارير العمل والبيانات الحساسة</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          إضافة صلاحيات جديدة
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Permission Templates Info */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
        <div className="flex">
          <KeyIcon className="h-5 w-5 text-blue-400" />
          <div className="mr-3">
            <p className="text-sm text-blue-700">
              <strong>مستويات الصلاحيات المتاحة:</strong>
            </p>
            <ul className="text-sm text-blue-600 mt-1 space-y-1">
              <li>• <strong>موظف عادي:</strong> عرض العملاء وإنشاء سجلات العمل (بدون كلمات المرور)</li>
              <li>• <strong>مشرف:</strong> إدارة العملاء + الوصول لكلمات المرور + التقارير</li>
              <li>• <strong>مدير:</strong> صلاحيات كاملة + إدارة الصلاحيات + حذف البيانات</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Users with Permissions */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            الموظفون والصلاحيات ({users.length})
          </h2>
        </div>

        {users.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {users.map((user) => {
              const userInfo = getUserInfo(user.user_id);
              return (
                <div key={user.id} className="p-6 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center mb-3">
                        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                          {getPermissionLevelIcon(user.permission_level)}
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{user.user_name}</h3>
                          <p className="text-sm text-gray-500">{userInfo.email}</p>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPermissionLevelColor(user.permission_level)}`}>
                            {permissionTemplates[user.permission_level]?.name || user.permission_level}
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="flex items-center">
                          {user.can_view_credentials ? 
                            <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" /> : 
                            <XMarkIcon className="h-4 w-4 text-red-500 mr-1" />
                          }
                          <span>عرض بيانات الاعتماد</span>
                        </div>
                        <div className="flex items-center">
                          {user.can_reveal_passwords ? 
                            <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" /> : 
                            <XMarkIcon className="h-4 w-4 text-red-500 mr-1" />
                          }
                          <span>كشف كلمات المرور</span>
                        </div>
                        <div className="flex items-center">
                          {user.can_create_credentials ? 
                            <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" /> : 
                            <XMarkIcon className="h-4 w-4 text-red-500 mr-1" />
                          }
                          <span>إضافة بيانات اعتماد</span>
                        </div>
                        <div className="flex items-center">
                          {user.can_manage_permissions ? 
                            <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" /> : 
                            <XMarkIcon className="h-4 w-4 text-red-500 mr-1" />
                          }
                          <span>إدارة الصلاحيات</span>
                        </div>
                      </div>

                      <div className="mt-3 text-xs text-gray-500">
                        تم الإنشاء: {new Date(user.granted_at).toLocaleDateString('ar-SA')} | 
                        آخر تحديث: {new Date(user.last_updated).toLocaleDateString('ar-SA')}
                      </div>
                    </div>

                    <div className="flex space-x-2 mr-4">
                      <button
                        onClick={() => handleEditUser(user)}
                        className="text-blue-600 hover:text-blue-800"
                        title="تعديل الصلاحيات"
                      >
                        <PencilIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleRevokePermissions(user.user_id, user.user_name)}
                        className="text-red-600 hover:text-red-800"
                        title="إلغاء الصلاحيات"
                      >
                        <LockClosedIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <UserGroupIcon className="mx-auto h-16 w-16 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">لا توجد صلاحيات محددة</h3>
            <p className="mt-2 text-gray-500">
              ابدأ بإضافة صلاحيات للموظفين للوصول لنظام تقارير العمل
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="mt-4 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              إضافة صلاحيات جديدة
            </button>
          </div>
        )}
      </div>

      {/* Add Permission Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-1/2 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              إضافة صلاحيات جديدة للموظف
            </h3>
            <form onSubmit={handleCreatePermission} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">اختر الموظف *</label>
                <select
                  required
                  value={newUserData.user_id}
                  onChange={(e) => setNewUserData({...newUserData, user_id: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">اختر موظف</option>
                  {getAvailableUsers().map(user => (
                    <option key={user.id} value={user.id}>
                      {user.name} - {user.email}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">مستوى الصلاحيات *</label>
                <select
                  required
                  value={newUserData.permission_level}
                  onChange={(e) => setNewUserData({...newUserData, permission_level: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(permissionTemplates).map(([level, template]) => (
                    <option key={level} value={level}>
                      {template.name} - {template.description}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">ملاحظات</label>
                <textarea
                  value={newUserData.notes}
                  onChange={(e) => setNewUserData({...newUserData, notes: e.target.value})}
                  rows={3}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="ملاحظات حول منح هذه الصلاحيات..."
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setNewUserData({ user_id: '', permission_level: 'user', notes: '' });
                  }}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                >
                  إنشاء الصلاحيات
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Permission Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 max-h-screen overflow-y-auto shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              تعديل صلاحيات: {selectedUser.user_name}
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Quick Level Selection */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900">مستوى الصلاحيات السريع</h4>
                <select
                  value={editPermissions.permission_level}
                  onChange={(e) => {
                    const template = permissionTemplates[e.target.value];
                    if (template) {
                      setEditPermissions({
                        ...editPermissions,
                        permission_level: e.target.value,
                        ...template.permissions
                      });
                    }
                  }}
                  className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(permissionTemplates).map(([level, template]) => (
                    <option key={level} value={level}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Custom Permissions */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900">صلاحيات مخصصة</h4>
                
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editPermissions.can_view_credentials}
                      onChange={(e) => setEditPermissions({...editPermissions, can_view_credentials: e.target.checked})}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                    <span className="mr-3 text-sm">عرض بيانات الاعتماد</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editPermissions.can_reveal_passwords}
                      onChange={(e) => setEditPermissions({...editPermissions, can_reveal_passwords: e.target.checked})}
                      className="h-4 w-4 text-red-600 rounded"
                    />
                    <span className="mr-3 text-sm text-red-600 font-medium">كشف كلمات المرور (حساس)</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editPermissions.can_create_credentials}
                      onChange={(e) => setEditPermissions({...editPermissions, can_create_credentials: e.target.checked})}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                    <span className="mr-3 text-sm">إنشاء بيانات اعتماد</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editPermissions.can_edit_credentials}
                      onChange={(e) => setEditPermissions({...editPermissions, can_edit_credentials: e.target.checked})}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                    <span className="mr-3 text-sm">تعديل بيانات اعتماد</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editPermissions.can_delete_credentials}
                      onChange={(e) => setEditPermissions({...editPermissions, can_delete_credentials: e.target.checked})}
                      className="h-4 w-4 text-red-600 rounded"
                    />
                    <span className="mr-3 text-sm text-red-600">حذف بيانات اعتماد</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editPermissions.can_import_clients}
                      onChange={(e) => setEditPermissions({...editPermissions, can_import_clients: e.target.checked})}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                    <span className="mr-3 text-sm">استيراد العملاء من Excel</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editPermissions.can_export_excel}
                      onChange={(e) => setEditPermissions({...editPermissions, can_export_excel: e.target.checked})}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                    <span className="mr-3 text-sm">تصدير Excel</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editPermissions.can_manage_permissions}
                      onChange={(e) => setEditPermissions({...editPermissions, can_manage_permissions: e.target.checked})}
                      className="h-4 w-4 text-red-600 rounded"
                    />
                    <span className="mr-3 text-sm text-red-600 font-medium">إدارة صلاحيات الآخرين (حساس)</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-6 mt-6 border-t">
              <button
                type="button"
                onClick={() => {
                  setShowEditModal(false);
                  setSelectedUser(null);
                  setEditPermissions({});
                }}
                className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors"
              >
                إلغاء
              </button>
              <button
                onClick={handleUpdatePermissions}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                حفظ التغييرات
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PermissionsManager;