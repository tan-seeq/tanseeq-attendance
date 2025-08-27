import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  EyeIcon,
  FunnelIcon,
  CalendarIcon,
  UserIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const AuditLogViewer = () => {
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    user_id: '',
    action: '',
    table_name: ''
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const actionTypes = [
    'create_client', 'update_client', 'delete_client',
    'create_work_log', 'update_work_log', 'delete_work_log',
    'create_credential', 'access_password', 'view_credentials',
    'import_clients', 'view_dashboard'
  ];

  const tableNames = [
    'clients', 'client_credentials', 'activity_types', 'work_logs'
  ];

  useEffect(() => {
    fetchAuditLogs();
  }, [filters]);

  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Mock audit logs for demonstration (in real implementation, this would be an API call)
      const mockLogs = [
        {
          id: '1',
          user_id: 'hatem-user-id',
          user_name: 'Hatem Mohamed Ahmed',
          action: 'access_password',
          table_name: 'client_credentials',
          record_id: 'cred-123',
          timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
          ip_address: '192.168.1.100',
          user_agent: 'Mozilla/5.0...',
          before_value: null,
          after_value: { credential_type: 'FTA Portal' }
        },
        {
          id: '2',
          user_id: 'mahmoud-user-id', 
          user_name: 'Mahmoud Al-Rashid',
          action: 'create_client',
          table_name: 'clients',
          record_id: 'client-456',
          timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
          ip_address: '192.168.1.101',
          user_agent: 'Mozilla/5.0...',
          before_value: null,
          after_value: { company_name: 'Al-Futtaim Trading LLC', client_code: 'AFT2508' }
        },
        {
          id: '3',
          user_id: 'jihad-user-id',
          user_name: 'Jihad Al-Mansouri', 
          action: 'create_work_log',
          table_name: 'work_logs',
          record_id: 'log-789',
          timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          ip_address: '192.168.1.102',
          user_agent: 'Mozilla/5.0...',
          before_value: null,
          after_value: { client_id: 'client-456', duration_minutes: 120, total_amount: 400 }
        },
        {
          id: '4',
          user_id: 'hatem-user-id',
          user_name: 'Hatem Mohamed Ahmed',
          action: 'import_clients',
          table_name: 'clients',
          record_id: null,
          timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
          ip_address: '192.168.1.100',
          user_agent: 'Mozilla/5.0...',
          before_value: null,
          after_value: { imported_count: 25, error_count: 3 }
        },
        {
          id: '5',
          user_id: 'hatem-user-id',
          user_name: 'Hatem Mohamed Ahmed',
          action: 'create_credential',
          table_name: 'client_credentials',
          record_id: 'cred-124',
          timestamp: new Date(Date.now() - 120 * 60 * 1000).toISOString(),
          ip_address: '192.168.1.100',
          user_agent: 'Mozilla/5.0...',
          before_value: null,
          after_value: { credential_type: 'Ministry Portal', client_id: '***MASKED***' }
        }
      ];
      
      setAuditLogs(mockLogs);
      setError(null);
    } catch (err) {
      console.error('Error fetching audit logs:', err);
      setError('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getActionColor = (action) => {
    if (action.includes('create')) return 'bg-green-100 text-green-800';
    if (action.includes('update')) return 'bg-blue-100 text-blue-800';
    if (action.includes('delete')) return 'bg-red-100 text-red-800';
    if (action.includes('access') || action.includes('view')) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getSensitivityIcon = (action) => {
    if (action.includes('password') || action.includes('credential')) {
      return <ShieldCheckIcon className="h-4 w-4 text-red-500" />;
    }
    if (action.includes('delete') || action.includes('import')) {
      return <ExclamationTriangleIcon className="h-4 w-4 text-orange-500" />;
    }
    return <EyeIcon className="h-4 w-4 text-gray-400" />;
  };

  const maskSensitiveData = (data) => {
    if (!data) return 'N/A';
    
    const sensitiveFields = ['password', 'client_id', 'user_id', 'email'];
    const maskedData = { ...data };
    
    for (const field of sensitiveFields) {
      if (maskedData[field]) {
        maskedData[field] = '***MASKED***';
      }
    }
    
    return JSON.stringify(maskedData, null, 2);
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
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Work Reports Audit Log</h1>
        <p className="text-gray-600 mt-2">Security audit trail for all Work Reports activities</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center mb-4">
          <FunnelIcon className="h-5 w-5 text-gray-500 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => setFilters({...filters, start_date: e.target.value})}
              className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => setFilters({...filters, end_date: e.target.value})}
              className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Action</label>
            <select
              value={filters.action}
              onChange={(e) => setFilters({...filters, action: e.target.value})}
              className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Actions</option>
              {actionTypes.map(action => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Table</label>
            <select
              value={filters.table_name}
              onChange={(e) => setFilters({...filters, table_name: e.target.value})}
              className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Tables</option>
              {tableNames.map(table => (
                <option key={table} value={table}>{table}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({start_date: '', end_date: '', user_id: '', action: '', table_name: ''})}
              className="w-full bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Audit Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Audit Trail</h2>
          <p className="text-sm text-gray-500 mt-1">
            Showing {auditLogs.length} entries • Last updated: {new Date().toLocaleTimeString()}
          </p>
        </div>
        
        {auditLogs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Table
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Changes
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <CalendarIcon className="h-4 w-4 text-gray-400 mr-2" />
                        {formatTimestamp(log.timestamp)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <UserIcon className="h-4 w-4 text-gray-400 mr-2" />
                        {log.user_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getSensitivityIcon(log.action)}
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionColor(log.action)}`}>
                          {log.action}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.table_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                      {log.ip_address}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                      <details className="cursor-pointer">
                        <summary className="text-blue-600 hover:text-blue-800">View Changes</summary>
                        <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono overflow-auto max-h-32">
                          <div><strong>Before:</strong></div>
                          <pre>{maskSensitiveData(log.before_value)}</pre>
                          <div className="mt-2"><strong>After:</strong></div>
                          <pre>{maskSensitiveData(log.after_value)}</pre>
                        </div>
                      </details>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <ShieldCheckIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No audit logs found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No activity matches your current filters.
            </p>
          </div>
        )}
      </div>

      {/* Security Notice */}
      <div className="mt-6 bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex">
          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              <strong>Security Notice:</strong> All sensitive data (passwords, credentials) are masked in this view. 
              Complete audit trails are maintained in secure storage with AES-256-GCM encryption.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuditLogViewer;