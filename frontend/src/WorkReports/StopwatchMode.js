import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  PlayIcon, 
  PauseIcon,
  StopIcon,
  ClockIcon,
  DocumentTextIcon,
  BuildingOfficeIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

const StopwatchMode = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [sessions, setSessions] = useState([]);
  const [clients, setClients] = useState([]);
  const [activityTypes, setActivityTypes] = useState([]);
  const [currentSession, setCurrentSession] = useState({
    client_id: '',
    activity_type_id: '',
    description: '',
    notes: ''
  });
  const [completedSessions, setCompletedSessions] = useState([]);

  const intervalRef = useRef(null);
  const startTimeRef = useRef(null);
  const pausedTimeRef = useRef(0);

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchClients();
    fetchActivityTypes();
    
    // Load saved session from localStorage
    const savedSession = localStorage.getItem('stopwatch_session');
    if (savedSession) {
      const parsed = JSON.parse(savedSession);
      setCurrentSession(parsed.session || currentSession);
      setTimeElapsed(parsed.timeElapsed || 0);
      setIsPaused(parsed.isPaused || false);
      
      if (parsed.isRunning && !parsed.isPaused) {
        // Resume timer if it was running
        const savedStartTime = parsed.startTime;
        const now = Date.now();
        const additionalTime = Math.floor((now - savedStartTime) / 1000);
        setTimeElapsed(parsed.timeElapsed + additionalTime);
        startTimer();
      }
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  useEffect(() => {
    // Auto-save session state
    const sessionState = {
      session: currentSession,
      timeElapsed,
      isRunning,
      isPaused,
      startTime: startTimeRef.current
    };
    localStorage.setItem('stopwatch_session', JSON.stringify(sessionState));
  }, [currentSession, timeElapsed, isRunning, isPaused]);

  const fetchClients = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/work-reports/clients`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClients(response.data);
    } catch (err) {
      console.error('Error fetching clients:', err);
    }
  };

  const fetchActivityTypes = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${backendUrl}/api/work-reports/activity-types`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setActivityTypes(response.data);
    } catch (err) {
      console.error('Error fetching activity types:', err);
    }
  };

  const startTimer = () => {
    if (intervalRef.current) return; // Prevent multiple intervals
    
    if (!isPaused) {
      startTimeRef.current = Date.now() - (timeElapsed * 1000);
    } else {
      startTimeRef.current = Date.now() - (pausedTimeRef.current * 1000);
    }
    
    setIsRunning(true);
    setIsPaused(false);
    
    intervalRef.current = setInterval(() => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTimeRef.current) / 1000);
      setTimeElapsed(elapsed);
    }, 1000);
  };

  const pauseTimer = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    pausedTimeRef.current = timeElapsed;
    setIsPaused(true);
    setIsRunning(false);
  };

  const stopTimer = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    if (timeElapsed > 0) {
      // Add to completed sessions
      const session = {
        ...currentSession,
        duration: timeElapsed,
        startTime: startTimeRef.current ? new Date(startTimeRef.current) : new Date(),
        endTime: new Date(),
        id: Date.now() // Temporary ID
      };
      
      setCompletedSessions(prev => [...prev, session]);
    }
    
    // Reset timer
    setTimeElapsed(0);
    setIsRunning(false);
    setIsPaused(false);
    pausedTimeRef.current = 0;
    
    // Clear saved session
    localStorage.removeItem('stopwatch_session');
  };

  const resetTimer = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    setTimeElapsed(0);
    setIsRunning(false);
    setIsPaused(false);
    pausedTimeRef.current = 0;
    
    // Clear saved session
    localStorage.removeItem('stopwatch_session');
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSessionChange = (field, value) => {
    setCurrentSession(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const canStart = currentSession.client_id && currentSession.activity_type_id && currentSession.description.trim();

  const saveCompletedSessions = async () => {
    if (completedSessions.length === 0) return;
    
    try {
      const token = localStorage.getItem('token');
      
      for (const session of completedSessions) {
        const logData = {
          client_id: session.client_id,
          activity_type_id: session.activity_type_id,
          date: session.startTime.toISOString(),
          start_time: session.startTime.toISOString(),
          end_time: session.endTime.toISOString(),
          duration_minutes: Math.floor(session.duration / 60),
          description: session.description,
          notes: session.notes,
          is_billable: true
        };
        
        await axios.post(`${backendUrl}/api/work-reports/logs`, logData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }
      
      alert(`${completedSessions.length} work sessions saved successfully!`);
      setCompletedSessions([]);
      
    } catch (err) {
      console.error('Error saving sessions:', err);
      alert('Failed to save some sessions. Please try again.');
    }
  };

  const deleteCompletedSession = (sessionId) => {
    setCompletedSessions(prev => prev.filter(s => s.id !== sessionId));
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Stopwatch Mode</h1>
        <p className="text-gray-600">وضع ساعة الإيقاف - تتبع الوقت الفعلي للمهام</p>
      </div>

      {/* Main Stopwatch */}
      <div className="bg-white rounded-2xl shadow-2xl p-8 mb-8">
        {/* Timer Display */}
        <div className="text-center mb-8">
          <div className="text-6xl font-mono font-bold text-blue-600 mb-4">
            {formatTime(timeElapsed)}
          </div>
          <div className="flex justify-center items-center space-x-2 text-sm text-gray-500">
            <ClockIcon className="h-4 w-4" />
            <span>
              {isRunning && !isPaused ? 'Running' : 
               isPaused ? 'Paused' : 'Stopped'}
            </span>
          </div>
        </div>

        {/* Session Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Client - العميل *
            </label>
            <select
              value={currentSession.client_id}
              onChange={(e) => handleSessionChange('client_id', e.target.value)}
              disabled={isRunning}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              required
            >
              <option value="">Select client - اختر العميل</option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.company_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Activity - النشاط *
            </label>
            <select
              value={currentSession.activity_type_id}
              onChange={(e) => handleSessionChange('activity_type_id', e.target.value)}
              disabled={isRunning}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              required
            >
              <option value="">Select activity - اختر النشاط</option>
              {activityTypes.map(activity => (
                <option key={activity.id} value={activity.id}>
                  {activity.name}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Task Description - وصف المهمة *
            </label>
            <textarea
              value={currentSession.description}
              onChange={(e) => handleSessionChange('description', e.target.value)}
              disabled={isRunning}
              rows={3}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              placeholder="Describe what you're working on..."
              required
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes - ملاحظات
            </label>
            <textarea
              value={currentSession.notes}
              onChange={(e) => handleSessionChange('notes', e.target.value)}
              rows={2}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Additional notes..."
            />
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex justify-center space-x-4">
          {!isRunning && !isPaused && (
            <button
              onClick={startTimer}
              disabled={!canStart}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-3 px-8 rounded-lg flex items-center space-x-2 text-lg transition-colors"
            >
              <PlayIcon className="h-6 w-6" />
              <span>Start</span>
            </button>
          )}

          {isRunning && !isPaused && (
            <button
              onClick={pauseTimer}
              className="bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-3 px-8 rounded-lg flex items-center space-x-2 text-lg transition-colors"
            >
              <PauseIcon className="h-6 w-6" />
              <span>Pause</span>
            </button>
          )}

          {isPaused && (
            <button
              onClick={startTimer}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg flex items-center space-x-2 text-lg transition-colors"
            >
              <PlayIcon className="h-6 w-6" />
              <span>Resume</span>
            </button>
          )}

          {(isRunning || isPaused) && (
            <button
              onClick={stopTimer}
              className="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-8 rounded-lg flex items-center space-x-2 text-lg transition-colors"
            >
              <StopIcon className="h-6 w-6" />
              <span>Stop</span>
            </button>
          )}

          {!isRunning && timeElapsed > 0 && (
            <button
              onClick={resetTimer}
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-8 rounded-lg text-lg transition-colors"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Completed Sessions */}
      {completedSessions.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              Completed Sessions - الجلسات المكتملة ({completedSessions.length})
            </h2>
            <button
              onClick={saveCompletedSessions}
              className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-6 rounded-md flex items-center space-x-2 transition-colors"
            >
              <CheckIcon className="h-5 w-5" />
              <span>Save All Sessions</span>
            </button>
          </div>

          <div className="space-y-4">
            {completedSessions.map((session) => {
              const client = clients.find(c => c.id === session.client_id);
              const activity = activityTypes.find(a => a.id === session.activity_type_id);
              
              return (
                <div key={session.id} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4 mb-2">
                        <div className="flex items-center text-blue-600">
                          <BuildingOfficeIcon className="h-4 w-4 mr-1" />
                          <span className="font-medium">{client?.company_name}</span>
                        </div>
                        <div className="flex items-center text-green-600">
                          <DocumentTextIcon className="h-4 w-4 mr-1" />
                          <span>{activity?.name}</span>
                        </div>
                        <div className="flex items-center text-purple-600">
                          <ClockIcon className="h-4 w-4 mr-1" />
                          <span className="font-mono font-bold">{formatTime(session.duration)}</span>
                        </div>
                      </div>
                      
                      <p className="text-gray-700 text-sm mb-1">
                        <strong>Description:</strong> {session.description}
                      </p>
                      
                      {session.notes && (
                        <p className="text-gray-600 text-sm">
                          <strong>Notes:</strong> {session.notes}
                        </p>
                      )}
                      
                      <p className="text-gray-500 text-xs mt-2">
                        {session.startTime.toLocaleTimeString()} - {session.endTime.toLocaleTimeString()}
                      </p>
                    </div>
                    
                    <button
                      onClick={() => deleteCompletedSession(session.id)}
                      className="text-red-600 hover:text-red-800 text-sm font-medium ml-4"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
        <div className="flex">
          <ClockIcon className="h-5 w-5 text-blue-400 mt-0.5" />
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              <strong>Tips for Effective Time Tracking:</strong>
            </p>
            <ul className="text-sm text-blue-600 mt-1 space-y-1">
              <li>• Fill in client and activity details before starting the timer</li>
              <li>• Use descriptive task descriptions for better reporting</li>
              <li>• Take breaks between different tasks to maintain accuracy</li>
              <li>• Save sessions regularly to avoid data loss</li>
              <li>• Review completed sessions before saving to work logs</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StopwatchMode;