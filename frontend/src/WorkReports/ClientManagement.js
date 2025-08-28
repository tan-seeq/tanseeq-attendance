import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  PlusIcon, 
  PencilIcon,
  TrashIcon,
  BuildingOfficeIcon,
  UserIcon,
  PhoneIcon,
  EnvelopeIcon,
  KeyIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import ClientCredentialsManager from './ClientCredentialsManager';

const ClientManagement = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [selectedClientForCredentials, setSelectedClientForCredentials] = useState(null);
  const [formData, setFormData] = useState({
    company_name: '',
    company_name_ar: '',
    client_code: '',
    industry: '',
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    tax_number: '',
    commercial_registration: '',
    notes: ''
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/work-reports/clients`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setClients(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching clients:', err);
      setError('Failed to load clients');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      
      if (selectedClient) {
        // Update existing client
        await axios.put(`${backendUrl}/api/work-reports/clients/${selectedClient.id}`, formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      } else {
        // Create new client
        await axios.post(`${backendUrl}/api/work-reports/clients`, formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }
      
      setShowAddModal(false);
      setSelectedClient(null);
      setFormData({
        company_name: '',
        company_name_ar: '',
        client_code: '',
        industry: '',
        contact_person: '',
        phone: '',
        email: '',
        address: '',
        tax_number: '',
        commercial_registration: '',
        notes: ''
      });
      fetchClients();
    } catch (err) {
      console.error('Error saving client:', err);
      setError('Failed to save client');
    }
  };

  const handleEdit = (client) => {
    setSelectedClient(client);
    setFormData({
      company_name: client.company_name || '',
      company_name_ar: client.company_name_ar || '',
      client_code: client.client_code || '',
      industry: client.industry || '',
      contact_person: client.contact_person || '',
      phone: client.phone || '',
      email: client.email || '',
      address: client.address || '',
      tax_number: client.tax_number || '',
      commercial_registration: client.commercial_registration || '',
      notes: client.notes || ''
    });
    setShowAddModal(true);
  };

  const handleDelete = async (clientId) => {
    if (!window.confirm('Are you sure you want to delete this client?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${backendUrl}/api/work-reports/clients/${clientId}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      fetchClients();
    } catch (err) {
      console.error('Error deleting client:', err);
      setError('Failed to delete client');
    }
  };

  const handleImportClients = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${backendUrl}/api/work-reports/import-clients`, {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      const { imported_count, skipped_empty_rows, error_count, summary } = response.data;
      
      // Create detailed message in Arabic and English
      let message = `استيراد مكتمل!\nImport Completed!\n\n`;
      message += `✅ عملاء مستوردون: ${imported_count}\n✅ Clients Imported: ${imported_count}\n`;
      
      if (skipped_empty_rows > 0) {
        message += `⚠️ صفوف فارغة تم تجاهلها: ${skipped_empty_rows}\n⚠️ Empty Rows Skipped: ${skipped_empty_rows}\n`;
      }
      
      if (error_count > 0) {
        message += `❌ أخطاء: ${error_count}\n❌ Errors: ${error_count}\n`;
      }
      
      if (summary) {
        message += `\nإجمالي الصفوف المعالجة: ${summary.total_rows_processed}\nTotal Rows Processed: ${summary.total_rows_processed}`;
      }
      
      alert(message);
      fetchClients();
    } catch (err) {
      console.error('Error importing clients:', err);
      setError('فشل في استيراد العملاء - Failed to import clients');
    }
  };

  const viewCredentials = (client) => {
    setSelectedClient(client);
    setShowCredentialsModal(true);
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
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Client Management</h1>
          <p className="text-gray-600 mt-2">Manage your clients and their information</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleImportClients}
            className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Import from Excel
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Client
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Clients Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clients.map((client) => (
          <div key={client.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center">
                <BuildingOfficeIcon className="h-8 w-8 text-blue-500 mr-3" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{client.company_name}</h3>
                  {client.client_code && (
                    <span className="text-sm text-gray-500">#{client.client_code}</span>
                  )}
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleEdit(client)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <PencilIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => viewCredentials(client)}
                  className="text-green-600 hover:text-green-800"
                >
                  <KeyIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => handleDelete(client.id)}
                  className="text-red-600 hover:text-red-800"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
            
            <div className="space-y-2">
              {client.contact_person && (
                <div className="flex items-center text-sm text-gray-600">
                  <UserIcon className="h-4 w-4 mr-2" />
                  {client.contact_person}
                </div>
              )}
              {client.phone && (
                <div className="flex items-center text-sm text-gray-600">
                  <PhoneIcon className="h-4 w-4 mr-2" />
                  {client.phone}
                </div>
              )}
              {client.email && (
                <div className="flex items-center text-sm text-gray-600">
                  <EnvelopeIcon className="h-4 w-4 mr-2" />
                  {client.email}
                </div>
              )}
              {client.industry && (
                <div className="mt-3">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {client.industry}
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {clients.length === 0 && !loading && (
        <div className="text-center py-12">
          <BuildingOfficeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No clients found</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by adding your first client.</p>
          <div className="mt-6">
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              Add Client
            </button>
          </div>
        </div>
      )}

      {/* Add/Edit Client Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {selectedClient ? 'Edit Client' : 'Add New Client'}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Company Name *</label>
                    <input
                      type="text"
                      required
                      value={formData.company_name}
                      onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Arabic Name</label>
                    <input
                      type="text"
                      value={formData.company_name_ar}
                      onChange={(e) => setFormData({...formData, company_name_ar: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Client Code</label>
                    <input
                      type="text"
                      value={formData.client_code}
                      onChange={(e) => setFormData({...formData, client_code: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Industry</label>
                    <input
                      type="text"
                      value={formData.industry}
                      onChange={(e) => setFormData({...formData, industry: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Contact Person</label>
                    <input
                      type="text"
                      value={formData.contact_person}
                      onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Phone</label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Tax Number</label>
                    <input
                      type="text"
                      value={formData.tax_number}
                      onChange={(e) => setFormData({...formData, tax_number: e.target.value})}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Address</label>
                  <textarea
                    value={formData.address}
                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                    rows={3}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddModal(false);
                      setSelectedClient(null);
                    }}
                    className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
                  >
                    {selectedClient ? 'Update' : 'Create'} Client
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Credentials Modal Placeholder */}
      {showCredentialsModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Client Credentials - {selectedClient?.company_name}
              </h3>
              <p className="text-gray-600 mb-4">Credential management coming in Phase 2</p>
              <div className="flex justify-end">
                <button
                  onClick={() => setShowCredentialsModal(false)}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientManagement;