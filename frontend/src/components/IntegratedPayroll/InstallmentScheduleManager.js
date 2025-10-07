import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  CalendarIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  PlusIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  ArrowRightIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const InstallmentScheduleManager = () => {
  const [loading, setLoading] = useState(true);
  const [approvedAdvances, setApprovedAdvances] = useState([]);
  const [existingSchedules, setExistingSchedules] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedAdvance, setSelectedAdvance] = useState(null);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  
  // Form data for creating installment schedule
  const [formData, setFormData] = useState({
    installment_amount: '',
    number_of_installments: '',
    start_date: new Date().toISOString().split('T')[0],
    respect_ceiling: true
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch approved advances without installment schedules
      const advancesRes = await axios.get(`${API}/advances/admin/all-transactions?status=approved`);
      const allAdvances = advancesRes.data.transactions || [];
      
      // Filter only advance transactions (السلف فقط - العهد تتم تسويتها وليس جدولتها)
      const advanceTransactions = allAdvances.filter(t => 
        t.transaction_type === 'advance' && 
        t.status === 'approved'
      );
      
      // Fetch existing installment schedules
      const schedulesRes = await axios.get(`${API}/payroll/installment-schedules`);
      const schedules = schedulesRes.data.schedules || [];
      
      // Filter out advances that already have installment schedules
      const scheduledAdvanceIds = schedules.map(s => s.advance_transaction_id);
      const unscheduledAdvances = advanceTransactions.filter(a => 
        !scheduledAdvanceIds.includes(a.id)
      );
      
      setApprovedAdvances(unscheduledAdvances);
      setExistingSchedules(schedules);
      
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSchedule = async (e) => {
    e.preventDefault();
    
    if (!selectedAdvance) {
      alert('يرجى تحديد السلفة');
      return;
    }
    
    // Validation
    if (!formData.installment_amount || !formData.number_of_installments || !formData.start_date) {
      alert('يرجى تعبئة جميع الحقول المطلوبة');
      return;
    }
    
    if (parseFloat(formData.installment_amount) <= 0) {
      alert('مبلغ القسط يجب أن يكون أكبر من صفر');
      return;
    }
    
    if (parseInt(formData.number_of_installments) < 1 || parseInt(formData.number_of_installments) > 60) {
      alert('عدد الأقساط يجب أن يكون بين 1 و 60');
      return;
    }

    try {
      await axios.post(`${API}/advances/${selectedAdvance.id}/installments`, {
        installment_amount: parseFloat(formData.installment_amount),
        number_of_installments: parseInt(formData.number_of_installments),
        start_date: formData.start_date,
        respect_ceiling: formData.respect_ceiling
      });
      
      setShowCreateModal(false);
      setSelectedAdvance(null);
      setFormData({
        installment_amount: '',
        number_of_installments: '',
        start_date: new Date().toISOString().split('T')[0],
        respect_ceiling: true
      });
      
      fetchData();
      alert('تم إنشاء جدولة الأقساط بنجاح');
      
    } catch (error) {
      console.error('Error creating installment schedule:', error);
      const errorMsg = error.response?.data?.detail || 'خطأ في إنشاء جدولة الأقساط';
      alert(errorMsg);
    }
  };

  const viewScheduleDetails = async (schedule) => {
    try {
      const response = await axios.get(`${API}/advances/${schedule.advance_transaction_id}/installments`);
      setSelectedSchedule({
        ...schedule,
        installments: response.data.installments || []
      });
      setShowDetailsModal(true);
    } catch (error) {
      console.error('Error fetching schedule details:', error);
      alert('خطأ في جلب تفاصيل الجدولة');
    }
  };

  const calculateTotalAmount = () => {
    if (!formData.installment_amount || !formData.number_of_installments) return 0;
    return parseFloat(formData.installment_amount) * parseInt(formData.number_of_installments);
  };

  const getInstallmentStatusColor = (status) => {
    switch (status) {
      case 'deducted': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'skipped': return 'bg-orange-100 text-orange-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getInstallmentStatusText = (status) => {
    switch (status) {
      case 'deducted': return 'تم خصمه';
      case 'pending': return 'في الانتظار';
      case 'skipped': return 'تم تخطيه';
      case 'cancelled': return 'ملغى';
      default: return status;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('ar-SA');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <CalendarIcon className="h-8 w-8 text-blue-600 ml-3" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">إدارة جدولة الأقساط</h1>
              <p className="text-gray-600">جدولة أقساط السلف والعهد في دورات الرواتب</p>
            </div>
          </div>
        </div>

        {/* Statistics */}
        {/* تنبيه مهم حول الفرق بين السلف والعهد */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mt-0.5 ml-2" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800">ملاحظة مهمة</h3>
              <p className="text-sm text-yellow-700 mt-1">
                <strong>السُلف:</strong> يتم جدولتها وخصمها من الراتب على أقساط شهرية<br/>
                <strong>العُهد:</strong> يتم تسويتها كمصروفات وليس جدولتها (لا تظهر في هذه الصفحة)
              </p>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-blue-600" />
              <div className="mr-3">
                <p className="text-sm text-blue-600">سلف بدون جدولة</p>
                <p className="text-2xl font-bold text-blue-600">{approvedAdvances.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center">
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
              <div className="mr-3">
                <p className="text-sm text-green-600">جدولات نشطة</p>
                <p className="text-2xl font-bold text-green-600">
                  {existingSchedules.filter(s => s.is_active && !s.is_completed).length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-purple-600" />
              <div className="mr-3">
                <p className="text-sm text-purple-600">جدولات مكتملة</p>
                <p className="text-2xl font-bold text-purple-600">
                  {existingSchedules.filter(s => s.is_completed).length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg">
            <div className="flex items-center">
              <CurrencyDollarIcon className="h-8 w-8 text-orange-600" />
              <div className="mr-3">
                <p className="text-sm text-orange-600">إجمالي الرصيد المتبقي</p>
                <p className="text-lg font-bold text-orange-600">
                  {existingSchedules.reduce((sum, s) => sum + (s.remaining_balance || 0), 0).toFixed(2)} درهم
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Unscheduled Advances */}
      {approvedAdvances.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              سلف وعهد معتمدة بحاجة لجدولة أقساط ({approvedAdvances.length})
            </h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الموظف</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">النوع</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">المبلغ</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">تاريخ الاعتماد</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الإجراءات</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {approvedAdvances.map((advance) => (
                  <tr key={advance.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {advance.employee_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        advance.transaction_type === 'advance' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {advance.transaction_type_ar || advance.transaction_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className="font-semibold">{advance.amount?.toFixed(2)} درهم</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(advance.approved_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => {
                          setSelectedAdvance(advance);
                          setShowCreateModal(true);
                        }}
                        className="flex items-center text-blue-600 hover:text-blue-900"
                      >
                        <PlusIcon className="h-4 w-4 ml-1" />
                        إنشاء جدولة
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Existing Schedules */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">جدولات الأقساط الموجودة</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الموظف</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">المبلغ الإجمالي</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">قسط شهري</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">التقدم</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الرصيد المتبقي</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الحالة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {existingSchedules.map((schedule) => (
                <tr key={schedule.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {schedule.employee_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="font-semibold">{schedule.total_amount?.toFixed(2)} درهم</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {schedule.installment_amount?.toFixed(2)} درهم
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <div className="w-full bg-gray-200 rounded-full h-2 ml-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{
                            width: `${((schedule.completed_installments || 0) / (schedule.number_of_installments || 1)) * 100}%`
                          }}
                        ></div>
                      </div>
                      <span className="text-xs">
                        {schedule.completed_installments || 0}/{schedule.number_of_installments || 0}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="font-semibold text-orange-600">
                      {schedule.remaining_balance?.toFixed(2)} درهم
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      schedule.is_completed ? 'bg-green-100 text-green-800' :
                      schedule.is_active ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {schedule.is_completed ? 'مكتملة' : schedule.is_active ? 'نشطة' : 'غير نشطة'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => viewScheduleDetails(schedule)}
                      className="flex items-center text-blue-600 hover:text-blue-900"
                    >
                      <EyeIcon className="h-4 w-4 ml-1" />
                      التفاصيل
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {existingSchedules.length === 0 && (
            <div className="text-center py-12">
              <CalendarIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500">لا توجد جدولات أقساط</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Schedule Modal */}
      {showCreateModal && selectedAdvance && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  إنشاء جدولة أقساط - {selectedAdvance.employee_name}
                </h3>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setSelectedAdvance(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="mb-4 p-3 bg-blue-50 rounded-md">
                <p className="text-sm text-blue-800">
                  <strong>النوع:</strong> {selectedAdvance.transaction_type_ar}<br/>
                  <strong>المبلغ الإجمالي:</strong> {selectedAdvance.amount?.toFixed(2)} درهم
                </p>
              </div>
              
              <form onSubmit={handleCreateSchedule} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    مبلغ القسط الشهري *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    max={selectedAdvance.amount}
                    value={formData.installment_amount}
                    onChange={(e) => setFormData({...formData, installment_amount: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="مبلغ القسط بالدرهم"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    عدد الأقساط *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={formData.number_of_installments}
                    onChange={(e) => setFormData({...formData, number_of_installments: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="1-60 قسط"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    تاريخ بداية الاستقطاع *
                  </label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="respect_ceiling"
                    checked={formData.respect_ceiling}
                    onChange={(e) => setFormData({...formData, respect_ceiling: e.target.checked})}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                  <label htmlFor="respect_ceiling" className="mr-2 block text-sm text-gray-900">
                    احترام سقف الخصم الشهري (33% من الراتب)
                  </label>
                </div>

                {formData.installment_amount && formData.number_of_installments && (
                  <div className="p-3 bg-yellow-50 rounded-md">
                    <p className="text-sm text-yellow-800">
                      <strong>إجمالي المبلغ المحسوب:</strong> {calculateTotalAmount().toFixed(2)} درهم<br/>
                      <strong>مبلغ السلفة:</strong> {selectedAdvance.amount?.toFixed(2)} درهم<br/>
                      {calculateTotalAmount() !== selectedAdvance.amount && (
                        <span className="text-orange-600">
                          <strong>الفرق:</strong> {Math.abs(calculateTotalAmount() - selectedAdvance.amount).toFixed(2)} درهم
                        </span>
                      )}
                    </p>
                  </div>
                )}

                <div className="flex space-x-3">
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    إنشاء الجدولة
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false);
                      setSelectedAdvance(null);
                    }}
                    className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                  >
                    إلغاء
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Details Modal */}
      {showDetailsModal && selectedSchedule && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-4/5 max-w-4xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  تفاصيل جدولة الأقساط - {selectedSchedule.employee_name}
                </h3>
                <button
                  onClick={() => {
                    setShowDetailsModal(false);
                    setSelectedSchedule(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>
              
              {/* Schedule Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-3 rounded-md">
                  <p className="text-xs text-blue-600">المبلغ الإجمالي</p>
                  <p className="text-lg font-bold text-blue-600">{selectedSchedule.total_amount?.toFixed(2)} درهم</p>
                </div>
                <div className="bg-green-50 p-3 rounded-md">
                  <p className="text-xs text-green-600">مبلغ القسط</p>
                  <p className="text-lg font-bold text-green-600">{selectedSchedule.installment_amount?.toFixed(2)} درهم</p>
                </div>
                <div className="bg-purple-50 p-3 rounded-md">
                  <p className="text-xs text-purple-600">الأقساط المكتملة</p>
                  <p className="text-lg font-bold text-purple-600">
                    {selectedSchedule.completed_installments}/{selectedSchedule.number_of_installments}
                  </p>
                </div>
                <div className="bg-orange-50 p-3 rounded-md">
                  <p className="text-xs text-orange-600">الرصيد المتبقي</p>
                  <p className="text-lg font-bold text-orange-600">{selectedSchedule.remaining_balance?.toFixed(2)} درهم</p>
                </div>
              </div>
              
              {/* Individual Installments */}
              <div className="max-h-96 overflow-y-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">رقم القسط</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">المبلغ المجدول</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">المبلغ الفعلي</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">تاريخ الاستحقاق</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">الحالة</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {(selectedSchedule.installments || []).map((installment, index) => (
                      <tr key={installment.id || index} className="hover:bg-gray-50">
                        <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                          {installment.installment_number}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                          {installment.scheduled_amount?.toFixed(2)} درهم
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                          {installment.actual_amount?.toFixed(2) || '0.00'} درهم
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(installment.due_date)}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs ${getInstallmentStatusColor(installment.status)}`}>
                            {getInstallmentStatusText(installment.status)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => {
                    setShowDetailsModal(false);
                    setSelectedSchedule(null);
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  إغلاق
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InstallmentScheduleManager;