import { useState } from 'react';

export default function AttendanceApp() {
  const [employeeCode, setEmployeeCode] = useState('');
  const [employeeName, setEmployeeName] = useState('');
  const [status, setStatus] = useState('');
  const [location, setLocation] = useState(null);

  const handleCheck = async (type) => {
    if (!employeeCode || !employeeName) {
      setStatus('الرجاء إدخال اسم الموظف والكود');
      return;
    }

    if (!navigator.geolocation) {
      setStatus('المتصفح لا يدعم تحديد الموقع');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const coords = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          timestamp: new Date().toLocaleString(),
        };
        setLocation(coords);

        const data = {
          employeeCode,
          employeeName,
          checkType: type,
          date: new Date().toLocaleDateString(),
          time: new Date().toLocaleTimeString(),
          latitude: coords.latitude,
          longitude: coords.longitude,
        };

        try {
          const res = await fetch("https://sheetdb.io/api/v1/5q2tw4v6r04le", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ data }),
          });

          if (res.ok) {
            setStatus(`تم تسجيل ${type} بنجاح عند الساعة ${data.time}`);
          } else {
            setStatus("فشل في إرسال البيانات، تأكد من الاتصال بالإنترنت.");
          }
        } catch (err) {
          setStatus("حدث خطأ أثناء الإرسال.");
        }
      },
      () => {
        setStatus('تعذر الحصول على الموقع الجغرافي');
      }
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="w-full max-w-md bg-white shadow-lg rounded-xl p-6 space-y-4">
        <h1 className="text-2xl font-bold text-center">شركة التنسيق للإستشارات الضريبية</h1>
        <p className="text-sm text-center text-gray-500">نظام تسجيل الحضور والانصراف</p>

        <input
          type="text"
          placeholder="اسم الموظف"
          value={employeeName}
          onChange={(e) => setEmployeeName(e.target.value)}
          className="w-full border rounded p-2"
        />
        <input
          type="text"
          placeholder="كود الموظف"
          value={employeeCode}
          onChange={(e) => setEmployeeCode(e.target.value)}
          className="w-full border rounded p-2"
        />

        <div className="flex justify-around">
          <button
            onClick={() => handleCheck('حضور')}
            className="bg-green-600 text-white px-4 py-2 rounded"
          >
            تسجيل حضور
          </button>
          <button
            onClick={() => handleCheck('انصراف')}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            تسجيل انصراف
          </button>
        </div>

        {status && <div className="text-center text-green-700 mt-4">{status}</div>}

        {location && (
          <div className="text-xs text-center text-gray-400">
            الموقع: {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
          </div>
        )}
      </div>
    </div>
  );
}
