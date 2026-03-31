import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DocumentArrowDownIcon, EnvelopeIcon, ArrowPathIcon, ClockIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SalarySlips = () => {
  const [employees, setEmployees] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [selectedCycle, setSelectedCycle] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState({});
  const [emailing, setEmailing] = useState({});
  const [bulkEmailing, setBulkEmailing] = useState(false);
  const [emailLogs, setEmailLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('slips');
  const [emailPrefs, setEmailPrefs] = useState([]);
  const [testingEmail, setTestingEmail] = useState(false);
  const [slipsData, setSlipsData] = useState([]);
  // Auto Report state
  const [autoConfig, setAutoConfig] = useState({ enabled: false, day_of_month: 28, last_run: null });
  const [autoHistory, setAutoHistory] = useState([]);
  const [sendingReports, setSendingReports] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);

  useEffect(() => {
    fetchData();
    fetchAutoConfig();
  }, []);

  const fetchData = async () => {
    try {
      const results = await Promise.allSettled([
        axios.get(`${API}/users`),
        axios.get(`${API}/payroll/cycles`),
        axios.get(`${API}/email/logs`),
        axios.get(`${API}/email/preferences`)
      ]);
      if (results[0].status === 'fulfilled') setEmployees(Array.isArray(results[0].value?.data) ? results[0].value.data : []);
      if (results[1].status === 'fulfilled') {
        const cyclesData = Array.isArray(results[1].value?.data) ? results[1].value.data : [];
        setCycles(cyclesData);
        if (cyclesData.length > 0) setSelectedCycle(cyclesData[0].month);
      }
      if (results[2].status === 'fulfilled') setEmailLogs(results[2].value?.data?.logs || []);
      if (results[3].status === 'fulfilled') setEmailPrefs(results[3].value?.data?.preferences || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSlip = async (employeeId) => {
    if (!selectedCycle) return alert('اختر دورة الرواتب أولاً');
    setGenerating(prev => ({...prev, [employeeId]: true}));
    try {
      const res = await axios.get(`${API}/salary-slip/${employeeId}/${selectedCycle}`);
      if (res.data.success && res.data.file_content) {
        const byteChars = atob(res.data.file_content);
        const byteNums = new Array(byteChars.length);
        for (let i = 0; i < byteChars.length; i++) byteNums[i] = byteChars.charCodeAt(i);
        const blob = new Blob([new Uint8Array(byteNums)], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = res.data.filename;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      alert('خطأ في إنشاء قسيمة الراتب');
    } finally {
      setGenerating(prev => ({...prev, [employeeId]: false}));
    }
  };

  const handleEmailSlip = async (employeeId) => {
    if (!selectedCycle) return alert('اختر دورة الرواتب أولاً');
    setEmailing(prev => ({...prev, [employeeId]: true}));
    try {
      const res = await axios.post(`${API}/email/send-salary-slip`, {
        employee_id: employeeId,
        cycle_month: selectedCycle
      });
      if (res.data.success) {
        alert('تم إرسال قسيمة الراتب بالبريد بنجاح');
        fetchData();
      } else {
        alert(res.data.error || 'خطأ في الإرسال');
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'خطأ في إرسال البريد');
    } finally {
      setEmailing(prev => ({...prev, [employeeId]: false}));
    }
  };

  const handleBulkEmail = async () => {
    if (!selectedCycle) return alert('اختر دورة الرواتب أولاً');
    if (!window.confirm(`هل تريد إرسال قسائم الرواتب لجميع الموظفين عن شهر ${selectedCycle}؟`)) return;
    setBulkEmailing(true);
    try {
      const res = await axios.post(`${API}/email/send-bulk-salary-slips`, {
        cycle_month: selectedCycle
      });
      alert(`تم الإرسال: ${res.data.sent} | فشل: ${res.data.failed}`);
      fetchData();
    } catch (error) {
      alert('خطأ في الإرسال الجماعي');
    } finally {
      setBulkEmailing(false);
    }
  };

  const handleTestEmail = async () => {
    setTestingEmail(true);
    try {
      const res = await axios.post(`${API}/email/test`);
      alert(res.data.success ? 'تم اختبار البريد بنجاح!' : `فشل: ${res.data.error}`);
    } catch (error) {
      alert('فشل اختبار البريد');
    } finally {
      setTestingEmail(false);
    }
  };

  const handleLoadSlips = async () => {
    if (!selectedCycle) return;
    try {
      const res = await axios.post(`${API}/salary-slips/bulk/${selectedCycle}`, {});
      setSlipsData(res.data.slips || []);
    } catch (error) {
      console.error('Error loading slips:', error);
    }
  };

  useEffect(() => {
    if (selectedCycle) handleLoadSlips();
  }, [selectedCycle]);

  const handleSavePrefs = async () => {
    try {
      await axios.put(`${API}/email/preferences`, { preferences: emailPrefs });
      alert('تم حفظ إعدادات البريد');
    } catch (error) {
      alert('خطأ في حفظ الإعدادات');
    }
  };

  // ===== Auto Report Functions =====
  const fetchAutoConfig = async () => {
    try {
      const [configRes, historyRes] = await Promise.allSettled([
        axios.get(`${API}/payroll/auto-report-config`),
        axios.get(`${API}/payroll/auto-report-history`)
      ]);
      if (configRes.status === 'fulfilled') setAutoConfig(configRes.value.data);
      if (historyRes.status === 'fulfilled') setAutoHistory(historyRes.value.data.runs || []);
    } catch (e) { console.error(e); }
  };

  const handleSaveAutoConfig = async () => {
    setSavingConfig(true);
    try {
      await axios.put(`${API}/payroll/auto-report-config`, {
        enabled: autoConfig.enabled,
        day_of_month: autoConfig.day_of_month
      });
      alert(autoConfig.enabled ? `تم تفعيل الإرسال التلقائي في يوم ${autoConfig.day_of_month} من كل شهر` : 'تم إيقاف الإرسال التلقائي');
      fetchAutoConfig();
    } catch (e) { alert('خطأ في حفظ الإعدادات'); }
    finally { setSavingConfig(false); }
  };

  const handleSendReportsNow = async () => {
    if (!selectedCycle) return alert('اختر دورة الرواتب أولاً');
    if (!window.confirm(`سيتم إرسال التقرير الشهري (ملخص + PDF) لجميع الموظفين عن شهر ${selectedCycle}. متابعة؟`)) return;
    setSendingReports(true);
    try {
      const res = await axios.post(`${API}/payroll/send-monthly-reports`, { cycle_month: selectedCycle });
      alert(`تم الإرسال: ${res.data.sent} ناجح | ${res.data.failed} فاشل من أصل ${res.data.total}`);
      fetchAutoConfig();
    } catch (e) { alert('خطأ في إرسال التقارير'); }
    finally { setSendingReports(false); }
  };

  if (loading) return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>;

  return (
    <div className="p-6 max-w-7xl mx-auto" data-testid="salary-slips-page">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">قسائم الرواتب والبريد الإلكتروني</h2>
        <div className="flex items-center space-x-3 space-x-reverse">
          <select value={selectedCycle} onChange={e => setSelectedCycle(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm" data-testid="cycle-select">
            <option value="">اختر الدورة</option>
            {cycles.map(c => <option key={c.id || c.month} value={c.month}>{c.month}</option>)}
          </select>
        </div>
      </div>

      <div className="flex space-x-1 space-x-reverse mb-6 bg-gray-100 rounded-lg p-1">
        {[
          { id: 'slips', label: 'قسائم الرواتب', icon: DocumentArrowDownIcon },
          { id: 'auto', label: 'التقرير التلقائي', icon: ClockIcon },
          { id: 'email', label: 'إعدادات البريد', icon: EnvelopeIcon },
          { id: 'logs', label: 'سجل الإرسال', icon: ArrowPathIcon }
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-600 hover:text-gray-800'
            }`} data-testid={`salary-tab-${tab.id}`}>
            <tab.icon className="h-4 w-4 ml-2" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'slips' && (
        <div className="bg-white rounded-lg shadow-sm border" data-testid="slips-section">
          <div className="p-4 border-b flex justify-between items-center">
            <h3 className="font-semibold">قسائم الرواتب - {selectedCycle || 'اختر دورة'}</h3>
            <button onClick={handleBulkEmail} disabled={bulkEmailing || !selectedCycle}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm disabled:opacity-50"
              data-testid="bulk-email-btn">
              <EnvelopeIcon className="h-4 w-4 ml-1" />
              {bulkEmailing ? 'جاري الإرسال...' : 'إرسال الكل بالبريد'}
            </button>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">الموظف</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">البريد</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">الراتب</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">الخصومات</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">الصافي</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {employees.map(emp => {
                const slip = slipsData.find(s => s.employee_id === emp.id) || {};
                return (
                  <tr key={emp.id}>
                    <td className="px-4 py-3 text-sm font-medium">{emp.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{emp.email}</td>
                    <td className="px-4 py-3 text-sm">{(slip.basic_salary || emp.monthly_salary || 0).toLocaleString()} AED</td>
                    <td className="px-4 py-3 text-sm text-red-600">{(slip.total_deductions || 0).toLocaleString()} AED</td>
                    <td className="px-4 py-3 text-sm font-semibold text-green-700">{(slip.net_salary || emp.monthly_salary || 0).toLocaleString()} AED</td>
                    <td className="px-4 py-3">
                      <div className="flex space-x-2 space-x-reverse">
                        <button onClick={() => handleGenerateSlip(emp.id)} disabled={generating[emp.id]}
                          className="flex items-center px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200 disabled:opacity-50"
                          title="تحميل PDF" data-testid={`download-slip-${emp.id}`}>
                          <DocumentArrowDownIcon className="h-3.5 w-3.5 ml-1" />
                          {generating[emp.id] ? '...' : 'PDF'}
                        </button>
                        <button onClick={() => handleEmailSlip(emp.id)} disabled={emailing[emp.id]}
                          className="flex items-center px-2 py-1 bg-green-100 text-green-700 rounded text-xs hover:bg-green-200 disabled:opacity-50"
                          title="إرسال بالبريد" data-testid={`email-slip-${emp.id}`}>
                          <EnvelopeIcon className="h-3.5 w-3.5 ml-1" />
                          {emailing[emp.id] ? '...' : 'بريد'}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'auto' && (
        <div className="space-y-5" data-testid="auto-report-section">
          {/* Manual trigger card */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-lg text-gray-800">إرسال التقارير الشهرية الآن</h3>
                <p className="text-sm text-gray-500 mt-1">إرسال ملخص الحضور + كشف الراتب PDF لجميع الموظفين</p>
              </div>
              <button
                data-testid="send-reports-now-btn"
                onClick={handleSendReportsNow}
                disabled={sendingReports || !selectedCycle}
                className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all font-medium"
              >
                {sendingReports ? (
                  <><ArrowPathIcon className="h-5 w-5 animate-spin" /> جاري الإرسال...</>
                ) : (
                  <><EnvelopeIcon className="h-5 w-5" /> إرسال التقارير</>
                )}
              </button>
            </div>
            <p className="text-xs text-gray-400">الدورة المحددة: <strong>{selectedCycle || 'لم يتم التحديد'}</strong></p>
          </div>

          {/* Auto scheduler config */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="font-bold text-lg text-gray-800 mb-4">
              <ClockIcon className="h-5 w-5 inline ml-2 text-blue-600" />
              الإرسال التلقائي الشهري
            </h3>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 p-4 bg-gray-50 rounded-lg">
              <label className="flex items-center gap-3 cursor-pointer">
                <div className="relative">
                  <input
                    data-testid="auto-report-toggle"
                    type="checkbox"
                    checked={autoConfig.enabled}
                    onChange={e => setAutoConfig({ ...autoConfig, enabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:right-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </div>
                <span className="font-medium text-gray-700">{autoConfig.enabled ? 'مفعّل' : 'معطّل'}</span>
              </label>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">يوم الإرسال:</span>
                <select
                  data-testid="auto-report-day"
                  value={autoConfig.day_of_month}
                  onChange={e => setAutoConfig({ ...autoConfig, day_of_month: parseInt(e.target.value) })}
                  className="px-3 py-1.5 border rounded-lg text-sm"
                >
                  {Array.from({ length: 28 }, (_, i) => i + 1).map(d => (
                    <option key={d} value={d}>يوم {d}</option>
                  ))}
                </select>
                <span className="text-sm text-gray-500">من كل شهر</span>
              </div>
              <button
                data-testid="save-auto-config-btn"
                onClick={handleSaveAutoConfig}
                disabled={savingConfig}
                className="px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium disabled:opacity-50 transition-all"
              >
                {savingConfig ? 'جاري الحفظ...' : 'حفظ الإعدادات'}
              </button>
            </div>
            {autoConfig.enabled && (
              <p className="text-sm text-green-700 mt-3 bg-green-50 px-3 py-2 rounded-lg">
                سيتم إرسال التقارير تلقائياً في يوم <strong>{autoConfig.day_of_month}</strong> من كل شهر الساعة 8:00 صباحاً
              </p>
            )}
          </div>

          {/* Run history */}
          <div className="bg-white rounded-xl shadow-sm border">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="font-bold text-gray-800">سجل الإرسال التلقائي</h3>
              <button onClick={fetchAutoConfig} className="text-blue-600 text-sm hover:underline">تحديث</button>
            </div>
            {autoHistory.length === 0 ? (
              <div className="p-8 text-center text-gray-400">لا يوجد سجل إرسال بعد</div>
            ) : (
              <div className="divide-y">
                {autoHistory.map((run, i) => (
                  <div key={i} className="p-4 flex items-center justify-between hover:bg-gray-50">
                    <div>
                      <p className="font-medium text-sm">
                        الشهر: <strong>{run.cycle_month}</strong>
                        <span className="text-gray-400 text-xs mr-3">({run.triggered_by})</span>
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(run.run_at).toLocaleString('ar-EG')}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <span className="flex items-center gap-1 text-green-700 bg-green-50 px-2 py-1 rounded">
                        <CheckCircleIcon className="h-4 w-4" /> {run.sent} ناجح
                      </span>
                      {run.failed > 0 && (
                        <span className="flex items-center gap-1 text-red-700 bg-red-50 px-2 py-1 rounded">
                          <XCircleIcon className="h-4 w-4" /> {run.failed} فاشل
                        </span>
                      )}
                      <span className="text-gray-500">{run.total} موظف</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'email' && (
        <div className="space-y-4" data-testid="email-settings-section">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold">اختبار اتصال البريد</h3>
              <button onClick={handleTestEmail} disabled={testingEmail}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm disabled:opacity-50"
                data-testid="test-email-btn">
                {testingEmail ? 'جاري الاختبار...' : 'اختبار الاتصال'}
              </button>
            </div>
            <p className="text-sm text-gray-500">سيرسل بريد تجريبي للتحقق من صحة إعدادات SMTP</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="font-semibold mb-4">إعدادات إشعارات البريد التلقائية</h3>
            <div className="space-y-3">
              {[
                { type: 'lateness', label: 'إشعار التأخير', desc: 'إرسال بريد عند تسجيل تأخير' },
                { type: 'absence', label: 'إشعار الغياب', desc: 'إرسال بريد عند تسجيل غياب' },
                { type: 'advance_request', label: 'طلب سلفة جديد', desc: 'إشعار المدير عند تقديم طلب سلفة' }
              ].map(item => {
                const pref = emailPrefs.find(p => p.type === item.type) || { type: item.type, enabled: false, recipients: 'employee' };
                return (
                  <div key={item.type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-sm">{item.label}</p>
                      <p className="text-xs text-gray-500">{item.desc}</p>
                    </div>
                    <div className="flex items-center space-x-3 space-x-reverse">
                      <select value={pref.recipients} onChange={e => {
                        setEmailPrefs(emailPrefs.map(p => p.type === item.type ? {...p, recipients: e.target.value} : p));
                      }} className="px-2 py-1 border rounded text-xs">
                        <option value="employee">الموظف</option>
                        <option value="admin">المدير</option>
                        <option value="both">كلاهما</option>
                      </select>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" checked={pref.enabled}
                          onChange={e => {
                            const exists = emailPrefs.find(p => p.type === item.type);
                            if (exists) {
                              setEmailPrefs(emailPrefs.map(p => p.type === item.type ? {...p, enabled: e.target.checked} : p));
                            } else {
                              setEmailPrefs([...emailPrefs, { type: item.type, enabled: e.target.checked, recipients: 'employee' }]);
                            }
                          }}
                          className="sr-only peer" />
                        <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:right-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-green-600"></div>
                      </label>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-4 flex justify-end">
              <button onClick={handleSavePrefs}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                data-testid="save-email-prefs">حفظ الإعدادات</button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="bg-white rounded-lg shadow-sm border" data-testid="email-logs-section">
          <div className="p-4 border-b">
            <h3 className="font-semibold">سجل إرسال البريد الإلكتروني</h3>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">الموظف</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">البريد</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">النوع</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">الدورة</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">تاريخ الإرسال</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {emailLogs.length === 0 ? (
                <tr><td colSpan="5" className="px-4 py-8 text-center text-gray-400">لا توجد سجلات إرسال بعد</td></tr>
              ) : emailLogs.map((log, i) => (
                <tr key={i}>
                  <td className="px-4 py-3 text-sm">{log.employee_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{log.email}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                      {log.type === 'salary_slip' ? 'قسيمة راتب' : log.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{log.cycle_month}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{new Date(log.sent_at).toLocaleString('ar-EG')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default SalarySlips;
