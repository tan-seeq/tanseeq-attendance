import React, { useState } from 'react';
import axios from 'axios';
import {
  CalculatorIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  DocumentArrowDownIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MonthlyDeductionsCalculator = () => {
  const [mode, setMode] = useState('monthly');
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [calculating, setCalculating] = useState(false);
  const [applying, setApplying] = useState(false);
  const [calculatedData, setCalculatedData] = useState(null);
  const [error, setError] = useState('');
  const [expandedEmployees, setExpandedEmployees] = useState({});

  const handleCalculate = async () => {
    try {
      setCalculating(true);
      setError('');
      
      if (mode === 'custom') {
        if (!fromDate || !toDate) {
          setError('Please specify complete period (from and to)');
          setCalculating(false);
          return;
        }
        
        const diffDays = Math.floor((new Date(toDate) - new Date(fromDate)) / (1000 * 60 * 60 * 24));
        
        if (new Date(fromDate) > new Date(toDate)) {
          setError('Start date must be before end date');
          setCalculating(false);
          return;
        }
        
        if (diffDays > 93) {
          setError('Period exceeds 93 days, please reduce range');
          setCalculating(false);
          return;
        }
      }
      
      let apiUrl;
      if (mode === 'monthly') {
        // Parse month (YYYY-MM) to separate month and year
        const [year, month] = selectedMonth.split('-').map(Number);
        apiUrl = `${API}/deductions/calculate-monthly?month=${month}&year=${year}`;
      } else {
        apiUrl = `${API}/deductions/calculate?mode=custom&from_date=${fromDate}&to_date=${toDate}`;
      }
      
      const response = await axios.post(apiUrl, {});
      
      let transformedData = null;
      
      if (response.data.items) {
        transformedData = {
          success: true,
          employee_count: response.data.employees_count || response.data.items.length,
          total_deductions: response.data.items.reduce((sum, emp) => sum + (emp.amount || 0), 0),
          employees: response.data.items.map(item => ({
            employee_id: item.employee_id,
            employee_name: item.employee_name,
            late_count: 0,
            absence_count: 0,
            installment_count: 0,
            late_deduction: 0,
            absence_deduction: 0,
            advance_deduction: 0,
            total_deduction: item.amount || 0,
            deduction_details: [`Total Deductions: ${(item.amount || 0).toFixed(2)} AED`]
          }))
        };
      } else if (response.data.success && response.data.employees) {
        if (!response.data.total_deductions) {
          response.data.total_deductions = response.data.employees.reduce((sum, emp) => sum + (emp.total_deduction || 0), 0);
        }
        transformedData = response.data;
      } else {
        transformedData = {
          success: true,
          employees: [],
          employee_count: 0,
          total_deductions: 0
        };
      }
      
      setCalculatedData(transformedData);
    } catch (err) {
      console.error('Error calculating deductions:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Error calculating deductions';
      setError(errorMsg);
    } finally {
      setCalculating(false);
    }
  };

  const handleApply = async () => {
    // Parse month (YYYY-MM)
    const [year, month] = selectedMonth.split('-').map(Number);
    
    if (!window.confirm(
      `Apply deductions for ${calculatedData.employee_count} employees?\n` +
      `Total Deductions: ${(calculatedData.total_deductions || 0).toFixed(2)} AED\n\n` +
      `This will:\n` +
      `• Update payroll cycle for ${selectedMonth}\n` +
      `• Apply all deductions (Late, Absence)\n` +
      `• Send notifications to employees`
    )) {
      return;
    }
    
    try {
      setApplying(true);
      const response = await axios.post(`${API}/deductions/apply-monthly?month=${month}&year=${year}`);
      alert(`Deductions applied successfully!\nEmployees: ${response.data.employees_affected || 0}\nTotal: ${response.data.total_deduction_amount || 0} AED`);
      handleCalculate();
    } catch (error) {
      console.error('Error applying deductions:', error);
      alert('Error applying deductions: ' + (error.response?.data?.detail || error.message));
    } finally {
      setApplying(false);
    }
  };

  const exportToExcel = () => {
    if (!calculatedData || !calculatedData.employees || calculatedData.employees.length === 0) {
      alert('No data to export');
      return;
    }

    let csvContent = 'Employee,Late Count,Absence Days,Total Minutes,Late Deduction,Absence Deduction,Total Deduction\n';
    
    calculatedData.employees.forEach(emp => {
      csvContent += `${emp.employee_name},${emp.late_count || 0},${emp.absence_count || 0},${emp.total_late_minutes || 0},${(emp.late_deduction || 0).toFixed(2)},${(emp.absence_deduction || 0).toFixed(2)},${(emp.total_deduction || 0).toFixed(2)}\n`;
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    const filename = mode === 'monthly' 
      ? `deductions_${selectedMonth}.csv`
      : `deductions_${fromDate}_to_${toDate}.csv`;
    link.download = filename;
    link.click();
  };

  const exportToPDF = () => {
    if (!calculatedData || !calculatedData.employees || calculatedData.employees.length === 0) {
      alert('No data to export');
      return;
    }

    const doc = new jsPDF();
    
    doc.setFontSize(16);
    doc.text('Advanced Deductions Report', 14, 15);
    doc.setFontSize(10);
    doc.text(`Period: ${mode === 'monthly' ? selectedMonth : `${fromDate} to ${toDate}`}`, 14, 22);
    doc.text(`Total Employees: ${calculatedData.employee_count}`, 14, 28);
    doc.text(`Total Deductions: ${(calculatedData.total_deductions || 0).toFixed(2)} AED`, 14, 34);
    
    const tableData = calculatedData.employees.map(emp => [
      emp.employee_name,
      emp.late_count || 0,
      emp.absence_count || 0,
      emp.total_late_minutes || 0,
      `${(emp.late_deduction || 0).toFixed(2)}`,
      `${(emp.absence_deduction || 0).toFixed(2)}`,
      `${(emp.total_deduction || 0).toFixed(2)}`
    ]);
    
    doc.autoTable({
      startY: 40,
      head: [['Employee', 'Late Days', 'Absent Days', 'Minutes', 'Late Ded.', 'Absence Ded.', 'Total']],
      body: tableData,
      theme: 'grid',
      headStyles: { fillColor: [59, 130, 246] }
    });
    
    const filename = mode === 'monthly' 
      ? `deductions_${selectedMonth}.pdf`
      : `deductions_${fromDate}_to_${toDate}.pdf`;
    doc.save(filename);
  };

  const toggleEmployeeDetails = (employeeId) => {
    setExpandedEmployees(prev => ({
      ...prev,
      [employeeId]: !prev[employeeId]
    }));
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg shadow-lg mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">🧮 Advanced Deductions System</h1>
            <p className="text-blue-100">Calculate Late Arrivals & Absences</p>
          </div>
          <CalculatorIcon className="h-16 w-16 text-blue-200" />
        </div>
      </div>

      {/* Rules */}
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded-lg">
        <h3 className="font-bold text-blue-900 mb-2">📋 Deduction Rules:</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• First 15 minutes late × 4 times = <strong>Free</strong></li>
          <li>• More than 4 times: Minutes accumulated and deducted from salary</li>
          <li>• More than 20 minutes: Actual time deduction</li>
          <li>• 1 to 2 hours: <strong>Half day</strong> deduction</li>
          <li>• More than 2 hours: <strong>Full day</strong> deduction</li>
          <li>• Absence: Full day deduction</li>
        </ul>
      </div>

      {/* Mode Selector & Filters */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="mb-6 pb-4 border-b-2 border-gray-300">
          <label className="block text-gray-800 font-bold mb-3 text-lg">📋 Calculation Type</label>
          <div className="flex flex-wrap items-center gap-6">
            <label className="flex items-center gap-2 cursor-pointer bg-blue-50 px-4 py-3 rounded-lg border-2 border-blue-200 hover:bg-blue-100 transition">
              <input
                type="radio"
                name="mode"
                value="monthly"
                checked={mode === 'monthly'}
                onChange={() => {
                  setMode('monthly');
                  setCalculatedData(null);
                  setError('');
                }}
                className="w-5 h-5 text-blue-600"
              />
              <span className="text-gray-800 font-semibold text-base">🗓️ Monthly Calculation</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer bg-green-50 px-4 py-3 rounded-lg border-2 border-green-200 hover:bg-green-100 transition">
              <input
                type="radio"
                name="mode"
                value="custom"
                checked={mode === 'custom'}
                onChange={() => {
                  setMode('custom');
                  setCalculatedData(null);
                  setError('');
                }}
                className="w-5 h-5 text-green-600"
              />
              <span className="text-gray-800 font-semibold text-base">📅 Custom Period</span>
            </label>
          </div>
        </div>

        {mode === 'custom' && (
          <div className="mb-4 p-4 bg-blue-50 border-2 border-blue-400 rounded-lg">
            <p className="text-sm text-blue-800 font-semibold">
              ℹ️ <strong>Note:</strong> Calculate deductions for any custom period (Maximum: 93 days).
            </p>
          </div>
        )}

        <div className="flex items-center justify-between flex-wrap gap-4">
          {mode === 'monthly' ? (
            <div className="flex items-center gap-4">
              <CalendarIcon className="h-6 w-6 text-gray-500" />
              <label className="text-sm font-medium text-gray-700">Select Month:</label>
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => {
                  setSelectedMonth(e.target.value);
                  setCalculatedData(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ) : (
            <div className="flex items-center gap-4 flex-wrap">
              <CalendarIcon className="h-6 w-6 text-gray-500" />
              <label className="text-sm font-medium text-gray-700">From:</label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => {
                  setFromDate(e.target.value);
                  setCalculatedData(null);
                  setError('');
                }}
                className="px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <label className="text-sm font-medium text-gray-700">To:</label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => {
                  setToDate(e.target.value);
                  setCalculatedData(null);
                  setError('');
                }}
                className="px-4 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>
          )}
          
          <div className="flex gap-3">
            <button
              onClick={handleCalculate}
              disabled={calculating || (mode === 'custom' && (!fromDate || !toDate))}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-semibold shadow-md"
            >
              {calculating ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Calculating...
                </>
              ) : (
                <>
                  <CalculatorIcon className="h-5 w-5" />
                  🧮 Calculate Deductions
                </>
              )}
            </button>

            {calculatedData && (
              <button
                onClick={handleApply}
                disabled={applying}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-semibold shadow-md"
              >
                {applying ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Applying...
                  </>
                ) : (
                  <>
                    <CheckCircleIcon className="h-5 w-5" />
                    Apply Deductions
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-100 border-2 border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4 font-semibold">
          ❌ {error}
        </div>
      )}

      {/* Results */}
      {calculatedData && calculatedData.employees && calculatedData.employees.length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Summary */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-6 border-b flex justify-between items-center">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 flex-1">
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-600">{calculatedData.employee_count}</p>
                <p className="text-gray-600 text-sm">Total Employees</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-orange-600">
                  {calculatedData.employees.reduce((sum, s) => sum + (s.late_count || 0), 0)}
                </p>
                <p className="text-gray-600 text-sm">Total Late Days</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-red-600">
                  {(calculatedData.total_deductions || 0).toFixed(2)} AED
                </p>
                <p className="text-gray-600 text-sm">Total Deductions</p>
              </div>
            </div>
            
            <div className="flex gap-2 ml-4">
              <button
                onClick={exportToExcel}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 text-sm font-semibold"
              >
                <DocumentArrowDownIcon className="h-5 w-5" />
                Excel
              </button>
              <button
                onClick={exportToPDF}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2 text-sm font-semibold"
              >
                <DocumentArrowDownIcon className="h-5 w-5" />
                PDF
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-blue-600 text-white">
                <tr>
                  <th className="px-4 py-3 text-left">#</th>
                  <th className="px-4 py-3 text-left">Employee</th>
                  <th className="px-4 py-3 text-center">Late Days</th>
                  <th className="px-4 py-3 text-center">Absent Days</th>
                  <th className="px-4 py-3 text-center">Late Minutes</th>
                  <th className="px-4 py-3 text-center">Late Deduction</th>
                  <th className="px-4 py-3 text-center">Absence Deduction</th>
                  <th className="px-4 py-3 text-center">Total Deduction</th>
                  <th className="px-4 py-3 text-center">Details</th>
                </tr>
              </thead>
              <tbody>
                {calculatedData.employees.map((emp, index) => (
                  <React.Fragment key={emp.employee_id}>
                    <tr className={`border-b hover:bg-gray-50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                      <td className="px-4 py-3">{index + 1}</td>
                      <td className="px-4 py-3 font-semibold">{emp.employee_name}</td>
                      <td className="px-4 py-3 text-center">
                        <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-bold">
                          {emp.late_count || 0}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-bold">
                          {emp.absence_count || 0}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-orange-600 font-bold">{emp.total_late_minutes || 0}</td>
                      <td className="px-4 py-3 text-center text-orange-600 font-medium">
                        {emp.late_deduction ? `${emp.late_deduction.toFixed(2)} AED` : '-'}
                      </td>
                      <td className="px-4 py-3 text-center text-red-600 font-medium">
                        {emp.absence_deduction ? `${emp.absence_deduction.toFixed(2)} AED` : '-'}
                      </td>
                      <td className="px-4 py-3 text-center font-bold text-red-700">
                        {(emp.total_deduction || 0).toFixed(2)} AED
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => toggleEmployeeDetails(emp.employee_id)}
                          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm flex items-center gap-1 mx-auto"
                        >
                          {expandedEmployees[emp.employee_id] ? (
                            <>
                              <ChevronUpIcon className="h-4 w-4" />
                              Hide
                            </>
                          ) : (
                            <>
                              <ChevronDownIcon className="h-4 w-4" />
                              View
                            </>
                          )}
                        </button>
                      </td>
                    </tr>

                    {expandedEmployees[emp.employee_id] && (
                      <tr>
                        <td colSpan="9" className="bg-gray-50 p-4">
                          <div className="bg-white rounded-lg p-4 border-2 border-blue-200">
                            <h4 className="font-bold text-lg mb-3 text-gray-700">📋 Deduction Details</h4>
                            {emp.deduction_details && emp.deduction_details.length > 0 ? (
                              <ul className="list-disc list-inside space-y-2 text-gray-700">
                                {emp.deduction_details.map((detail, idx) => (
                                  <li key={idx} className="text-sm">{detail}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-gray-500 text-sm">No detailed information available</p>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!calculatedData && !calculating && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <CalculatorIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            Start Calculating Deductions
          </h3>
          <p className="text-gray-500 mb-6">
            Select period and click "Calculate Deductions" to view details
          </p>
        </div>
      )}
    </div>
  );
};

export default MonthlyDeductionsCalculator;
