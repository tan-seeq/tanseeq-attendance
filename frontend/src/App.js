import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import ErrorBoundary from './components/ErrorBoundary';

// Import Contexts
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';

// Import Layout & Auth
import Layout from './components/Layout/Layout';
import Login from './components/Auth/Login';

// Import Core Page Components
import Dashboard from './components/Dashboard/Dashboard';
import Attendance from './components/Attendance/Attendance';
import Employees from './components/Employees/Employees';
import FieldExits from './components/FieldExits/FieldExits';
import Leaves from './components/Leaves/Leaves';
import Payroll from './components/Payroll/Payroll';
import ReportsPage from './components/Reports/ReportsPage';
import OvertimeReport from './components/Reports/OvertimeReport';

// Import Admin Components
import LeaveManagement from './components/Leaves/LeaveManagement';
import FieldExitManagement from './components/FieldExits/FieldExitManagement';
import AdminRequestCreation from './components/Admin/AdminRequestCreation';
import AttachmentViewer from './components/Admin/AttachmentViewer';
import BackupManagement from './components/Admin/BackupManagement';
import AttendanceManagement from './components/Attendance/AttendanceManagement';
import AdminConfig from './components/Admin/AdminConfig';
import LiveMonitoring from './components/Admin/LiveMonitoring';
import SalarySlips from './components/Admin/SalarySlips';
import SystemHealth from './components/Admin/SystemHealth';

// Import Work Reports Components
import WorkReportsDashboard from './WorkReports/WorkReportsDashboard';
import ClientManagement from './WorkReports/ClientManagement';
import WorkLogManagement from './WorkReports/WorkLogManagement';
import AuditLogViewer from './WorkReports/AuditLogViewer';
import StopwatchMode from './WorkReports/StopwatchMode';
import ReportsDashboard from './WorkReports/ReportsDashboard';
import PermissionsManager from './WorkReports/PermissionsManager';
import NotificationSystem from './components/NotificationSystem';
import MarketingVisits from './components/MarketingVisits';
import PushNotifications from './components/PushNotifications/PushNotifications';

// Import Advances & Loans Components
import AdvancesDashboard from './components/AdvancesLoans/AdvancesDashboard';
import AdminDashboard from './components/AdvancesLoans/AdminDashboard';
import SubmitExpense from './components/AdvancesLoans/SubmitExpense';
import MyTransactions from './components/AdvancesLoans/MyTransactions';

// Import Notification Modal
import NotificationModal from './components/NotificationModal';

// Import Attendance Deductions Components
import AttendanceDeductionsAdmin from './components/AttendanceDeductions/AttendanceDeductionsAdmin';
import MyAttendanceDeductions from './components/AttendanceDeductions/MyAttendanceDeductions';
import MonthlyDeductionsCalculator from './components/AttendanceDeductions/MonthlyDeductionsCalculator';

// Import Integrated Payroll Components
import PayrollCycleManagement from './components/IntegratedPayroll/PayrollCycleManagement';
import InstallmentScheduleManager from './components/IntegratedPayroll/InstallmentScheduleManager';
import PayrollSummary from './components/IntegratedPayroll/PayrollSummary';

// Import Payroll Ledger Components
import EmployeeLedger from './components/PayrollLedger/EmployeeLedger';

// Import Reports Components
import DeductionsReport from './components/Reports/DeductionsReport';
import AdvancesReport from './components/Reports/AdvancesReport';
import AttendanceReport from './components/Reports/AttendanceReport';
import AdvancedDeductionsReport from './components/Reports/AdvancedDeductionsReport';

// Import Dashboard Components
import HRDashboard from './components/Dashboard/HRDashboard';

const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  if (requiredRole && user.role !== requiredRole && user.role !== 'super_admin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

const AppWithNotifications = () => {
  const { user, showNotificationModal, dismissNotifications } = useAuth();
  
  const handleCloseNotificationModal = () => {
    dismissNotifications();
  };
  
  return (
    <>
      <Router>
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Layout><Dashboard /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/attendance" element={
              <ProtectedRoute>
                <Layout><Attendance /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/employees" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><Employees /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/field-exits" element={
              <ProtectedRoute>
                <Layout><FieldExits /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/leaves" element={
              <ProtectedRoute>
                <Layout><Leaves /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/attendance-management" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><AttendanceManagement /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/attendance-deductions" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><MonthlyDeductionsCalculator /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/my-deductions" element={
              <ProtectedRoute>
                <Layout><MyAttendanceDeductions currentUser={user} /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/leave-management" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><LeaveManagement /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/field-exit-management" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><FieldExitManagement /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><ReportsPage /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/overtime-report" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><OvertimeReport /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/payroll" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><Payroll /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/backup-management" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><BackupManagement /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/admin/config" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><AdminConfig /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/admin/live" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><LiveMonitoring /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/salary-slips" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><SalarySlips /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/system-health" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><SystemHealth /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/admin-request-creation" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><AdminRequestCreation /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/attachment-viewer" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><AttachmentViewer /></Layout>
              </ProtectedRoute>
            } />
            {/* Work Reports Module Routes */}
            <Route path="/work-reports" element={
              <ProtectedRoute>
                <Layout><WorkReportsDashboard /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/work-reports/clients" element={
              <ProtectedRoute>
                <Layout><ClientManagement /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/work-reports/logs" element={
              <ProtectedRoute>
                <Layout><WorkLogManagement /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/work-reports/audit" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><AuditLogViewer /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/work-reports/stopwatch" element={
              <ProtectedRoute>
                <Layout><StopwatchMode /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/work-reports/reports" element={
              <ProtectedRoute>
                <Layout><ReportsDashboard /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/work-reports/permissions" element={
              <ProtectedRoute>
                <Layout><PermissionsManager /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/notifications" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><NotificationSystem /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/push-notifications" element={
              <ProtectedRoute>
                <Layout><PushNotifications /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/marketing-visits" element={
              <ProtectedRoute>
                <Layout><MarketingVisits /></Layout>
              </ProtectedRoute>
            } />
            {/* Integrated Payroll System */}
            <Route path="/payroll-cycles" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><ErrorBoundary><PayrollCycleManagement /></ErrorBoundary></Layout>
              </ProtectedRoute>
            } />
            <Route path="/installment-schedules" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><InstallmentScheduleManager /></Layout>
              </ProtectedRoute>
            } />
            {/* Advances & Loans Routes */}
            <Route path="/advances" element={
              <ProtectedRoute>
                <Layout><AdvancesDashboard /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/advances/admin" element={
              <ProtectedRoute requiredRole="super_admin">
                <Layout><AdminDashboard /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/advances/submit-expense" element={
              <ProtectedRoute>
                <Layout><SubmitExpense /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/payroll-summary/:id" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><ErrorBoundary><PayrollSummary /></ErrorBoundary></Layout>
              </ProtectedRoute>
            } />
            <Route path="/payroll-ledger" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><ErrorBoundary><EmployeeLedger /></ErrorBoundary></Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports/deductions" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><ErrorBoundary><DeductionsReport /></ErrorBoundary></Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports/advances" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><ErrorBoundary><AdvancesReport /></ErrorBoundary></Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports/attendance" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><ErrorBoundary><AttendanceReport /></ErrorBoundary></Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports/advanced-deductions" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><ErrorBoundary><AdvancedDeductionsReport /></ErrorBoundary></Layout>
              </ProtectedRoute>
            } />
            <Route path="/hr-dashboard" element={
              <ProtectedRoute requiredRole="admin">
                <Layout><ErrorBoundary><HRDashboard /></ErrorBoundary></Layout>
              </ProtectedRoute>
            } />
            <Route path="/advances/my-transactions" element={
              <ProtectedRoute>
                <Layout><MyTransactions /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/advances/balance-details" element={
              <ProtectedRoute>
                <Layout><AdvancesDashboard /></Layout>
              </ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
        
        {/* Notification Modal */}
        <NotificationModal 
          isOpen={showNotificationModal}
          onClose={handleCloseNotificationModal}
        />
      </>
    );
  };

function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
        <AppWithNotifications />
      </LanguageProvider>
    </AuthProvider>
  );
}

export default App;
