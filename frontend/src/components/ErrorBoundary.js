import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // You can log to an external service here
    // console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-3xl mx-auto p-6" dir="rtl">
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4">
            <h2 className="text-lg font-bold mb-2">حدث خطأ غير متوقع</h2>
            <p className="mb-2">يرجى تحديث الصفحة أو العودة لاحقاً. إذا استمرت المشكلة، تواصل مع الدعم.</p>
            <pre className="whitespace-pre-wrap text-xs text-red-700">{String(this.state.error)}</pre>
          </div>
        </div>
      );
    }
    return this.props.children; 
  }
}

export default ErrorBoundary;
