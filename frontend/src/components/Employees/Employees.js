import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  UserIcon, PlusIcon, PencilIcon, TrashIcon, ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API } from '../../config';

const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'user',
    position: '',
    monthly_salary: '',
    working_hours_start: '09:00',
    working_hours_end: '18:00',
    phone: '',
    has_flexible_schedule: false,
    flexible_hours_per_day: 8,
    flexible_start_range: '07:00-10:00',
    flexible_end_range: '16:00-19:00',
    flexible_core_hours: '10:00-15:00',
    flexible_days_per_week: 5
  });
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!selectedEmployee || !newPassword) return;
    
    try {
      await axios.post(`${API}/users/${selectedEmployee.id}/change-password`, {
        new_password: newPassword
      });
      setShowPasswordModal(false);
      setNewPassword('');
      setSelectedEmployee(null);
      alert('Password changed successfully');
    } catch (error) {
      console.error('Error changing password:', error);
      alert('Error changing password');
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    
    try {
      await axios.post(`${API}/users`, {
        ...formData,
        monthly_salary: parseFloat(formData.monthly_salary),
        hire_date: new Date().toISOString()
      });
      setShowAddModal(false);
      setFormData({
        name: '',
        email: '',
        password: '',
        role: 'user',
        position: '',
        monthly_salary: '',
        working_hours_start: '09:00',
        working_hours_end: '18:00',
        phone: ''
      });
      fetchEmployees();
      alert('Employee added successfully');
    } catch (error) {
      console.error('Error adding employee:', error);
      alert('Error adding employee: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const handleEditEmployee = async (e) => {
    e.preventDefault();
    
    try {
      await axios.put(`${API}/users/${selectedEmployee.id}`, {
        ...formData,
        monthly_salary: parseFloat(formData.monthly_salary)
      });
      setShowEditModal(false);
      setSelectedEmployee(null);
      setFormData({
        name: '',
        email: '',
        password: '',
        role: 'user',
        position: '',
        monthly_salary: '',
        working_hours_start: '09:00',
        working_hours_end: '18:00',
        phone: ''
      });
      fetchEmployees();
      alert('Employee updated successfully');
    } catch (error) {
      console.error('Error updating employee:', error);
      alert('Error updating employee: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const handleDeleteEmployee = async (employee) => {
    if (window.confirm(`Are you sure you want to delete ${employee.name}?`)) {
      try {
        await axios.delete(`${API}/users/${employee.id}`);
        fetchEmployees();
        alert('Employee deleted successfully');
      } catch (error) {
        console.error('Error deleting employee:', error);
        alert('Error deleting employee: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    }
  };

  const openPasswordModal = (employee) => {
    setSelectedEmployee(employee);
    setShowPasswordModal(true);
  };

  const openAddModal = () => {
    setFormData({
      name: '',
      email: '',
      password: '',
      role: 'user',
      position: '',
      monthly_salary: '',
      working_hours_start: '09:00',
      working_hours_end: '18:00',
      phone: '',
      has_flexible_schedule: false,
      flexible_hours_per_day: 8,
      flexible_start_range: '07:00-10:00',
      flexible_end_range: '16:00-19:00',
      flexible_core_hours: '10:00-15:00',
      flexible_days_per_week: 5
    });
    setShowAddModal(true);
  };

  const openEditModal = (employee) => {
    setSelectedEmployee(employee);
    setFormData({
      name: employee.name,
      email: employee.email,
      password: '',
      role: employee.role,
      position: employee.position,
      monthly_salary: employee.monthly_salary.toString(),
      working_hours_start: employee.working_hours_start,
      working_hours_end: employee.working_hours_end,
      phone: employee.phone,
      has_flexible_schedule: employee.has_flexible_schedule || false,
      flexible_hours_per_day: employee.flexible_hours_per_day || 8,
      flexible_start_range: employee.flexible_start_range || '07:00-10:00',
      flexible_end_range: employee.flexible_end_range || '16:00-19:00',
      flexible_core_hours: employee.flexible_core_hours || '10:00-15:00',
      flexible_days_per_week: employee.flexible_days_per_week || 5
    });
    setShowEditModal(true);
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">TANSEEQ Tax Consultancy - {t('employees')}</h2>
          <div className="flex items-center space-x-2">
            <div className="text-sm text-gray-600">
              Total: {employees.length} employees
            </div>
            {(user?.role === 'admin' || user?.role === 'super_admin') && (
              <button
                onClick={openAddModal}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                إضافة موظف
              </button>
            )}
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('name')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  البريد الإلكتروني
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('role')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('position')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الراتب الشهري
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  المعدل اليومي
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ساعات العمل
                </th>
                {user?.role === 'super_admin' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('actions')}
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {employees.map((employee) => (
                <tr key={employee.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <UserIcon className="h-8 w-8 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">{employee.name}</div>
                        <div className="text-sm text-gray-500">{employee.phone}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {employee.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      employee.role === 'super_admin' ? 'bg-purple-100 text-purple-800' :
                      employee.role === 'admin' ? 'bg-blue-100 text-blue-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {t(employee.role)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {employee.position}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="font-medium">AED {employee.monthly_salary.toLocaleString()}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>AED {employee.daily_rate.toFixed(2)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>{employee.working_hours_start} - {employee.working_hours_end}</div>
                    {employee.has_custom_schedule && (
                      <div className="text-xs text-blue-600">Custom Schedule</div>
                    )}
                    {employee.has_flexible_schedule && (
                      <div className="text-xs text-green-600">دوام مرن</div>
                    )}
                  </td>
                  {user?.role === 'super_admin' && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => openEditModal(employee)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Edit Employee"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => openPasswordModal(employee)}
                          className="text-green-600 hover:text-green-900"
                          title="Change Password"
                        >
                          <ExclamationCircleIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteEmployee(employee)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete Employee"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Employee Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                إضافة موظف جديد
              </h3>
              <form onSubmit={handleAddEmployee} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الاسم</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">البريد الإلكتروني</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">كلمة المرور</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الدور</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="user">موظف</option>
                    <option value="admin">مدير</option>
                    <option value="super_admin">مدير عام</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">المنصب</label>
                  <input
                    type="text"
                    value={formData.position}
                    onChange={(e) => setFormData({...formData, position: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الراتب الشهري (AED)</label>
                  <input
                    type="number"
                    value={formData.monthly_salary}
                    onChange={(e) => setFormData({...formData, monthly_salary: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">بداية الدوام</label>
                    <input
                      type="time"
                      value={formData.working_hours_start}
                      onChange={(e) => setFormData({...formData, working_hours_start: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">نهاية الدوام</label>
                    <input
                      type="time"
                      value={formData.working_hours_end}
                      onChange={(e) => setFormData({...formData, working_hours_end: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                <div className="border-t pt-4">
                  <label className="flex items-center space-x-2 mb-4">
                    <input
                      type="checkbox"
                      checked={formData.has_flexible_schedule}
                      onChange={(e) => setFormData({...formData, has_flexible_schedule: e.target.checked})}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium text-gray-700">تفعيل الدوام المرن</span>
                  </label>

                  {formData.has_flexible_schedule && (
                    <div className="space-y-4 bg-blue-50 p-4 rounded-md">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">ساعات العمل اليومية</label>
                          <input
                            type="number"
                            value={formData.flexible_hours_per_day}
                            onChange={(e) => setFormData({...formData, flexible_hours_per_day: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="1"
                            max="12"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">أيام العمل الأسبوعية</label>
                          <input
                            type="number"
                            value={formData.flexible_days_per_week}
                            onChange={(e) => setFormData({...formData, flexible_days_per_week: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="1"
                            max="7"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">نطاق بداية الدوام (مثال: 07:00-10:00)</label>
                        <input
                          type="text"
                          value={formData.flexible_start_range}
                          onChange={(e) => setFormData({...formData, flexible_start_range: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="07:00-10:00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">نطاق نهاية الدوام (مثال: 16:00-19:00)</label>
                        <input
                          type="text"
                          value={formData.flexible_end_range}
                          onChange={(e) => setFormData({...formData, flexible_end_range: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="16:00-19:00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">ساعات الحضور الأساسية (مثال: 10:00-15:00)</label>
                        <input
                          type="text"
                          value={formData.flexible_core_hours}
                          onChange={(e) => setFormData({...formData, flexible_core_hours: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="10:00-15:00"
                        />
                        <p className="text-xs text-gray-500 mt-1">الساعات التي يجب على الموظف التواجد فيها</p>
                      </div>
                    </div>
                  )}
                </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">رقم الهاتف</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex space-x-2">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  >
                    إضافة الموظف
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
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

      {/* Edit Employee Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                تعديل بيانات الموظف - {selectedEmployee?.name}
              </h3>
              <form onSubmit={handleEditEmployee} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الاسم</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">البريد الإلكتروني</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الدور</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="user">موظف</option>
                    <option value="admin">مدير</option>
                    <option value="super_admin">مدير عام</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">المنصب</label>
                  <input
                    type="text"
                    value={formData.position}
                    onChange={(e) => setFormData({...formData, position: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">الراتب الشهري (AED)</label>
                  <input
                    type="number"
                    value={formData.monthly_salary}
                    onChange={(e) => setFormData({...formData, monthly_salary: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">بداية الدوام</label>
                    <input
                      type="time"
                      value={formData.working_hours_start}
                      onChange={(e) => setFormData({...formData, working_hours_start: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">نهاية الدوام</label>
                    <input
                      type="time"
                      value={formData.working_hours_end}
                      onChange={(e) => setFormData({...formData, working_hours_end: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                <div className="border-t pt-4 col-span-2">
                  <label className="flex items-center space-x-2 mb-4">
                    <input
                      type="checkbox"
                      checked={formData.has_flexible_schedule}
                      onChange={(e) => setFormData({...formData, has_flexible_schedule: e.target.checked})}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium text-gray-700">تفعيل الدوام المرن</span>
                  </label>

                  {formData.has_flexible_schedule && (
                    <div className="space-y-4 bg-blue-50 p-4 rounded-md">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">ساعات العمل اليومية</label>
                          <input
                            type="number"
                            value={formData.flexible_hours_per_day}
                            onChange={(e) => setFormData({...formData, flexible_hours_per_day: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="1"
                            max="12"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">أيام العمل الأسبوعية</label>
                          <input
                            type="number"
                            value={formData.flexible_days_per_week}
                            onChange={(e) => setFormData({...formData, flexible_days_per_week: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            min="1"
                            max="7"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">نطاق بداية الدوام (مثال: 07:00-10:00)</label>
                        <input
                          type="text"
                          value={formData.flexible_start_range}
                          onChange={(e) => setFormData({...formData, flexible_start_range: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="07:00-10:00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">نطاق نهاية الدوام (مثال: 16:00-19:00)</label>
                        <input
                          type="text"
                          value={formData.flexible_end_range}
                          onChange={(e) => setFormData({...formData, flexible_end_range: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="16:00-19:00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">ساعات الحضور الأساسية (مثال: 10:00-15:00)</label>
                        <input
                          type="text"
                          value={formData.flexible_core_hours}
                          onChange={(e) => setFormData({...formData, flexible_core_hours: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="10:00-15:00"
                        />
                        <p className="text-xs text-gray-500 mt-1">الساعات التي يجب على الموظف التواجد فيها</p>
                      </div>
                    </div>
                  )}
                </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">رقم الهاتف</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex space-x-2">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  >
                    حفظ التعديلات
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
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

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                تغيير كلمة المرور - {selectedEmployee?.name}
              </h3>
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
                <p className="text-sm text-yellow-800">
                  ⚠️ ملاحظة: كلمات المرور مشفرة ولا يمكن عرضها. سيتم تعيين كلمة مرور جديدة.
                </p>
              </div>
              <div className="mt-2 px-7 py-3">
                <label className="block text-sm font-medium text-gray-700 mb-2 text-right">كلمة المرور الجديدة</label>
                <input
                  type="text"
                  placeholder="أدخل كلمة المرور الجديدة"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-2 text-right">يرجى حفظ كلمة المرور ومشاركتها مع الموظف</p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleChangePassword}
                  className="px-4 py-2 bg-blue-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                >
                  تأكيد تغيير كلمة المرور
                </button>
                <button
                  onClick={() => {
                    setShowPasswordModal(false);
                    setNewPassword('');
                    setSelectedEmployee(null);
                  }}
                  className="mt-3 px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-300"
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

// Field Exit Component

export default Employees;
