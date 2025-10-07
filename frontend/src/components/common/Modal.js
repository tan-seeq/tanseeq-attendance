import React, { useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

/**
 * مكون Modal محسّن مع إدارة صحيحة للـ backdrop و z-index
 * يحل مشكلة Modal Overlay التي تمنع التفاعل
 */
const Modal = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'medium',
  showCloseButton = true,
  closeOnBackdropClick = true,
  footer = null
}) => {
  // منع scroll عند فتح Modal
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // إغلاق عند الضغط على ESC
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    small: 'max-w-md',
    medium: 'max-w-2xl',
    large: 'max-w-4xl',
    xlarge: 'max-w-6xl',
    full: 'max-w-7xl'
  };

  const handleBackdropClick = (e) => {
    // فقط إذا تم النقر على الـ backdrop نفسه وليس المحتوى
    if (e.target === e.currentTarget && closeOnBackdropClick) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop - يمكن النقر عليه للإغلاق */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleBackdropClick}
        aria-hidden="true"
      />
      
      {/* Modal Content Container */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div 
          className={`relative bg-white rounded-lg shadow-xl ${sizeClasses[size]} w-full mx-auto`}
          onClick={(e) => e.stopPropagation()} // منع إغلاق عند النقر على المحتوى
        >
          {/* Header */}
          {(title || showCloseButton) && (
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900" dir="rtl">
                {title}
              </h3>
              {showCloseButton && (
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                  aria-label="إغلاق"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              )}
            </div>
          )}

          {/* Body */}
          <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
            {children}
          </div>

          {/* Footer */}
          {footer && (
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Modal;
