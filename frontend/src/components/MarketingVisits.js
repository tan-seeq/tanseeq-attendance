import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  PlayIcon, 
  StopIcon, 
  ClockIcon,
  MapPinIcon,
  UserIcon,
  BuildingOfficeIcon,
  DocumentTextIcon,
  CameraIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MarketingVisits = () => {
  const [activeVisit, setActiveVisit] = useState(null);
  const [visits, setVisits] = useState([]);
  const [showStartModal, setShowStartModal] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [gpsSupported, setGpsSupported] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);
  
  // Timer reference
  const timerRef = useRef(null);
  
  // بيانات بدء الزيارة
  const [startVisitData, setStartVisitData] = useState({
    client_name: '',
    location_name: '',
    area: '',
    purpose: 'client_meeting',
    purpose_details: '',
    gps_location: null
  });
  
  // بيانات تقرير إنهاء الزيارة
  const [visitReport, setVisitReport] = useState({
    summary: '',
    details: '',
    result: 'successful',
    next_actions: '',
    client_feedback: '',
    attachments: []
  });

  // Purpose options with Arabic translations
  const purposeOptions = [
    { value: 'client_meeting', label: 'لقاء عميل' },
    { value: 'marketing', label: 'تسويق' },
    { value: 'follow_up', label: 'متابعة' },
    { value: 'new_client', label: 'عميل جديد' },
    { value: 'document_collection', label: 'جمع مستندات' },
    { value: 'consultation', label: 'استشارة' },
    { value: 'site_visit', label: 'زيارة موقع' },
    { value: 'other', label: 'أخرى' }
  ];

  // Result options with Arabic translations
  const resultOptions = [
    { value: 'successful', label: 'ناجحة' },
    { value: 'partially_successful', label: 'ناجحة جزئياً' },
    { value: 'unsuccessful', label: 'غير ناجحة' },
    { value: 'rescheduled', label: 'أُجلت' },
    { value: 'client_unavailable', label: 'العميل غير متاح' }
  ];

  useEffect(() => {
    checkGPSSupport();
    fetchActiveVisit();
    fetchVisitsHistory();
  }, []);

  // إعداد Timer للزيارة النشطة
  useEffect(() => {
    if (activeVisit) {
      // حساب الوقت المنقضي من بداية الزيارة
      const startTime = new Date(activeVisit.start_time);
      
      timerRef.current = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now - startTime) / 1000 / 60); // بالدقائق
        setElapsedTime(elapsed);
      }, 1000);
      
      return () => {
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
      };
    }
  }, [activeVisit]);

  const checkGPSSupport = () => {
    if ('geolocation' in navigator) {
      setGpsSupported(true);
    } else {
      console.log('GPS not supported');
    }
  };

  const getCurrentLocation = () => {
    return new Promise((resolve, reject) => {
      if (!gpsSupported) {
        resolve(null);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: new Date().toISOString()
          };
          resolve(location);
        },
        (error) => {
          console.log('GPS Error:', error.message);
          resolve(null);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        }
      );
    });
  };

  const fetchActiveVisit = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/marketing-visits/active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.active_visit) {
        setActiveVisit(response.data.active_visit);
        setElapsedTime(response.data.active_visit.elapsed_minutes);
      }
    } catch (error) {
      console.error('Error fetching active visit:', error);
    }
  };

  const fetchVisitsHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/marketing-visits/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVisits(response.data.visits || []);
    } catch (error) {
      console.error('Error fetching visits history:', error);
    }
  };

  const handleStartVisit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // الحصول على الموقع الحالي
      const gpsLocation = await getCurrentLocation();
      
      const visitData = {
        ...startVisitData,
        gps_location: gpsLocation
      };

      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/marketing-visits/start`, visitData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('تم بدء الزيارة الخارجية بنجاح! 🎯');
      setShowStartModal(false);
      setStartVisitData({
        client_name: '',
        location_name: '',
        area: '',
        purpose: 'client_meeting',
        purpose_details: '',
        gps_location: null
      });
      
      await fetchActiveVisit();
    } catch (error) {
      console.error('Error starting visit:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في بدء الزيارة');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteVisit = async (e) => {
    e.preventDefault();
    
    // التحقق من اكتمال الحقول الإلزامية
    if (!visitReport.summary || visitReport.summary.length < 20) {
      alert('يجب أن يحتوي الملخص على 20 حرف على الأقل');
      return;
    }
    
    if (!visitReport.details || visitReport.details.length < 50) {
      alert('يجب أن تحتوي التفاصيل على 50 حرف على الأقل');
      return;
    }
    
    if (!visitReport.next_actions || visitReport.next_actions.length < 10) {
      alert('يجب تحديد الإجراءات القادمة (10 أحرف على الأقل)');
      return;
    }

    setLoading(true);

    try {
      // الحصول على الموقع الحالي
      const gpsLocation = await getCurrentLocation();
      
      const completionData = {
        visit_report: visitReport,
        gps_location: gpsLocation
      };

      const token = localStorage.getItem('token');
      await axios.post(`${API}/marketing-visits/${activeVisit.id}/complete`, completionData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('تم إنهاء الزيارة وإرسال التقرير بنجاح! ✅');
      setShowCompleteModal(false);
      setVisitReport({
        summary: '',
        details: '',
        result: 'successful',
        next_actions: '',
        client_feedback: '',
        attachments: []
      });
      
      setActiveVisit(null);
      setElapsedTime(0);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      
      await fetchVisitsHistory();
    } catch (error) {
      console.error('Error completing visit:', error);
      alert(error.response?.data?.detail || 'حدث خطأ في إنهاء الزيارة');
    } finally {
      setLoading(false);
    }
  };

  const formatElapsedTime = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}س ${mins}د` : `${mins}د`;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          🏢 الزيارات الخارجية التسويقية
        </h1>
        
        {!activeVisit && (
          <button
            onClick={() => setShowStartModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center"
          >
            <PlayIcon className="h-5 w-5 mr-2" />
            بدء زيارة جديدة
          </button>
        )}
      </div>

      {/* Active Visit Card */}
      {activeVisit && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-blue-900 mb-2">
                🎯 زيارة قيد التنفيذ
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center text-blue-700">
                  <UserIcon className="h-4 w-4 mr-2" />
                  العميل: <span className="font-medium mr-1">{activeVisit.client_name}</span>
                </div>
                <div className="flex items-center text-blue-700">
                  <MapPinIcon className="h-4 w-4 mr-2" />
                  المكان: <span className="font-medium mr-1">{activeVisit.location_name}</span>
                </div>
                <div className="flex items-center text-blue-700">
                  <BuildingOfficeIcon className="h-4 w-4 mr-2" />
                  المنطقة: <span className="font-medium mr-1">{activeVisit.area}</span>
                </div>
                <div className="flex items-center text-blue-700">
                  <ClockIcon className="h-4 w-4 mr-2" />
                  المدة: <span className="font-bold text-lg mr-1">{formatElapsedTime(elapsedTime)}</span>
                </div>
              </div>
            </div>
            
            <button
              onClick={() => setShowCompleteModal(true)}
              disabled={loading}
              className="bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center disabled:bg-gray-400"
            >
              <StopIcon className="h-5 w-5 mr-2" />
              إنهاء الزيارة
            </button>
          </div>
        </div>
      )}

      {/* Visits History */}
      <div className="bg-white shadow-lg rounded-xl overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">📋 تاريخ الزيارات</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">العميل</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">المكان</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الغرض</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">التاريخ</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">المدة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">النتيجة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الحالة</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {visits.map((visit) => (
                <tr key={visit.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {visit.client_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {visit.location_name} - {visit.area}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {visit.purpose_ar}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {visit.start_time_display}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {visit.duration_minutes ? formatElapsedTime(visit.duration_minutes) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {visit.result_ar || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      visit.status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : visit.status === 'started'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {visit.status === 'completed' ? 'مكتملة' : 
                       visit.status === 'started' ? 'جارية' : 'ملغية'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Start Visit Modal */}
      {showStartModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-6 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl leading-6 font-medium text-gray-900">
                  🎯 بدء زيارة خارجية جديدة
                </h3>
                <button
                  onClick={() => setShowStartModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <form onSubmit={handleStartVisit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      اسم العميل *
                    </label>
                    <input
                      type="text"
                      value={startVisitData.client_name}
                      onChange={(e) => setStartVisitData({...startVisitData, client_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="اسم الشركة أو الشخص"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      اسم المكان *
                    </label>
                    <input
                      type="text"
                      value={startVisitData.location_name}
                      onChange={(e) => setStartVisitData({...startVisitData, location_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="مكان الزيارة"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      المنطقة *
                    </label>
                    <input
                      type="text"
                      value={startVisitData.area}
                      onChange={(e) => setStartVisitData({...startVisitData, area: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="المنطقة أو الحي"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      الغرض من الزيارة *
                    </label>
                    <select
                      value={startVisitData.purpose}
                      onChange={(e) => setStartVisitData({...startVisitData, purpose: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      {purposeOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    تفاصيل إضافية (اختياري)
                  </label>
                  <textarea
                    value={startVisitData.purpose_details}
                    onChange={(e) => setStartVisitData({...startVisitData, purpose_details: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                    placeholder="أي تفاصيل إضافية عن الزيارة..."
                  />
                </div>

                {gpsSupported && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="flex items-center">
                      <MapPinIcon className="h-5 w-5 text-blue-500 mr-2" />
                      <span className="text-sm text-blue-700">
                        سيتم تسجيل موقع GPS تلقائياً عند بدء الزيارة
                      </span>
                    </div>
                  </div>
                )}

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowStartModal(false)}
                    className="px-6 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
                  >
                    إلغاء
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-300"
                  >
                    {loading ? 'جاري البدء...' : 'بدء الزيارة'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Complete Visit Modal */}
      {showCompleteModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-5 mx-auto p-6 border w-full max-w-4xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl leading-6 font-medium text-gray-900">
                  📋 تقرير إنهاء الزيارة الخارجية
                </h3>
                <button
                  onClick={() => setShowCompleteModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {activeVisit && (
                <div className="bg-blue-50 p-4 rounded-lg mb-6">
                  <h4 className="font-semibold mb-2">معلومات الزيارة</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>العميل: <span className="font-medium">{activeVisit.client_name}</span></div>
                    <div>المكان: <span className="font-medium">{activeVisit.location_name}</span></div>
                    <div>المنطقة: <span className="font-medium">{activeVisit.area}</span></div>
                    <div>المدة: <span className="font-medium">{formatElapsedTime(elapsedTime)}</span></div>
                  </div>
                </div>
              )}

              <form onSubmit={handleCompleteVisit} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ملخص الزيارة * <span className="text-red-500">(الحد الأدنى 20 حرف)</span>
                  </label>
                  <textarea
                    value={visitReport.summary}
                    onChange={(e) => setVisitReport({...visitReport, summary: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                    placeholder="ملخص سريع عن الزيارة ونتائجها..."
                    required
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    عدد الأحرف: {visitReport.summary.length}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    تفاصيل الزيارة * <span className="text-red-500">(الحد الأدنى 50 حرف)</span>
                  </label>
                  <textarea
                    value={visitReport.details}
                    onChange={(e) => setVisitReport({...visitReport, details: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="4"
                    placeholder="تفاصيل مفصلة عما حدث في الزيارة، المناقشات، المشاكل، الحلول..."
                    required
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    عدد الأحرف: {visitReport.details.length}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      نتيجة الزيارة *
                    </label>
                    <select
                      value={visitReport.result}
                      onChange={(e) => setVisitReport({...visitReport, result: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      {resultOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      ملاحظات العميل (اختياري)
                    </label>
                    <input
                      type="text"
                      value={visitReport.client_feedback}
                      onChange={(e) => setVisitReport({...visitReport, client_feedback: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="تعليقات أو ملاحظات العميل..."
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    الإجراءات القادمة * <span className="text-red-500">(الحد الأدنى 10 أحرف)</span>
                  </label>
                  <textarea
                    value={visitReport.next_actions}
                    onChange={(e) => setVisitReport({...visitReport, next_actions: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                    placeholder="ما هي الخطوات التالية؟ متابعة، اتصال، زيارة أخرى، إرسال عرض سعر..."
                    required
                  />
                  <div className="text-xs text-gray-500 mt-1">
                    عدد الأحرف: {visitReport.next_actions.length}
                  </div>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowCompleteModal(false)}
                    className="px-6 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
                  >
                    إلغاء
                  </button>
                  <button
                    type="submit"
                    disabled={loading || visitReport.summary.length < 20 || visitReport.details.length < 50 || visitReport.next_actions.length < 10}
                    className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-300"
                  >
                    {loading ? 'جاري الإنهاء...' : 'إنهاء الزيارة وإرسال التقرير'}
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

export default MarketingVisits;