import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  PlusIcon, CheckCircleIcon, XCircleIcon, XMarkIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { API } from '../../config';

const FieldExits = () => {
  const [fieldExits, setFieldExits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    visit_type: 'client_visit',
    client_name: '',
    expected_start_time: '',
    expected_end_time: '',
    report: ''
  });
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    fetchFieldExits();
  }, []);

  const fetchFieldExits = async () => {
    try {
      const response = await axios.get(`${API}/field-exits`);
      setFieldExits(response.data);
    } catch (error) {
      console.error('Error fetching field exits:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('visit_type', formData.visit_type);
      formDataToSend.append('client_name', formData.client_name);
      formDataToSend.append('expected_start_time', formData.expected_start_time);
      formDataToSend.append('expected_end_time', formData.expected_end_time);
      formDataToSend.append('report', formData.report);
      
      await axios.post(`${API}/field-exits`, formDataToSend);
      
      setShowModal(false);
      setFormData({
        visit_type: 'client_visit',
        client_name: '',
        expected_start_time: '',
        expected_end_time: '',
        report: ''
      });
      fetchFieldExits();
      alert('تم إنشاء طلب الخروج بنجاح');
    } catch (error) {
      console.error('Error creating field exit:', error);
      alert('حدث خطأ في إنشاء طلب الخروج');
    }
  };

  const handleDepartureTime = async (id) => {
    try {
      await axios.post(`${API}/field-exits/${id}/start`);
      fetchFieldExits();
      alert('تم تسجيل وقت الذهاب بنجاح');
    } catch (error) {
      console.error('Error recording departure time:', error);
      alert('حدث خطأ في تسجيل وقت الذهاب');
    }
  };

  // State for visit report modal
  const [showReportModal, setShowReportModal] = useState(false);
  const [selectedFieldExit, setSelectedFieldExit] = useState(null);
  const [visitReport, setVisitReport] = useState({
    detailed_report: '',
    accomplishments: '',
    challenges: '',
    next_steps: ''
  });

  const handleSubmitReport = async (id) => {
    const fieldExit = fieldExits.find(fe => fe.id === id);
    if (fieldExit.exit_status !== 'departed') {
      alert('يجب أولاً تسجيل وقت المغادرة');
      return;
    }
    
    setSelectedFieldExit(fieldExit);
    setShowReportModal(true);
    setVisitReport({
      detailed_report: '',
      accomplishments: '',
      challenges: '',
      next_steps: ''
    });
  };

  const submitVisitReport = async () => {
    if (!visitReport.detailed_report || visitReport.detailed_report.trim().length < 20) {
      alert('يجب أن يحتوي التقرير المفصل على 20 حرف على الأقل');
      return;
    }

    try {
      await axios.post(`${API}/field-exits/${selectedFieldExit.id}/report`, visitReport);
      setShowReportModal(false);
      fetchFieldExits();
      alert('تم إرسال تقرير الزيارة بنجاح! يمكنك الآن تسجيل وقت العودة');
    } catch (error) {
      console.error('Error submitting report:', error);
      if (error.response?.data?.detail) {
        const d = error.response.data.detail;
        alert(typeof d === 'string' ? d : 'حدث خطأ في إرسال التقرير');
      } else {
        alert('حدث خطأ في إرسال التقرير');
      }
    }
  };

  const handleReturnTime = async (id) => {
    const fieldExit = fieldExits.find(fe => fe.id === id);
    
    // Check if report is already submitted
    if (fieldExit.exit_status !== 'report_submitted') {
      alert('يجب كتابة تقرير مفصل عن الزيارة قبل تسجيل وقت العودة');
      return;
    }
    
    try {
      await axios.post(`${API}/field-exits/${id}/end`);
      fetchFieldExits();
      alert('تم تسجيل وقت العودة بنجاح');
    } catch (error) {
      console.error('Error recording return time:', error);
      if (error.response?.data?.detail) {
        const d = error.response.data.detail;
        alert(typeof d === 'string' ? d : 'حدث خطأ في تسجيل وقت العودة');
      } else {
        alert('حدث خطأ في تسجيل وقت العودة');
      }
    }
  };

  const handleApprove = async (id) => {
    try {
      await axios.post(`${API}/field-exits/${id}/approve`);
      fetchFieldExits();
    } catch (error) {
      console.error('Error approving field exit:', error);
    }
  };

  const handleReject = async (id) => {
    try {
      await axios.post(`${API}/field-exits/${id}/reject`);
      fetchFieldExits();
    } catch (error) {
      console.error('Error rejecting field exit:', error);
    }
  };

  const visitTypeOptions = {
    client_visit: 'زيارة عميل',
    collection: 'تحصيل',
    bank_visit: 'زيارة بنك',
    personal: 'شخصي',
    admin_errand: 'مهمة إدارية'
  };

  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">خروج أثناء الدوام</h2>
          {user?.role === 'user' && (
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <PlusIcon className="h-4 w-4 inline mr-2" />
              طلب خروج
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
                  نوع الزيارة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  اسم العميل
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الوقت المتوقع
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الوقت الفعلي
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الحالة
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  الإجراءات
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {fieldExits.map((exit) => (
                <tr key={exit.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {exit.user_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {visitTypeOptions[exit.visit_type]}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {exit.client_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="text-xs">
                      <div>من: {exit.expected_start_time || exit.start_time}</div>
                      <div>إلى: {exit.expected_end_time || exit.end_time}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="text-xs">
                      <div>ذهب: {exit.actual_start_time || '-'}</div>
                      <div>عاد: {exit.actual_end_time || '-'}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      exit.status === 'approved' ? 'bg-green-100 text-green-800' :
                      exit.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {exit.status === 'approved' ? 'موافق عليه' : 
                       exit.status === 'rejected' ? 'مرفوض' : 'معلق'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex flex-col space-y-2">
                      {/* User Actions */}
                      {user?.role === 'user' && exit.user_id === user.id && exit.status === 'approved' && (
                        <div className="flex flex-col space-y-1">
                          {!exit.actual_start_time && (
                            <button
                              onClick={() => handleDepartureTime(exit.id)}
                              className="px-3 py-1 bg-blue-500 text-white text-xs rounded-md hover:bg-blue-600"
                            >
                              تسجيل الذهاب
                            </button>
                          )}
                          {exit.actual_start_time && exit.exit_status === 'departed' && (
                            <button
                              onClick={() => handleSubmitReport(exit.id)}
                              className="px-3 py-1 bg-orange-500 text-white text-xs rounded-md hover:bg-orange-600"
                            >
                              كتابة تقرير الزيارة
                            </button>
                          )}
                          {exit.exit_status === 'report_submitted' && !exit.actual_end_time && (
                            <button
                              onClick={() => handleReturnTime(exit.id)}
                              className="px-3 py-1 bg-green-500 text-white text-xs rounded-md hover:bg-green-600"
                            >
                              تسجيل العودة
                            </button>
                          )}
                          {exit.exit_status === 'report_submitted' && (
                            <span className="text-xs text-green-600 font-medium">
                              ✓ تم تسليم التقرير
                            </span>
                          )}
                        </div>
                      )}
                      
                      {/* Admin Actions */}
                      {user?.role !== 'user' && exit.status === 'pending' && (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleApprove(exit.id)}
                            className="text-green-600 hover:text-green-900"
                            title="Approve"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleReject(exit.id)}
                            className="text-red-600 hover:text-red-900"
                            title="Reject"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Field Exit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                طلب خروج أثناء الدوام
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    نوع الزيارة
                  </label>
                  <select
                    value={formData.visit_type}
                    onChange={(e) => setFormData({...formData, visit_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {Object.entries(visitTypeOptions).map(([key, value]) => (
                      <option key={key} value={key}>{value}</option>
                    ))}
                  </select>
                </div>

                {formData.visit_type === 'client_visit' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      اسم العميل
                    </label>
                    <input
                      type="text"
                      value={formData.client_name}
                      onChange={(e) => setFormData({...formData, client_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    وقت البداية المتوقع
                  </label>
                  <input
                    type="time"
                    value={formData.expected_start_time}
                    onChange={(e) => setFormData({...formData, expected_start_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    وقت النهاية المتوقع
                  </label>
                  <input
                    type="time"
                    value={formData.expected_end_time}
                    onChange={(e) => setFormData({...formData, expected_end_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    تقرير الزيارة
                  </label>
                  <textarea
                    value={formData.report}
                    onChange={(e) => setFormData({...formData, report: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="اكتب تفاصيل الزيارة..."
                  />
                </div>

                <div className="flex space-x-2">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    إنشاء الطلب
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    إلغاء
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Visit Report Modal */}
      {showReportModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-6 border w-full max-w-3xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  تقرير مفصل عن الزيارة الخارجية
                </h3>
                <button
                  onClick={() => setShowReportModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              
              {selectedFieldExit && (
                <div className="bg-gray-50 p-4 rounded-lg mb-6">
                  <h4 className="font-semibold mb-2">معلومات الزيارة</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>نوع الزيارة: <span className="font-medium">{visitTypeOptions[selectedFieldExit.visit_type]}</span></div>
                    <div>العميل: <span className="font-medium">{selectedFieldExit.client_name || 'غير محدد'}</span></div>
                    <div>التاريخ: <span className="font-medium">{selectedFieldExit.date}</span></div>
                    <div>وقت المغادرة: <span className="font-medium">{selectedFieldExit.actual_start_time}</span></div>
                  </div>
                </div>
              )}

              <form onSubmit={(e) => {e.preventDefault(); submitVisitReport();}} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    تقرير مفصل عن الزيارة* <span className="text-red-500">(الحد الأدنى 20 حرف)</span>
                  </label>
                  <textarea
                    value={visitReport.detailed_report}
                    onChange={(e) => setVisitReport({...visitReport, detailed_report: e.target.value})}
                    required
                    rows="4"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="اكتب تقريراً مفصلاً عما تم إنجازه في الزيارة، مثل: زيارة سوق الحراج للسيارات المستعملة، مقابلة العميل أحمد محمد، تسليم المستندات المطلوبة، مناقشة الاحتياجات المستقبلية..."
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    عدد الأحرف: {visitReport.detailed_report.length}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    الإنجازات المحققة
                  </label>
                  <textarea
                    value={visitReport.accomplishments}
                    onChange={(e) => setVisitReport({...visitReport, accomplishments: e.target.value})}
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ما الذي تم إنجازه بنجاح؟ (مثال: توقيع عقد، تحصيل دفعة، تسليم مستندات)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    التحديات أو المشاكل المواجهة
                  </label>
                  <textarea
                    value={visitReport.challenges}
                    onChange={(e) => setVisitReport({...visitReport, challenges: e.target.value})}
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="هل واجهت أي صعوبات أو تحديات؟ (اختياري)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    الخطوات التالية المطلوبة
                  </label>
                  <textarea
                    value={visitReport.next_steps}
                    onChange={(e) => setVisitReport({...visitReport, next_steps: e.target.value})}
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ما هي المتابعة المطلوبة؟ (مثال: اتصال تأكيدي، تسليم مستندات إضافية، زيارة أخرى)"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={visitReport.detailed_report.length < 20}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    إرسال التقرير
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowReportModal(false)}
                    className="px-6 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    إلغاء
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Protected Route Component

export default FieldExits;
