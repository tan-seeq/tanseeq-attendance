import React, { useState } from 'react';
import {
  DocumentTextIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  PhotoIcon,
  XMarkIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AttachmentViewer = ({ attachments, baseUrl, className = '' }) => {
  const [showModal, setShowModal] = useState(false);
  const [selectedAttachment, setSelectedAttachment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType) => {
    if (fileType?.includes('image')) {
      return PhotoIcon;
    }
    return DocumentTextIcon;
  };

  const getFileTypeColor = (fileType) => {
    if (fileType?.includes('image')) {
      return 'text-green-600';
    } else if (fileType?.includes('pdf')) {
      return 'text-red-600';
    }
    return 'text-blue-600';
  };

  const viewAttachment = (attachment) => {
    setSelectedAttachment(attachment);
    setShowModal(true);
    setError('');
  };

  const downloadAttachment = (attachment) => {
    try {
      const downloadUrl = attachment.url || attachment.file_path || attachment.attachment_url;
      if (!downloadUrl) {
        console.error('No download URL found for attachment:', attachment);
        return;
      }

      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = attachment.original_filename || attachment.filename || 'download';
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error downloading attachment:', error);
      setError('حدث خطأ في تحميل الملف');
    }
  };

  const openInNewTab = (attachment) => {
    try {
      const viewUrl = attachment.url || attachment.file_path || attachment.attachment_url;
      if (!viewUrl) {
        console.error('No view URL found for attachment:', attachment);
        return;
      }

      window.open(viewUrl, '_blank');
    } catch (error) {
      console.error('Error opening attachment:', error);
      setError('حدث خطأ في فتح الملف');
    }
  };

  if (!attachments || attachments.length === 0) {
    return null;
  }

  return (
    <div className={className}>
      <div className="space-y-2">
        {attachments.map((attachment, index) => {
          const FileIcon = getFileIcon(attachment.file_type || attachment.type);
          const iconColor = getFileTypeColor(attachment.file_type || attachment.type);
          const fileName = attachment.original_filename || attachment.filename || `ملف ${index + 1}`;
          const fileSize = attachment.file_size || attachment.size;

          return (
            <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg border hover:bg-gray-100 transition-colors">
              <div className="flex items-center flex-1 min-w-0">
                <div className="flex-shrink-0 ml-3">
                  <FileIcon className={`h-6 w-6 ${iconColor}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{fileName}</p>
                  {fileSize && (
                    <p className="text-xs text-gray-500">{formatFileSize(fileSize)}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => viewAttachment(attachment)}
                  className="text-blue-600 hover:text-blue-800 p-1 rounded hover:bg-blue-100 transition-colors"
                  title="عرض الملف"
                >
                  <EyeIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => downloadAttachment(attachment)}
                  className="text-green-600 hover:text-green-800 p-1 rounded hover:bg-green-100 transition-colors"
                  title="تحميل الملف"
                >
                  <ArrowDownTrayIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Attachment Modal */}
      {showModal && selectedAttachment && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl max-h-full w-full overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedAttachment.original_filename || selectedAttachment.filename || 'عرض الملف'}
                </h3>
                {selectedAttachment.file_size && (
                  <p className="text-sm text-gray-500">
                    {formatFileSize(selectedAttachment.file_size)}
                  </p>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => openInNewTab(selectedAttachment)}
                  className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 text-sm flex items-center"
                >
                  <EyeIcon className="h-4 w-4 ml-1" />
                  فتح في تبويب جديد
                </button>
                <button
                  onClick={() => downloadAttachment(selectedAttachment)}
                  className="bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700 text-sm flex items-center"
                >
                  <ArrowDownTrayIcon className="h-4 w-4 ml-1" />
                  تحميل
                </button>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </div>

            <div className="p-4 max-h-96 overflow-auto">
              {error ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
                    <p className="text-red-600">{error}</p>
                    <button
                      onClick={() => openInNewTab(selectedAttachment)}
                      className="mt-2 text-blue-600 hover:text-blue-800 underline"
                    >
                      محاولة فتح في تبويب جديد
                    </button>
                  </div>
                </div>
              ) : loading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <AttachmentPreview attachment={selectedAttachment} onError={setError} onLoad={() => setLoading(false)} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Component for previewing different file types
const AttachmentPreview = ({ attachment, onError, onLoad }) => {
  const [imageError, setImageError] = useState(false);
  
  const fileType = attachment.file_type || attachment.type || '';
  const fileUrl = attachment.url || attachment.file_path || attachment.attachment_url;

  // Handle different file types
  if (fileType.includes('image') && !imageError) {
    // For images, we need to handle authentication by opening in new tab
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <PhotoIcon className="h-16 w-16 text-green-600 mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          {attachment.original_filename || attachment.filename}
        </h3>
        <p className="text-gray-500 mb-4">
          صورة - انقر لعرضها في نافذة جديدة
        </p>
        <button
          onClick={() => {
            const token = localStorage.getItem('token');
            window.open(`${fileUrl}?token=${token}`, '_blank');
          }}
          className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center"
        >
          <EyeIcon className="h-4 w-4 ml-2" />
          عرض الصورة
        </button>
      </div>
    );
  } else if (fileType.includes('pdf')) {
    // For PDFs, we need to handle authentication properly
    // Since iframe can't pass custom headers, we'll show download option instead
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <DocumentTextIcon className="h-16 w-16 text-red-600 mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          {attachment.original_filename || attachment.filename}
        </h3>
        <p className="text-gray-500 mb-4">
          ملف PDF - يرجى تحميل الملف لعرضه
        </p>
        <button
          onClick={() => {
            // Create authenticated download
            const token = localStorage.getItem('token');
            const link = document.createElement('a');
            link.href = `${fileUrl}?token=${token}`;
            link.download = attachment.original_filename || attachment.filename;
            link.target = '_blank';
            link.click();
          }}
          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 flex items-center"
        >
          <ArrowDownTrayIcon className="h-4 w-4 ml-2" />
          تحميل ملف PDF
        </button>
      </div>
    );
  } else {
    // For other file types, show info and download option
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <DocumentTextIcon className="h-16 w-16 text-gray-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          {attachment.original_filename || attachment.filename}
        </h3>
        <p className="text-gray-500 mb-4">
          لا يمكن معاينة هذا النوع من الملفات في المتصفح
        </p>
        <button
          onClick={() => {
            const link = document.createElement('a');
            link.href = fileUrl;
            link.download = attachment.original_filename || attachment.filename;
            link.click();
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
        >
          <ArrowDownTrayIcon className="h-4 w-4 ml-2" />
          تحميل الملف
        </button>
      </div>
    );
  }
};

export default AttachmentViewer;