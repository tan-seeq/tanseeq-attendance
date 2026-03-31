import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Cog6ToothIcon, UserGroupIcon, TrashIcon, PlusIcon, ArrowPathIcon, DocumentArrowDownIcon } from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminConfig = () => {
  const [activeTab, setActiveTab] = useState('system');
  const [config, setConfig] = useState(null);
  const [exceptions, setExceptions] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAddException, setShowAddException] = useState(false);
  const [newException, setNewException] = useState({
    employee_id: '', custom_start: '09:00', custom_end: '18:00',
    grace_period: 15, exempt_from_deductions: false, reason: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const results = await Promise.allSettled([
        axios.get(`${API}/admin/config/system`),
        axios.get(`${API}/admin/config/exceptions`),
        axios.get(`${API}/admin/config/import-mappings`),
        axios.get(`${API}/users`)
      ]);
      if (results[0].status === 'fulfilled') setConfig(results[0].value.data.config);
      if (results[1].status === 'fulfilled') setExceptions(results[1].value.data.exceptions);
      if (results[2].status === 'fulfilled') setMappings(results[2].value.data.mappings);
      if (results[3].status === 'fulfilled') setEmployees(Array.isArray(results[3].value.data) ? results[3].value.data : []);
    } catch (error) {
      console.error('Error fetching config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/config/system`, config);
      alert('تم حفظ الإعدادات بنجاح');
    } catch (error) {
      alert('خطأ في حفظ الإعدادات');
    } finally {
      setSaving(false);
    }
  };

  const handleAddException = async () => {
    try {
      const res = await axios.post(`${API}/admin/config/exceptions`, newException);
      setExceptions([...exceptions, res.data.exception]);
      setShowAddException(false);
      setNewException({ employee_id: '', custom_start: '09:00', custom_end: '18:00', grace_period: 15, exempt_from_deductions: false, reason: '' });
    } catch (error) {
      alert(error.response?.data?.detail || 'خطأ في إضافة الاستثناء');
    }
  };

  const handleDeleteException = async (employeeId) => {
    if (!window.confirm('هل تريد حذف هذا الاستثناء؟')) return;
    try {
      await axios.delete(`${API}/admin/config/exceptions/${employeeId}`);
      setExceptions(exceptions.filter(e => e.employee_id !== employeeId));
    } catch (error) {
      alert('خطأ في حذف الاستثناء');
    }
  };

  const handleSaveMappings = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/config/import-mappings`, { mappings });
      alert('تم حفظ خرائط الاستيراد بنجاح');
    } catch (error) {
      alert('خطأ في حفظ خرائط الاستيراد');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>;

  const tabs = [
    { id: 'system', label: 'إعدادات النظام', icon: Cog6ToothIcon },
    { id: 'exceptions', label: 'استثناءات الحضور', icon: UserGroupIcon },
    { id: 'mappings', label: 'خرائط الاستيراد', icon: DocumentArrowDownIcon }
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto" data-testid="admin-config-page">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">لوحة إعدادات النظام</h2>

      <div className="flex space-x-1 space-x-reverse mb-6 bg-gray-100 rounded-lg p-1">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-600 hover:text-gray-800'
            }`}
            data-testid={`config-tab-${tab.id}`}
          >
            <tab.icon className="h-4 w-4 ml-2" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'system' && config && (
        <div className="bg-white rounded-lg shadow-sm border p-6" data-testid="system-config-section">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">إعدادات النظام العامة</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">اسم الشركة</label>
              <input type="text" value={config.company_name || ''} onChange={e => setConfig({...config, company_name: e.target.value})}
                className="w-full px-3 py-2 border rounded-md" data-testid="config-company-name" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">المنطقة الزمنية</label>
              <input type="text" value={config.timezone || ''} onChange={e => setConfig({...config, timezone: e.target.value})}
                className="w-full px-3 py-2 border rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">بداية ساعات العمل</label>
              <input type="time" value={config.working_hours_start || '09:00'} onChange={e => setConfig({...config, working_hours_start: e.target.value})}
                className="w-full px-3 py-2 border rounded-md" data-testid="config-work-start" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">نهاية ساعات العمل</label>
              <input type="time" value={config.working_hours_end || '18:00'} onChange={e => setConfig({...config, working_hours_end: e.target.value})}
                className="w-full px-3 py-2 border rounded-md" data-testid="config-work-end" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">فترة السماح (دقائق)</label>
              <input type="number" value={config.grace_period_minutes || 15} onChange={e => setConfig({...config, grace_period_minutes: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border rounded-md" data-testid="config-grace-period" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">أيام العطلة</label>
              <div className="flex flex-wrap gap-2 mt-1">
                {['sunday','monday','tuesday','wednesday','thursday','friday','saturday'].map(day => (
                  <label key={day} className="flex items-center space-x-1 space-x-reverse bg-gray-50 px-2 py-1 rounded">
                    <input type="checkbox" checked={(config.weekend_days || []).includes(day)}
                      onChange={e => {
                        const days = config.weekend_days || [];
                        setConfig({...config, weekend_days: e.target.checked ? [...days, day] : days.filter(d => d !== day)});
                      }} className="h-3.5 w-3.5" />
                    <span className="text-xs">{{'sunday':'الأحد','monday':'الإثنين','tuesday':'الثلاثاء','wednesday':'الأربعاء','thursday':'الخميس','friday':'الجمعة','saturday':'السبت'}[day]}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex items-center space-x-3 space-x-reverse">
              <input type="checkbox" checked={config.overtime_enabled || false} onChange={e => setConfig({...config, overtime_enabled: e.target.checked})}
                className="h-4 w-4" />
              <label className="text-sm text-gray-700">تفعيل حساب العمل الإضافي</label>
            </div>
            <div className="flex items-center space-x-3 space-x-reverse">
              <input type="checkbox" checked={config.auto_deduction_enabled || false} onChange={e => setConfig({...config, auto_deduction_enabled: e.target.checked})}
                className="h-4 w-4" />
              <label className="text-sm text-gray-700">تفعيل الخصم التلقائي</label>
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <button onClick={handleSaveConfig} disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              data-testid="save-system-config">
              {saving ? 'جاري الحفظ...' : 'حفظ الإعدادات'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'exceptions' && (
        <div className="bg-white rounded-lg shadow-sm border p-6" data-testid="exceptions-section">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-800">استثناءات الحضور</h3>
            <button onClick={() => setShowAddException(true)}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
              data-testid="add-exception-btn">
              <PlusIcon className="h-4 w-4 ml-1" /> إضافة استثناء
            </button>
          </div>

          {showAddException && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4" data-testid="add-exception-form">
              <h4 className="font-medium text-green-800 mb-3">إضافة استثناء جديد</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <select value={newException.employee_id} onChange={e => setNewException({...newException, employee_id: e.target.value})}
                  className="px-3 py-2 border rounded-md" data-testid="exception-employee-select">
                  <option value="">اختر الموظف</option>
                  {employees.filter(emp => !exceptions.find(ex => ex.employee_id === emp.id)).map(emp => (
                    <option key={emp.id} value={emp.id}>{emp.name}</option>
                  ))}
                </select>
                <input type="time" value={newException.custom_start} onChange={e => setNewException({...newException, custom_start: e.target.value})}
                  className="px-3 py-2 border rounded-md" placeholder="بداية الدوام" />
                <input type="time" value={newException.custom_end} onChange={e => setNewException({...newException, custom_end: e.target.value})}
                  className="px-3 py-2 border rounded-md" placeholder="نهاية الدوام" />
                <input type="number" value={newException.grace_period} onChange={e => setNewException({...newException, grace_period: parseInt(e.target.value)})}
                  className="px-3 py-2 border rounded-md" placeholder="فترة السماح" />
                <input type="text" value={newException.reason} onChange={e => setNewException({...newException, reason: e.target.value})}
                  className="px-3 py-2 border rounded-md" placeholder="السبب" />
                <label className="flex items-center space-x-2 space-x-reverse px-3 py-2">
                  <input type="checkbox" checked={newException.exempt_from_deductions}
                    onChange={e => setNewException({...newException, exempt_from_deductions: e.target.checked})} className="h-4 w-4" />
                  <span className="text-sm">معفى من الخصومات</span>
                </label>
              </div>
              <div className="flex justify-end space-x-2 space-x-reverse mt-3">
                <button onClick={() => setShowAddException(false)} className="px-4 py-1.5 bg-gray-200 rounded-md text-sm">إلغاء</button>
                <button onClick={handleAddException} disabled={!newException.employee_id}
                  className="px-4 py-1.5 bg-green-600 text-white rounded-md text-sm disabled:opacity-50" data-testid="confirm-add-exception">حفظ</button>
              </div>
            </div>
          )}

          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">الموظف</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">بداية الدوام</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">نهاية الدوام</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">فترة السماح</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">معفى</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">السبب</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {exceptions.length === 0 ? (
                <tr><td colSpan="7" className="px-4 py-8 text-center text-gray-400">لا توجد استثناءات حالياً</td></tr>
              ) : exceptions.map(ex => (
                <tr key={ex.employee_id}>
                  <td className="px-4 py-3 text-sm font-medium">{ex.employee_name}</td>
                  <td className="px-4 py-3 text-sm">{ex.custom_start}</td>
                  <td className="px-4 py-3 text-sm">{ex.custom_end}</td>
                  <td className="px-4 py-3 text-sm">{ex.grace_period} دقيقة</td>
                  <td className="px-4 py-3 text-sm">{ex.exempt_from_deductions ? 'نعم' : 'لا'}</td>
                  <td className="px-4 py-3 text-sm">{ex.reason}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => handleDeleteException(ex.employee_id)} className="text-red-600 hover:text-red-800"
                      data-testid={`delete-exception-${ex.employee_id}`}>
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'mappings' && (
        <div className="bg-white rounded-lg shadow-sm border p-6" data-testid="mappings-section">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">خرائط استيراد البيانات</h3>
          <p className="text-sm text-gray-500 mb-4">حدد تطابق أعمدة ملفات الاستيراد مع حقول النظام</p>
          <table className="min-w-full divide-y divide-gray-200 mb-4">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">عمود المصدر</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">حقل النظام</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">النوع</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {mappings.map((m, i) => (
                <tr key={i}>
                  <td className="px-4 py-2"><input type="text" value={m.source_column} onChange={e => {
                    const updated = [...mappings]; updated[i].source_column = e.target.value; setMappings(updated);
                  }} className="w-full px-2 py-1 border rounded text-sm" /></td>
                  <td className="px-4 py-2"><input type="text" value={m.target_field} onChange={e => {
                    const updated = [...mappings]; updated[i].target_field = e.target.value; setMappings(updated);
                  }} className="w-full px-2 py-1 border rounded text-sm" /></td>
                  <td className="px-4 py-2"><input type="text" value={m.type || 'attendance'} onChange={e => {
                    const updated = [...mappings]; updated[i].type = e.target.value; setMappings(updated);
                  }} className="w-full px-2 py-1 border rounded text-sm" /></td>
                  <td className="px-4 py-2">
                    <button onClick={() => setMappings(mappings.filter((_, idx) => idx !== i))} className="text-red-500 hover:text-red-700">
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex justify-between">
            <button onClick={() => setMappings([...mappings, {source_column: '', target_field: '', type: 'attendance'}])}
              className="flex items-center text-sm text-blue-600 hover:text-blue-800">
              <PlusIcon className="h-4 w-4 ml-1" /> إضافة صف
            </button>
            <button onClick={handleSaveMappings} disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              data-testid="save-mappings">
              {saving ? 'جاري الحفظ...' : 'حفظ الخرائط'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminConfig;
