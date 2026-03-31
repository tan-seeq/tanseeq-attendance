import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import jwt_decode from 'jwt-decode';
import { API } from '../config';

const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [showNotificationModal, setShowNotificationModal] = useState(false);
  const [notificationDismissed, setNotificationDismissed] = useState(
    () => sessionStorage.getItem('notificationDismissed') === 'true'
  );
  
  const dismissNotifications = () => {
    setShowNotificationModal(false);
    setNotificationDismissed(true);
    sessionStorage.setItem('notificationDismissed', 'true');
  };

  useEffect(() => {
    const reqId = axios.interceptors.request.use((config) => {
      const t = localStorage.getItem('token');
      if (t && !config.headers?.Authorization) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${t}`;
      }
      return config;
    });
    const resId = axios.interceptors.response.use(
      (resp) => resp,
      (err) => {
        if (err?.response?.status === 401) {
          // token invalid or expired
        }
        return Promise.reject(err);
      }
    );

    if (token) {
      try {
        const decoded = jwt_decode(token);
        if (decoded.exp * 1000 > Date.now()) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          fetchUser();
        } else {
          logout();
        }
      } catch (error) {
        logout();
      }
    } else {
      setLoading(false);
    }

    return () => {
      axios.interceptors.request.eject(reqId);
      axios.interceptors.response.eject(resId);
    };
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      if (response.data) {
        setUser(response.data);
        setTimeout(() => {
          checkMandatoryNotifications();
        }, 1000);
      }
      setLoading(false);
    } catch (error) {
      try {
        const statsResponse = await axios.get(`${API}/dashboard/stats`);
        if (token) {
          const decoded = jwt_decode(token);
          const userData = {
            id: decoded.sub || decoded.user_id || decoded.id,
            name: decoded.name || 'User',
            email: decoded.email || decoded.username,
            role: decoded.role || 'user'
          };
          setUser(userData);
          setTimeout(() => {
            checkMandatoryNotifications();
          }, 1000);
        }
        setLoading(false);
      } catch (fallbackError) {
        console.error('Both user fetch attempts failed:', error, fallbackError);
        logout();
      }
    }
  };

  const checkMandatoryNotifications = async () => {
    if (notificationDismissed) return;
    try {
      const response = await axios.get(`${API}/notifications/count`);
      if (response.data.unread_count > 0) {
        setShowNotificationModal(true);
      }
    } catch (error) {
      console.error('Error checking notifications:', error);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setTimeout(() => {
        checkMandatoryNotifications();
      }, 1000);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    sessionStorage.removeItem('notificationDismissed');
    setNotificationDismissed(false);
    delete axios.defaults.headers.common['Authorization'];
    setLoading(false);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      login, 
      logout, 
      loading, 
      showNotificationModal, 
      setShowNotificationModal,
      dismissNotifications,
      checkMandatoryNotifications 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export { AuthContext, AuthProvider, useAuth };
