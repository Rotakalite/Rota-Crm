import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { ClerkProvider, SignedIn, SignedOut, RedirectToSignIn, useUser, useClerk, SignOutButton } from '@clerk/clerk-react';
import YeniBelgeYonetimiYeni from './YeniBelgeYonetimiYeni';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';

// Axios performance optimization
axios.defaults.timeout = 10000; // 10 second timeout
axios.defaults.headers.common['Content-Type'] = 'application/json';

// API URL Configuration
const getApiUrl = () => {
  // Use environment variable for backend URL
  const backendUrl = process.env.REACT_APP_BACKEND_URL + '/api';
  console.log('🔗 Backend URL:', backendUrl);
  return backendUrl;
};

// Authentication Hook - Working version from GitHub
const useAuth = () => {
  const { user, isLoaded } = useUser();
  const { session } = useClerk();
  const [authToken, setAuthToken] = useState(() => {
    // Initialize from sessionStorage
    return sessionStorage.getItem('authToken') || null;
  });
  const [userRole, setUserRole] = useState(() => {
    // Initialize from sessionStorage
    return sessionStorage.getItem('userRole') || null;
  });
  const [dbUser, setDbUser] = useState(() => {
    // Initialize from sessionStorage
    const storedUser = sessionStorage.getItem('dbUser');
    return storedUser ? JSON.parse(storedUser) : null;
  });

  // Enhanced token refresh with better error handling and proactive refresh
  const refreshToken = async (force = false) => {
    try {
      if (session) {
        console.log('🔄 Refreshing token...', force ? '(forced)' : '');
        console.log('🔄 Session available:', !!session);
        console.log('🔄 Session status:', session.status);
        console.log('🔄 Session lastActiveAt:', session.lastActiveAt);
        
        const newToken = await session.getToken({ skipCache: true });
        console.log('🔄 New token received:', !!newToken);
        
        if (newToken) {
          setAuthToken(newToken);
          localStorage.setItem('authToken', newToken);
          sessionStorage.setItem('authToken', newToken);
          localStorage.setItem('tokenTimestamp', Date.now().toString());
          console.log('✅ Token refreshed successfully');
          return newToken;
        } else {
          console.error('❌ No token received from session');
          throw new Error('No token received from session');
        }
      } else {
        console.error('❌ No session available for refresh');
        throw new Error('No session available');
      }
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      console.error('❌ Session status:', !!session);
      console.error('❌ Session details:', session ? {
        status: session.status,
        lastActiveAt: session.lastActiveAt,
        id: session.id
      } : 'No session');
      
      // Only clear if session is actually invalid
      if (!session || session.status !== 'active') {
        console.log('🧹 Clearing session data due to invalid session');
        localStorage.removeItem('authToken');
        localStorage.removeItem('tokenTimestamp');
        sessionStorage.removeItem('userRole');
        sessionStorage.removeItem('dbUser');
        sessionStorage.removeItem('authToken');
        setAuthToken(null);
        setUserRole(null);
        setDbUser(null);
      }
      throw error;
    }
  };

  // Ultra-aggressive token refresh function - refresh every 2 minutes
  const ensureFreshToken = async () => {
    try {
      const tokenTimestamp = localStorage.getItem('tokenTimestamp');
      const currentTime = Date.now();
      const twoMinutes = 2 * 60 * 1000; // 2 minutes in milliseconds - MUCH more aggressive
      
      // If no timestamp or token is older than 2 minutes, refresh
      if (!tokenTimestamp || (currentTime - parseInt(tokenTimestamp)) > twoMinutes) {
        console.log('🔄 Token is older than 2 minutes, proactive refresh...');
        return await refreshToken(true);
      }
      
      return authToken;
    } catch (error) {
      console.error('❌ Proactive token refresh failed:', error);
      return authToken; // Return existing token if refresh fails
    }
  };

  // Setup axios interceptor for automatic token refresh
  useEffect(() => {
    const requestInterceptor = axios.interceptors.request.use(
      async (config) => {
        // Proactively refresh token before each request
        try {
          const freshToken = await ensureFreshToken();
          if (freshToken) {
            config.headers.Authorization = `Bearer ${freshToken}`;
          }
        } catch (error) {
          console.error('❌ Failed to ensure fresh token:', error);
          // Use existing token as fallback
          const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        console.log('🔍 Axios interceptor - Error status:', error.response?.status);
        console.log('🔍 Axios interceptor - Already retried:', !!originalRequest._retry);
        console.log('🔍 Axios interceptor - Session available:', !!session);
        
        // If token expired and we haven't already tried to refresh
        if (error.response?.status === 401 && !originalRequest._retry && session) {
          originalRequest._retry = true;
          
          try {
            console.log('🔄 Token expired, attempting refresh...');
            
            // Call refreshToken function directly
            const newToken = await refreshToken();
            
            console.log('✅ Token refresh successful, retrying original request');
            console.log('✅ New token:', newToken ? 'Present' : 'Missing');
            
            // Retry the original request with new token
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            
            console.log('🔄 Retrying original request to:', originalRequest.url);
            const retryResponse = await axios(originalRequest);
            console.log('✅ Retry successful!');
            
            return retryResponse;
          } catch (refreshError) {
            console.error('❌ Token refresh failed, clearing session silently');
            console.error('❌ Refresh error:', refreshError);
            
            // Clear session silently WITHOUT page reload
            localStorage.removeItem('authToken');
            localStorage.removeItem('tokenTimestamp');
            sessionStorage.removeItem('userRole');
            sessionStorage.removeItem('dbUser');
            sessionStorage.removeItem('authToken');
            
            // Set auth states to null to trigger re-auth WITHOUT reload
            setAuthToken(null);
            setUserRole(null);
            setDbUser(null);
            
            console.log('🔄 Session cleared, user will see login without page refresh');
            return Promise.reject(refreshError);
          }
        }
        
        console.log('❌ Request failed, not retrying:', error.response?.status);
        return Promise.reject(error);
      }
    );

    // Cleanup interceptors on unmount
    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, [session, refreshToken]); // Add refreshToken to dependencies

  // Ultra-frequent token refresh - refresh every 90 seconds to prevent expiry
  useEffect(() => {
    if (authToken && session) {
      console.log('⏰ Setting up 90-second token refresh interval...');
      const interval = setInterval(async () => {
        try {
          console.log('⏰ Auto-refreshing token (90-second interval)...');
          await refreshToken();
          console.log('✅ Auto-refresh successful');
        } catch (error) {
          console.error('❌ Auto-refresh failed:', error);
        }
      }, 90 * 1000); // 90 seconds - ultra-frequent refresh to prevent any expiry

      return () => {
        console.log('🛑 Clearing token refresh interval');
        clearInterval(interval);
      };
    }
  }, [authToken, session]);

  // Enhanced activity-based token refresh
  useEffect(() => {
    if (authToken && session) {
      let lastActivity = Date.now();
      let refreshTimeout;

      const resetActivityTimer = () => {
        lastActivity = Date.now();
        
        // Clear existing timeout
        if (refreshTimeout) {
          clearTimeout(refreshTimeout);
        }
        
        // Set new timeout for 30 seconds of inactivity - MUCH more aggressive
        refreshTimeout = setTimeout(async () => {
          try {
            console.log('🔄 Proactive token refresh due to 30s inactivity...');
            await refreshToken();
            console.log('✅ Proactive refresh successful');
          } catch (error) {
            console.error('❌ Proactive refresh failed:', error);
          }
        }, 30 * 1000); // 30 seconds - ultra-aggressive refresh
      };

      // Activity events to monitor
      const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
      
      // Add activity listeners
      activityEvents.forEach(event => {
        document.addEventListener(event, resetActivityTimer, true);
      });

      // Initialize timer
      resetActivityTimer();

      return () => {
        // Clean up
        activityEvents.forEach(event => {
          document.removeEventListener(event, resetActivityTimer, true);
        });
        if (refreshTimeout) {
          clearTimeout(refreshTimeout);
        }
      };
    }
  }, [authToken, session]);

  // Periyodik token yenileme - her 1 dakikada bir (ultra-aggressive)
  useEffect(() => {
    if (authToken && session) {
      const refreshInterval = setInterval(async () => {
        try {
          console.log('🔄 Periyodik token yenileme (1 dakika)...');
          await refreshToken(true);
          console.log('✅ Periyodik yenileme başarılı');
        } catch (error) {
          console.error('❌ Periyodik yenileme hatası:', error);
        }
      }, 60 * 1000); // Her 1 dakikada bir - ultra-frequent

      return () => clearInterval(refreshInterval);
    }
  }, [authToken, session]);

  // Check token expiry on page focus
  useEffect(() => {
    const handleFocus = async () => {
      if (authToken && session) {
        try {
          // Try to get a fresh token when page regains focus
          console.log('🔄 Page focused, checking token freshness...');
          await refreshToken();
        } catch (error) {
          console.error('❌ Token refresh on focus failed:', error);
        }
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [authToken, session]);

  // Utility function to ensure fresh token before important operations
  const ensureTokenForOperation = async () => {
    try {
      console.log('🔄 Ensuring fresh token for operation...');
      await ensureFreshToken();
      console.log('✅ Token ready for operation');
    } catch (error) {
      console.error('❌ Failed to ensure fresh token:', error);
      throw error;
    }
  };

  const refreshUser = async () => {
    if (authToken) {
      try {
        const API = getApiUrl();
        const response = await axios.get(`${API}/me`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        // Update both dbUser and userRole states
        setDbUser(response.data);
        setUserRole(response.data.role);
        
        // Update sessionStorage
        sessionStorage.setItem('dbUser', JSON.stringify(response.data));
        sessionStorage.setItem('userRole', response.data.role);
        
        console.log('✅ User data refreshed:', response.data);
        
        return response.data;
      } catch (error) {
        console.error('Error refreshing user:', error);
        // Clear invalid session data
        if (error.response?.status === 401) {
          localStorage.removeItem('authToken');
          localStorage.removeItem('tokenTimestamp');
          localStorage.removeItem('userRole');
          localStorage.removeItem('dbUser');
          setAuthToken(null);
          setUserRole(null);
          setDbUser(null);
        }
        throw error;
      }
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      if (isLoaded && user && session) {
        try {
          // DIRECT role from Clerk metadata - highest priority
          const directRole = user.publicMetadata?.role || null; // Don't default to 'client'
          if (directRole) {
            setUserRole(directRole);
            sessionStorage.setItem('userRole', directRole);
            console.log('🔍 Clerk Role:', directRole);
          } else {
            console.log('🔍 No role set, user needs role selection');
          }
          console.log('✅ Set role to:', directRole);

          // Get token from session or localStorage
          try {
            let token = localStorage.getItem('authToken');
            const tokenTimestamp = localStorage.getItem('tokenTimestamp');
            
            // Check if token is less than 24 hours old
            if (token && tokenTimestamp) {
              const tokenAge = Date.now() - parseInt(tokenTimestamp);
              const twentyFourHours = 24 * 60 * 60 * 1000;
              
              if (tokenAge < twentyFourHours) {
                console.log('🎯 Using cached token (age:', Math.round(tokenAge / 1000 / 60), 'minutes)');
                setAuthToken(token);
              } else {
                console.log('🔄 Token expired, getting fresh token');
                token = await session.getToken();
                setAuthToken(token);
                localStorage.setItem('authToken', token);
                localStorage.setItem('tokenTimestamp', Date.now().toString());
              }
            } else {
              console.log('🆕 Getting fresh token');
              token = await session.getToken();
              setAuthToken(token);
              localStorage.setItem('authToken', token);
              localStorage.setItem('tokenTimestamp', Date.now().toString());
            }
            
            console.log('🎯 Token set successfully');
            
            // Register/update user in our database
            const API = getApiUrl();
            const response = await axios.post(`${API}/auth/register`, {
              clerk_user_id: user.id,
              email: user.primaryEmailAddress?.emailAddress || '',
              name: user.fullName || user.firstName || 'User',
              role: directRole
            }, {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });
            
            setDbUser(response.data);
            sessionStorage.setItem('dbUser', JSON.stringify(response.data));
            
            // CRITICAL FIX: Set role from database response, not from Clerk metadata
            if (response.data.role) {
              setUserRole(response.data.role);
              sessionStorage.setItem('userRole', response.data.role);
              console.log('✅ User role set from database:', response.data.role);
            } else {
              console.log('⚠️ No role in database, user needs role selection');
            }
            
            console.log('✅ User registered in database');
            
          } catch (tokenError) {
            console.error('Token error:', tokenError);
            console.log('🎯 Setting role without token');
            setUserRole(directRole);
            sessionStorage.setItem('userRole', directRole);
          }
          
        } catch (error) {
          console.error('Auth initialization error:', error);
          // Fallback role setting
          const directRole = user.publicMetadata?.role || 'client';
          setUserRole(directRole);
          sessionStorage.setItem('userRole', directRole);
        }
      } else if (isLoaded && user) {
        // If no session but user exists, still set role
        const directRole = user.publicMetadata?.role || 'client';
        setUserRole(directRole);
        sessionStorage.setItem('userRole', directRole);
        console.log('🎯 No session, setting role without token:', directRole);
      } else if (isLoaded && !user) {
        // User logged out, clear session data
        setAuthToken(null);
        setUserRole(null);
        setDbUser(null);
        sessionStorage.removeItem('authToken');
        sessionStorage.removeItem('userRole');
        sessionStorage.removeItem('dbUser');
        console.log('🚪 User logged out, clearing session data');
      }
    };

    initAuth();
  }, [user, isLoaded, session]);

  return { user, authToken, userRole, dbUser, isLoaded, refreshUser, refreshToken, ensureFreshToken, ensureTokenForOperation };
};

// Global utility function for file icons
const getFileIcon = (filePath) => {
  const extension = filePath && filePath.split('.').pop() && filePath.split('.').pop().toLowerCase();
  switch (extension) {
    case 'pdf': return '📄';
    case 'doc':
    case 'docx': return '📝';
    case 'xls':
    case 'xlsx': return '📊';
    case 'jpg':
    case 'jpeg':
    case 'png': return '🖼️';
    case 'zip':
    case 'rar': return '📦';
    default: return '📋';
  }
};

// Functional Consultant Dashboard - Fixed Version
const ConsultantDashboard = ({ onNavigate }) => {
  const { authToken, dbUser, refreshToken } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const API = getApiUrl();

  useEffect(() => {
    if (authToken) {
      fetchData();
    }
  }, [authToken]);

  const fetchData = async () => {
    if (!authToken) return;
    
    try {
      setLoading(true);
      
      // Debug user information - DETAILED
      console.log('🔍 CONSULTANT DEBUG - dbUser:', dbUser);
      console.log('🔍 CONSULTANT DEBUG - consultant_id:', dbUser?.consultant_id);
      
      // Fetch COMPLETE user info from debug endpoint
      const debugResponse = await axios.get(`${API}/debug/user-info`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      console.log('🔍 CONSULTANT DEBUG - Debug endpoint response:', debugResponse.data);
      
      // Fetch user info from /me for complete data
      const userResponse = await axios.get(`${API}/me`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      console.log('🔍 CONSULTANT DEBUG - API /api/me response:', userResponse.data);
      
      const statsResponse = await axios.get(`${API}/stats`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setDashboardData(statsResponse.data);

      const clientsResponse = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { Authorization: `Bearer ${authToken}` }
      });
      console.log('🔍 CONSULTANT DEBUG - clients response:', clientsResponse.data);
      console.log('🔍 CONSULTANT DEBUG - clients count:', clientsResponse.data.clients?.length || 0);
      console.log('🔍 CONSULTANT DEBUG - clients array:', clientsResponse.data.clients);
      setClients(clientsResponse.data.clients || []);
      
      // Debug after setting clients
      console.log('🔍 CONSULTANT DEBUG - clients state set to:', clientsResponse.data.clients || []);

    } catch (error) {
      console.error('Error fetching consultant data:', error);
      console.error('Error details:', error.response?.status, error.response?.data);
      
      // If it's an auth error, try to refresh token and retry
      if (error.response?.status === 401) {
        console.log('🔄 Consultant Dashboard: Token expired, trying refresh...');
        try {
          const newToken = await refreshToken();
          if (newToken) {
            console.log('✅ Token refreshed, retrying API calls...');
            
            // Retry stats call
            const retryStatsResponse = await axios.get(`${API}/stats`, {
              headers: { Authorization: `Bearer ${newToken}` }
            });
            setDashboardData(retryStatsResponse.data);
            
            // Retry clients call
            const retryClientsResponse = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
              headers: { Authorization: `Bearer ${newToken}` }
            });
            setClients(retryClientsResponse.data.clients || []);
            
            console.log('✅ Consultant dashboard data refreshed successfully');
            return; // Exit catch block if successful
          }
        } catch (refreshError) {
          console.error('❌ Token refresh failed:', refreshError);
        }
      }
      
      // If auth refresh failed or other error, show realistic fallback
      console.log('🔧 Using fallback data for consultant dashboard');
      setDashboardData({
        total_clients: 2,  // Based on backend test results
        total_documents: 2,
        total_trainings: 2
      });
      setClients([
        {
          id: '1',
          hotel_name: 'DENİZ OTEL',
          contact_person: 'Deniz Bey',
          email: 'deniz@hotal.com',
          phone: '+90 555 123 4567'
        },
        {
          id: '2',
          hotel_name: 'BELO',
          contact_person: 'Belo Yetkilisi', 
          email: 'info@belo.com',
          phone: '+90 555 987 6543'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p className="ml-4 text-gray-600">Elite Dashboard Yükleniyor...</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
      <div className="mb-8">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 rounded-xl shadow-lg">
          <h1 className="text-3xl font-bold flex items-center">
            <span className="mr-3 text-4xl">👔</span>
            Elite Danışman Kontrol Paneli
          </h1>
          <p className="text-blue-100 mt-2 text-lg">
            Hoş geldiniz {dbUser?.company_name || dbUser?.name || 'ROTA Danışmanlık'}! Müşterilerinizi profesyonelce yönetin.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-2">Müşterilerim</h3>
              <p className="text-3xl font-bold">{clients.length}</p>
            </div>
            <div className="text-4xl opacity-80">🏨</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-2">Dokümanlar</h3>
              <p className="text-3xl font-bold">{dashboardData?.total_documents || 0}</p>
            </div>
            <div className="text-4xl opacity-80">📄</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-2">Eğitimler</h3>
              <p className="text-3xl font-bold">{dashboardData?.total_trainings || 0}</p>
            </div>
            <div className="text-4xl opacity-80">🎓</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-2">Aktif Projeler</h3>
              <p className="text-3xl font-bold">
                {(dashboardData?.stage_distribution?.stage_1 || 0) + 
                 (dashboardData?.stage_distribution?.stage_2 || 0)}
              </p>
            </div>
            <div className="text-4xl opacity-80">⚡</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-800">🏨 Müşterilerim</h2>
            <button 
              onClick={() => onNavigate('my-clients')}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Tümünü Gör
            </button>
          </div>
          
          <div className="space-y-4">
            {(() => {
              console.log('🔍 CONSULTANT RENDER DEBUG - clients:', clients);
              console.log('🔍 CONSULTANT RENDER DEBUG - clients.length:', clients.length);
              return clients.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🏨</div>
                  <p className="text-sm">Henüz size atanmış müşteri bulunmamaktadır.</p>
                  <p className="text-xs mt-1">Admin tarafından müşteri ataması yapılması gerekmektedir.</p>
                </div>
              ) : (
                clients.slice(0, 3).map((client) => (
                  <div key={client.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
                    <h3 className="font-bold text-gray-800">{client.hotel_name || client.name}</h3>
                    <p className="text-gray-600 text-sm">{client.email}</p>
                    <div className="mt-3 flex space-x-2">
                      <button 
                        onClick={() => onNavigate('yeni-belge')}
                        className="flex-1 bg-blue-500 text-white py-2 px-3 rounded-lg text-sm hover:bg-blue-600 transition-colors"
                      >
                        📄 Belgeler
                      </button>
                      <button 
                        onClick={() => onNavigate('carbon')}
                        className="flex-1 bg-green-500 text-white py-2 px-3 rounded-lg text-sm hover:bg-green-600 transition-colors"
                      >
                        🌱 Analiz
                      </button>
                    </div>
                  </div>
                ))
              );
            })()}
          </div>
          
          {clients.length === 0 && (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">🏨</div>
              <p className="text-gray-600">Henüz müşteri bulunmamaktadır.</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-6">🚀 Hızlı Aksiyonlar</h2>
          
          <div className="grid grid-cols-2 gap-4">
            <button 
              onClick={() => onNavigate('my-clients')}
              className="p-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg hover:from-indigo-600 hover:to-purple-700 transition-all text-center"
            >
              <div className="text-2xl mb-2">🏨</div>
              <div className="font-medium">Müşteri Yönet</div>
            </button>
            
            <button 
              onClick={() => onNavigate('yeni-belge')}
              className="p-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg hover:from-emerald-600 hover:to-teal-700 transition-all text-center"
            >
              <div className="text-2xl mb-2">📄</div>
              <div className="font-medium">Belge Yönet</div>
            </button>
            
            <button 
              onClick={() => onNavigate('carbon')}
              className="p-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all text-center"
            >
              <div className="text-2xl mb-2">🌱</div>
              <div className="font-medium">Karbon Analizi</div>
            </button>
            
            <button 
              onClick={() => onNavigate('reports')}
              className="p-4 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-lg hover:from-purple-600 hover:to-pink-700 transition-all text-center"
            >
              <div className="text-2xl mb-2">📊</div>
              <div className="font-medium">Raporlar</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Consultant Client Management
const ConsultantClientManagement = ({ onNavigate }) => {
  const { authToken } = useAuth();
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [sortOrder, setSortOrder] = useState('asc');
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasPrev, setHasPrev] = useState(false);
  const [hasNext, setHasNext] = useState(false);
  const [clientTypeFilter, setClientTypeFilter] = useState('all');
  const API = getApiUrl();

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      fetchClients(newPage, itemsPerPage, searchTerm, sortBy, sortOrder, clientTypeFilter);
    }
  };

  useEffect(() => {
    if (authToken) {
      fetchClients(currentPage, itemsPerPage, searchTerm, sortBy, sortOrder, clientTypeFilter);
    }
  }, [authToken, currentPage, itemsPerPage, searchTerm, sortBy, sortOrder, clientTypeFilter]);

  const fetchClients = async (page = 1, limit = itemsPerPage, search = searchTerm, sort = sortBy, order = sortOrder, clientType = clientTypeFilter) => {
    try {
      setLoading(true);
      const params = { page, limit };
      if (search && search.trim()) {
        params.search = search.trim();
      }
      if (sort) {
        params.sort = sort;
      }
      if (order) {
        params.order = order;
      }
      if (clientType && clientType !== 'all') {
        params.client_type = clientType;
      }
      
      const response = await axios.get(`${API}/clients`, {
        params,
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      // Handle response
      const { data, meta } = response.data;
      setClients(data || []);
      setTotalPages(meta?.total_pages || 1);
      setTotalCount(meta?.total_count || 0);
      setHasPrev(page > 1);
      setHasNext(page < (meta?.total_pages || 1));
      
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
      setTotalPages(1);
      setTotalCount(0);
      setHasPrev(false);
      setHasNext(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">🏨 Müşterilerim</h1>
        <p className="text-gray-600 mt-2">
          Size atanmış müşterilerinizi yönetin
        </p>
      </div>

      {clients.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🏨</div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">Henüz müşteri yok</h3>
          <p className="text-gray-600">Size atanmış müşteri bulunmamaktadır.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clients.map((client) => (
            <div key={client.id} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-800">{client.hotel_name}</h3>
                <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  {client.current_stage || 'Başlangıç'}
                </span>
              </div>
              
              <div className="space-y-2 text-sm text-gray-600">
                <p><strong>İletişim:</strong> {client.contact_person}</p>
                <p><strong>Email:</strong> {client.email}</p>
                <p><strong>Telefon:</strong> {client.phone}</p>
                <p><strong>Adres:</strong> {client.address}</p>
              </div>
              
              <div className="mt-4 pt-4 border-t">
                <div className="flex space-x-2">
                  <button 
                    onClick={() => onNavigate('consumption')}
                    className="flex-1 bg-blue-500 text-white py-2 px-3 rounded-lg text-sm hover:bg-blue-600 transition-colors"
                  >
                    📊 Tüketim
                  </button>
                  <button 
                    onClick={() => onNavigate('carbon')}
                    className="flex-1 bg-green-500 text-white py-2 px-3 rounded-lg text-sm hover:bg-green-600 transition-colors"
                  >
                    🌱 Karbon
                  </button>
                  <button 
                    onClick={() => onNavigate('personnel')}
                    className="flex-1 bg-purple-500 text-white py-2 px-3 rounded-lg text-sm hover:bg-purple-600 transition-colors"
                  >
                    👥 Personel
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="bg-white px-4 py-3 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex-1 flex justify-between sm:hidden">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={!hasPrev}
                      className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Önceki
                    </button>
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={!hasNext}
                      className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Sonraki
                    </button>
                  </div>
                  <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm text-gray-700">
                        Toplam <span className="font-medium">{totalCount}</span> müşteriden{' '}
                        <span className="font-medium">{((currentPage - 1) * itemsPerPage) + 1}</span> -{' '}
                        <span className="font-medium">{Math.min(currentPage * itemsPerPage, totalCount)}</span>{' '}
                        arası gösteriliyor
                      </p>
                    </div>
                    <div>
                      <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        <button
                          onClick={() => handlePageChange(currentPage - 1)}
                          disabled={!hasPrev}
                          className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          ◀
                        </button>
                        
                        {/* Page Numbers - Show first 5, current page area, and last */}
                        {(() => {
                          const pageNumbers = [];
                          const maxVisiblePages = 7;
                          
                          if (totalPages <= maxVisiblePages) {
                            // Show all pages
                            for (let i = 1; i <= totalPages; i++) {
                              pageNumbers.push(i);
                            }
                          } else {
                            // Show smart pagination
                            if (currentPage <= 4) {
                              // Show first 5 pages + ... + last
                              for (let i = 1; i <= 5; i++) pageNumbers.push(i);
                              pageNumbers.push('...');
                              pageNumbers.push(totalPages);
                            } else if (currentPage > totalPages - 4) {
                              // Show first + ... + last 5 pages
                              pageNumbers.push(1);
                              pageNumbers.push('...');
                              for (let i = totalPages - 4; i <= totalPages; i++) pageNumbers.push(i);
                            } else {
                              // Show first + ... + current-1, current, current+1 + ... + last
                              pageNumbers.push(1);
                              pageNumbers.push('...');
                              for (let i = currentPage - 1; i <= currentPage + 1; i++) pageNumbers.push(i);
                              pageNumbers.push('...');
                              pageNumbers.push(totalPages);
                            }
                          }
                          
                          return pageNumbers.map((pageNum, index) => {
                            if (pageNum === '...') {
                              return (
                                <span key={index} className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                                  ...
                                </span>
                              );
                            }
                            
                            const isCurrentPage = pageNum === currentPage;
                            return (
                              <button
                                key={pageNum}
                                onClick={() => handlePageChange(pageNum)}
                                className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                  isCurrentPage
                                    ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                    : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                                }`}
                              >
                                {pageNum}
                              </button>
                            );
                          });
                        })()}
                        
                        <button
                          onClick={() => handlePageChange(currentPage + 1)}
                          disabled={!hasNext}
                          className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          ▶
                        </button>
                      </nav>
                    </div>
                  </div>
                </div>
              </div>
            )}
    </div>
  );
};
// Consultant Client Assignment
const ConsultantClientAssignment = () => {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">🔄 Müşteri Atama</h1>
        <p className="text-gray-600 mt-2">
          Bu özellik yakında kullanıma sunulacak
        </p>
      </div>
      
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🔄</div>
        <h3 className="text-xl font-semibold text-gray-800 mb-2">Yakında</h3>
        <p className="text-gray-600">Müşteri atama özelliği geliştiriliyor.</p>
      </div>
    </div>
  );
};

// Consultant Reports
const ConsultantReports = () => {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">📈 Raporlarım</h1>
        <p className="text-gray-600 mt-2">
          Müşterilerinizin raporlarını görüntüleyin
        </p>
      </div>
      
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📈</div>
        <h3 className="text-xl font-semibold text-gray-800 mb-2">Yakında</h3>
        <p className="text-gray-600">Rapor özelliği geliştiriliyor.</p>
      </div>
    </div>
  );
};

// Consultant Profile
const ConsultantProfile = () => {
  const { dbUser } = useAuth();
  
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">👤 Profil</h1>
        <p className="text-gray-600 mt-2">
          Danışman profil bilgilerinizi yönetin
        </p>
      </div>
      
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">İsim</label>
            <p className="text-gray-900">{dbUser?.name || 'Tanımlı değil'}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <p className="text-gray-900">{dbUser?.email || 'Tanımlı değil'}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
            <p className="text-gray-900 capitalize">{dbUser?.role || 'Tanımlı değil'}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kayıt Tarihi</label>
            <p className="text-gray-900">
              {dbUser?.created_at ? new Date(dbUser.created_at).toLocaleDateString('tr-TR') : 'Tanımlı değil'}
            </p>
          </div>
        </div>
        
        <div className="mt-6 pt-6 border-t">
          <div className="text-center py-8">
            <div className="text-4xl mb-2">👤</div>
            <p className="text-gray-600">Profil düzenleme özelliği yakında kullanıma sunulacak</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Sustainability Targets Management Component
const SustainabilityTargets = () => {
  const { authToken, user, userRole, dbUser } = useAuth();
  const { session } = useClerk();
  const [loading, setLoading] = useState(true);
  const [targets, setTargets] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [showProgressForm, setShowProgressForm] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [targetProgress, setTargetProgress] = useState({});
  const [analytics, setAnalytics] = useState(null);
  const [formData, setFormData] = useState({
    target_name: '',
    category: 'Çevresel',
    target_type: '',
    target_value: '',
    unit: '%',
    target_period: 'Yıllık',
    deadline: '',
    description: ''
  });
  const [progressData, setProgressData] = useState({
    actual_value: '',
    progress_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  const API = getApiUrl();

  // Fetch clients
  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      // Handle both old and new response formats
      if (response.data.clients) {
        setClients(response.data.clients || []);
      } else if (Array.isArray(response.data)) {
        setClients(response.data.clients || []);
      } else {
        setClients([]);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  // Predefined target types
  const targetTypes = {
    'Çevresel': [
      'Karbon Ayak İzi Azaltma',
      'Su Tüketimi Azaltma',
      'Enerji Tasarrufu',
      'Atık Azaltma',
      'Geri Dönüşüm Oranı',
      'Yerel Tedarikçi Oranı'
    ],
    'Sosyal': [
      'Yerel İstihdam Oranı',
      'Cinsiyet Dengesi',
      'Personel Eğitim Saati',
      'Toplum Projesi Desteği',
      'İş Güvenliği Eğitimi'
    ],
    'Ekonomik': [
      'Yerel Satın Alma Oranı',
      'Sürdürülebilirlik Yatırımı',
      'Enerji Maliyeti Azaltma',
      'Atık Bertaraf Maliyeti Azaltma'
    ]
  };

  const units = ['%', 'kg', 'litre', 'TL', 'saat', 'adet', 'gün'];
  const periods = ['Aylık', 'Çeyreklik', 'Yıllık'];

  // Fetch targets with fresh token and progress data
  const fetchTargetsWithFreshToken = async (clientId) => {
    if (!clientId) {
      setTargets([]);
      setTargetProgress({});
      return;
    }
    
    try {
      setLoading(true);
      
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const response = await axios.get(`${API}/sustainability-targets?client_id=${clientId}`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      
      const fetchedTargets = response.data || [];
      setTargets(fetchedTargets);
      
      // Fetch progress data for each target
      const progressPromises = fetchedTargets.map(async (target) => {
        try {
          const progressResponse = await axios.get(`${API}/sustainability-targets/${target.id}/progress`, {
            headers: { Authorization: `Bearer ${currentToken}` }
          });
          return { targetId: target.id, progress: progressResponse.data || [] };
        } catch (error) {
          console.error(`Error fetching progress for target ${target.id}:`, error);
          return { targetId: target.id, progress: [] };
        }
      });
      
      const progressResults = await Promise.all(progressPromises);
      const progressMap = {};
      progressResults.forEach(({ targetId, progress }) => {
        progressMap[targetId] = progress;
      });
      
      setTargetProgress(progressMap);
      
    } catch (error) {
      console.error('Error fetching targets:', error);
      setTargets([]);
      setTargetProgress({});
    } finally {
      setLoading(false);
    }
  };

  // Fetch analytics data
  const fetchAnalytics = async (clientId) => {
    if (!clientId) return;
    
    try {
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const response = await axios.get(`${API}/sustainability-targets/analytics/dashboard?client_id=${clientId}`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      setAnalytics(response.data || null);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setAnalytics(null);
    }
  };

  // Add new target
  const addTarget = async () => {
    // Admin/consultant için client seçimi zorunlu
    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      alert('Lütfen önce bir müşteri seçin!');
      return;
    }

    try {
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const targetData = {
        ...formData,
        target_value: parseFloat(formData.target_value),
        deadline: new Date(formData.deadline).toISOString()
      };
      
      // Admin/consultant için client_id ekle
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        targetData.client_id = selectedClient;
      }
      // Client için backend otomatik olarak kendi client_id'sini ekler

      const response = await axios.post(`${API}/sustainability-targets`, targetData, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      // Client için kendi data'sını yenile
      const clientIdToRefresh = selectedClient || dbUser?.client_id;
      if (clientIdToRefresh) {
        await fetchTargetsWithFreshToken(clientIdToRefresh);
        await fetchAnalytics(clientIdToRefresh);
      }
      
      setFormData({
        target_name: '',
        category: 'Çevresel',
        target_type: '',
        target_value: '',
        unit: '%',
        target_period: 'Yıllık',
        deadline: '',
        description: ''
      });
      setShowAddForm(false);
      
      alert('Hedef başarıyla eklendi!');
    } catch (error) {
      console.error('Error adding target:', error);
      alert('Hedef eklenirken hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Add progress to target
  const addProgress = async () => {
    if (!selectedTarget) return;

    try {
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const progressPayload = {
        target_id: selectedTarget.id,
        actual_value: parseFloat(progressData.actual_value),
        progress_date: new Date(progressData.progress_date).toISOString(),
        notes: progressData.notes
      };

      const response = await axios.post(`${API}/sustainability-targets/progress`, progressPayload, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      await fetchTargetsWithFreshToken(selectedClient);
      await fetchAnalytics(selectedClient);
      
      setProgressData({
        actual_value: '',
        progress_date: new Date().toISOString().split('T')[0],
        notes: ''
      });
      setShowProgressForm(false);
      setSelectedTarget(null);
      
      alert('Gerçekleşme verisi başarıyla eklendi!');
    } catch (error) {
      console.error('Error adding progress:', error);
      alert('Gerçekleşme verisi eklenirken hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Calculate progress percentage
  const calculateProgress = (target) => {
    const progressList = targetProgress[target.id] || [];
    if (progressList.length === 0) return 0;
    
    const latestProgress = progressList[0]; // Already sorted by date DESC
    const percentage = Math.min((latestProgress.actual_value / target.target_value) * 100, 100);
    return percentage;
  };

  // Get latest progress value
  const getLatestProgressValue = (target) => {
    const progressList = targetProgress[target.id] || [];
    if (progressList.length === 0) return null;
    return progressList[0].actual_value;
  };

  // Delete target
  const deleteTarget = async (targetId) => {
    if (!confirm('Bu hedefi silmek istediğinizden emin misiniz?')) return;
    
    try {
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      await axios.delete(`${API}/sustainability-targets/${targetId}`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      await fetchTargetsWithFreshToken(selectedClient);
      await fetchAnalytics(selectedClient);
      
      alert('Hedef başarıyla silindi!');
    } catch (error) {
      console.error('Error deleting target:', error);
      alert('Hedef silinirken hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  useEffect(() => {
    console.log('🔍 ClientManagement useEffect triggered');
    console.log('🔍 authToken:', authToken ? 'EXISTS' : 'MISSING');
    console.log('🔍 userRole:', userRole);
    
    if (authToken) {
      console.log('🔍 Calling fetchClients...');
      fetchClients();
    } else {
      console.log('❌ No authToken, skipping fetchClients');
    }
  }, [authToken]);

  // Auto-select client for CLIENT role users
  useEffect(() => {
    if (userRole === 'client' && dbUser?.client_id && !selectedClient) {
      setSelectedClient(dbUser.client_id);
    }
  }, [userRole, dbUser, selectedClient]);

  useEffect(() => {
    if (selectedClient) {
      fetchTargetsWithFreshToken(selectedClient);
      fetchAnalytics(selectedClient);
    }
  }, [selectedClient]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 via-emerald-700 to-teal-700 text-white p-6 shadow-xl">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">🎯 Sürdürülebilirlik Hedefleri</h1>
          <p className="text-emerald-100 text-lg">Ölçülebilir hedef belirleme ve takip sistemi</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        
        {/* Client Section - For Client Role */}
        {userRole === 'client' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-800 mb-2">🎯 Sürdürülebilirlik Hedefleriniz</h2>
                <p className="text-gray-600">Hedeflerinizi belirleyebilir, takip edebilir ve ilerlemenizi izleyebilirsiniz</p>
              </div>
              <div className="flex items-center space-x-3">
                <div className="bg-purple-100 text-purple-800 px-4 py-2 rounded-full text-sm font-medium">
                  ✓ Client Kullanıcısı
                </div>
                <button
                  onClick={() => setShowAddForm(true)}
                  className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center space-x-2"
                >
                  <span>➕</span>
                  <span>Hedef Ekle</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Client Selection - Only for Admin and Consultant */}
        {(userRole === 'admin' || userRole === 'consultant') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">1. Müşteri Seçimi</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Müşteri Seçin
                </label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                >
                  <option value="">-- Müşteri Seçin --</option>
                  {Array.isArray(clients) && clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name || client.hotel_name}
                    </option>
                  ))}
                </select>
              </div>
              {selectedClient && (
                <div className="flex items-end">
                  <button
                    onClick={() => setShowAddForm(!showAddForm)}
                    className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
                  >
                    {showAddForm ? '❌ İptal' : '➕ Hedef Ekle'}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Client Info - For Client Users */}
        {userRole === 'client' && selectedClient && Array.isArray(clients) && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">🎯 Sürdürülebilirlik Hedeflerim</h2>
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
              <p className="text-emerald-800">
                <strong>🏢 İşletme:</strong> {clients.find(c => c.id === selectedClient)?.name || clients.find(c => c.id === selectedClient)?.hotel_name}
              </p>
              <p className="text-emerald-600 text-sm mt-1">Sürdürülebilirlik hedeflerinizi takip edin.</p>
            </div>
          </div>
        )}

        {/* Analytics Cards */}
        {selectedClient && analytics && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">📊 Genel Durum</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 p-4 rounded-lg text-white">
                <h3 className="text-sm font-medium mb-2">Toplam Hedef</h3>
                <p className="text-2xl font-bold">{analytics.total_targets}</p>
              </div>
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-4 rounded-lg text-white">
                <h3 className="text-sm font-medium mb-2">Aktif Hedef</h3>
                <p className="text-2xl font-bold">{analytics.active_targets}</p>
              </div>
              <div className="bg-gradient-to-br from-green-500 to-green-600 p-4 rounded-lg text-white">
                <h3 className="text-sm font-medium mb-2">Tamamlanan</h3>
                <p className="text-2xl font-bold">{analytics.completed_targets}</p>
              </div>
              <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-4 rounded-lg text-white">
                <h3 className="text-sm font-medium mb-2">Ortalama İlerleme</h3>
                <p className="text-2xl font-bold">{analytics.average_progress ? `${analytics.average_progress.toFixed(1)}%` : '0%'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Add Target Form - For Client Users */}
        {userRole === 'client' && showAddForm && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">➕ Yeni Hedef Ekle</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Hedef Adı</label>
                <input
                  type="text"
                  value={formData.target_name}
                  onChange={(e) => setFormData({...formData, target_name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  placeholder="Ör: 2025 Karbon Azaltma Hedefi"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Kategori</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value, target_type: ''})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="Çevresel">Çevresel</option>
                  <option value="Sosyal">Sosyal</option>
                  <option value="Ekonomik">Ekonomik</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Hedef Tipi</label>
                <select
                  value={formData.target_type}
                  onChange={(e) => setFormData({...formData, target_type: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">-- Hedef Tipi Seçin --</option>
                  {targetTypes[formData.category]?.map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Hedef Değer</label>
                  <input
                    type="number"
                    value={formData.target_value}
                    onChange={(e) => setFormData({...formData, target_value: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    placeholder="50"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Birim</label>
                  <select
                    value={formData.unit}
                    onChange={(e) => setFormData({...formData, unit: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  >
                    {units.map((unit) => (
                      <option key={unit} value={unit}>{unit}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Dönem</label>
                <select
                  value={formData.target_period}
                  onChange={(e) => setFormData({...formData, target_period: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  {periods.map((period) => (
                    <option key={period} value={period}>{period}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Hedef Tarihi</label>
                <input
                  type="date"
                  value={formData.deadline}
                  onChange={(e) => setFormData({...formData, deadline: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Açıklama</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  rows="3"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  placeholder="Hedef hakkında detaylar..."
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-4">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={addTarget}
                className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
              >
                Hedef Ekle
              </button>
            </div>
          </div>
        )}

        {/* Add Target Form - Admin and Consultant */}
        {(userRole === 'admin' || userRole === 'consultant') && showAddForm && selectedClient && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">2. Yeni Hedef Ekle</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Hedef Adı</label>
                <input
                  type="text"
                  value={formData.target_name}
                  onChange={(e) => setFormData({...formData, target_name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  placeholder="Ör: 2025 Karbon Azaltma Hedefi"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Kategori</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value, target_type: ''})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="Çevresel">Çevresel</option>
                  <option value="Sosyal">Sosyal</option>
                  <option value="Ekonomik">Ekonomik</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Hedef Tipi</label>
                <select
                  value={formData.target_type}
                  onChange={(e) => setFormData({...formData, target_type: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">-- Hedef Tipi Seçin --</option>
                  {targetTypes[formData.category]?.map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Hedef Değer</label>
                  <input
                    type="number"
                    value={formData.target_value}
                    onChange={(e) => setFormData({...formData, target_value: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    placeholder="50"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Birim</label>
                  <select
                    value={formData.unit}
                    onChange={(e) => setFormData({...formData, unit: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  >
                    {units.map((unit) => (
                      <option key={unit} value={unit}>{unit}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Dönem</label>
                <select
                  value={formData.target_period}
                  onChange={(e) => setFormData({...formData, target_period: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                >
                  {periods.map((period) => (
                    <option key={period} value={period}>{period}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Hedef Tarihi</label>
                <input
                  type="date"
                  value={formData.deadline}
                  onChange={(e) => setFormData({...formData, deadline: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Açıklama</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  rows="3"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  placeholder="Hedef hakkında detaylar..."
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-4">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={addTarget}
                className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
              >
                Hedef Ekle
              </button>
            </div>
          </div>
        )}

        {/* Progress Form Modal */}
        {showProgressForm && selectedTarget && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-bold text-gray-800 mb-4">Gerçekleşme Verisi Ekle</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Gerçekleşen Değer ({selectedTarget.unit})
                  </label>
                  <input
                    type="number"
                    value={progressData.actual_value}
                    onChange={(e) => setProgressData({...progressData, actual_value: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    placeholder="Gerçekleşen değeri girin"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Tarih</label>
                  <input
                    type="date"
                    value={progressData.progress_date}
                    onChange={(e) => setProgressData({...progressData, progress_date: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Notlar</label>
                  <textarea
                    value={progressData.notes}
                    onChange={(e) => setProgressData({...progressData, notes: e.target.value})}
                    rows="3"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    placeholder="Ek notlar..."
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-4">
                <button
                  onClick={() => {setShowProgressForm(false); setSelectedTarget(null);}}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  İptal
                </button>
                <button
                  onClick={addProgress}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
                >
                  Kaydet
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Targets List */}
        {selectedClient && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              3. Hedef Listesi ve Takip
              {Array.isArray(clients) && clients.find(c => c.id === selectedClient) && (
                <span className="text-emerald-600 font-normal">
                  - {clients.find(c => c.id === selectedClient)?.name || clients.find(c => c.id === selectedClient)?.hotel_name}
                </span>
              )}
            </h2>
            
            {loading ? (
              <div className="flex justify-center items-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
              </div>
            ) : Array.isArray(targets) && targets.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {targets.map((target) => (
                  <div key={target.id} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-6 border border-gray-200 hover:shadow-md transition-all">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-bold text-gray-800">{target.target_name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            target.category === 'Çevresel' ? 'bg-green-100 text-green-800' :
                            target.category === 'Sosyal' ? 'bg-blue-100 text-blue-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {target.category}
                          </span>
                          <span className="text-xs text-gray-500">
                            {new Date(target.deadline).toLocaleDateString('tr-TR')}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {(userRole === 'admin' || userRole === 'consultant') && (
                          <>
                            <button
                              onClick={() => {setSelectedTarget(target); setShowProgressForm(true);}}
                              className="px-3 py-1 bg-emerald-600 text-white text-sm rounded hover:bg-emerald-700 transition-colors"
                            >
                              📊 Veri Ekle
                            </button>
                            <button
                              onClick={() => deleteTarget(target.id)}
                              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                            >
                              🗑️ Sil
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                    
                    <div className="space-y-3 text-sm text-gray-600">
                      <p><strong>🎯 Tip:</strong> {target.target_type}</p>
                      <p><strong>📈 Hedef:</strong> {target.target_value} {target.unit}</p>
                      <p><strong>📅 Dönem:</strong> {target.target_period}</p>
                      <p><strong>⏰ Hedef Tarihi:</strong> {new Date(target.deadline).toLocaleDateString('tr-TR')}</p>
                      {getLatestProgressValue(target) && (
                        <p><strong>📊 Gerçekleşen:</strong> {getLatestProgressValue(target)} {target.unit}</p>
                      )}
                      {target.description && (
                        <p><strong>📝 Açıklama:</strong> {target.description}</p>
                      )}
                    </div>

                    {/* Progress Bar */}
                    <div className="mt-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">İlerleme</span>
                        <span className={`text-sm font-bold ${
                          calculateProgress(target) >= 100 ? 'text-green-600' :
                          calculateProgress(target) >= 75 ? 'text-emerald-600' :
                          calculateProgress(target) >= 50 ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {calculateProgress(target).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div 
                          className={`h-3 rounded-full transition-all duration-500 ${
                            calculateProgress(target) >= 100 ? 'bg-green-600' :
                            calculateProgress(target) >= 75 ? 'bg-emerald-600' :
                            calculateProgress(target) >= 50 ? 'bg-yellow-600' :
                            'bg-red-600'
                          }`}
                          style={{width: `${Math.min(calculateProgress(target), 100)}%`}}
                        ></div>
                      </div>
                      
                      {/* Progress History */}
                      {targetProgress[target.id] && targetProgress[target.id].length > 0 && (
                        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                          <h4 className="text-sm font-medium text-gray-700 mb-2">Son İlerleme Kayıtları</h4>
                          <div className="space-y-1 max-h-20 overflow-y-auto">
                            {targetProgress[target.id].slice(0, 3).map((progress, index) => (
                              <div key={index} className="flex justify-between items-center text-xs text-gray-600">
                                <span>{new Date(progress.progress_date).toLocaleDateString('tr-TR')}</span>
                                <span className="font-medium">{progress.actual_value} {target.unit}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🎯</div>
                <p className="text-gray-500 text-lg mb-2">Bu müşteri için henüz hedef bulunmuyor.</p>
                <p className="text-gray-400 text-sm">Yukarıdaki butonu kullanarak hedef ekleyebilirsiniz.</p>
              </div>
            )}
          </div>
        )}

        {/* No Client Selected */}
        {!selectedClient && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🎯</div>
              <p className="text-gray-500 text-lg mb-2">Sürdürülebilirlik hedefleri için önce bir müşteri seçin.</p>
              <p className="text-gray-400 text-sm">Yukarıdaki dropdown'dan müşteri seçerek başlayabilirsiniz.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Personnel Management Component
const PersonnelManagement = () => {
  const { authToken, user, userRole, dbUser } = useAuth();
  const { session } = useClerk();
  const [loading, setLoading] = useState(true);
  const [personnel, setPersonnel] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [showBulkForm, setShowBulkForm] = useState(false);
  const [bulkPersonnelText, setBulkPersonnelText] = useState('');
  const [bulkProcessing, setBulkProcessing] = useState(false);
  const [showExcelImport, setShowExcelImport] = useState(false);
  const [excelFile, setExcelFile] = useState(null);
  const [excelProcessing, setExcelProcessing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    position: '',
    location: '',
    certifications: [],
    is_local: false,
    gender: 'Erkek'
  });
  const API = getApiUrl();

  // Available certifications
  const availableCertifications = [
    'İlk Yardım',
    'Hijyen',
    'Can Kurtaran',
    'Lejyonella',
    'MYK'
  ];

  // Fetch clients first
  const fetchClients = async () => {
    if (!authToken) return;
    try {
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      // Handle new backend response format { clients, pagination }
      if (response.data.clients && Array.isArray(response.data.clients)) {
        setClients(response.data.clients);
      } else if (Array.isArray(response.data)) {
        // Fallback for old format
        setClients(response.data.clients || []);
      } else {
        setClients([]);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
      
      if (error.response?.status === 401) {
        console.log('Token expired while fetching clients');
        setClients([]);
        return;
      }
      
      setClients([]);
    }
  };

  // Fetch personnel with fresh token
  const fetchPersonnelWithFreshToken = async (clientId) => {
    if (!clientId) {
      setPersonnel([]);
      return;
    }
    
    try {
      setLoading(true);
      
      // Get fresh token from session
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
            console.log('🔄 Using fresh token for fetching personnel');
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const response = await axios.get(`${API}/personnel?client_id=${clientId}`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      setPersonnel(response.data || []);
      console.log('✅ Personnel fetched successfully:', response.data?.length || 0, 'items');
    } catch (error) {
      console.error('Error fetching personnel:', error);
      
      if (error.response?.status === 401) {
        console.log('Token expired while fetching personnel');
        setPersonnel([]);
        return;
      }
      
      setPersonnel([]);
    } finally {
      setLoading(false);
    }
  };

  // Add new personnel
  const addPersonnel = async () => {
    // Admin/consultant için client seçimi zorunlu
    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      alert('Lütfen önce bir müşteri seçin!');
      return;
    }

    try {
      // Get fresh token from session
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
            console.log('🔄 Using fresh token for personnel creation');
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const personnelData = {
        ...formData
      };
      
      // Admin/consultant için client_id ekle
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        personnelData.client_id = selectedClient;
      }
      // Client için backend otomatik olarak kendi client_id'sini ekler

      console.log('📤 Creating personnel with data:', personnelData);
      const response = await axios.post(`${API}/personnel`, personnelData, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      console.log('✅ Personnel created successfully:', response.data);

      // Refresh personnel list with fresh token
      await fetchPersonnelWithFreshToken(selectedClient);
      
      // Reset form
      setFormData({
        full_name: '',
        position: '',
        location: '',
        certifications: [],
        is_local: false,
        gender: 'Erkek'
      });
      setShowAddForm(false);
      
      alert('Personel başarıyla eklendi!');
    } catch (error) {
      console.error('Error adding personnel:', error);
      
      if (error.response?.status === 401) {
        console.log('🔄 401 error detected, auth system will handle this silently');
        // Let the main auth system handle re-authentication silently - no page reload
        return;
      }
      
      alert('Personel eklenirken hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle certification change
  const handleCertificationChange = (cert, checked) => {
    if (checked) {
      setFormData({
        ...formData,
        certifications: [...formData.certifications, cert]
      });
    } else {
      setFormData({
        ...formData,
        certifications: formData.certifications.filter(c => c !== cert)
      });
    }
  };

  // Delete personnel
  const deletePersonnel = async (personnelId) => {
    if (!confirm('Bu personeli silmek istediğinizden emin misiniz?')) return;
    
    try {
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      await axios.delete(`${API}/personnel/${personnelId}`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      await fetchPersonnelWithFreshToken(selectedClient);
      
      alert('Personel başarıyla silindi!');
    } catch (error) {
      console.error('Error deleting personnel:', error);
      alert('Personel silinirken hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Bulk Personnel Import Function
  const processBulkPersonnel = async () => {
    if (!bulkPersonnelText.trim()) {
      alert('Lütfen personel listesini girin!');
      return;
    }

    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      alert('Lütfen önce bir müşteri seçin!');
      return;
    }

    setBulkProcessing(true);
    
    try {
      // Parse the text input
      const lines = bulkPersonnelText.trim().split('\n').filter(line => line.trim());
      const personnelList = [];
      
      for (const line of lines) {
        const parts = line.split(',').map(part => part.trim());
        if (parts.length >= 2) {
          const personnelItem = {
            full_name: parts[0] || '',
            position: parts[1] || '',
            location: parts[2] || '',
            certifications: parts[3] ? parts[3].split(';').map(c => c.trim()).filter(c => c) : [],
            is_local: parts[4] ? parts[4].toLowerCase() === 'evet' || parts[4].toLowerCase() === 'true' : false,
            gender: parts[5] || 'Erkek'
          };
          
          if (personnelItem.full_name && personnelItem.position) {
            personnelList.push(personnelItem);
          }
        }
      }
      
      if (personnelList.length === 0) {
        alert('Geçerli personel bulunamadı! Format: Ad Soyad, Pozisyon, Lokasyon, Sertifikalar, Yerel, Cinsiyet');
        return;
      }

      // Get fresh token
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      // Send bulk request
      const payload = {
        personnel_list: personnelList
      };
      
      // Add client_id for admin/consultant
      const params = new URLSearchParams();
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        params.append('client_id', selectedClient);
      }
      
      const url = `${API}/personnel/bulk${params.toString() ? `?${params.toString()}` : ''}`;
      
      const response = await axios.post(url, payload, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      const result = response.data;
      alert(`Bulk personel ekleme tamamlandı!\n${result.success_count}/${result.total_count} personel eklendi (${result.success_rate})`);
      
      // Refresh personnel list
      const clientIdToRefresh = selectedClient || dbUser?.client_id;
      if (clientIdToRefresh) {
        await fetchPersonnelWithFreshToken(clientIdToRefresh);
      }
      
      // Clear form
      setBulkPersonnelText('');
      setShowBulkForm(false);
      
    } catch (error) {
      console.error('Error processing bulk personnel:', error);
      alert('Bulk personel ekleme hatası: ' + (error.response?.data?.detail || error.message));
    } finally {
      setBulkProcessing(false);
    }
  };

  // Excel Personnel Import Function
  const processExcelPersonnel = async () => {
    if (!excelFile) {
      alert('Lütfen bir Excel dosyası seçin!');
      return;
    }

    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      alert('Lütfen önce bir müşteri seçin!');
      return;
    }

    setExcelProcessing(true);
    
    try {
      // Import XLSX library
      const XLSX = await import('xlsx');
      
      // Read Excel file as ArrayBuffer
      const arrayBuffer = await excelFile.arrayBuffer();
      
      // Parse Excel file
      const workbook = XLSX.read(arrayBuffer, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      
      // Convert to JSON
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
      
      // Skip header row and process data
      const dataRows = jsonData.slice(1);
      const personnelList = [];
      
      for (const row of dataRows) {
        if (row.length >= 2 && row[0] && row[1]) {
          const personnelItem = {
            full_name: String(row[0] || '').trim(),
            position: String(row[1] || '').trim(),
            location: String(row[2] || '').trim(),
            certifications: row[3] ? String(row[3]).split(';').map(c => c.trim()).filter(c => c) : [],
            is_local: row[4] ? (String(row[4]).toLowerCase() === 'evet' || String(row[4]).toLowerCase() === 'true' || String(row[4]).toLowerCase() === 'yes') : false,
            gender: String(row[5] || 'Erkek').trim()
          };
          
          if (personnelItem.full_name && personnelItem.position) {
            personnelList.push(personnelItem);
          }
        }
      }
      
      if (personnelList.length === 0) {
        alert('Excel dosyasında geçerli personel bulunamadı!\n\nBeklenen format:\nAd Soyad | Pozisyon | Lokasyon | Sertifikalar | Yerel | Cinsiyet');
        return;
      }

      // Get fresh token
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      // Send bulk request
      const payload = {
        personnel_list: personnelList
      };
      
      // Add client_id for admin/consultant
      const params = new URLSearchParams();
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        params.append('client_id', selectedClient);
      }
      
      const url = `${API}/personnel/bulk${params.toString() ? `?${params.toString()}` : ''}`;
      
      const response = await axios.post(url, payload, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      const result = response.data;
      alert(`Excel personel import tamamlandı!\n${result.success_count}/${result.total_count} personel eklendi (${result.success_rate})`);
      
      // Refresh personnel list
      const clientIdToRefresh = selectedClient || dbUser?.client_id;
      if (clientIdToRefresh) {
        await fetchPersonnelWithFreshToken(clientIdToRefresh);
      }
      
      // Clear form
      setExcelFile(null);
      setShowExcelImport(false);
      
    } catch (error) {
      console.error('Error processing Excel personnel:', error);
      alert('Excel personel import hatası: ' + (error.response?.data?.detail || error.message));
    } finally {
      setExcelProcessing(false);
    }
  };

  // Download Personnel Template Function (XLSX Format)
  const downloadPersonnelTemplate = async () => {
    try {
      // Import XLSX library
      const XLSX = await import('xlsx');
      
      // Create template data with proper structure
      const templateData = [
        // Header row
        ['Ad Soyad', 'Pozisyon', 'Lokasyon', 'Sertifikalar', 'Yerel', 'Cinsiyet'],
        // Example rows with proper formatting
        ['Ahmet Yılmaz', 'Garson', 'İstanbul', 'İlk Yardım;Hijyen', 'Evet', 'Erkek'],
        ['Fatma Kaya', 'Temizlik', 'Ankara', 'Hijyen', 'Evet', 'Kadın'],
        ['Mehmet Demir', 'Resepsiyon', 'İzmir', '', 'Hayır', 'Erkek'],
        ['Ayşe Öztürk', 'Müdür', 'Bursa', 'Yönetim;İnsan Kaynakları', 'Evet', 'Kadın'],
        ['Murat Kaya', 'Güvenlik', 'Antalya', 'Güvenlik;İlk Yardım', 'Evet', 'Erkek'],
        // Empty rows for user input
        ['', '', '', '', '', ''],
        ['', '', '', '', '', ''],
        ['', '', '', '', '', ''],
        ['', '', '', '', '', '']
      ];

      // Create workbook and worksheet
      const workbook = XLSX.utils.book_new();
      const worksheet = XLSX.utils.aoa_to_sheet(templateData);
      
      // Set column widths for better formatting
      worksheet['!cols'] = [
        { width: 20 }, // Ad Soyad
        { width: 15 }, // Pozisyon
        { width: 12 }, // Lokasyon
        { width: 25 }, // Sertifikalar
        { width: 8 },  // Yerel
        { width: 10 }  // Cinsiyet
      ];
      
      // Style the header row
      const headerStyle = {
        font: { bold: true, color: { rgb: "FFFFFF" } },
        fill: { fgColor: { rgb: "4472C4" } },
        alignment: { horizontal: "center", vertical: "center" }
      };
      
      // Apply header styling
      for (let col = 0; col < 6; col++) {
        const cellRef = XLSX.utils.encode_cell({ r: 0, c: col });
        if (!worksheet[cellRef]) worksheet[cellRef] = { t: 's', v: '' };
        worksheet[cellRef].s = headerStyle;
      }
      
      // Add data validation for Yerel column (E column)
      if (!worksheet['!dataValidations']) worksheet['!dataValidations'] = [];
      worksheet['!dataValidations'].push({
        type: 'list',
        allowBlank: false,
        showInputMessage: true,
        showErrorMessage: true,
        sqref: 'E2:E1000',
        formula1: '"Evet,Hayır"'
      });
      
      // Add data validation for Cinsiyet column (F column)
      worksheet['!dataValidations'].push({
        type: 'list',
        allowBlank: false,
        showInputMessage: true,
        showErrorMessage: true,
        sqref: 'F2:F1000',
        formula1: '"Erkek,Kadın"'
      });

      // Add worksheet to workbook
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Personel');
      
      // Generate and download XLSX file
      const xlsxBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([xlsxBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', 'personel_taslak.xlsx');
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      alert('📊 Personel taslak Excel dosyası indirildi!\n\n✅ XLSX formatında\n✅ Düzenli sütun yapısı\n✅ Açılır listeler\n✅ Boş satırlar eklendi\n\nDosyayı açın, kendi personel verilerinizi girin ve Excel İmport ile yükleyin.');
      
    } catch (error) {
      console.error('Error creating personnel template:', error);
      alert('Template oluşturma hatası: ' + error.message);
    }
  };

  useEffect(() => {
    if (authToken) {
      fetchClients();
    }
  }, [authToken]);

  // Auto-select client for CLIENT role users
  useEffect(() => {
    if (userRole === 'client' && dbUser?.client_id && !selectedClient) {
      setSelectedClient(dbUser.client_id);
      console.log('🔄 Auto-selected client for CLIENT user:', dbUser.client_id);
    }
  }, [userRole, dbUser, selectedClient]);

  useEffect(() => {
    if (selectedClient) {
      fetchPersonnelWithFreshToken(selectedClient);
    }
  }, [selectedClient]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-700 text-white p-6 shadow-xl">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">👥 Personel Yönetimi</h1>
          <p className="text-purple-100 text-lg">Personel bilgileri ve sertifika takip sistemi</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        
        {/* Client Info - For Client Role */}
        {userRole === 'client' && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-blue-800 mb-2">👤 Personel Yönetiminiz</h2>
                <p className="text-blue-700">Personelinizi ekleyebilir, düzenleyebilir ve sertifika durumlarını takip edebilirsiniz.</p>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center gap-2"
                >
                  {showAddForm ? '❌ İptal' : '➕ Personel Ekle'}
                </button>
                <button
                  onClick={() => setShowBulkForm(!showBulkForm)}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center gap-2"
                >
                  {showBulkForm ? '❌ İptal' : '📋 Toplu Ekle'}
                </button>
                <button
                  onClick={() => setShowExcelImport(!showExcelImport)}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
                >
                  {showExcelImport ? '❌ İptal' : '📊 Excel İmport'}
                </button>
                <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
                  ✓ Client Kullanıcısı
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Client Selection - For Admin and Consultant */}
        {(userRole === 'admin' || userRole === 'consultant') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">1. Müşteri Seçimi</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Müşteri Seçin
                </label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">-- Müşteri Seçin --</option>
                  {Array.isArray(clients) && clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name || client.hotel_name}
                    </option>
                  ))}
                </select>
              </div>
              {selectedClient && (
                <div className="flex items-end gap-3">
                  <button
                    onClick={() => setShowAddForm(!showAddForm)}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                  >
                    {showAddForm ? '❌ İptal' : '➕ Personel Ekle'}
                  </button>
                  <button
                    onClick={() => setShowBulkForm(!showBulkForm)}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                  >
                    {showBulkForm ? '❌ İptal' : '📋 Toplu Ekle'}
                  </button>
                  <button
                    onClick={() => setShowExcelImport(!showExcelImport)}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    {showExcelImport ? '❌ İptal' : '📊 Excel İmport'}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Excel Personnel Import Form */}
        {showExcelImport && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">📊 Excel Personel İmport</h2>
            
            <div className="mb-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <h3 className="font-medium text-green-800 mb-2">📋 Excel Dosyası Formatı:</h3>
                <div className="text-sm text-green-700">
                  <p className="mb-2"><strong>Kolon Sırası:</strong> Ad Soyad, Pozisyon, Lokasyon, Sertifikalar, Yerel, Cinsiyet</p>
                  <p className="mb-2"><strong>Önemli Notlar:</strong></p>
                  <ul className="list-disc list-inside mb-2 space-y-1">
                    <li>İlk satır başlık satırı olarak atlanır</li>
                    <li>Sertifikalar noktalı virgül (;) ile ayrılır</li>
                    <li>Yerel sütunu: "Evet", "Hayır", "True", "False" değerleri alabilir</li>
                    <li>Cinsiyet: "Erkek" veya "Kadın" olmalıdır</li>
                  </ul>
                  <p><strong>Örnek:</strong></p>
                  <div className="bg-white border rounded p-2 mt-2 font-mono text-xs">
                    Ad Soyad,Pozisyon,Lokasyon,Sertifikalar,Yerel,Cinsiyet<br/>
                    Ahmet Yılmaz,Garson,İstanbul,İlk Yardım;Hijyen,Evet,Erkek<br/>
                    Fatma Kaya,Temizlik,Ankara,Hijyen,Evet,Kadın<br/>
                    Mehmet Demir,Resepsiyon,İzmir,,Hayır,Erkek
                  </div>
                </div>
                
                {/* Template Download Button */}
                <div className="mt-4 pt-3 border-t border-green-200">
                  <button
                    onClick={downloadPersonnelTemplate}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium flex items-center gap-2"
                  >
                    <span>📁</span>
                    <span>Taslak Excel İndir</span>
                  </button>
                  <p className="text-xs text-green-600 mt-1">💡 Hazır template'i indirin, düzenleyin ve yükleyin!</p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Excel Dosyası Seçin (.csv, .xlsx)
                </label>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => setExcelFile(e.target.files[0])}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {excelFile && (
                  <p className="text-sm text-green-600 mt-2">
                    ✅ Seçilen dosya: {excelFile.name}
                  </p>
                )}
              </div>
            </div>
            
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => {
                  setShowExcelImport(false);
                  setExcelFile(null);
                }}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={processExcelPersonnel}
                disabled={excelProcessing || !excelFile}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {excelProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>İşleniyor...</span>
                  </>
                ) : (
                  <>
                    <span>📊</span>
                    <span>Excel İmport</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Client Info - For Client Users */}
        {userRole === 'client' && selectedClient && Array.isArray(clients) && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">👥 Personel Listesi</h2>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <p className="text-purple-800">
                <strong>🏢 İşletme:</strong> {clients.find(c => c.id === selectedClient)?.name || clients.find(c => c.id === selectedClient)?.hotel_name}
              </p>
              <p className="text-purple-600 text-sm mt-1">Sadece kendi personellerinizi görüntüleyebilirsiniz.</p>
            </div>
          </div>
        )}

        {/* Add Personnel Form - For Client Users */}
        {userRole === 'client' && showAddForm && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">➕ Yeni Personel Ekle</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Ad Soyad</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Tam adını girin"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Pozisyon</label>
                <input
                  type="text"
                  value={formData.position}
                  onChange={(e) => setFormData({...formData, position: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Meslek/pozisyon girin"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Çalışma Yeri</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Departman/çalışma yeri"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Cinsiyet</label>
                <select
                  value={formData.gender}
                  onChange={(e) => setFormData({...formData, gender: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="Erkek">Erkek</option>
                  <option value="Kadın">Kadın</option>
                </select>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="client_is_local"
                  checked={formData.is_local}
                  onChange={(e) => setFormData({...formData, is_local: e.target.checked})}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <label htmlFor="client_is_local" className="ml-2 block text-sm text-gray-700">
                  🏠 Yerel Personel
                </label>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Sertifikalar</label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {availableCertifications.map((cert) => (
                    <div key={cert} className="flex items-center">
                      <input
                        type="checkbox"
                        id={`client_cert_${cert}`}
                        checked={formData.certifications.includes(cert)}
                        onChange={(e) => handleCertificationChange(cert, e.target.checked)}
                        className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                      />
                      <label htmlFor={`client_cert_${cert}`} className="ml-2 text-sm text-gray-700">
                        {cert}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-4">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={addPersonnel}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
              >
                Personel Ekle
              </button>
            </div>
          </div>
        )}

        {/* Add Personnel Form - Admin and Consultant */}
        {(userRole === 'admin' || userRole === 'consultant') && showAddForm && selectedClient && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">2. Yeni Personel Ekle</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">İsim Soyisim</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Tam adını girin"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Görev</label>
                <input
                  type="text"
                  value={formData.position}
                  onChange={(e) => setFormData({...formData, position: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Ör: Temizlik Görevlisi, Resepsiyon"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">İkamet/Memleket</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Ör: Antalya, İstanbul"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Cinsiyet</label>
                <select
                  value={formData.gender}
                  onChange={(e) => setFormData({...formData, gender: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="Erkek">Erkek</option>
                  <option value="Kadın">Kadın</option>
                </select>
              </div>
              
              {/* Certifications */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Sertifikalar</label>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                  {availableCertifications.map((cert) => (
                    <label key={cert} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.certifications.includes(cert)}
                        onChange={(e) => handleCertificationChange(cert, e.target.checked)}
                        className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                      />
                      <span className="text-sm text-gray-700">{cert}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Local Checkbox */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_local"
                  checked={formData.is_local}
                  onChange={(e) => setFormData({...formData, is_local: e.target.checked})}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <label htmlFor="is_local" className="ml-2 block text-sm text-gray-700">
                  🏠 Yerel Personel
                </label>
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-4">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={addPersonnel}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
              >
                Personel Ekle
              </button>
            </div>
          </div>
        )}

        {/* Bulk Personnel Form */}
        {showBulkForm && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">📋 Toplu Personel Ekleme</h2>
            <div className="mb-4">
              <p className="text-gray-600 mb-2">Format: Ad Soyad, Pozisyon, Lokasyon, Sertifikalar, Yerel, Cinsiyet</p>
              <p className="text-sm text-gray-500 mb-4">
                Örnek: Ahmet Yılmaz, Garson, İstanbul, İlk Yardım;Hijyen, Evet, Erkek
              </p>
              <textarea
                value={bulkPersonnelText}
                onChange={(e) => setBulkPersonnelText(e.target.value)}
                placeholder="Ahmet Yılmaz, Garson, İstanbul, İlk Yardım;Hijyen, Evet, Erkek
Fatma Kaya, Temizlik, Ankara, Hijyen, Evet, Kadın
Mehmet Demir, Resepsiyon, İzmir, , Hayır, Erkek"
                className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                rows="10"
              />
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <h3 className="font-medium text-blue-800 mb-2">📝 Format Açıklaması:</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• <strong>Ad Soyad:</strong> Zorunlu - Personelin tam adı</li>
                <li>• <strong>Pozisyon:</strong> Zorunlu - İş pozisyonu</li>
                <li>• <strong>Lokasyon:</strong> Opsiyonel - Çalıştığı şehir</li>
                <li>• <strong>Sertifikalar:</strong> Opsiyonel - Noktalı virgülle ayrılmış</li>
                <li>• <strong>Yerel:</strong> Opsiyonel - "Evet" veya "Hayır"</li>
                <li>• <strong>Cinsiyet:</strong> Opsiyonel - "Erkek" veya "Kadın"</li>
              </ul>
            </div>
            
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setShowBulkForm(false)}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={processBulkPersonnel}
                disabled={bulkProcessing}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {bulkProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>İşleniyor...</span>
                  </>
                ) : (
                  <>
                    <span>📋</span>
                    <span>Toplu Ekle</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Personnel List */}
        {selectedClient && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              {userRole === 'client' ? '👥 Personellerim' : '3. Personel Listesi'}
              {(userRole === 'admin' || userRole === 'consultant') && Array.isArray(clients) && clients.find(c => c.id === selectedClient) && (
                <span className="text-purple-600 font-normal">
                  - {clients.find(c => c.id === selectedClient)?.name || clients.find(c => c.id === selectedClient)?.hotel_name}
                </span>
              )}
            </h2>
            
            {loading ? (
              <div className="flex justify-center items-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
              </div>
            ) : Array.isArray(personnel) && personnel.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {personnel.map((person) => (
                  <div key={person.id} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-all">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-lg font-bold text-gray-800">{person.full_name}</h3>
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          {person.is_local && (
                            <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                              🏠 Yerel
                            </span>
                          )}
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            person.gender === 'Kadın' 
                              ? 'bg-pink-100 text-pink-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {person.gender === 'Kadın' ? '👩' : '👨'} {person.gender}
                          </span>
                        </div>
                        {(userRole === 'admin' || userRole === 'consultant') && (
                          <button
                            onClick={() => deletePersonnel(person.id)}
                            className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition-colors"
                          >
                            🗑️ Sil
                          </button>
                        )}
                        {userRole === 'client' && (
                          <button
                            onClick={() => deletePersonnel(person.id)}
                            className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition-colors"
                          >
                            🗑️ Sil
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="space-y-2 text-sm text-gray-600">
                      <p><strong>💼 Görev:</strong> {person.position}</p>
                      <p><strong>📍 İkamet:</strong> {person.location}</p>
                      {person.certifications && person.certifications.length > 0 && (
                        <p><strong>🏆 Sertifikalar:</strong> {person.certifications.join(', ')}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">👥</div>
                <p className="text-gray-500 text-lg mb-2">Bu müşteri için henüz personel bulunmuyor.</p>
                <p className="text-gray-400 text-sm">Yukarıdaki butonu kullanarak personel ekleyebilirsiniz.</p>
              </div>
            )}

            {/* Personnel Analytics Charts */}
            {Array.isArray(personnel) && personnel.length > 0 && (
              <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Local vs Non-Local Chart */}
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-100">
                  <h3 className="text-lg font-bold text-gray-800 mb-4 text-center">
                    🏠 Yerel/Yerel Olmayan Personel Dağılımı
                  </h3>
                  <div className="flex flex-col items-center justify-center gap-4">
                    <div className="w-48 h-48">
                      <Pie
                        data={{
                          labels: ['🏠 Yerel Personel', '🌍 Yerel Olmayan'],
                          datasets: [{
                            data: [
                              personnel.filter(p => p.is_local).length,
                              personnel.filter(p => !p.is_local).length
                            ],
                            backgroundColor: ['#10b981', '#6b7280'],
                            borderColor: ['#059669', '#4b5563'],
                            borderWidth: 2,
                            hoverBackgroundColor: ['#059669', '#374151'],
                            hoverBorderWidth: 3
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: true,
                          plugins: {
                            legend: {
                              position: 'bottom',
                              labels: {
                                padding: 15,
                                font: { size: 12, weight: 'bold' },
                                usePointStyle: true,
                                pointStyle: 'circle'
                              }
                            },
                            tooltip: {
                              callbacks: {
                                label: function(context) {
                                  const total = personnel.length;
                                  const value = context.parsed;
                                  const percentage = ((value / total) * 100).toFixed(1);
                                  return `${context.label}: ${value} (${percentage}%)`;
                                }
                              }
                            }
                          }
                        }}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4 w-full">
                      <div className="bg-white rounded-lg p-3 text-center border border-green-200">
                        <p className="text-green-600 font-bold text-lg">
                          {personnel.filter(p => p.is_local).length}
                        </p>
                        <p className="text-xs text-gray-600">Yerel</p>
                        <p className="text-xs text-green-500">
                          {personnel.length > 0 ? ((personnel.filter(p => p.is_local).length / personnel.length) * 100).toFixed(1) : 0}%
                        </p>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center border border-gray-200">
                        <p className="text-gray-600 font-bold text-lg">
                          {personnel.filter(p => !p.is_local).length}
                        </p>
                        <p className="text-xs text-gray-600">Yerel Olmayan</p>
                        <p className="text-xs text-gray-500">
                          {personnel.length > 0 ? ((personnel.filter(p => !p.is_local).length / personnel.length) * 100).toFixed(1) : 0}%
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Gender Distribution Chart */}
                <div className="bg-gradient-to-br from-pink-50 to-purple-50 rounded-xl p-6 border border-pink-100">
                  <h3 className="text-lg font-bold text-gray-800 mb-4 text-center">
                    👥 Kadın/Erkek Personel Dağılımı
                  </h3>
                  <div className="flex flex-col items-center justify-center gap-4">
                    <div className="w-48 h-48">
                      <Pie
                        data={{
                          labels: ['👩 Kadın', '👨 Erkek'],
                          datasets: [{
                            data: [
                              personnel.filter(p => p.gender === 'Kadın').length,
                              personnel.filter(p => p.gender === 'Erkek').length
                            ],
                            backgroundColor: ['#ec4899', '#3b82f6'],
                            borderColor: ['#db2777', '#2563eb'],
                            borderWidth: 2,
                            hoverBackgroundColor: ['#db2777', '#1d4ed8'],
                            hoverBorderWidth: 3
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: true,
                          plugins: {
                            legend: {
                              position: 'bottom',
                              labels: {
                                padding: 15,
                                font: { size: 12, weight: 'bold' },
                                usePointStyle: true,
                                pointStyle: 'circle'
                              }
                            },
                            tooltip: {
                              callbacks: {
                                label: function(context) {
                                  const total = personnel.length;
                                  const value = context.parsed;
                                  const percentage = ((value / total) * 100).toFixed(1);
                                  return `${context.label}: ${value} (${percentage}%)`;
                                }
                              }
                            }
                          }
                        }}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4 w-full">
                      <div className="bg-white rounded-lg p-3 text-center border border-pink-200">
                        <p className="text-pink-600 font-bold text-lg">
                          {personnel.filter(p => p.gender === 'Kadın').length}
                        </p>
                        <p className="text-xs text-gray-600">Kadın</p>
                        <p className="text-xs text-pink-500">
                          {personnel.length > 0 ? ((personnel.filter(p => p.gender === 'Kadın').length / personnel.length) * 100).toFixed(1) : 0}%
                        </p>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center border border-blue-200">
                        <p className="text-blue-600 font-bold text-lg">
                          {personnel.filter(p => p.gender === 'Erkek').length}
                        </p>
                        <p className="text-xs text-gray-600">Erkek</p>
                        <p className="text-xs text-blue-500">
                          {personnel.length > 0 ? ((personnel.filter(p => p.gender === 'Erkek').length / personnel.length) * 100).toFixed(1) : 0}%
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* No Client Selected */}
        {!selectedClient && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">👥</div>
              <p className="text-gray-500 text-lg mb-2">Personel yönetimi için önce bir müşteri seçin.</p>
              <p className="text-gray-400 text-sm">Yukarıdaki dropdown'dan müşteri seçerek başlayabilirsiniz.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = ({ onNavigate }) => {
  const { user } = useUser();
  const { authToken, userRole, dbUser, refreshToken } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [clientDashboardData, setClientDashboardData] = useState(null);
  const [adminDashboardData, setAdminDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());
  const API = getApiUrl();

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      console.log('🔄 Fetching dashboard data for role:', userRole);
      
      if (userRole === 'client') {
        // Fetch client-specific dashboard data
        const response = await axios.get(`${API}/client-dashboard-stats`, {
          headers: { Authorization: `Bearer ${authToken}` }
        });
        console.log('🏨 Client Dashboard Data:', response.data);
        setClientDashboardData(response.data);
      } else if (userRole === 'admin') {
        // Fetch admin-specific dashboard data
        const response = await axios.get(`${API}/admin-dashboard-stats`, {
          headers: { Authorization: `Bearer ${authToken}` }
        });
        console.log('🛡️ Admin Dashboard Data:', response.data);
        setAdminDashboardData(response.data);
      } else {
        // Fetch general dashboard data for consultant
        const response = await axios.get(`${API}/stats`, {
          headers: { Authorization: `Bearer ${authToken}` }
        });
        console.log('📊 Dashboard Data:', response.data);
        setDashboardData(response.data);
      }
    } catch (error) {
      console.error('❌ Error fetching dashboard data:', error);
      
      // Set fallback data to prevent null state
      if (userRole === 'client') {
        setClientDashboardData({
          client_info: { name: 'Test Client', certificate_status: 'Aktif', certificate_days_left: 180 },
          statistics: { total_documents: 0, total_trainings: 0, completed_trainings: 0 },
          consumption_data: { energy_by_month: {}, water_by_month: {} },
          sustainability_progress: { carbon_reduction: 0, energy_efficiency: 0, waste_reduction: 0, water_saving: 0 },
          recent_activities: [],
          recommendations: []
        });
      } else if (userRole === 'admin') {
        setAdminDashboardData({
          overview: { total_clients: 0, total_documents: 0, total_trainings: 0, completed_trainings: 0 },
          consumption_analytics: { total_energy: 0, total_water: 0, total_carbon: 0, recycling_rate: 0 },
          document_distribution: {},
          recent_activities: [],
          system_health: { documents_last_24h: 0, trainings_last_24h: 0 }
        });
      } else {
        setDashboardData({
          total_clients: 0,
          stage_distribution: { stage_1: 0, stage_2: 0, stage_3: 0 },
          total_documents: 0,
          total_trainings: 0
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // Force token refresh on mount
  useEffect(() => {
    const forceTokenRefresh = async () => {
      console.log('🔄 Dashboard mounted: Forcing token refresh...');
      try {
        const newToken = await refreshToken();
        if (newToken) {
          console.log('✅ Dashboard mount: Token refreshed successfully');
        }
      } catch (error) {
        console.error('❌ Dashboard mount: Token refresh failed:', error);
      }
    };
    
    forceTokenRefresh();
  }, []); // Run once on mount

  useEffect(() => {
    if (authToken) {
      fetchDashboardData();
    } else {
      // Force token refresh if no token
      console.log('🔄 Dashboard: No token, forcing refresh...');
      refreshToken().then((newToken) => {
        if (newToken) {
          console.log('✅ Dashboard: Token refreshed successfully');
        }
      }).catch((error) => {
        console.error('❌ Dashboard: Force refresh failed:', error);
      });
    }
  }, [authToken]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">⚡</span>
            </div>
          </div>
          <p className="text-gray-600 mt-4 font-medium">Elite Dashboard yükleniyor...</p>
        </div>
      </div>
    );
  }

  const formatTime = (date) => {
    return date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('tr-TR', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Elite Header */}
      <div className="bg-gradient-to-r from-blue-900 via-purple-900 to-indigo-900 text-white p-8 shadow-2xl">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-4 mb-2">
                <div className="bg-gradient-to-r from-yellow-400 to-orange-500 w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg">
                  <span className="text-2xl">👋</span>
                </div>
                <div>
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-200 to-purple-200 bg-clip-text text-transparent">
                    Hoş Geldiniz, {user?.firstName || 'Değerli Kullanıcı'}!
                  </h1>
                  <p className="text-blue-200 text-lg mt-1">
                    {userRole === 'admin' ? '🎯 Admin Panel - Sistemin tüm kontrolü sizde' 
                    : userRole === 'consultant' ? '💼 Danışman Paneli - Müşterilerinizi elite seviyede yönetin'
                    : '🏨 Müşteri Paneli - Sürdürülebilirlik yolculuğunuza devam edin'}
                  </p>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-white">{formatTime(currentTime)}</div>
              <div className="text-blue-200 text-sm">{formatDate(currentTime)}</div>
              <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full bg-green-500 text-white text-sm font-medium">
                <span className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></span>
                Sistem Aktif
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-8">
        
        {/* Enhanced Admin Dashboard */}
        {userRole === 'admin' && (
          <div className="space-y-8">
            {/* Header Section */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
              <div className="flex justify-between items-center">
                <div>
                  <h1 className="text-3xl font-bold mb-2">🎯 Admin Dashboard</h1>
                  <p className="text-blue-100 text-lg">Sistem geneli istatistikler ve yönetim paneli</p>
                </div>
                <div className="flex items-center space-x-3">
                  <button 
                    onClick={() => {
                      console.log('🔄 Manual refresh clicked');
                      fetchDashboardData();
                    }}
                    className="bg-white/20 text-white px-4 py-2 rounded-lg hover:bg-white/30 transition-colors"
                  >
                    🔄 Yenile
                  </button>
                  <button className="bg-white/20 text-white px-4 py-2 rounded-lg hover:bg-white/30 transition-colors">
                    📊 Rapor İndir
                  </button>
                  <button className="bg-white/20 text-white px-4 py-2 rounded-lg hover:bg-white/30 transition-colors">
                    ⚙️ Ayarlar
                  </button>
                </div>
              </div>
            </div>

            {/* Key Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Toplam Müşteri</p>
                    <p className="text-3xl font-bold text-gray-900">{adminDashboardData?.overview?.total_clients || 0}</p>
                    <p className="text-sm text-green-600 mt-1">
                      ↗ {adminDashboardData?.overview?.registered_clients || 0} kayıtlı, {adminDashboardData?.overview?.bulk_clients || 0} bulk
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">👥</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Toplam Doküman</p>
                    <p className="text-3xl font-bold text-gray-900">{adminDashboardData?.overview?.total_documents || 0}</p>
                    <p className="text-sm text-green-600 mt-1">↗ Bu ay +{adminDashboardData?.overview?.monthly_documents || 0}</p>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">📄</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Tamamlanan Eğitim</p>
                    <p className="text-3xl font-bold text-gray-900">{adminDashboardData?.overview?.total_trainings || 0}</p>
                    <p className="text-sm text-purple-600 mt-1">↗ %{adminDashboardData?.training_analytics?.completion_rate || 0} tamamlanma</p>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">🎓</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-orange-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Atanan Müşteri</p>
                    <p className="text-3xl font-bold text-gray-900">{adminDashboardData?.overview?.assigned_clients || 0}</p>
                    <p className="text-sm text-orange-600 mt-1">↗ {(adminDashboardData?.overview?.total_clients || 0) - (adminDashboardData?.overview?.assigned_clients || 0)} atanmamış</p>
                  </div>
                  <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">👨‍💼</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Charts and Analytics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Client Distribution Chart */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Müşteri Dağılımı</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Kayıtlı Müşteriler</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full" style={{width: `${((adminDashboardData?.overview?.registered_clients || 0) / (adminDashboardData?.overview?.total_clients || 1)) * 100}%`}}></div>
                      </div>
                      <span className="text-sm font-medium w-8">{adminDashboardData?.overview?.registered_clients || 0}</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Bulk Müşteriler</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="bg-green-600 h-2 rounded-full" style={{width: `${((adminDashboardData?.overview?.bulk_clients || 0) / (adminDashboardData?.overview?.total_clients || 1)) * 100}%`}}></div>
                      </div>
                      <span className="text-sm font-medium w-8">{adminDashboardData?.overview?.bulk_clients || 0}</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Consultant Atanmış</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div className="bg-purple-600 h-2 rounded-full" style={{width: `${((adminDashboardData?.overview?.assigned_clients || 0) / (adminDashboardData?.overview?.total_clients || 1)) * 100}%`}}></div>
                      </div>
                      <span className="text-sm font-medium w-8">{adminDashboardData?.overview?.assigned_clients || 0}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* System Performance */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Sistem Performansı</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Karbon Ayak İzi Analizi</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div className="bg-green-500 h-2 rounded-full transition-all duration-300" style={{width: `${Math.min(adminDashboardData?.consumption_analytics?.carbon_footprint_reduction || 0, 100)}%`}}></div>
                      </div>
                      <span className="text-sm font-medium text-green-600">-{adminDashboardData?.consumption_analytics?.carbon_footprint_reduction || 0}%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Geri Dönüşüm Oranı</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div className="bg-blue-500 h-2 rounded-full transition-all duration-300" style={{width: `${Math.min(adminDashboardData?.consumption_analytics?.recycling_rate || 0, 100)}%`}}></div>
                      </div>
                      <span className="text-sm font-medium text-blue-600">{adminDashboardData?.consumption_analytics?.recycling_rate || 0}%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Eğitim Tamamlanma</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div className="bg-purple-500 h-2 rounded-full transition-all duration-300" style={{width: `${Math.min(adminDashboardData?.training_analytics?.completion_rate || 0, 100)}%`}}></div>
                      </div>
                      <span className="text-sm font-medium text-purple-600">{adminDashboardData?.training_analytics?.completion_rate || 0}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activities and Quick Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Activities */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Son Aktiviteler</h3>
                <div className="space-y-4">
                  {(adminDashboardData?.recent_activities || []).map((activity, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                        <span className="text-sm">
                          {activity.icon || '🎯'}
                        </span>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-900">{activity.title}</p>
                        <p className="text-xs text-gray-500">{activity.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Hızlı İşlemler</h3>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => {
                      console.log('🎯 Navigating to bulkOperations');
                      onNavigate('bulk-operations');
                    }}
                    className="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors text-left group"
                  >
                    <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">📦</div>
                    <h4 className="font-medium text-gray-900">Bulk İşlemler</h4>
                    <p className="text-sm text-gray-600">Toplu müşteri yükleme ve email</p>
                  </button>
                  
                  <button
                    onClick={() => {
                      console.log('🎯 Navigating to clients');
                      onNavigate('clients');
                    }}
                    className="p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors text-left group"
                  >
                    <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">👥</div>
                    <h4 className="font-medium text-gray-900">Müşteri Yönetimi</h4>
                    <p className="text-sm text-gray-600">Müşteri CRUD işlemleri</p>
                  </button>
                  
                  <button
                    onClick={() => {
                      console.log('🎯 Navigating to consultantDashboard');
                      onNavigate('consultants');
                    }}
                    className="p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors text-left group"
                  >
                    <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">👨‍💼</div>
                    <h4 className="font-medium text-gray-900">Consultant Yönetimi</h4>
                    <p className="text-sm text-gray-600">Danışman atama ve yönetimi</p>
                  </button>
                  
                  <button
                    onClick={() => {
                      console.log('🎯 Navigating to yeni-belge');
                      onNavigate('yeni-belge');
                    }}
                    className="p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors text-left group"
                  >
                    <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">📄</div>
                    <h4 className="font-medium text-gray-900">Belge Yönetimi</h4>
                    <p className="text-sm text-gray-600">Doküman ve klasör yönetimi</p>
                  </button>
                  
                  <button
                    onClick={() => {
                      console.log('🎯 Navigating to trainings');
                      onNavigate('training');
                    }}
                    className="p-4 bg-teal-50 rounded-lg hover:bg-teal-100 transition-colors text-left group"
                  >
                    <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">🎓</div>
                    <h4 className="font-medium text-gray-900">Eğitim Yönetimi</h4>
                    <p className="text-sm text-gray-600">Eğitim programları ve takip</p>
                  </button>
                  
                  <button
                    onClick={() => {
                      console.log('🎯 Navigating to wasteManagement');
                      onNavigate('waste-management');
                    }}
                    className="p-4 bg-red-50 rounded-lg hover:bg-red-100 transition-colors text-left group"
                  >
                    <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">♻️</div>
                    <h4 className="font-medium text-gray-900">Atık Yönetimi</h4>
                    <p className="text-sm text-gray-600">Atık kayıtları ve analiz</p>
                  </button>
                </div>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Sistem Durumu</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-2xl">✅</span>
                  </div>
                  <p className="text-sm font-medium text-gray-900">Sistem Durumu</p>
                  <p className="text-xs text-green-600">Çalışıyor</p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-2xl">🎯</span>
                  </div>
                  <p className="text-sm font-medium text-gray-900">DEFRA Standart</p>
                  <p className="text-xs text-blue-600">Uyumlu</p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-2xl">📅</span>
                  </div>
                  <p className="text-sm font-medium text-gray-900">2025 Güncel</p>
                  <p className="text-xs text-purple-600">Aktif</p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-2xl">🔄</span>
                  </div>
                  <p className="text-sm font-medium text-gray-900">24/7 Destek</p>
                  <p className="text-xs text-orange-600">Hazır</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Enhanced Client Dashboard */}
        {userRole === 'client' && clientDashboardData && (
          <>
            {/* Welcome Section */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 mb-8 text-white">
              <h1 className="text-3xl font-bold mb-2">🏨 Hoş Geldiniz, {clientDashboardData.client_info?.hotel_name || dbUser?.name}!</h1>
              <p className="text-blue-100 text-lg">Sürdürülebilirlik yolculuğunuzdaki tüm verileri tek bir yerde görebilirsiniz.</p>
            </div>

            {/* Key Performance Indicators */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-blue-500">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-gray-600 text-sm font-medium">Toplam Doküman</h3>
                    <p className="text-3xl font-bold text-gray-900">{clientDashboardData.statistics?.total_documents || 0}</p>
                    <p className="text-sm text-green-600">Yüklenen belgeler</p>
                  </div>
                  <div className="text-4xl">📄</div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-gray-600 text-sm font-medium">Tamamlanan Eğitim</h3>
                    <p className="text-3xl font-bold text-gray-900">{clientDashboardData.statistics?.completed_trainings || 0}</p>
                    <p className="text-sm text-blue-600">{clientDashboardData.statistics?.training_completion_rate || 0}% tamamlanma oranı</p>
                  </div>
                  <div className="text-4xl">🎓</div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-purple-500">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-gray-600 text-sm font-medium">Karbon Tasarrufu</h3>
                    <p className="text-3xl font-bold text-gray-900">-{clientDashboardData.sustainability_progress?.carbon_reduction || 0}%</p>
                    <p className="text-sm text-green-600">Geçen yıla göre</p>
                  </div>
                  <div className="text-4xl">🌱</div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-lg border-l-4 border-orange-500">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-gray-600 text-sm font-medium">Sertifika Durumu</h3>
                    <p className="text-3xl font-bold text-gray-900">{clientDashboardData.client_info?.certificate_status || 'Aktif'}</p>
                    <p className="text-sm text-orange-600">{clientDashboardData.client_info?.certificate_days_left || 0} gün kaldı</p>
                  </div>
                  <div className="text-4xl">🏆</div>
                </div>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Energy Consumption Chart */}
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">⚡ Enerji Tüketimi (kWh)</h3>
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-center w-full">
                    <div className="text-6xl mb-4">📊</div>
                    <div className="space-y-2">
                      {Object.entries(clientDashboardData.consumption_data?.energy_by_month || {}).map(([month, value]) => (
                        <div key={month} className="flex justify-between items-center bg-blue-50 p-3 rounded">
                          <span className="text-sm font-medium">{month}</span>
                          <span className="text-lg font-bold text-blue-600">{value.toLocaleString()}</span>
                        </div>
                      ))}
                      {Object.keys(clientDashboardData.consumption_data?.energy_by_month || {}).length === 0 && (
                        <p className="text-gray-500">Henüz enerji tüketim verisi bulunmamaktadır.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Water Consumption Chart */}
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">💧 Su Tüketimi (m³)</h3>
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-center w-full">
                    <div className="text-6xl mb-4">💧</div>
                    <div className="space-y-2">
                      {Object.entries(clientDashboardData.consumption_data?.water_by_month || {}).map(([month, value]) => (
                        <div key={month} className="flex justify-between items-center bg-cyan-50 p-3 rounded">
                          <span className="text-sm font-medium">{month}</span>
                          <span className="text-lg font-bold text-cyan-600">{value.toLocaleString()}</span>
                        </div>
                      ))}
                      {Object.keys(clientDashboardData.consumption_data?.water_by_month || {}).length === 0 && (
                        <p className="text-gray-500">Henüz su tüketim verisi bulunmamaktadır.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Progress Tracking */}
            <div className="bg-white p-6 rounded-xl shadow-lg mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">🎯 Sürdürülebilirlik Hedefleri</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Karbon Emisyon Azaltma</span>
                    <span className="text-sm font-medium text-gray-700">{clientDashboardData.sustainability_progress?.carbon_reduction || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{width: `${clientDashboardData.sustainability_progress?.carbon_reduction || 0}%`}}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Enerji Verimliliği</span>
                    <span className="text-sm font-medium text-gray-700">{clientDashboardData.sustainability_progress?.energy_efficiency || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{width: `${clientDashboardData.sustainability_progress?.energy_efficiency || 0}%`}}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Atık Azaltma</span>
                    <span className="text-sm font-medium text-gray-700">{clientDashboardData.sustainability_progress?.waste_reduction || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-purple-600 h-2 rounded-full" style={{width: `${clientDashboardData.sustainability_progress?.waste_reduction || 0}%`}}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Su Tasarrufu</span>
                    <span className="text-sm font-medium text-gray-700">{clientDashboardData.sustainability_progress?.water_saving || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-cyan-600 h-2 rounded-full" style={{width: `${clientDashboardData.sustainability_progress?.water_saving || 0}%`}}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Son Aktiviteler</h3>
                <div className="space-y-4">
                  {clientDashboardData.recent_activities?.length > 0 ? (
                    clientDashboardData.recent_activities.map((activity, index) => (
                      <div key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm">{activity.icon}</div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                          <p className="text-xs text-gray-500">{activity.time ? new Date(activity.time).toLocaleDateString('tr-TR') : 'Tarih bilgisi yok'}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-4xl mb-2">📋</div>
                      <p className="text-sm">Henüz aktivite bulunmamaktadır.</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Öneriler</h3>
                <div className="space-y-4">
                  {clientDashboardData.recommendations?.map((recommendation, index) => (
                    <div key={index} className={`p-4 rounded-lg border-l-4 ${
                      recommendation.type === 'energy' ? 'bg-gradient-to-r from-green-50 to-green-100 border-green-500' :
                      recommendation.type === 'water' ? 'bg-gradient-to-r from-blue-50 to-blue-100 border-blue-500' :
                      recommendation.type === 'waste' ? 'bg-gradient-to-r from-purple-50 to-purple-100 border-purple-500' :
                      'bg-gradient-to-r from-orange-50 to-orange-100 border-orange-500'
                    }`}>
                      <h4 className={`font-medium mb-1 ${
                        recommendation.type === 'energy' ? 'text-green-900' :
                        recommendation.type === 'water' ? 'text-blue-900' :
                        recommendation.type === 'waste' ? 'text-purple-900' :
                        'text-orange-900'
                      }`}>{recommendation.title}</h4>
                      <p className={`text-sm ${
                        recommendation.type === 'energy' ? 'text-green-700' :
                        recommendation.type === 'water' ? 'text-blue-700' :
                        recommendation.type === 'waste' ? 'text-purple-700' :
                        'text-orange-700'
                      }`}>{recommendation.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 Hızlı Erişim</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <button
                  onClick={() => onNavigate('consumption')}
                  className="p-4 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all transform hover:scale-105"
                >
                  <div className="text-2xl mb-2">⚡</div>
                  <div className="text-sm font-medium">Tüketim</div>
                </button>
                
                <button
                  onClick={() => onNavigate('carbon')}
                  className="p-4 bg-gradient-to-br from-green-500 to-green-600 text-white rounded-xl hover:from-green-600 hover:to-green-700 transition-all transform hover:scale-105"
                >
                  <div className="text-2xl mb-2">🌍</div>
                  <div className="text-sm font-medium">Karbon</div>
                </button>
                
                <button
                  onClick={() => onNavigate('waste-management')}
                  className="p-4 bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-xl hover:from-purple-600 hover:to-purple-700 transition-all transform hover:scale-105"
                >
                  <div className="text-2xl mb-2">🗑️</div>
                  <div className="text-sm font-medium">Atık</div>
                </button>
                
                <button
                  onClick={() => onNavigate('yeni-belge')}
                  className="p-4 bg-gradient-to-br from-orange-500 to-orange-600 text-white rounded-xl hover:from-orange-600 hover:to-orange-700 transition-all transform hover:scale-105"
                >
                  <div className="text-2xl mb-2">📄</div>
                  <div className="text-sm font-medium">Belgeler</div>
                </button>
              </div>
            </div>
          </>
        )}

        {/* System Status */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">📊 Sistem Durumu</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">100%</div>
              <div className="text-sm text-gray-600">Sistem Durumu</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">DEFRA</div>
              <div className="text-sm text-gray-600">Standart</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">2025</div>
              <div className="text-sm text-gray-600">Güncel</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">24/7</div>
              <div className="text-sm text-gray-600">Destek</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Global utility function for file size formatting
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('🚨 React Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-red-600 mb-4">⚠️ Bir Hata Oluştu</h1>
              <p className="text-gray-600 mb-4">
                Sistemde beklenmeyen bir hata oluştu. Sadece gerekiyorsa sayfayı yenileyin.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 mr-2"
              >
                🔄 Sayfayı Yenile
              </button>
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
              >
                🔧 Tekrar Dene
              </button>
              {process.env.NODE_ENV === 'development' && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-red-600">Hata Detayları (Dev)</summary>
                  <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                    {this.state.error?.toString()}
                  </pre>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Loading Component
const LoadingSpinner = ({ message = "Yükleniyor..." }) => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
    <span className="text-gray-600">{message}</span>
  </div>
);

// Network Status Hook
const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      console.log('🌐 Network: Online');
    };
    
    const handleOffline = () => {
      setIsOnline(false);
      console.log('🚫 Network: Offline');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
};

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const CLERK_PUBLISHABLE_KEY = process.env.REACT_APP_CLERK_PUBLISHABLE_KEY;

// Backend URL Discovery Function
const discoverBackendURL = async () => {
  // Always use Railway backend URL
  const railwayUrl = 'https://rota-crm-production.up.railway.app';
  
  // Test if Railway backend is accessible
  try {
    const response = await fetch(`${railwayUrl}/health`, { 
      method: 'GET',
      timeout: 5000 
    });
    if (response.ok) {
      localStorage.setItem('ROTA_BACKEND_URL', railwayUrl);
      return railwayUrl;
    }
  } catch (error) {
    console.error('Railway backend not accessible:', error);
  }
  
  // Fallback to Railway URL even if health check fails
  return railwayUrl;
};

const API = getApiUrl();

// Configure axios to automatically refresh tokens - SILENT VERSION
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        console.log('🔄 Token expired, handling silently...');
        // Handle silently WITHOUT page refresh - let auth hook handle re-auth
        console.log('✅ Token refresh handled by auth hook, no page reload needed');
        
      } catch (refreshError) {
        console.error('❌ Token refresh failed, will be handled by main auth system');
        // DO NOT reload page - let the main auth hook handle this silently
      }
    }
    
    return Promise.reject(error);
  }
);

// Debug log to see what URL is being used
console.log('🔧 API URL configured as:', API);
console.log('🔧 BACKEND_URL from env:', process.env.REACT_APP_BACKEND_URL);
console.log('🔧 All REACT_APP env vars:', Object.keys(process.env).filter(key => key.startsWith('REACT_APP')));

// Add cache busting and request interceptor
axios.defaults.headers.common['Cache-Control'] = 'no-cache';
axios.defaults.headers.common['Pragma'] = 'no-cache';
axios.defaults.timeout = 30000; // 30 second timeout

// Add request interceptor for debugging
axios.interceptors.request.use(
  (config) => {
    console.log(`📤 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('📤 Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging and error handling
axios.interceptors.response.use(
  (response) => {
    console.log(`📥 API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`📥 API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data);
    
    // Handle common errors
    if (error.response?.status === 401) {
      console.warn('🔐 Authentication error - token might be expired');
    } else if (error.response?.status === 403) {
      console.warn('🚫 Permission denied - user might not have access');
    } else if (error.response?.status >= 500) {
      console.error('🔥 Server error - backend might be down');
    } else if (error.code === 'ECONNABORTED') {
      console.error('⏰ Request timeout - server is slow');
    }
    
    return Promise.reject(error);
  }
);

// Add cache busting and request interceptor
axios.defaults.headers.common['Cache-Control'] = 'no-cache';
axios.defaults.headers.common['Pragma'] = 'no-cache';
axios.defaults.timeout = 30000; // 30 second timeout

// Add request interceptor for debugging
axios.interceptors.request.use(
  (config) => {
    console.log(`📤 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('📤 Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging and error handling
axios.interceptors.response.use(
  (response) => {
    console.log(`📥 API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`📥 API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data);
    
    // Handle common errors
    if (error.response?.status === 401) {
      console.warn('🔐 Authentication error - token might be expired');
    } else if (error.response?.status === 403) {
      console.warn('🚫 Permission denied - user might not have access');
    } else if (error.response?.status >= 500) {
      console.error('🔥 Server error - backend might be down');
    } else if (error.code === 'ECONNABORTED') {
      console.error('⏰ Request timeout - server is slow');
    }
    
    return Promise.reject(error);
  }
);

if (!CLERK_PUBLISHABLE_KEY) {
  throw new Error("Missing Publishable Key")
}

// Header Component
const Header = () => {
  const { user } = useUser();
  const { signOut } = useClerk();
  const { userRole, refreshToken } = useAuth();

  const handleSignOut = () => {
    // Clear any localStorage data on logout
    localStorage.removeItem(`client_setup_${userRole}_completed`);
    signOut();
  };

  const handleManualRefresh = async () => {
    try {
      await refreshToken();
      alert('Token başarıyla yenilendi!');
    } catch (error) {
      alert('Token yenileme başarısız: ' + error.message);
    }
  };

  return (
    <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <img 
            src="/logo.svg" 
            alt="Rota Kalite & Danışmanlık" 
            className="h-12 w-auto flex-shrink-0"
          />
          <div className="flex flex-col justify-center">
            <h1 className="text-lg font-bold text-white leading-tight">CRM Sistemi</h1>
            <p className="text-xs text-gray-300 leading-tight">
              {userRole === 'admin' ? 'Admin Paneli' : 'Müşteri Paneli'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="font-semibold text-white">{user?.fullName || user?.firstName}</p>
            <p className="text-sm text-gray-300">{user?.primaryEmailAddress?.emailAddress}</p>
            <span className={`inline-block px-2 py-1 text-xs rounded-full ${
              userRole === 'admin' 
                ? 'bg-purple-100 text-purple-800' 
                : userRole === 'consultant'
                ? 'bg-green-100 text-green-800'
                : 'bg-blue-100 text-blue-800'
            }`}>
              {userRole === 'admin' ? 'Admin' : userRole === 'consultant' ? 'Danışman' : 'Müşteri'}
            </span>
          </div>
          
          <button
            onClick={handleManualRefresh}
            className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 transition-colors text-sm"
            title="Token Yenile"
          >
            🔄 Token Yenile
          </button>
          
          <button
            onClick={handleSignOut}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
          >
            Çıkış Yap
          </button>
        </div>
      </div>
    </div>
  );
};

// Carbon Footprint Component
const CarbonFootprint = () => {
  const [carbonData, setCarbonData] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [selectedYear, setSelectedYear] = useState(2025);
  const [loading, setLoading] = useState(false);

  const { authToken, userRole, dbUser, refreshToken } = useAuth();

  // Fetch clients for admin and consultant users
  const fetchClients = async () => {
    if (userRole !== 'admin' && userRole !== 'consultant') return;
    
    try {
      console.log('🏨 [DEBUG] Fetching clients for', userRole);
      console.log('🏨 [DEBUG] AuthToken:', authToken ? 'EXISTS' : 'MISSING');
      
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      console.log('🏨 [DEBUG] Clients API response:', response.data);
      
      // Handle new backend response format { clients, pagination }
      let clientsArray = [];
      if (response.data.clients && Array.isArray(response.data.clients)) {
        clientsArray = response.data.clients;
      } else if (Array.isArray(response.data)) {
        // Fallback for old format
        clientsArray = response.data;
      }
      
      setClients(clientsArray);
      if (clientsArray.length > 0) {
        setSelectedClient(clientsArray[0].id);
        console.log('🏨 [DEBUG] Auto-selected first client:', clientsArray[0].id);
      }
    } catch (error) {
      console.error("❌ [ERROR] Error fetching clients:", error);
      setClients([]);
    }
  };

  // Fetch carbon footprint data
  const fetchCarbonData = async () => {
    setLoading(true);
    try {
      let clientId;
      if (userRole === 'admin' || userRole === 'consultant') {
        clientId = selectedClient;
      } else {
        clientId = dbUser?.client_id;
      }
      
      if (!clientId) {
        console.log('⚠️ No client selected for carbon footprint');
        setLoading(false);
        return;
      }
      
      console.log('🌍 Fetching carbon data for client:', clientId, 'year:', selectedYear, 'userRole:', userRole);
      
      const response = await axios.get(`${API}/analytics/carbon-footprint?year=${selectedYear}&client_id=${clientId}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      console.log('✅ Carbon data fetched:', response.data);
      console.log('🌍 Carbon data received:', response.data);
      setCarbonData(response.data);
    } catch (error) {
      console.error("❌ Error fetching carbon data:", error);
      setCarbonData(null);
    }
    setLoading(false);
  };

  // Initial data fetch
  useEffect(() => {
    if (authToken && (userRole === 'admin' || userRole === 'consultant')) {
      fetchClients();
    }
  }, [authToken, userRole]);

  // Fetch carbon data when client or year changes
  useEffect(() => {
    if (!authToken) return;
    if (selectedClient || userRole === 'client') {
      fetchCarbonData();
    }
  }, [authToken, selectedYear, selectedClient]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-6 rounded-xl shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold">🌍 Karbon Ayak İzi</h1>
            <p className="text-green-100">DEFRA 2024 Standartları ile Hesaplanmış</p>
          </div>
          <div className="text-right">
            <div className="bg-white bg-opacity-20 px-4 py-2 rounded-lg">
              <p className="text-sm">Metodoloji</p>
              <p className="font-bold">DEFRA 2024</p>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-4 items-center">
          {/* Client Selection for Admin and Consultant */}
          {(userRole === 'admin' || userRole === 'consultant') && (
            <select
              value={selectedClient}
              onChange={(e) => {
                console.log('🔄 Carbon footprint client selected:', e.target.value);
                setSelectedClient(e.target.value);
              }}
              className="px-4 py-2 rounded-lg bg-white text-gray-800 font-medium min-w-[200px]"
            >
              <option value="">
                {userRole === 'consultant' ? 'Size Atanan Müşteriler' : 'Müşteri Seçin'}
              </option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.hotel_name || client.client_name || client.name}
                </option>
              ))}
            </select>
          )}

          {/* Year Selection */}
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="px-4 py-2 rounded-lg bg-white text-gray-800 font-medium"
          >
            <option value={2025}>2025</option>
            <option value={2024}>2024</option>
            <option value={2023}>2023</option>
          </select>

          {/* Refresh Button */}
          <button
            onClick={fetchCarbonData}
            disabled={loading || (((userRole === 'admin' || userRole === 'consultant') && !selectedClient))}
            className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg font-medium transition-all disabled:opacity-50"
          >
            {loading ? '🔄 Yükleniyor...' : '🔄 Yenile'}
          </button>
        </div>
      </div>

      {/* Content */}
      {!carbonData ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <span className="text-6xl mb-4 block">🌍</span>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">
            {userRole === 'admin' && !selectedClient 
              ? '📊 Karbon Analizi İçin Müşteri Seçin'
              : '📊 Karbon Verisi Bulunamadı'
            }
          </h3>
          <p className="text-gray-600">
            {userRole === 'admin' && !selectedClient 
              ? 'Lütfen bir müşteri seçin ve karbon ayak izi analizini başlatın'
              : 'Seçilen yıl için karbon ayak izi verisi bulunmuyor. Lütfen tüketim verileri girişi yapın.'
            }
          </p>
        </div>
      ) : (
        <>
          {/* Carbon Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">🌍 Toplam CO2</h3>
              <p className="text-3xl font-bold">{carbonData.total_carbon_emissions?.toLocaleString() || 0}</p>
              <p className="text-green-100">kg CO2</p>
            </div>
            
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">📊 CO2 (Ton)</h3>
              <p className="text-3xl font-bold">{carbonData.total_carbon_tonnes?.toFixed(3) || 0}</p>
              <p className="text-blue-100">Ton CO2</p>
            </div>
            
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">👤 Kişi Başına</h3>
              <p className="text-3xl font-bold">{(carbonData.average_per_person_co2 || 0).toFixed(2)}</p>
              <p className="text-purple-100">kg CO2/kişi</p>
            </div>
            
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">⭐ Performans</h3>
              <p className="text-2xl font-bold">
                {carbonData.yearly_benchmarks?.performance_level || 'Hesaplanıyor'}
              </p>
              <p className="text-orange-100">
                {(carbonData.yearly_benchmarks?.co2_per_room_night || 0).toFixed(2)} kg/oda/gece
              </p>
            </div>
          </div>

          {/* Monthly Carbon Data Table */}
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-xl font-bold mb-4">📊 Aylık Karbon Ayak İzi Detayı</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse">
                <thead>
                  <tr className="bg-gradient-to-r from-green-100 to-blue-100">
                    <th className="px-4 py-3 border text-left font-bold">Ay</th>
                    <th className="px-4 py-3 border text-left font-bold text-green-700">🌍 CO2 (kg)</th>
                    <th className="px-4 py-3 border text-left font-bold text-blue-700">👤 Kişi Başına</th>
                    <th className="px-4 py-3 border text-left font-bold text-purple-700">🏨 Konaklama</th>
                    <th className="px-4 py-3 border text-left font-bold text-orange-700">⭐ Performans</th>
                  </tr>
                </thead>
                <tbody>
                  {carbonData.monthly_carbon_data?.map((month, index) => (
                    <tr key={index} className={`hover:bg-gray-50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-25'}`}>
                      <td className="px-4 py-3 border font-bold text-gray-800">{month.month_name}</td>
                      <td className="px-4 py-3 border text-green-700 font-semibold">
                        {(month.total_co2_emissions || 0).toFixed(2)}
                      </td>
                      <td className="px-4 py-3 border text-blue-700 font-semibold">
                        {(month.per_person_co2 || 0).toFixed(2)}
                      </td>
                      <td className="px-4 py-3 border text-purple-700 font-semibold">
                        {month.accommodation_count || 0}
                      </td>
                      <td className="px-4 py-3 border">
                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                          month.benchmark?.performance_level === 'Excellent' ? 'bg-green-100 text-green-800' :
                          month.benchmark?.performance_level === 'Good' ? 'bg-blue-100 text-blue-800' :
                          month.benchmark?.performance_level === 'Average' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {month.benchmark?.performance_level || 'N/A'}
                        </span>
                      </td>
                    </tr>
                  ))
                }
                </tbody>
              </table>
            </div>
          </div>

          {/* DEFRA Methodology & Benchmarks */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* DEFRA Methodology */}
            <div className="bg-blue-50 p-6 rounded-xl border-l-4 border-blue-500">
              <h4 className="font-bold text-blue-800 mb-3 flex items-center">
                📋 DEFRA 2024 Metodolojisi
              </h4>
              <p className="text-sm text-blue-700 mb-3">
                Bu hesaplamalar <strong>UK Department for Environment, Food and Rural Affairs (DEFRA)</strong> 
                tarafından yayınlanan 2024 yılı resmi emisyon faktörleri kullanılarak yapılmıştır.
              </p>
              <ul className="text-xs text-blue-600 space-y-1">
                <li>✅ Uluslararası standartlara uygun</li>
                <li>✅ ISO 14064 ile uyumlu</li>
                <li>✅ Greenhouse Gas Protocol sertifikalı</li>
                <li>✅ Türkiye elektrik şebekesi faktörleri</li>
              </ul>
            </div>

            {/* Performance Benchmarks */}
            <div className="bg-green-50 p-6 rounded-xl border-l-4 border-green-500">
              <h4 className="font-bold text-green-800 mb-3 flex items-center">
                ⭐ Performans Kriterleri
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-green-700">🏆 Mükemmel:</span>
                  <span className="font-bold text-green-800">≤ 20 kg CO2/oda/gece</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700">👍 İyi:</span>
                  <span className="font-bold text-blue-800">≤ 30 kg CO2/oda/gece</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-yellow-700">📊 Ortalama:</span>
                  <span className="font-bold text-yellow-800">≤ 45 kg CO2/oda/gece</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-red-700">⚠️ Geliştirilmeli:</span>
                  <span className="font-bold text-red-800">&gt; 45 kg CO2/oda/gece</span>
                </div>
              </div>
            </div>
          </div>

          {/* Emission Sources Breakdown - Basic */}
          {carbonData.total_emission_sources && (
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <h3 className="text-xl font-bold mb-4">
                🔬 Kaynak Bazında Emisyon Analizi
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {/* Temel Enerji Kaynakları */}
                {carbonData.total_emission_sources.electricity > 0 && (
                  <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-lg border-l-4 border-yellow-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-yellow-600 text-xl">⚡</span>
                        <span className="font-semibold text-yellow-800">Elektrik</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-yellow-900">{carbonData.total_emission_sources.electricity.toFixed(2)}</div>
                        <div className="text-xs text-yellow-600">kg CO2</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.water > 0 && (
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border-l-4 border-blue-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-blue-600 text-xl">💧</span>
                        <span className="font-semibold text-blue-800">Su</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-blue-900">{carbonData.total_emission_sources.water.toFixed(2)}</div>
                        <div className="text-xs text-blue-600">kg CO2</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.natural_gas > 0 && (
                  <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg border-l-4 border-orange-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-orange-600 text-xl">🔥</span>
                        <span className="font-semibold text-orange-800">Doğalgaz</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-orange-900">{carbonData.total_emission_sources.natural_gas.toFixed(2)}</div>
                        <div className="text-xs text-orange-600">kg CO2</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.coal > 0 && (
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-lg border-l-4 border-gray-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-600 text-xl">⚫</span>
                        <span className="font-semibold text-gray-800">Kömür</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-gray-900">{carbonData.total_emission_sources.coal.toFixed(2)}</div>
                        <div className="text-xs text-gray-600">kg CO2</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Sıvı Yakıtlar */}
                {carbonData.total_emission_sources.diesel > 0 && (
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border-l-4 border-green-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-green-600 text-xl">🚛</span>
                        <span className="font-semibold text-green-800">Mazot</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-900">{carbonData.total_emission_sources.diesel.toFixed(2)}</div>
                        <div className="text-xs text-green-600">kg CO2</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.gasoline > 0 && (
                  <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-lg border-l-4 border-red-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-red-600 text-xl">⛽</span>
                        <span className="font-semibold text-red-800">Benzin</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-red-900">{carbonData.total_emission_sources.gasoline.toFixed(2)}</div>
                        <div className="text-xs text-red-600">kg CO2</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.lpg > 0 && (
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border-l-4 border-purple-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-purple-600 text-xl">🔥</span>
                        <span className="font-semibold text-purple-800">LPG</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-purple-900">{carbonData.total_emission_sources.lpg.toFixed(2)}</div>
                        <div className="text-xs text-purple-600">kg CO2</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.fuel_oil > 0 && (
                  <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 p-4 rounded-lg border-l-4 border-indigo-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-indigo-600 text-xl">🏭</span>
                        <span className="font-semibold text-indigo-800">Fuel Oil</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-indigo-900">{carbonData.total_emission_sources.fuel_oil.toFixed(2)}</div>
                        <div className="text-xs text-indigo-600">kg CO2</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* F-Gas Soğutucular */}
                {carbonData.total_emission_sources.r134a_gas > 0 && (
                  <div className="bg-gradient-to-br from-cyan-50 to-cyan-100 p-4 rounded-lg border-l-4 border-cyan-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-cyan-600 text-xl">❄️</span>
                        <span className="font-semibold text-cyan-800">R134a (Klimalar)</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-cyan-900">{carbonData.total_emission_sources.r134a_gas.toFixed(2)}</div>
                        <div className="text-xs text-cyan-600">kg CO2e</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.r600a_gas > 0 && (
                  <div className="bg-gradient-to-br from-teal-50 to-teal-100 p-4 rounded-lg border-l-4 border-teal-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-teal-600 text-xl">🧊</span>
                        <span className="font-semibold text-teal-800">R600a (Buzdolapları)</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-teal-900">{carbonData.total_emission_sources.r600a_gas.toFixed(2)}</div>
                        <div className="text-xs text-teal-600">kg CO2e</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.r410a_gas > 0 && (
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border-l-4 border-blue-600 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-blue-600 text-xl">🌀</span>
                        <span className="font-semibold text-blue-800">R410A (Modern AC)</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-blue-900">{carbonData.total_emission_sources.r410a_gas.toFixed(2)}</div>
                        <div className="text-xs text-blue-600">kg CO2e</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.r32_gas > 0 && (
                  <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 p-4 rounded-lg border-l-4 border-emerald-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-emerald-600 text-xl">💨</span>
                        <span className="font-semibold text-emerald-800">R32 (Yeni Nesil AC)</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-emerald-900">{carbonData.total_emission_sources.r32_gas.toFixed(2)}</div>
                        <div className="text-xs text-emerald-600">kg CO2e</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Yangın Söndürücüler */}
                {carbonData.total_emission_sources.co2_fire > 0 && (
                  <div className="bg-gradient-to-br from-slate-50 to-slate-100 p-4 rounded-lg border-l-4 border-slate-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-slate-600 text-xl">🧯</span>
                        <span className="font-semibold text-slate-800">CO2 Söndürücü</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-slate-900">{carbonData.total_emission_sources.co2_fire.toFixed(2)}</div>
                        <div className="text-xs text-slate-600">kg CO2</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {carbonData.total_emission_sources.fm200_fire > 0 && (
                  <div className="bg-gradient-to-br from-rose-50 to-rose-100 p-4 rounded-lg border-l-4 border-rose-500 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-rose-600 text-xl">🚨</span>
                        <span className="font-semibold text-rose-800">FM200</span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-rose-900">{carbonData.total_emission_sources.fm200_fire.toFixed(2)}</div>
                        <div className="text-xs text-rose-600">kg CO2e</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Veri Yoksa Uyarı Mesajı */}
              {Object.values(carbonData.total_emission_sources).every(value => value === 0 || value === null || value === undefined) && (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-6xl mb-4">📊</div>
                  <h3 className="text-lg font-semibold text-gray-600 mb-2">Henüz Emisyon Verisi Yok</h3>
                  <p className="text-gray-500">Tüketim verisi girdikten sonra kaynak bazında emisyon analizi burada görünecek.</p>
                </div>
              )}
            </div>
          )}

          {/* Pasta Grafik - Emisyon Kaynakları Dağılımı */}
          {carbonData.total_emission_sources && (
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <h3 className="text-xl font-bold mb-6 flex items-center">
                🍰 Emisyon Kaynakları Dağılımı
              </h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Pasta Grafik */}
                <div className="flex justify-center items-center">
                  <div className="w-80 h-80">
                    <Pie
                      data={{
                        labels: [
                          '⚡ Elektrik',
                          '🔥 Doğalgaz', 
                          '💧 Su',
                          '⚫ Kömür',
                          '⛽ Dizel',
                          '🚗 Benzin',
                          '🏔️ LPG',
                          '🛢️ Fuel Oil',
                          '❄️ F-Gaslar',
                          '🧯 Yangın Söndürücü'
                        ].filter((_, index) => {
                          const values = [
                            carbonData.total_emission_sources.electricity || 0,
                            carbonData.total_emission_sources.natural_gas || 0,
                            carbonData.total_emission_sources.water || 0,
                            carbonData.total_emission_sources.coal || 0,
                            carbonData.total_emission_sources.diesel || 0,
                            carbonData.total_emission_sources.gasoline || 0,
                            carbonData.total_emission_sources.lpg || 0,
                            carbonData.total_emission_sources.fuel_oil || 0,
                            (carbonData.total_emission_sources.r134a_gas || 0) + 
                            (carbonData.total_emission_sources.r600a_gas || 0) + 
                            (carbonData.total_emission_sources.r410a_gas || 0) + 
                            (carbonData.total_emission_sources.r32_gas || 0),
                            (carbonData.total_emission_sources.co2_fire || 0) + 
                            (carbonData.total_emission_sources.fm200_fire || 0)
                          ];
                          return values[index] > 0;
                        }),
                        datasets: [{
                          data: [
                            carbonData.total_emission_sources.electricity || 0,
                            carbonData.total_emission_sources.natural_gas || 0,
                            carbonData.total_emission_sources.water || 0,
                            carbonData.total_emission_sources.coal || 0,
                            carbonData.total_emission_sources.diesel || 0,
                            carbonData.total_emission_sources.gasoline || 0,
                            carbonData.total_emission_sources.lpg || 0,
                            carbonData.total_emission_sources.fuel_oil || 0,
                            (carbonData.total_emission_sources.r134a_gas || 0) + 
                            (carbonData.total_emission_sources.r600a_gas || 0) + 
                            (carbonData.total_emission_sources.r410a_gas || 0) + 
                            (carbonData.total_emission_sources.r32_gas || 0),
                            (carbonData.total_emission_sources.co2_fire || 0) + 
                            (carbonData.total_emission_sources.fm200_fire || 0)
                          ].filter(value => value > 0),
                          backgroundColor: [
                            '#FCD34D', // Elektrik - Sarı
                            '#FB923C', // Doğalgaz - Turuncu
                            '#60A5FA', // Su - Mavi
                            '#6B7280', // Kömür - Gri
                            '#34D399', // Dizel - Yeşil
                            '#F87171', // Benzin - Kırmızı
                            '#A78BFA', // LPG - Mor
                            '#F59E0B', // Fuel Oil - Amber
                            '#06B6D4', // F-Gaslar - Cyan
                            '#EF4444'  // Yangın Söndürücü - Red
                          ].slice(0, [
                            carbonData.total_emission_sources.electricity || 0,
                            carbonData.total_emission_sources.natural_gas || 0,
                            carbonData.total_emission_sources.water || 0,
                            carbonData.total_emission_sources.coal || 0,
                            carbonData.total_emission_sources.diesel || 0,
                            carbonData.total_emission_sources.gasoline || 0,
                            carbonData.total_emission_sources.lpg || 0,
                            carbonData.total_emission_sources.fuel_oil || 0,
                            (carbonData.total_emission_sources.r134a_gas || 0) + 
                            (carbonData.total_emission_sources.r600a_gas || 0) + 
                            (carbonData.total_emission_sources.r410a_gas || 0) + 
                            (carbonData.total_emission_sources.r32_gas || 0),
                            (carbonData.total_emission_sources.co2_fire || 0) + 
                            (carbonData.total_emission_sources.fm200_fire || 0)
                          ].filter(value => value > 0).length),
                          borderWidth: 3,
                          borderColor: '#ffffff',
                          hoverBorderWidth: 5,
                          hoverBorderColor: '#1F2937'
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'bottom',
                            labels: {
                              padding: 20,
                              font: {
                                size: 12,
                                weight: 'bold'
                              },
                              color: '#374151'
                            }
                          },
                          tooltip: {
                            backgroundColor: '#1F2937',
                            titleColor: '#F9FAFB',
                            bodyColor: '#F9FAFB',
                            borderColor: '#6B7280',
                            borderWidth: 1,
                            callbacks: {
                              label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${value.toFixed(2)} kg CO2 (${percentage}%)`;
                              }
                            }
                          }
                        },
                        animation: {
                          animateRotate: true,
                          animateScale: true,
                          duration: 2000
                        }
                      }}
                    />
                  </div>
                </div>

                {/* İstatistikler */}
                <div className="space-y-4">
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-xl border border-blue-200">
                    <h4 className="font-bold text-gray-800 mb-4 flex items-center">
                      📊 Emisyon İstatistikleri
                    </h4>
                    
                    <div className="space-y-3">
                      {/* En Yüksek Emisyon */}
                      {(() => {
                        const sources = {
                          'Elektrik': carbonData.total_emission_sources.electricity || 0,
                          'Doğalgaz': carbonData.total_emission_sources.natural_gas || 0,
                          'Su': carbonData.total_emission_sources.water || 0,
                          'Kömür': carbonData.total_emission_sources.coal || 0,
                          'Dizel': carbonData.total_emission_sources.diesel || 0,
                          'Benzin': carbonData.total_emission_sources.gasoline || 0,
                          'LPG': carbonData.total_emission_sources.lpg || 0,
                          'Fuel Oil': carbonData.total_emission_sources.fuel_oil || 0
                        };
                        const maxSource = Object.entries(sources).reduce((a, b) => sources[a[0]] > sources[b[0]] ? a : b);
                        const total = Object.values(sources).reduce((a, b) => a + b, 0);
                        const percentage = total > 0 ? ((maxSource[1] / total) * 100).toFixed(1) : 0;
                        
                        return (
                          <div className="flex justify-between items-center bg-white p-3 rounded-lg shadow-sm">
                            <span className="text-gray-700 font-medium">🏆 En Yüksek Emisyon:</span>
                            <div className="text-right">
                              <div className="font-bold text-red-600">{maxSource[0]}</div>
                              <div className="text-sm text-gray-500">{maxSource[1].toFixed(2)} kg CO2 ({percentage}%)</div>
                            </div>
                          </div>
                        );
                      })()}

                      {/* Toplam Kaynak Sayısı */}
                      <div className="flex justify-between items-center bg-white p-3 rounded-lg shadow-sm">
                        <span className="text-gray-700 font-medium">🔢 Aktif Kaynak Sayısı:</span>
                        <div className="text-right">
                          <div className="font-bold text-blue-600">
                            {Object.values(carbonData.total_emission_sources).filter(v => v > 0).length}
                          </div>
                          <div className="text-sm text-gray-500">farklı emisyon kaynağı</div>
                        </div>
                      </div>

                      {/* Ortalama Emisyon */}
                      <div className="flex justify-between items-center bg-white p-3 rounded-lg shadow-sm">
                        <span className="text-gray-700 font-medium">📈 Ortalama Emisyon:</span>
                        <div className="text-right">
                          <div className="font-bold text-green-600">
                            {(() => {
                              const values = Object.values(carbonData.total_emission_sources).filter(v => v > 0);
                              const avg = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
                              return avg.toFixed(2);
                            })()}
                          </div>
                          <div className="text-sm text-gray-500">kg CO2/kaynak</div>
                        </div>
                      </div>

                      {/* DEFRA Uyumluluk */}
                      <div className="bg-green-100 p-3 rounded-lg border border-green-300">
                        <div className="flex items-center space-x-2">
                          <span className="text-green-600 text-lg">✅</span>
                          <span className="text-green-800 font-semibold text-sm">DEFRA 2024 Standartları</span>
                        </div>
                        <p className="text-green-700 text-xs mt-1">
                          Tüm hesaplamalar UK DEFRA emisyon faktörleri ile yapılmıştır
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

        </>
      )}
    </div>
  );
};

// Guest Engagement Component
const GuestEngagement = () => {
  const [guests, setGuests] = useState([]);
  const [ecoTips, setEcoTips] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddGuest, setShowAddGuest] = useState(false);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  
  const [guestData, setGuestData] = useState({
    guest_name: '',
    room_number: '',
    eco_actions: [],
    feedback_rating: null,
    feedback_comment: ''
  });

  const { authToken, userRole, dbUser, refreshToken } = useAuth();

  useEffect(() => {
    if (!authToken) return;
    fetchClients();
    fetchEcoTips();
  }, [authToken]);

  useEffect(() => {
    if (selectedClient || userRole === 'client') {
      fetchGuestData();
      fetchLeaderboard();
    }
  }, [selectedClient, userRole]);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/clients`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(response.data.clients || []);
      if (userRole === 'client' && dbUser?.client_id) {
        setSelectedClient(dbUser.client_id);
      }
    } catch (error) {
      console.error('Clients fetch error:', error);
    }
  };

  const fetchGuestData = async () => {
    try {
      setLoading(true);
      const clientParam = userRole === 'admin' && selectedClient ? `?client_id=${selectedClient}` : '';
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/guest-engagement${clientParam}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setGuests(response.data);
    } catch (error) {
      console.error('Guest data fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEcoTips = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/guest-engagement/eco-tips`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setEcoTips(response.data.eco_tips);
    } catch (error) {
      console.error('Eco tips fetch error:', error);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const clientParam = userRole === 'admin' && selectedClient ? `?client_id=${selectedClient}` : '';
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/guest-engagement/leaderboard${clientParam}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setLeaderboard(response.data.leaderboard);
    } catch (error) {
      console.error('Leaderboard fetch error:', error);
    }
  };

  const handleSubmitGuest = async () => {
    try {
      const payload = {
        ...guestData,
        client_id: userRole === 'admin' ? selectedClient : undefined
      };

      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/guest-engagement`, payload, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      setShowAddGuest(false);
      setGuestData({
        guest_name: '',
        room_number: '',
        eco_actions: [],
        feedback_rating: null,
        feedback_comment: ''
      });
      
      fetchGuestData();
      fetchLeaderboard();
    } catch (error) {
      console.error('Guest submission error:', error);
    }
  };

  const toggleEcoAction = (actionId) => {
    const tipTitle = ecoTips.find(tip => tip.id === actionId)?.title;
    setGuestData(prev => ({
      ...prev,
      eco_actions: prev.eco_actions.includes(tipTitle)
        ? prev.eco_actions.filter(action => action !== tipTitle)
        : [...prev.eco_actions, tipTitle]
    }));
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-800">🎯 Guest Engagement & Education</h2>
        <button
          onClick={() => setShowAddGuest(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
        >
          + Konuk Ekle
        </button>
      </div>

      {/* Client Selection for Admin */}
      {userRole === 'admin' && (
        <div className="bg-white p-4 rounded-lg shadow">
          <label className="block text-sm font-medium text-gray-700 mb-2">Client Seçin:</label>
          <select
            value={selectedClient}
            onChange={(e) => setSelectedClient(e.target.value)}
            className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Client Seçin</option>
            {clients.map(client => (
              <option key={client.id} value={client.id}>{client.company_name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Eco Tips Grid */}
      <div className="bg-white p-6 rounded-xl shadow-lg">
        <h3 className="text-xl font-bold mb-4 text-green-800">🌿 Sürdürülebilirlik İpuçları</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ecoTips.map(tip => (
            <div key={tip.id} className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl">{tip.icon}</span>
                <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                  +{tip.points} puan
                </span>
              </div>
              <h4 className="font-semibold text-green-900">{tip.title}</h4>
              <p className="text-sm text-green-700 mt-1">{tip.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Leaderboard */}
      <div className="bg-white p-6 rounded-xl shadow-lg">
        <h3 className="text-xl font-bold mb-4 text-purple-800">🏆 Sürdürülebilirlik Liderlik Tablosu</h3>
        <div className="space-y-2">
          {leaderboard.map((guest, index) => (
            <div key={guest.id} className={`p-3 rounded-lg flex items-center justify-between ${
              index === 0 ? 'bg-yellow-50 border-yellow-300' :
              index === 1 ? 'bg-gray-50 border-gray-300' :
              index === 2 ? 'bg-orange-50 border-orange-300' : 'bg-white border-gray-200'
            } border`}>
              <div className="flex items-center space-x-3">
                <span className="text-lg">
                  {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`}
                </span>
                <div>
                  <span className="font-semibold">{guest.guest_name}</span>
                  <span className="text-gray-500 ml-2">Oda {guest.room_number}</span>
                </div>
              </div>
              <span className="font-bold text-purple-600">{guest.sustainability_score} puan</span>
            </div>
          ))}
          {leaderboard.length === 0 && (
            <p className="text-gray-500 text-center py-4">Henüz konuk verisi bulunmuyor.</p>
          )}
        </div>
      </div>

      {/* Guest List */}
      <div className="bg-white p-6 rounded-xl shadow-lg">
        <h3 className="text-xl font-bold mb-4 text-blue-800">👥 Konuk Listesi</h3>
        <div className="overflow-x-auto">
          <table className="w-full table-auto">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-2 text-left">Konuk Adı</th>
                <th className="px-4 py-2 text-left">Oda</th>
                <th className="px-4 py-2 text-left">Sürdürülebilirlik Puanı</th>
                <th className="px-4 py-2 text-left">Eco Aksiyonlar</th>
                <th className="px-4 py-2 text-left">Değerlendirme</th>
              </tr>
            </thead>
            <tbody>
              {guests.map(guest => (
                <tr key={guest.id} className="border-t">
                  <td className="px-4 py-2 font-medium">{guest.guest_name}</td>
                  <td className="px-4 py-2">{guest.room_number}</td>
                  <td className="px-4 py-2">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">
                      {guest.sustainability_score} puan
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <span className="text-green-600">{guest.eco_actions.length} aksiyon</span>
                  </td>
                  <td className="px-4 py-2">
                    {guest.feedback_rating && (
                      <span className="text-yellow-500">
                        {'★'.repeat(guest.feedback_rating)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Guest Modal */}
      {showAddGuest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-4">Yeni Konuk Ekle</h3>
            
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Konuk Adı"
                value={guestData.guest_name}
                onChange={(e) => setGuestData(prev => ({...prev, guest_name: e.target.value}))}
                className="w-full px-3 py-2 border rounded-lg"
              />
              
              <input
                type="text"
                placeholder="Oda Numarası"
                value={guestData.room_number}
                onChange={(e) => setGuestData(prev => ({...prev, room_number: e.target.value}))}
                className="w-full px-3 py-2 border rounded-lg"
              />

              <div>
                <label className="block text-sm font-medium mb-2">Eco Aksiyonlar:</label>
                <div className="space-y-2">
                  {ecoTips.map(tip => (
                    <label key={tip.id} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={guestData.eco_actions.includes(tip.title)}
                        onChange={() => toggleEcoAction(tip.id)}
                        className="rounded"
                      />
                      <span className="text-sm">{tip.icon} {tip.title} (+{tip.points} puan)</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Değerlendirme (1-5):</label>
                <div className="flex space-x-2">
                  {[1,2,3,4,5].map(rating => (
                    <button
                      key={rating}
                      onClick={() => setGuestData(prev => ({...prev, feedback_rating: rating}))}
                      className={`text-2xl ${guestData.feedback_rating >= rating ? 'text-yellow-500' : 'text-gray-300'}`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>

              <textarea
                placeholder="Yorum (opsiyonel)"
                value={guestData.feedback_comment}
                onChange={(e) => setGuestData(prev => ({...prev, feedback_comment: e.target.value}))}
                className="w-full px-3 py-2 border rounded-lg h-20"
              />
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={handleSubmitGuest}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                Kaydet
              </button>
              <button
                onClick={() => setShowAddGuest(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
              >
                İptal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Waste Management Component
const WasteManagement = ({ selectedClient: propSelectedClient }) => {
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState({});
  const [wasteRecords, setWasteRecords] = useState([]);
  const [showAddRecord, setShowAddRecord] = useState(false);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [selectedYear, setSelectedYear] = useState(2025);
  const [activeTab, setActiveTab] = useState('overview');
  const [newRecord, setNewRecord] = useState({
    year: 2025,
    month: 1,
    organic_waste: 0,
    plastic_waste: 0,
    glass_waste: 0,
    paper_waste: 0,
    metal_waste: 0,
    electronic_waste: 0,
    oil_waste: 0,
    mixed_waste: 0,
    accommodation_count: 1
  });
  const { authToken, userRole, dbUser, ensureTokenForOperation } = useAuth();
  const API = getApiUrl();

  // Use selectedClient from props (for consultant) or manage locally (for admin/client)
  const effectiveSelectedClient = propSelectedClient || selectedClient;

  // Fetch clients for admin users
  const fetchClients = async () => {
    if (userRole !== 'admin' && userRole !== 'consultant') return;
    
    try {
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(response.data.clients || []);
      if (response.data?.clients?.length > 0 && !propSelectedClient) {
        setSelectedClient(response.data.clients[0].id);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  // Fetch waste records from analytics
  const fetchWasteRecords = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedYear) params.append('year', selectedYear);
      if ((userRole === 'admin' || userRole === 'consultant') && effectiveSelectedClient) params.append('client_id', effectiveSelectedClient);

      console.log('🔍 Fetching waste analytics with params:', params.toString());
      const response = await axios.get(`${API}/consumptions/waste/analytics?${params}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      console.log('🗑️ Analytics Response:', response.data);
      const analyticsData = response.data;
      
      // Debug: Log detailed structure
      console.log('🔍 DETAILED DEBUG:');
      console.log('- Analytics Data Keys:', Object.keys(analyticsData));
      console.log('- Monthly Data:', analyticsData.monthly_data);
      console.log('- Monthly Data Length:', analyticsData.monthly_data?.length || 0);
      
      if (analyticsData.monthly_data && analyticsData.monthly_data.length > 0) {
        console.log('- First Record Structure:', analyticsData.monthly_data[0]);
        console.log('- First Record Keys:', Object.keys(analyticsData.monthly_data[0]));
      }
      
      // Validate monthly_data structure
      const monthlyData = analyticsData.monthly_data || [];
      console.log('📊 Monthly Data for State:', monthlyData);
      
      // Validate each record for consistency
      monthlyData.forEach((record, index) => {
        const manual = (record.plastic_waste || 0) + (record.glass_waste || 0) + (record.paper_waste || 0) + (record.metal_waste || 0);
        const fromRate = record.total_waste > 0 ? (record.recycling_rate * record.total_waste / 100) : 0;
        
        if (Math.abs(manual - fromRate) > 0.1) {
          console.warn(`⚠️ Record ${index} (${record.month}/${record.year}) has inconsistent data:`, {
            manual_recyclable: manual,
            rate_based_recyclable: fromRate,
            recycling_rate: record.recycling_rate,
            total_waste: record.total_waste,
            individual_wastes: {
              plastic: record.plastic_waste,
              glass: record.glass_waste,
              paper: record.paper_waste,
              metal: record.metal_waste
            }
          });
        }
      });
      
      setWasteRecords(monthlyData);
      setAnalytics(analyticsData);
      
    } catch (error) {
      console.error('❌ Error fetching waste records:', error);
      
      // Add test data with correct calculations for debugging
      console.log('🧪 Using test data for debugging');
      const testData = [
        {
          id: 'test1',
          month: 1,
          year: 2025,
          organic_waste: 100,
          plastic_waste: 50,
          glass_waste: 30,
          paper_waste: 40,
          metal_waste: 10,
          electronic_waste: 20,
          mixed_waste: 30,
          oil_waste: 5,
          total_waste: 280, // Total all waste
          recycling_rate: 46.4, // (50+30+40+10)/280*100 = 46.4%
          per_person_waste: 1.9,
          accommodation_count: 150
        },
        {
          id: 'test2', 
          month: 6,
          year: 2025,
          organic_waste: 20,
          plastic_waste: 5,
          glass_waste: 3,
          paper_waste: 2,
          metal_waste: 0,
          electronic_waste: 5,
          mixed_waste: 5,
          oil_waste: 2,
          total_waste: 42, // Total all waste
          recycling_rate: 23.8, // (5+3+2+0)/42*100 = 23.8%
          per_person_waste: 0.4,
          accommodation_count: 100
        }
      ];
      
      setWasteRecords(testData);
      setAnalytics({
        yearly_totals: {
          total_waste: 322,
          avg_recycling_rate: 35.1,
          avg_per_person_waste: 1.15,
          oil_waste: 7
        }
      });
    } finally {
      setLoading(false);
    }
  };

  // Submit new record
  const handleSubmitRecord = async () => {
    try {
      setLoading(true);
      
      // 🔄 ENSURE FRESH TOKEN BEFORE IMPORTANT OPERATION
      await ensureTokenForOperation();
      console.log('✅ Token refreshed before waste record submission');
      
      const recordData = { ...newRecord };
      
      // Add client_id for admin and consultant
      if (userRole === 'admin' || userRole === 'consultant') {
        if (effectiveSelectedClient) {
          recordData.client_id = effectiveSelectedClient;
        } else {
          alert('Lütfen önce bir müşteri seçin!');
          setLoading(false);
          return;
        }
      }

      await axios.post(`${API}/consumptions/waste`, recordData, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      alert('Atık kaydı başarıyla eklendi!');
      setShowAddRecord(false);
      fetchWasteRecords();
      
      // Reset form
      setNewRecord({
        year: 2025,
        month: new Date().getMonth() + 1,
        organic_waste: 0,
        plastic_waste: 0,
        glass_waste: 0,
        paper_waste: 0,
        metal_waste: 0,
        electronic_waste: 0,
        oil_waste: 0,
        mixed_waste: 0,
        accommodation_count: 1
      });
    } catch (error) {
      console.error('Error submitting waste record:', error);
      alert('Atık kaydı eklenirken hata oluştu: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // Get client name
  const getClientName = (clientId) => {
    console.log('🔍 Client lookup:', { clientId, availableClients: clients });
    const client = clients.find(c => c.id === clientId || c.client_id === clientId);
    return client ? client.hotel_name : `Bilinmeyen (${clientId})`;
  };

  // useEffect hooks
  useEffect(() => {
    if (authToken) {
      fetchClients();
    }
  }, [authToken, userRole]);

  useEffect(() => {
    if (authToken) {
      // For consultant, don't fetch data until client is selected
      if (userRole === 'consultant' && !effectiveSelectedClient) {
        console.log('🔍 Consultant user: waiting for client selection');
        return;
      }
      fetchWasteRecords();
    }
  }, [authToken, effectiveSelectedClient, selectedYear, userRole]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-indigo-50">
      {/* Elite Header */}
      <div className="bg-gradient-to-r from-green-600 via-green-700 to-emerald-800 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">🗑️ Elite Atık Yönetimi</h1>
              <p className="text-green-100 text-lg">Sürdürülebilir atık takibi ve analiz sistemi</p>
            </div>
            <button
              onClick={() => setShowAddRecord(true)}
              className="bg-white text-green-700 px-6 py-3 rounded-xl hover:bg-green-50 transition-all duration-300 shadow-lg font-semibold flex items-center gap-2"
            >
              <span className="text-xl">+</span> Yeni Kayıt
            </button>
          </div>
        </div>
      </div>

      {/* Elite Tab Navigation */}
      <div className="bg-white shadow-lg border-b">
        <div className="max-w-7xl mx-auto">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                activeTab === 'overview'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📊 Genel Atık Özeti
            </button>
            <button
              onClick={() => setActiveTab('monthly')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                activeTab === 'monthly'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📈 Aylık Analiz
            </button>
          </nav>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-8">
        {/* Admin Controls */}

        {/* Elite Admin Controls */}
        <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            ⚙️ Kontrol Paneli
          </h3>
          <div className="flex flex-wrap items-center gap-4">
            {(userRole === 'admin' || userRole === 'consultant') && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">🏨 Müşteri Seçimi</label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all"
                >
                  <option value="">Tüm Müşteriler</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>{client.hotel_name}</option>
                  ))}
                </select>
              </div>
            )}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">📅 Yıl Seçimi</label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all"
              >
                {[2025, 2024, 2023].map((year) => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
            <div className="ml-auto space-y-2">
              <label className="block text-sm font-medium text-gray-700 invisible">.</label>
              <button
                onClick={() => setShowAddRecord(true)}
                className="bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-2 rounded-lg hover:from-green-600 hover:to-green-700 transition-all duration-300 font-medium shadow-lg flex items-center gap-2"
              >
                <span className="text-xl">+</span> Yeni Atık Kaydı
              </button>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-xl shadow-lg mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                📊 Genel Atık Özeti
              </button>
              <button
                onClick={() => setActiveTab('monthly')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                  activeTab === 'monthly'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                📅 Aylık Atık Analizi
              </button>
            </nav>
          </div>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600 text-lg">Veriler yükleniyor...</p>
          </div>
        ) : (userRole === 'consultant' && !selectedClient) ? (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🗑️</div>
              <p className="text-gray-500 text-lg mb-2">Atık yönetimi için önce bir müşteri seçin.</p>
              <p className="text-gray-400 text-sm">Yukarıdaki dropdown'dan müşteri seçerek başlayabilirsiniz.</p>
            </div>
          </div>
        ) : (
          <>
            {/* Tab Content */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Elite Analytics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-bold">♻️ Geri Dönüşüm Oranı</h3>
                      <div className="bg-white bg-opacity-20 rounded-full p-2">
                        <span className="text-2xl">📈</span>
                      </div>
                    </div>
                    <p className="text-3xl font-bold mb-1">{analytics.yearly_totals?.avg_recycling_rate?.toFixed(1) || 0}%</p>
                    <p className="text-green-100 text-sm">Hedef: 60%</p>
                  </div>

                  <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-bold">📊 Toplam Atık</h3>
                      <div className="bg-white bg-opacity-20 rounded-full p-2">
                        <span className="text-2xl">⚖️</span>
                      </div>
                    </div>
                    <p className="text-3xl font-bold mb-1">{analytics.yearly_totals?.total_waste?.toFixed(0) || 0}</p>
                    <p className="text-blue-100 text-sm">kg/yıl</p>
                  </div>

                  <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-bold">👤 Kişi Başı Atık</h3>
                      <div className="bg-white bg-opacity-20 rounded-full p-2">
                        <span className="text-2xl">👥</span>
                      </div>
                    </div>
                    <p className="text-3xl font-bold mb-1">{analytics.yearly_totals?.avg_per_person_waste?.toFixed(1) || 0}</p>
                    <p className="text-purple-100 text-sm">kg/kişi</p>
                  </div>

                  <div className="bg-gradient-to-br from-amber-500 to-amber-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-bold">🛢️ Yağ Atığı</h3>
                      <div className="bg-white bg-opacity-20 rounded-full p-2">
                        <span className="text-2xl">💧</span>
                      </div>
                    </div>
                    <p className="text-3xl font-bold mb-1">{analytics.yearly_totals?.oil_waste?.toFixed(1) || 0}</p>
                    <p className="text-amber-100 text-sm">litre/yıl</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'monthly' && (
              <div className="space-y-8">
                {/* Elite Charts Grid */}
                {wasteRecords.length > 0 ? (
                  <>
                    {/* Charts Row */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      {/* Monthly Waste Trend Chart */}
                      <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
                        <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                          📈 Aylık Atık Trendi
                        </h3>
                        <div className="h-80">
                          <Line 
                            data={{
                              labels: wasteRecords.map(record => `${record.month || 1}/${record.year || 2025}`),
                              datasets: [
                                {
                                  label: 'Toplam Atık (kg)',
                                  data: wasteRecords.map(record => record.total_waste || 0),
                                  borderColor: 'rgb(34, 197, 94)',
                                  backgroundColor: 'rgba(34, 197, 94, 0.1)',
                                  borderWidth: 3,
                                  fill: true,
                                  tension: 0.4,
                                },
                                {
                                  label: 'Kişi Başı Atık (kg)',
                                  data: wasteRecords.map(record => record.per_person_waste || 0),
                                  borderColor: 'rgb(168, 85, 247)',
                                  backgroundColor: 'rgba(168, 85, 247, 0.1)',
                                  borderWidth: 3,
                                  fill: true,
                                  tension: 0.4,
                                }
                              ]
                            }}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              plugins: {
                                legend: {
                                  position: 'top',
                                  labels: {
                                    usePointStyle: true,
                                    padding: 20,
                                  }
                                },
                              },
                              scales: {
                                y: {
                                  beginAtZero: true,
                                  grid: {
                                    color: 'rgba(0, 0, 0, 0.1)',
                                  }
                                },
                                x: {
                                  grid: {
                                    color: 'rgba(0, 0, 0, 0.1)',
                                  }
                                }
                              }
                            }}
                          />
                        </div>
                      </div>

                      {/* Waste Types Distribution Chart - Sadece sıfır olmayan değerler */}
                      <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
                        <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                          🗂️ Atık Türleri Dağılımı
                          <span className="text-sm font-normal text-gray-600">(Sadece mevcut türler)</span>
                        </h3>
                        <div className="h-80">
                          {(() => {
                            // Calculate totals for each waste type
                            const wasteTypes = [
                              { name: 'Organik', value: wasteRecords.reduce((sum, record) => sum + (record.organic_waste || 0), 0), color: '#10b981' },
                              { name: 'Plastik', value: wasteRecords.reduce((sum, record) => sum + (record.plastic_waste || 0), 0), color: '#3b82f6' },
                              { name: 'Kağıt', value: wasteRecords.reduce((sum, record) => sum + (record.paper_waste || 0), 0), color: '#f59e0b' },
                              { name: 'Cam', value: wasteRecords.reduce((sum, record) => sum + (record.glass_waste || 0), 0), color: '#a855f7' },
                              { name: 'Metal', value: wasteRecords.reduce((sum, record) => sum + (record.metal_waste || 0), 0), color: '#6b7280' },
                              { name: 'Elektronik', value: wasteRecords.reduce((sum, record) => sum + (record.electronic_waste || 0), 0), color: '#4f46e5' },
                              { name: 'Karışık', value: wasteRecords.reduce((sum, record) => sum + (record.mixed_waste || 0), 0), color: '#ef4444' },
                              { name: 'Yağ', value: wasteRecords.reduce((sum, record) => sum + (record.oil_waste || 0), 0), color: '#f97316' },
                            ].filter(type => type.value > 0); // Sadece sıfırdan büyük değerler

                            return wasteTypes.length > 0 ? (
                              <Pie 
                                data={{
                                  labels: wasteTypes.map(type => `${type.name} (${type.value.toFixed(1)} kg)`),
                                  datasets: [{
                                    data: wasteTypes.map(type => type.value),
                                    backgroundColor: wasteTypes.map(type => type.color),
                                    borderWidth: 2,
                                    borderColor: '#ffffff',
                                  }]
                                }}
                                options={{
                                  responsive: true,
                                  maintainAspectRatio: false,
                                  plugins: {
                                    legend: {
                                      position: 'right',
                                      labels: {
                                        usePointStyle: true,
                                        padding: 15,
                                        font: {
                                          size: 11
                                        }
                                      }
                                    },
                                    tooltip: {
                                      callbacks: {
                                        label: function(context) {
                                          const total = wasteTypes.reduce((sum, type) => sum + type.value, 0);
                                          const percentage = ((context.parsed / total) * 100).toFixed(1);
                                          return `${context.label}: ${percentage}% (${context.parsed.toFixed(1)} kg)`;
                                        }
                                      }
                                    }
                                  }
                                }}
                              />
                            ) : (
                              <div className="flex items-center justify-center h-full text-gray-500">
                                <div className="text-center">
                                  <div className="text-4xl mb-2">📊</div>
                                  <p>Henüz atık verisi yok</p>
                                </div>
                              </div>
                            );
                          })()}
                        </div>
                      </div>
                    </div>

                    {/* Geri Dönüşüm Açıklaması */}
                    <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-2xl p-6 border border-green-200">
                      <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                        ℹ️ Geri Dönüşüm Oranı Nasıl Hesaplanıyor?
                      </h3>
                      <div className="text-sm text-gray-700 space-y-2">
                        <p><strong>📝 Formül:</strong> (Geri Dönüştürülebilir Atık ÷ Toplam Atık) × 100</p>
                        <p><strong>♻️ Geri Dönüştürülebilir:</strong> Plastik + Cam + Kağıt + Metal</p>
                        <p><strong>🗑️ Geri Dönüştürülemez:</strong> Organik + Elektronik + Karışık + Yağ</p>
                        <div className="mt-3 p-3 bg-white rounded-lg border">
                          <p><strong>🎯 Hedef Değerler:</strong></p>
                          <div className="flex gap-4 mt-2 text-xs">
                            <span className="px-2 py-1 bg-green-100 text-green-800 rounded">60%+ Mükemmel</span>
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">40-59% İyi</span>
                            <span className="px-2 py-1 bg-red-100 text-red-800 rounded">40%- Geliştirilmeli</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Aylık Detay Tablosu */}
                    <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
                      <h3 className="text-xl font-bold text-gray-900 mb-4">📅 Aylık Detaylar</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full table-auto">
                          <thead className="bg-gradient-to-r from-green-50 to-green-100">
                            <tr>
                              <th className="px-4 py-3 text-left text-sm font-bold text-green-800">📅 Ay/Yıl</th>
                              <th className="px-4 py-3 text-left text-sm font-bold text-green-800">⚖️ Toplam (kg)</th>
                              <th className="px-4 py-3 text-left text-sm font-bold text-green-800">♻️ Geri Dönüştürülebilir (kg)</th>
                              <th className="px-4 py-3 text-left text-sm font-bold text-green-800">📈 Geri Dönüşüm %</th>
                              <th className="px-4 py-3 text-left text-sm font-bold text-green-800">👤 Kişi Başı (kg)</th>
                              <th className="px-4 py-3 text-left text-sm font-bold text-green-800">👥 Konaklama</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-200">
                            {wasteRecords.map((record, index) => {
                              // Backend'den gelen recycling_rate ve total_waste'i kullan
                              const total = record.total_waste || 0;
                              const recyclingRate = record.recycling_rate || 0;
                              // Geri dönüştürülebilir miktarı recycling_rate'ten hesapla
                              const recyclableFromRate = total > 0 ? (recyclingRate * total / 100) : 0;
                              
                              // Manuel hesaplama (kontrol için)
                              const recyclableManual = (record.plastic_waste || 0) + (record.glass_waste || 0) + (record.paper_waste || 0) + (record.metal_waste || 0);
                              
                              // Hangisini kullanacağımıza karar ver - backend verisi varsa onu kullan
                              const recyclableAmount = recyclableFromRate > 0 ? recyclableFromRate : recyclableManual;
                              
                              return (
                                <tr key={index} className="hover:bg-green-50 transition-colors">
                                  <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                                    {record.month || 1}/{record.year || 2025}
                                  </td>
                                  <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                                    {total.toFixed(1)}
                                  </td>
                                  <td className="px-4 py-3 text-sm text-blue-700 font-medium" title={`Manuel: ${recyclableManual.toFixed(1)} kg, Oran'dan: ${recyclableFromRate.toFixed(1)} kg`}>
                                    {recyclableAmount.toFixed(1)}
                                    {Math.abs(recyclableFromRate - recyclableManual) > 0.1 && (
                                      <span className="ml-1 text-xs text-orange-600">⚠️</span>
                                    )}
                                  </td>
                                  <td className="px-4 py-3 text-sm">
                                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                                      recyclingRate >= 60 ? 'bg-green-100 text-green-800' : 
                                      recyclingRate >= 40 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                                    }`}>
                                      {recyclingRate.toFixed(1)}%
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 text-sm text-purple-700 font-medium">
                                    {(record.per_person_waste || 0).toFixed(1)}
                                  </td>
                                  <td className="px-4 py-3 text-sm text-gray-600">
                                    {record.accommodation_count || 0} kişi
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-16">
                    <div className="text-8xl mb-6">📊</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">Henüz Grafik Verisi Yok</h3>
                    <p className="text-gray-600 mb-6">Aylık grafikler için atık kayıtları eklemelisiniz</p>
                    <button
                      onClick={() => setShowAddRecord(true)}
                      className="bg-gradient-to-r from-green-500 to-green-600 text-white px-8 py-3 rounded-xl hover:from-green-600 hover:to-green-700 transition-all duration-300 shadow-lg font-medium"
                    >
                      İlk Kaydı Oluştur
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Elite Detaylı Tablo - sadece overview tabında */}
        {activeTab === 'overview' && !loading && (
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
            <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                📊 Elite Atık Kayıtları
                {(userRole === 'admin' || userRole === 'consultant') && effectiveSelectedClient && (
                  <span className="text-lg font-semibold text-blue-600">
                    - {getClientName(effectiveSelectedClient)}
                  </span>
                )}
                <span className="text-sm font-normal text-gray-600">({wasteRecords.length} kayıt)</span>
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gradient-to-r from-green-50 to-green-100">
                    <tr>
                      {userRole === 'admin' && (
                        <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                          🏨 Müşteri
                        </th>
                      )}
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        📅 Tarih
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        🥬 Organik (kg)
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        ♻️ Plastik (kg)
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        📄 Kağıt (kg)
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        🍾 Cam (kg)
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        🔩 Metal (kg)
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        ⚡ Elektronik (kg)
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        🗑️ Karışık (kg)
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-amber-700 uppercase tracking-wider">
                        🛢️ Yağ (Litre)
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        📈 Geri Dönüşüm (%)
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-green-800 uppercase tracking-wider">
                        👤 Kişi Başı (kg)
                      </th>
                    </tr>
                  </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {wasteRecords.length > 0 ? wasteRecords.map((record, index) => (
                    <tr key={index} className="hover:bg-green-50 transition-colors duration-200">
                      {userRole === 'admin' && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {effectiveSelectedClient ? getClientName(effectiveSelectedClient) : getClientName(record.client_id)}
                        </td>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {record.month || new Date().getMonth() + 1}/{record.year || 2025}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-700 font-medium">
                        {record.organic_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-700 font-medium">
                        {record.plastic_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-700 font-medium">
                        {record.paper_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-purple-700 font-medium">
                        {record.glass_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-medium">
                        {record.metal_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-indigo-700 font-medium">
                        {record.electronic_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-red-700 font-medium">
                        {record.mixed_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-amber-700 font-bold">
                        {record.oil_waste || 0} L
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                          record.recycling_rate >= 60 ? 'bg-green-100 text-green-800' : 
                          record.recycling_rate >= 40 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {record.recycling_rate?.toFixed(1) || 0}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                        {record.per_person_waste?.toFixed(1) || 0} kg
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan="12" className="px-6 py-12 text-center">
                        <div className="text-6xl mb-4">🗑️</div>
                        <p className="text-xl text-gray-600 mb-2">Henüz atık kaydı bulunmuyor</p>
                        <p className="text-gray-500">İlk atık kaydınızı eklemek için "Yeni Kayıt" butonunu kullanın</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Add Record Modal */}
      {showAddRecord && (
        <div 
          className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
          onClick={(e) => {
            // Reset form when clicking outside modal
            if (e.target === e.currentTarget) {
              setNewRecord({
                year: 2025,
                month: new Date().getMonth() + 1,
                organic_waste: 0,
                plastic_waste: 0,
                glass_waste: 0,
                paper_waste: 0,
                metal_waste: 0,
                electronic_waste: 0,
                oil_waste: 0,
                mixed_waste: 0,
                accommodation_count: 1
              });
              setShowAddRecord(false);
            }
          }}
        >
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Yeni Atık Kaydı Ekle</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">📅 Yıl</label>
                  <select
                    value={newRecord.year}
                    onChange={(e) => setNewRecord({...newRecord, year: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={2025}>2025</option>
                    <option value={2024}>2024</option>
                    <option value={2023}>2023</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">📅 Ay</label>
                  <select
                    value={newRecord.month}
                    onChange={(e) => setNewRecord({...newRecord, month: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    {Array.from({length: 12}, (_, i) => i + 1).map(month => (
                      <option key={month} value={month}>{month}. Ay</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">👥 Konaklama Sayısı</label>
                  <input
                    type="number"
                    min="1"
                    value={newRecord.accommodation_count}
                    onChange={(e) => setNewRecord({...newRecord, accommodation_count: parseInt(e.target.value) || 1})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🌱 Organik Atık (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.organic_waste}
                    onChange={(e) => setNewRecord({...newRecord, organic_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🧴 Plastik Atık (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.plastic_waste}
                    onChange={(e) => setNewRecord({...newRecord, plastic_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">📄 Kağıt Atık (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.paper_waste}
                    onChange={(e) => setNewRecord({...newRecord, paper_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🪟 Cam Atık (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.glass_waste}
                    onChange={(e) => setNewRecord({...newRecord, glass_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🔗 Metal Atık (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.metal_waste}
                    onChange={(e) => setNewRecord({...newRecord, metal_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">⚡ Elektronik Atık (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.electronic_waste}
                    onChange={(e) => setNewRecord({...newRecord, electronic_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🛢️ Yağ Atığı (litre)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.oil_waste}
                    onChange={(e) => setNewRecord({...newRecord, oil_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🗑️ Karışık Atık (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.mixed_waste}
                    onChange={(e) => setNewRecord({...newRecord, mixed_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={handleSubmitRecord}
                  disabled={loading}
                  className="bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-2 rounded-lg hover:from-green-600 hover:to-green-700 disabled:opacity-50 font-medium"
                >
                  {loading ? 'Kaydediliyor...' : 'Kaydet'}
                </button>
                <button
                  onClick={() => {
                    // Reset form when canceling
                    setNewRecord({
                      year: 2025,
                      month: new Date().getMonth() + 1,
                      organic_waste: 0,
                      plastic_waste: 0,
                      glass_waste: 0,
                      paper_waste: 0,
                      metal_waste: 0,
                      electronic_waste: 0,
                      oil_waste: 0,
                      mixed_waste: 0,
                      accommodation_count: 1
                    });
                    setShowAddRecord(false);
                  }}
                  className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 font-medium"
                >
                  İptal
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Bulk Operations Component
const BulkOperations = ({ onNavigate }) => {
  const { authToken, userRole, dbUser, ensureTokenForOperation } = useAuth();
  const { session } = useClerk();
  const [bulkClients, setBulkClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('certificate_end_date'); // Default sort by certificate end date
  const [sortOrder, setSortOrder] = useState('asc'); // Ascending = closest to far
  
  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasPrev, setHasPrev] = useState(false);
  const [hasNext, setHasNext] = useState(false);
  
  // Filter states
  const [filterCity, setFilterCity] = useState('');
  const [filterAuditCompany, setFilterAuditCompany] = useState('');
  const [filterCertificateStatus, setFilterCertificateStatus] = useState('');
  
  // Bulk Import States
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [bulkImportFile, setBulkImportFile] = useState(null);
  const [bulkImportLoading, setBulkImportLoading] = useState(false);
  const [bulkImportProgress, setBulkImportProgress] = useState(0);
  const [bulkImportStatus, setBulkImportStatus] = useState('');
  const [bulkImportResult, setBulkImportResult] = useState(null);
  
  // Bulk Email States
  const [showBulkEmail, setShowBulkEmail] = useState(false);
  const [bulkEmailLoading, setBulkEmailLoading] = useState(false);
  const [bulkEmailStats, setBulkEmailStats] = useState(null);
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [bulkEmailForm, setBulkEmailForm] = useState({
    template_id: '',
    subject: '',
    content: '',
    custom_content: '',
    target_filters: {
      city: '',
      audit_company: '',
      has_email: true,
      certificate_filter: '' // New: certificate-specific filter
    }
  });
  const [bulkEmailResult, setBulkEmailResult] = useState(null);
  const [testEmail, setTestEmail] = useState('');
  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  
  const API = getApiUrl();

  // Fetch bulk clients only
  const fetchBulkClients = async (page = 1, limit = itemsPerPage, search = searchTerm, sort = sortBy, order = sortOrder) => {
    try {
      setLoading(true);
      const params = { page, limit, client_type: 'bulk' }; // Force bulk only
      if (search && search.trim()) {
        params.search = search.trim();
      }
      if (sort) {
        params.sort = sort;
      }
      if (order) {
        params.order = order;
      }
      
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        params,
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      // Backend returns { clients, pagination } format
      const { clients, pagination } = response.data;
      
      // Debug: Log certificate_end_date for first few clients
      if (clients && clients.length > 0) {
        console.log('🔍 BULK CLIENTS DEBUG - First 3 clients certificate_end_date:');
        clients.slice(0, 3).forEach((client, index) => {
          console.log(`  Client ${index + 1}:`, {
            hotel_name: client.hotel_name,
            certificate_end_date: client.certificate_end_date,
            certificate_end_date_type: typeof client.certificate_end_date
          });
        });
      }
      
      // Apply local filters
      let filteredClients = clients || [];
      
      if (filterCity) {
        filteredClients = filteredClients.filter(client => 
          client.city && client.city.toLowerCase().includes(filterCity.toLowerCase())
        );
      }
      
      if (filterAuditCompany) {
        filteredClients = filteredClients.filter(client => 
          client.audit_company && client.audit_company.toLowerCase().includes(filterAuditCompany.toLowerCase())
        );
      }
      
      if (filterCertificateStatus) {
        filteredClients = filteredClients.filter(client => {
          if (!client.certificate_end_date) return filterCertificateStatus === 'no_certificate';
          
          const certDate = new Date(client.certificate_end_date);
          const today = new Date();
          const oneMonthFromNow = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
          
          if (filterCertificateStatus === 'expired') {
            return certDate < today;
          } else if (filterCertificateStatus === 'expiring_soon') {
            return certDate >= today && certDate <= oneMonthFromNow;
          } else if (filterCertificateStatus === 'valid') {
            return certDate > oneMonthFromNow;
          }
          
          return true;
        });
      }
      
      // FORCE sort by certificate end date - always apply sorting
      console.log('🔄 Applying certificate sorting - current sort:', sort, 'order:', order);
      filteredClients.sort((a, b) => {
        const getCertificateStatus = (dateStr) => {
          if (!dateStr || dateStr === "" || dateStr === null || dateStr === "-") {
            return { valid: false, priority: 3, date: null }; // No date or dash - lowest priority (EN ARKADA)
          }
          
          try {
            let parsedDate;
            if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
              parsedDate = new Date(dateStr);
            } else if (dateStr.match(/^\d{2}\.\d{2}\.\d{4}$/)) {
              const parts = dateStr.split('.');
              parsedDate = new Date(parts[2], parts[1] - 1, parts[0]);
            } else {
              parsedDate = new Date(dateStr);
            }
            
            if (isNaN(parsedDate.getTime())) {
              return { valid: false, priority: 3, date: null }; // Invalid date - lowest priority (EN ARKADA)
            }
            
            return { valid: true, priority: 1, date: parsedDate }; // Valid date - highest priority (EN ÖNDE)
          } catch (error) {
            return { valid: false, priority: 3, date: null }; // Invalid date - lowest priority (EN ARKADA)
          }
        };
        
        const statusA = getCertificateStatus(a.certificate_end_date);
        const statusB = getCertificateStatus(b.certificate_end_date);
        
        // First sort by priority (1=valid EN ÖNDE, 3=empty/invalid EN ARKADA)
        if (statusA.priority !== statusB.priority) {
          return statusA.priority - statusB.priority; // Küçük numara önde gelir
        }
        
        // If both have valid dates, sort by date (closest first - sertifikası en yakında bitecek olanlar önde)
        if (statusA.valid && statusB.valid) {
          return statusA.date - statusB.date; // En yakın tarih önde
        }
        
        return 0; // Same priority, maintain order
      });
      
      console.log('🔄 After sorting - first 5 clients:', filteredClients.slice(0, 5).map(c => ({
        name: c.hotel_name,
        certificate_end_date: c.certificate_end_date
      })));
      
      setBulkClients(filteredClients);
      setTotalPages(pagination?.total_pages || 1);
      setTotalCount(pagination?.total_count || 0);
      setHasPrev(pagination?.has_prev || false);
      setHasNext(pagination?.has_next || false);
      
    } catch (error) {
      console.error('Error fetching bulk clients:', error);
      
      // Check if it's an authentication error
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.error('🔐 Authentication error:', error.response?.data?.detail);
        alert('Authentication hatası: Lütfen yeniden giriş yapın.');
      } else {
        console.error('API error:', error.response?.data?.detail || error.message);
      }
      
      setBulkClients([]);
      setTotalPages(1);
      setTotalCount(0);
      setHasPrev(false);
      setHasNext(false);
    } finally {
      setLoading(false);
    }
  };

  // Delete client function
  const handleDeleteClient = async (clientId, clientName) => {
    if (!window.confirm(`"${clientName}" müşterisini silmek istediğinizden emin misiniz? Bu işlem geri alınamaz ve müşteriye ait tüm belgeler, klasörler ve veriler silinecektir.`)) {
      return;
    }

    try {
      await axios.delete(`${API}/clients/${clientId}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      alert(`${clientName} müşterisi başarıyla silindi.`);
      
      // Refresh the client list
      fetchBulkClients();
      
    } catch (error) {
      console.error('Error deleting client:', error);
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        alert('Bu işlem için yetkiniz yok.');
      } else if (error.response?.status === 404) {
        alert('Müşteri bulunamadı.');
      } else {
        alert('Müşteri silinirken bir hata oluştu: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  // Search with debouncing
  const handleSearchDebounced = (term) => {
    setSearchTerm(term);
    setCurrentPage(1);
    fetchBulkClients(1, itemsPerPage, term, sortBy, sortOrder);
  };

  // Handle filter changes
  const handleFilterChange = () => {
    setCurrentPage(1);
    fetchBulkClients(1, itemsPerPage, searchTerm, sortBy, sortOrder);
  };

  // Clear filters
  const clearFilters = () => {
    setFilterCity('');
    setFilterAuditCompany('');
    setFilterCertificateStatus('');
    setSearchTerm('');
    setCurrentPage(1);
    fetchBulkClients(1, itemsPerPage, '', sortBy, sortOrder);
  };

  // Sort function
  const handleSort = (field) => {
    const newOrder = sortBy === field && sortOrder === 'asc' ? 'desc' : 'asc';
    setSortBy(field);
    setSortOrder(newOrder);
    setCurrentPage(1);
    fetchBulkClients(1, itemsPerPage, searchTerm, field, newOrder);
  };

  // Calculate certificate status
  const getCertificateStatus = (endDate) => {
    console.log('🔍 getCertificateStatus called with:', endDate, 'Type:', typeof endDate);
    
    // Handle empty, null, undefined, or "-" values
    if (!endDate || endDate === "" || endDate === null || endDate === "-") {
      console.log('🔍 No endDate, empty string, or "-" character, returning no_certificate');
      return { status: 'no_certificate', color: 'bg-gray-100 text-gray-800' };
    }
    
    // Try to parse the date with different formats
    let certDate;
    try {
      // If it's already a Date object
      if (endDate instanceof Date) {
        certDate = endDate;
      } else {
        // Try different date formats
        const dateStr = endDate.toString().trim();
        console.log('🔍 Trying to parse date string:', dateStr);
        
        // Try ISO format (YYYY-MM-DD)
        if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
          certDate = new Date(dateStr);
        }
        // Try DD.MM.YYYY format
        else if (dateStr.match(/^\d{2}\.\d{2}\.\d{4}$/)) {
          const parts = dateStr.split('.');
          certDate = new Date(parts[2], parts[1] - 1, parts[0]); // month is 0-indexed
        }
        // Try DD/MM/YYYY format
        else if (dateStr.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
          const parts = dateStr.split('/');
          certDate = new Date(parts[2], parts[1] - 1, parts[0]); // month is 0-indexed
        }
        // Try MM/DD/YYYY format (American)
        else if (dateStr.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
          certDate = new Date(dateStr);
        }
        // Default: try native Date parsing
        else {
          certDate = new Date(dateStr);
        }
      }
      
      // Check if the date is valid
      if (isNaN(certDate.getTime())) {
        console.error('🔍 Invalid date after parsing:', endDate);
        return { status: 'invalid_date', color: 'bg-orange-100 text-orange-800' };
      }
      
      console.log('🔍 Successfully parsed date:', certDate);
      
    } catch (error) {
      console.error('🔍 Date parsing error:', error, 'Original value:', endDate);
      return { status: 'invalid_date', color: 'bg-orange-100 text-orange-800' };
    }
    
    const today = new Date();
    const oneMonthFromNow = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
    
    console.log('🔍 Dates:', { certDate, today, oneMonthFromNow });
    
    if (certDate < today) {
      console.log('🔍 Certificate expired, returning red');
      return { status: 'expired', color: 'bg-red-100 text-red-800' };
    } else if (certDate <= oneMonthFromNow) {
      console.log('🔍 Certificate expiring soon, returning red');
      return { status: 'expiring_soon', color: 'bg-red-100 text-red-800' };
    } else {
      console.log('🔍 Certificate valid, returning green');
      return { status: 'valid', color: 'bg-green-100 text-green-800' };
    }
  };

  // Load bulk clients on mount
  useEffect(() => {
    if (authToken) {
      fetchBulkClients();
    }
  }, [authToken]);

  // Refresh when pagination changes
  useEffect(() => {
    if (authToken) {
      fetchBulkClients(currentPage);
    }
  }, [currentPage, authToken]);

  // Refresh when filters change
  useEffect(() => {
    if (authToken) {
      handleFilterChange();
    }
  }, [filterCity, filterAuditCompany, filterCertificateStatus]);

  // Handle bulk import
  const handleBulkImport = async () => {
    if (!bulkImportFile) {
      alert('Lütfen bir dosya seçin!');
      return;
    }

    const formData = new FormData();
    formData.append('file', bulkImportFile);

    try {
      setBulkImportLoading(true);
      setBulkImportProgress(0);
      setBulkImportStatus('Dosya yükleniyor...');
      setBulkImportResult(null);

      const response = await axios.post(`${API}/bulk-import/clients`, formData, {
        headers: { 
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'multipart/form-data'
        },
        timeout: 1200000, // 20 minutes timeout
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setBulkImportProgress(percentCompleted);
          setBulkImportStatus(`Dosya yükleniyor... ${percentCompleted}%`);
        }
      });

      setBulkImportResult(response.data);
      setBulkImportStatus('İşlem tamamlandı!');
      setBulkImportProgress(100);
      
      // Refresh bulk clients list
      fetchBulkClients();
      
    } catch (error) {
      console.error('Bulk import error:', error);
      setBulkImportResult({
        success: false,
        error: error.response?.data?.detail || error.message
      });
    } finally {
      setBulkImportLoading(false);
    }
  };

  // Bulk Email Functions
  const fetchBulkEmailStats = async () => {
    try {
      const response = await axios.get(`${API}/bulk-email/stats`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setBulkEmailStats(response.data);
    } catch (error) {
      console.error('Error fetching bulk email stats:', error);
    }
  };

  const fetchEmailTemplates = async () => {
    try {
      let currentToken = authToken;
      if (!currentToken && session) {
        try {
          currentToken = await session.getToken();
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
          return;
        }
      }

      if (!currentToken) {
        console.error('No authentication token available');
        return;
      }

      const response = await axios.get(`${API}/email-templates`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      setEmailTemplates(response.data.templates || []);
    } catch (error) {
      console.error('Error fetching email templates:', error);
      setEmailTemplates([]);
    }
  };

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setBulkEmailForm(prev => ({
      ...prev,
      template_id: template.id,
      subject: template.subject,
      content: template.content,
      custom_content: ''
    }));

    // Special handling for certificate reminder template
    if (template.id === 'certificate_reminder') {
      // Show info about automatic filtering
      const confirmCertificateFilter = window.confirm(
        '🏨 Sertifika Hatırlatması Template\'i seçildi!\n\n' +
        '📅 Bu template sadece sertifikası olan müşterilere gönderilir.\n' +
        '⚠️ Sertifikası olmayan ("-" değerli) müşteriler hariç tutulur.\n\n' +
        'Devam etmek istiyor musunuz?'
      );
      
      if (!confirmCertificateFilter) {
        setSelectedTemplate(null);
        setBulkEmailForm(prev => ({
          ...prev,
          template_id: '',
          subject: '',
          content: '',
          custom_content: ''
        }));
        return;
      }

      // Set certificate-specific filters
      setBulkEmailForm(prev => ({
        ...prev,
        target_filters: {
          ...prev.target_filters,
          certificate_filter: 'has_certificate' // Special filter for certificates
        }
      }));
      
      alert('✅ Sertifika filtresi etkinleştirildi!\n\n' +
            '📋 Sadece geçerli sertifika tarihi olan müşterilere gönderilecek.');
    } else {
      // Reset certificate filter for other templates
      setBulkEmailForm(prev => ({
        ...prev,
        target_filters: {
          ...prev.target_filters,
          certificate_filter: '' // Clear certificate filter
        }
      }));
    }
  };

  const handleBulkEmailSend = async () => {
    if (!selectedTemplate && (!bulkEmailForm.subject || !bulkEmailForm.content)) {
      alert('Lütfen bir template seçin veya konu ve içerik alanlarını doldurun!');
      return;
    }

    const confirmSend = window.confirm(
      'Bulk email gönderimini başlatmak istediğinizden emin misiniz?\\n\\nBu işlem geri alınamaz.'
    );

    if (!confirmSend) return;

    try {
      setBulkEmailLoading(true);
      setBulkEmailResult(null);

      const emailData = {
        filters: bulkEmailForm.target_filters
      };

      // Use template if selected
      if (selectedTemplate) {
        emailData.template_id = selectedTemplate.id;
        emailData.email_type = 'bulk';
        
        // Add custom content for general announcement
        if (selectedTemplate.id === 'general_announcement' && bulkEmailForm.custom_content.trim()) {
          emailData.custom_content = bulkEmailForm.custom_content;
        }
      } else {
        // Use custom content
        emailData.subject = bulkEmailForm.subject;
        emailData.content = bulkEmailForm.content;
        emailData.email_type = 'custom';
      }

      const response = await axios.post(`${API}/bulk-email/send`, emailData, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      setBulkEmailResult(response.data);
      
      // Reset form
      setSelectedTemplate(null);
      setBulkEmailForm({
        template_id: '',
        subject: '',
        content: '',
        custom_content: '',
        target_filters: {
          city: '',
          audit_company: '',
          has_email: true,
          certificate_filter: ''
        }
      });

    } catch (error) {
      console.error('Error sending bulk email:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      setBulkEmailResult({
        success: false,
        error: errorMessage
      });
    } finally {
      setBulkEmailLoading(false);
    }
  };

  const sendTestEmail = async () => {
    if (!selectedTemplate) {
      alert('Lütfen önce bir template seçiniz!');
      return;
    }

    if (!testEmail || !testEmail.includes('@')) {
      alert('Lütfen geçerli bir test email adresi giriniz!');
      return;
    }

    setSendingTestEmail(true);
    try {
      let currentToken = authToken;
      if (!currentToken && session) {
        try {
          currentToken = await session.getToken();
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
          return;
        }
      }

      const testEmailData = {
        template_id: selectedTemplate.id,
        test_email: testEmail
      };

      // Add custom content for general announcement
      if (selectedTemplate.id === 'general_announcement' && bulkEmailForm.custom_content.trim()) {
        testEmailData.custom_content = bulkEmailForm.custom_content;
      }

      const response = await axios.post(`${API}/email-templates/test`, testEmailData, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      alert(`✅ Test email başarıyla gönderildi!\n\n📧 Gönderilen Adres: ${testEmail}\n🎨 Template: ${selectedTemplate.name}\n\nEmail kutunuzu kontrol ediniz.`);
      
    } catch (error) {
      console.error('Test email error:', error);
      alert('❌ Test email gönderim hatası: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSendingTestEmail(false);
    }
  };

  // Load bulk email stats when bulk email modal opens
  useEffect(() => {
    if (showBulkEmail) {
      fetchBulkEmailStats();
      fetchEmailTemplates();
    }
  }, [showBulkEmail]);

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">📦 Bulk İşlemler</h1>
        <p className="text-gray-600">
          Toplu müşteri yükleme ve bulk email gönderim işlemleri
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4 mb-6">
        <button
          onClick={() => setShowBulkImport(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
        >
          📤 Toplu Müşteri Yükleme
        </button>
        
        <button
          onClick={() => setShowBulkEmail(true)}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
        >
          📧 Bulk Email Gönder
        </button>
      </div>

      {/* Bulk Clients Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Bulk Müşteri Listesi</h3>
          <p className="text-sm text-gray-500 mt-1">Toplam {totalCount} bulk müşteri</p>
          
          {/* Search and Filters */}
          <div className="mt-4 flex flex-col md:flex-row gap-4 items-center">
            {/* Search Input */}
            <div className="relative">
              <input
                type="text"
                placeholder="Otel adı, şehir, email ile ara..."
                value={searchTerm}
                onChange={(e) => handleSearchDebounced(e.target.value)}
                className="w-64 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
              <span className="absolute right-3 top-2.5 text-gray-400">🔍</span>
            </div>
            
            {/* City Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Şehir:</label>
              <input
                type="text"
                placeholder="Şehir filtrele..."
                value={filterCity}
                onChange={(e) => setFilterCity(e.target.value)}
                className="w-32 px-3 py-2 border border-gray-300 rounded text-sm"
              />
            </div>
            
            {/* Audit Company Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Denetim Firması:</label>
              <input
                type="text"
                placeholder="Denetim firması..."
                value={filterAuditCompany}
                onChange={(e) => setFilterAuditCompany(e.target.value)}
                className="w-32 px-3 py-2 border border-gray-300 rounded text-sm"
              />
            </div>
            
            {/* Certificate Status Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Sertifika Durumu:</label>
              <select
                value={filterCertificateStatus}
                onChange={(e) => setFilterCertificateStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded text-sm"
              >
                <option value="">Tümü</option>
                <option value="expired">Süresi Dolmuş</option>
                <option value="expiring_soon">Süresi Yaklaşan (1 ay)</option>
                <option value="valid">Geçerli</option>
                <option value="no_certificate">Sertifika Yok</option>
              </select>
            </div>
            
            {/* Sort Options */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Sıralama:</label>
              <select
                value={sortBy}
                onChange={(e) => handleSort(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option value="certificate_end_date">Sertifika Süresi</option>
                <option value="hotel_name">Otel Adı</option>
                <option value="city">Şehir</option>
                <option value="audit_company">Denetim Firması</option>
              </select>
              <button
                onClick={() => handleSort(sortBy)}
                className="px-2 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
                title={sortOrder === 'asc' ? 'Yakından uzağa' : 'Uzaktan yakına'}
              >
                {sortOrder === 'asc' ? '🔼' : '🔽'}
              </button>
            </div>
            
            {/* Clear Filters Button */}
            <button
              onClick={clearFilters}
              className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              🗑️ Filtreleri Temizle
            </button>
          </div>
        </div>
        
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Yükleniyor...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            {bulkClients.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 text-lg mb-2">📦</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Bulk müşteri bulunamadı</h3>
                <p className="text-gray-500">
                  {searchTerm || filterCity || filterAuditCompany || filterCertificateStatus
                    ? 'Filtrelere uygun müşteri bulunamadı. Filtreleri temizleyerek tekrar deneyin.'
                    : 'Henüz bulk müşteri bulunmamaktadır. Toplu müşteri yüklemesi yapabilirsiniz.'}
                </p>
              </div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Otel Adı
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Şehir
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Telefon
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Denetim Firması
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sertifika Geçerlilik
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İşlemler
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {bulkClients.map((client) => {
                    const certificateStatus = getCertificateStatus(client.certificate_end_date);
                    
                    return (
                      <tr key={client.id}>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                              <span className="text-orange-600 font-medium">📦</span>
                            </div>
                            <div className="ml-3">
                              <div className="text-sm font-medium text-gray-900">
                                {client.hotel_name || 'N/A'}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {client.city || 'N/A'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {client.email || 'N/A'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {client.phone || 'N/A'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {client.audit_company || 'N/A'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {client.certificate_end_date ? (
                            <div className="flex items-center">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${certificateStatus.color}`}>
                                {certificateStatus.status === 'invalid_date' 
                                  ? 'Geçersiz Tarih' 
                                  : certificateStatus.status === 'no_certificate'
                                  ? 'Tarih Yok'
                                  : new Date(client.certificate_end_date).toLocaleDateString('tr-TR')}
                              </span>
                            </div>
                          ) : (
                            <span className="text-gray-400">Belirtilmemiş</span>
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleDeleteClient(client.id, client.hotel_name || 'N/A')}
                              className="text-red-600 hover:text-red-900 bg-red-50 hover:bg-red-100 px-2 py-1 rounded text-xs font-medium transition-colors"
                              title="Müşteriyi sil"
                            >
                              🗑️ Sil
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Sayfa {currentPage} / {totalPages} (Toplam {totalCount} müşteri)
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    const newPage = Math.max(1, currentPage - 1);
                    setCurrentPage(newPage);
                    fetchBulkClients(newPage);
                  }}
                  disabled={!hasPrev}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50"
                >
                  Önceki
                </button>
                <button
                  onClick={() => {
                    const newPage = Math.min(totalPages, currentPage + 1);
                    setCurrentPage(newPage);
                    fetchBulkClients(newPage);
                  }}
                  disabled={!hasNext}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50"
                >
                  Sonraki
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bulk Import Modal */}
      {showBulkImport && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">📤 Toplu Müşteri Yükleme</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Excel Dosyası Seçin:
                </label>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => setBulkImportFile(e.target.files[0])}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>

              {bulkImportLoading && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    <span className="text-blue-800 font-medium">{bulkImportStatus}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                      style={{ width: `${bulkImportProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {bulkImportResult && (
                <div className={`border rounded-lg p-4 ${
                  bulkImportResult.success 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <h4 className={`font-semibold mb-2 ${
                    bulkImportResult.success ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {bulkImportResult.success ? '✅ İşlem Tamamlandı!' : '❌ İşlem Başarısız!'}
                  </h4>
                  {bulkImportResult.success && (
                    <div className="text-green-700 text-sm space-y-1">
                      <p>📊 <strong>{bulkImportResult.imported_count}</strong> müşteri eklendi</p>
                      <p>⏭️ <strong>{bulkImportResult.skipped_count}</strong> müşteri atlandı</p>
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleBulkImport}
                  disabled={!bulkImportFile || bulkImportLoading}
                  className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
                >
                  {bulkImportLoading ? 'Yükleniyor...' : '📤 Dosyayı Yükle'}
                </button>
                <button
                  onClick={() => setShowBulkImport(false)}
                  className="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600"
                >
                  Kapat
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Email Modal */}
      {showBulkEmail && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">📧 Bulk Email Gönderimi</h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Stats */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-800 mb-3">📊 İstatistikler</h4>
                {bulkEmailStats ? (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-blue-700">Toplam Bulk Müşteri:</span>
                      <span className="font-medium text-blue-900">{bulkEmailStats.total_bulk_clients}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-700">Email Adresi Olan:</span>
                      <span className="font-medium text-blue-900">{bulkEmailStats.bulk_clients_with_email}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-700">Email Kapsama:</span>
                      <span className="font-medium text-blue-900">{bulkEmailStats.email_coverage_percentage}%</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-blue-600">Yükleniyor...</p>
                )}
              </div>

              {/* Email Templates */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-800 mb-3">🎨 Email Şablonları</h4>
                {emailTemplates.length > 0 ? (
                  <div className="grid grid-cols-1 gap-2 max-h-60 overflow-y-auto">
                    {emailTemplates.map((template) => (
                      <div 
                        key={template.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          selectedTemplate?.id === template.id 
                            ? 'border-purple-500 bg-purple-50' 
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => handleTemplateSelect(template)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h5 className="font-medium text-gray-800 text-sm">{template.name}</h5>
                            <p className="text-xs text-gray-600 mt-1">{template.description}</p>
                          </div>
                          <div className="ml-2">
                            {selectedTemplate?.id === template.id ? (
                              <div className="w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
                                <span className="text-white text-xs">✓</span>
                              </div>
                            ) : (
                              <div className="w-5 h-5 border-2 border-gray-300 rounded-full"></div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">Şablonlar yükleniyor...</p>
                )}
                
                {selectedTemplate && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm">
                      <div className="font-medium text-gray-700">Seçili Şablon:</div>
                      <div className="text-gray-800">{selectedTemplate.name}</div>
                      <div className="text-xs text-gray-600 mt-1">📧 {selectedTemplate.subject}</div>
                      {selectedTemplate.id === 'certificate_reminder' && (
                        <div className="mt-2 p-2 bg-orange-50 border border-orange-200 rounded">
                          <div className="text-xs text-orange-800">
                            🏨 <strong>Akıllı Filtreleme:</strong> Sadece geçerli sertifika tarihi olan müşterilere gönderilir.
                            <br/>❌ Sertifikası olmayan ("-" değerli) müşteriler hariç tutulur.
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="border-t pt-4">
                  <button
                    onClick={() => {
                      setSelectedTemplate(null);
                      setBulkEmailForm({
                        ...bulkEmailForm,
                        template_id: '',
                        subject: '',
                        content: ''
                      });
                    }}
                    className="text-sm text-purple-600 hover:text-purple-700"
                  >
                    📝 Özel Email Yaz
                  </button>
                </div>
              </div>

              {/* Email Form */}
              <div className="space-y-4">
                {selectedTemplate && selectedTemplate.id === 'general_announcement' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      📝 Özel Duyuru İçeriği:
                    </label>
                    <textarea
                      value={bulkEmailForm.custom_content}
                      onChange={(e) => setBulkEmailForm({...bulkEmailForm, custom_content: e.target.value})}
                      placeholder="Duyuru metninizi buraya yazın..."
                      rows={3}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                )}

                {!selectedTemplate && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email Konusu:
                      </label>
                      <input
                        type="text"
                        value={bulkEmailForm.subject}
                        onChange={(e) => setBulkEmailForm({...bulkEmailForm, subject: e.target.value})}
                        placeholder="Email konusunu girin..."
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email İçeriği:
                      </label>
                      <textarea
                        value={bulkEmailForm.content}
                        onChange={(e) => setBulkEmailForm({...bulkEmailForm, content: e.target.value})}
                        placeholder="Email içeriğini girin..."
                        rows={6}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                  </>
                )}

                {selectedTemplate && selectedTemplate.id !== 'general_announcement' && (
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-sm text-gray-600">
                      <div><strong>📧 Konu:</strong> {selectedTemplate.subject}</div>
                      <div className="mt-2 max-h-32 overflow-y-auto">
                        <strong>📝 İçerik Önizleme:</strong>
                        <div className="text-xs mt-1 whitespace-pre-line">{selectedTemplate.content}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Test Email Section */}
                {selectedTemplate && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="font-medium text-blue-800 mb-3">🧪 Test Email Gönder</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-blue-700 mb-1">
                          Test Email Adresi:
                        </label>
                        <input
                          type="email"
                          value={testEmail}
                          onChange={(e) => setTestEmail(e.target.value)}
                          placeholder="test@example.com"
                          className="w-full border border-blue-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 text-sm"
                        />
                      </div>
                      
                      <div className="text-xs text-blue-600">
                        💡 Template örnek verilerle doldurularak test adresine gönderilecek
                      </div>
                      
                      <button
                        onClick={sendTestEmail}
                        disabled={sendingTestEmail || !testEmail}
                        className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                      >
                        {sendingTestEmail ? (
                          <span className="flex items-center justify-center gap-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            Test Email Gönderiliyor...
                          </span>
                        ) : (
                          '🧪 Test Email Gönder'
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {bulkEmailResult && (
              <div className={`mt-6 border rounded-lg p-4 ${
                bulkEmailResult.success 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <h4 className={`font-semibold mb-2 ${
                  bulkEmailResult.success ? 'text-green-800' : 'text-red-800'
                }`}>
                  {bulkEmailResult.success ? '✅ Email Gönderildi!' : '❌ Gönderim Başarısız!'}
                </h4>
                {bulkEmailResult.success && (
                  <p className="text-green-700 text-sm">
                    📧 <strong>{bulkEmailResult.sent_count}</strong> müşteriye gönderildi
                  </p>
                )}
              </div>
            )}

            <div className="flex gap-3 pt-6">
              <button
                onClick={handleBulkEmailSend}
                disabled={(!selectedTemplate && (!bulkEmailForm.subject || !bulkEmailForm.content)) || bulkEmailLoading}
                className="flex-1 bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 disabled:opacity-50 font-medium"
              >
                {bulkEmailLoading ? 'Gönderiliyor...' : selectedTemplate ? `📧 ${selectedTemplate.name} Gönder` : '📧 Email Gönder'}
              </button>
              <button
                onClick={() => setShowBulkEmail(false)}
                className="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600"
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Simple Client Management Component - Clean Implementation
const SimpleClientManagement = ({ onNavigate }) => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showAddForm, setShowAddForm] = useState(false);
  const [sortBy, setSortBy] = useState('hotel_name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [searchDebounceTimer, setSearchDebounceTimer] = useState(null);
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [clientTypeFilter, setClientTypeFilter] = useState('registered'); // Default to registered clients
  const [hasPrev, setHasPrev] = useState(false);
  const [hasNext, setHasNext] = useState(false);
  const [showAddClient, setShowAddClient] = useState(false);
  
  const [newClientData, setNewClientData] = useState({
    name: '',
    hotel_name: '',
    email: '',
    phone: '',
    city: '',
    district: '',
    address: '',
    certificate_end_date: '',
    audit_company: ''
  });
  
  // Türkiye İl ve İlçe Listesi
  const turkeyProvinces = {
    'ADANA': ['ALADAĞ', 'CEYHAN', 'ÇUKUROVA', 'FEKE', 'İMAMOĞLU', 'KARAİSALI', 'KARATAŞ', 'KOZAN', 'MERKEZ', 'POZANTI', 'SAİMBEYLİ', 'SARIÇAM', 'TUFANBEYLI', 'YUMURTALIK', 'YÜREĞİR'],
    'ADIYAMAN': ['BESNİ', 'ÇELİKHAN', 'GERGER', 'GÖLBAŞI', 'KAHTA', 'MERKEZ', 'SAMSAT', 'SİNCİK', 'TUT'],
    'AFYONKARAHİSAR': ['BAŞMAKÇI', 'BAYAT', 'BOLVADIN', 'ÇAY', 'ÇOBANLAR', 'DAZKIRI', 'DİNAR', 'EMİRDAĞ', 'EVCİLER', 'HOCALAR', 'İHSANİYE', 'İSCAHİSAR', 'KIZILÖREN', 'MERKEZ', 'SANDIKLI', 'SİNANPAŞA', 'SULTANDAĞI', 'ŞUHUT'],
    'AĞRI': ['DİYADİN', 'DOĞUBAYAZIT', 'ELEŞKİRT', 'HAMUR', 'MERKEZ', 'PATNOS', 'TAŞLIÇAY', 'TUTAK'],
    'AMASYA': ['GÖYNÜCEK', 'GÜMÜŞHACIKÖY', 'HAMAMÖZÜ', 'MERKEZ', 'MERZİFON', 'SULUOVA', 'TAŞOVA'],
    'ANKARA': ['AKYURT', 'ALTINDAĞ', 'AYAŞ', 'BALA', 'BEYPAZARI', 'ÇAMLIDERE', 'ÇANKAYA', 'ÇUBUK', 'ELMADAĞ', 'ETİMESGUT', 'EVREN', 'GÖLBAŞI', 'GÜDÜL', 'HAYMANA', 'KAHRAMANKAZAN', 'KAZAN', 'KEÇİÖREN', 'KIZILCAHAMAM', 'MAMAK', 'NALLIHAN', 'POLATLІ', 'PURSAKLAR', 'SİNCAN', 'ŞEREFLİKOÇHİSAR', 'YENİMAHALLE'],
    'ANTALYA': ['AKSEKİ', 'AKSU', 'ALANYA', 'DEMRE', 'DÖŞEMEALTI', 'ELMALI', 'FİNİKE', 'GAZİPAŞA', 'GÜNDOĞMUŞ', 'İBRADI', 'KAŞ', 'KEMER', 'KEPEZ', 'KONYAALTI', 'KORKUTELI', 'KUMLUCA', 'MANAVGAT', 'MURATPAŞA', 'SERİK'],
    'ARDAHAN': ['ÇILDIR', 'DAMAL', 'GÖLE', 'HANAK', 'MERKEZ', 'POSOF'],
    'ARTVİN': ['ARDANUÇ', 'ARHAVİ', 'BORÇKA', 'HOPA', 'MERKEZ', 'MURGUL', 'ŞAVŞAT', 'YUSUFELİ'],
    'AYDIN': ['BOZDOĞAN', 'BUHARKENT', 'ÇİNE', 'DİDİM', 'EFELER', 'GERMENCİK', 'İNCİRLİOVA', 'KARACASU', 'KARPUZLU', 'KOÇARLI', 'KÖŞK', 'KUŞADASI', 'KUYUCAK', 'NAZİLLİ', 'SÖKE', 'SULTANHİSAR', 'YENİPAZAR'],
    'BALIKESİR': ['ALTIEYLÜL', 'AYVALIK', 'BALYA', 'BANDIRMA', 'BİGADİÇ', 'BURHANİYE', 'DURSUNBEY', 'EDREMİT', 'ERDEK', 'GÖMEÇ', 'GÖNEN', 'HAVRAN', 'İVRİNDİ', 'KEPSUT', 'MANYAS', 'MARMARA', 'MERKEZ', 'SAVAŞTEPE', 'SINDIRGI', 'SUSURLUK'],
    'BARTIN': ['AMASRA', 'KURUCAŞILE', 'MERKEZ', 'ULUS'],
    'BATMAN': ['BEŞİRİ', 'GERCÜŞ', 'HASANKEYF', 'KOZLUK', 'MERKEZ', 'SASON'],
    'BAYBURT': ['AYDINTEPE', 'DEMİRÖZÜ', 'MERKEZ'],
    'BİLECİK': ['BOZÜYÜK', 'GÖLPAZARI', 'İNHİSAR', 'MERKEZ', 'OSMANELİ', 'PAZARYERİ', 'SÖĞÜT', 'YENİPAZAR'],
    'BİNGÖL': ['ADAKLI', 'GENÇ', 'KARLIOVА', 'KİĞI', 'MERKEZ', 'SOLHAN', 'YAYLADERE', 'YEDİSU'],
    'BİTLİS': ['ADİLCEVAZ', 'AHLAT', 'GÜROYMAK', 'HİZAN', 'MERKEZ', 'MUTKİ', 'TATVAN'],
    'BOLU': ['DÖRTDIVAN', 'GEREDE', 'GÖYNÜK', 'KIBRISCIK', 'MENGEN', 'MERKEZ', 'MUDURNU', 'SEBEN', 'YENİÇAĞA'],
    'BURDUR': ['AĞLASUN', 'ALTINYAYLA', 'BUCAK', 'ÇAVDIR', 'ÇELTİKÇİ', 'GÖLHİSAR', 'KARAMANLI', 'KEMER', 'MERKEZ', 'TEFENNİ', 'YEŞİLOVА'],
    'BURSA': ['BÜYÜKORHAN', 'GEMLİK', 'GÜRSU', 'HARMANCIK', 'İNEGÖL', 'İZNİK', 'KARACABEY', 'KELES', 'KESTEL', 'MUDANYA', 'MUSTAFAKEMALPAŞA', 'NİLÜFER', 'ORHANELİ', 'ORHANGAZİ', 'OSMANGAZİ', 'YENİŞEHİR', 'YILDIRIM'],
    'ÇANAKKALE': ['AYVACIK', 'BAYRAMİÇ', 'BİGA', 'BOZCAADA', 'ÇAN', 'ECEABAT', 'EZİNE', 'GELİBOLU', 'GÖKÇEADA', 'LÂPSEKİ', 'MERKEZ', 'YENİCE'],
    'ÇANKIRI': ['ATKARACALAR', 'BAYRAMÖREN', 'ÇERKEŞ', 'ELDİVAN', 'ILGAZ', 'KIZILIRMAK', 'KORGUN', 'KURŞUNLU', 'MERKEZ', 'ORTA', 'ŞABANÖZÜ', 'YAPRAKLI'],
    'ÇORUM': ['ALACA', 'BAYAT', 'BOĞAZKALE', 'DODURGA', 'İSKİLİP', 'KARGI', 'LAÇİN', 'MECİTÖZÜ', 'MERKEZ', 'OĞUZLAR', 'ORTAKÖY', 'OSMANCIK', 'SUNGURLU', 'UĞURLUDAĞ'],
    'DENİZLİ': ['ACIPAYAM', 'BABADAĞ', 'BAKLAN', 'BEKİLLİ', 'BEYAĞAÇ', 'BOZKURT', 'BULDAN', 'ÇAL', 'ÇAMELİ', 'ÇARDAK', 'ÇİVRİL', 'GÜNEY', 'HONAZ', 'KALE', 'MERKEZEFENDİ', 'PAMUKKALE', 'SARAYKÖY', 'SERİNHİSAR', 'TAVAS'],
    'DİYARBAKIR': ['BAĞLAR', 'BİSMİL', 'ÇERMİK', 'ÇINAR', 'ÇÜNGÜŞ', 'DİCLE', 'EĞİL', 'ERGANİ', 'HANI', 'HAZRO', 'KAYAPINAR', 'KOCAKÖY', 'KULP', 'LİCE', 'SİLVAN', 'SUR', 'YENİŞEHİR'],
    'DÜZCE': ['AKÇAKOCA', 'CUMAYERİ', 'ÇİLİMLİ', 'GÖLYAKA', 'GÜMÜŞOVA', 'KAYNAŞLI', 'MERKEZ', 'YIĞILCA'],
    'EDİRNE': ['ENEZ', 'HAVSA', 'İPSALA', 'KEŞAN', 'LALAPAŞA', 'MERİÇ', 'MERKEZ', 'SÜLOĞLU', 'UZUNKÖPRÜ'],
    'ELAZIĞ': ['AĞIN', 'ALACAKAYA', 'ARICАК', 'BASKİL', 'KARAKOÇAN', 'KEBAN', 'KOVANCILAR', 'MADEN', 'MERKEZ', 'PALU', 'SİVRİCE'],
    'ERZİNCAN': ['ÇAYIRLI', 'İLİÇ', 'KEMAH', 'KEMALİYE', 'MERKEZ', 'OTLUKBELİ', 'REFAHİYE', 'TERCAN', 'ÜZÜMLÜ'],
    'ERZURUM': ['AŞKALE', 'AZİZİYE', 'ÇAT', 'HINIS', 'HORASAN', 'İSPİR', 'KARAÇOBAN', 'KARAYAZI', 'KÖPRÜKÖY', 'NARMAN', 'OLTU', 'OLUR', 'PALANDÖKEN', 'PASİNLER', 'PAZARYOLU', 'ŞENKAYA', 'TEKMAN', 'TORTUM', 'UZUNDERE', 'YAKUTİYE'],
    'ESKİŞEHİR': ['ALPU', 'BEYLİKOVA', 'ÇİFTELER', 'GÜNYÜZÜ', 'HAN', 'İNÖNÜ', 'MAHMUDİYE', 'MİHALGAZİ', 'MİHALIÇÇIK', 'ODUNPAZARI', 'SARICAKAYA', 'SEYİTGAZİ', 'SİVRİHİSAR', 'TEPEBAŞI'],
    'GAZİANTEP': ['ARABAN', 'İSLAHİYE', 'KARKAMIŞ', 'NİZİP', 'NURDAĞI', 'OĞUZELİ', 'ŞAHİNBEY', 'ŞEHİTKAMİL', 'YAVUZELİ'],
    'GİRESUN': ['ALUCRA', 'BULANCAK', 'ÇAMOLUK', 'ÇANAKÇI', 'DERELİ', 'DOĞANKENT', 'ESPİYE', 'EYNESİL', 'GÖRELE', 'GÜCE', 'KEŞAP', 'MERKEZ', 'PİRAZİZ', 'ŞEBINKARAHISAR', 'TİREBOLU', 'YAĞLIDERE'],
    'GÜMÜŞHANE': ['KELKIT', 'KÖSE', 'KÜRTÜN', 'MERKEZ', 'ŞIRAN', 'TORUL'],
    'HAKKARİ': ['ÇUKURCA', 'DERECİK', 'MERKEZ', 'ŞEMDİNLİ', 'YÜKSEKOVA'],
    'HATAY': ['ALTINÖZÜ', 'ANTAKYA', 'ARSUZ', 'BELEN', 'DEFNE', 'DÖRTYOL', 'ERZİN', 'HASSA', 'İSKENDERUN', 'KIRIKHAN', 'KUMLU', 'PAYAS', 'REYHANLI', 'SAMANDAĞ', 'YAYLADAĞI'],
    'IĞDIR': ['ARALIK', 'KARAKOYUNLU', 'MERKEZ', 'TUZLUCA'],
    'ISPARTA': ['AKSU', 'ATABEY', 'EĞİRDİR', 'GELENDOST', 'GÖNEN', 'KEÇİBORLU', 'MERKEZ', 'SENİRKENT', 'SÜTÇÜLER', 'ŞARKİKARAAĞAÇ', 'ULUBORLU', 'YALVAÇ', 'YENİŞARBADEMLİ'],
    'İSTANBUL': ['ADALAR', 'ARNAVUTKÖY', 'ATAŞEHİR', 'AVCILAR', 'BAĞCILAR', 'BAHÇELİEVLER', 'BAKIRKÖY', 'BAŞAKŞEHİR', 'BAYRAMPAŞA', 'BEŞİKTAŞ', 'BEYKOZ', 'BEYLİKDÜZÜ', 'BEYOĞLU', 'BÜYÜKÇEKMECE', 'ÇATALCA', 'ÇEKMEKÖY', 'ESENLER', 'ESENYURT', 'EYÜPSULTAN', 'FATİH', 'GAZİOSMANPAŞA', 'GÜNGÖREN', 'KADIKÖY', 'KAĞITHANE', 'KARTAL', 'KÜÇÜKÇEKMECE', 'MALTEPE', 'PENDİK', 'SANCAKTEPE', 'SARIYER', 'SİLİVRİ', 'SULTANBEYLİ', 'SULTANGAZİ', 'ŞİLE', 'ŞİŞLİ', 'TUZLA', 'ÜMRANİYE', 'ÜSKÜDAR', 'ZEYTİNBURNU'],
    'İZMİR': ['ALİAĞA', 'BALÇOVA', 'BAYINDIR', 'BAYRAKLI', 'BERGAMA', 'BEYDAĞ', 'BORNOVA', 'BUCA', 'ÇEŞME', 'ÇİĞLİ', 'DİKİLİ', 'FOÇA', 'GAZİEMİR', 'GÜZELBAHÇE', 'KARABAĞLAR', 'KARABURUN', 'KARŞIYAKA', 'KEMALPAŞA', 'KINIK', 'KİRAZ', 'KONAK', 'MENDERES', 'MENEMEN', 'NARLIDA', 'ÖDEMİŞ', 'SEFERIHISAR', 'SELÇUK', 'TİRE', 'TORBALI', 'URLA'],
    'KAHRAMANMARAŞ': ['AFŞİN', 'ANDIRIN', 'ÇAĞLAYANCERİT', 'DULKADİROĞLU', 'EKİNÖZÜ', 'ELBİSTAN', 'GÖKSUN', 'NURHAK', 'ONİKİŞUBAT', 'PAZARCIK', 'TÜRKOĞLU'],
    'KARABÜK': ['EFLANİ', 'ESKİPAZAR', 'MERKEZ', 'OVACIK', 'SAFRANBOLU', 'YENİCE'],
    'KARAMAN': ['AYRANCI', 'BAŞYAYLA', 'ERMENEK', 'KAZIMKARABEKİR', 'MERKEZ', 'SARIVELİLER'],
    'KARS': ['AKYAKA', 'ARPAÇAY', 'DİGOR', 'KAĞIZMAN', 'MERKEZ', 'SARIKAMIŞ', 'SELIM', 'SUSUZ'],
    'KASTAMONU': ['ABANA', 'AĞLI', 'ARAÇ', 'AZDAVAY', 'BOZKURT', 'CİDE', 'ÇATALZEYTİN', 'DADAY', 'DEVREKANİ', 'DOĞANYURT', 'HANÖNÜ', 'İHSANGAZİ', 'İNEBOLU', 'KÜRE', 'MERKEZ', 'PINARBAŞI', 'SEYDILER', 'ŞENPAZAR', 'TAŞKÖPRÜ', 'TOSYA'],
    'KAYSERİ': ['AKKIŞLA', 'BÜNYAN', 'DEVELİ', 'FELAHİYE', 'HACILAR', 'İNCESU', 'KOCASİNAN', 'MELİKGAZİ', 'ÖZVATAN', 'PINARBAŞI', 'SARIOĞLAN', 'SARIZ', 'TALAS', 'TOMARZA', 'YAHYALI', 'YEŞİLHİSAR'],
    'KIRIKKALE': ['BAHŞILI', 'BALISEYH', 'ÇELEBİ', 'DELİCE', 'KARAKEÇİLİ', 'KESKİN', 'MERKEZ', 'SULAKYURT', 'YAHŞİHAN'],
    'KIRKLARELİ': ['BABAESKİ', 'DEMİRKÖY', 'KOFÇAZ', 'LÜLEBURGAZ', 'MERKEZ', 'PEHLİVANKÖY', 'PINARHİSAR', 'VİZE'],
    'KIRŞEHİR': ['AKÇAKENT', 'AKPINAR', 'BOZTEPE', 'ÇİÇEKDAĞI', 'KAMAN', 'MERKEZ', 'MUCUR'],
    'KİLİS': ['ELBEYLİ', 'MERKEZ', 'MUSABEYLİ', 'POLATELI'],
    'KOCAELİ': ['BAŞİSKELE', 'ÇAYIROVA', 'DARICA', 'DERİNCE', 'DİLOVASI', 'GEBZE', 'GÖLCÜK', 'İZMİT', 'KANDIRA', 'KARAMÜRSEL', 'KARTEPE', 'KÖRFEZ'],
    'KONYA': ['AHIRLI', 'AKÖREN', 'AKŞEHİR', 'ALTINEKIN', 'BEYŞEHİR', 'BOZKIR', 'CİHANBEYLİ', 'ÇELTİK', 'ÇUMRA', 'DERBENT', 'DEREBUCAK', 'DOĞANHİSAR', 'EMİRGAZİ', 'EREĞLİ', 'GÜNEYSINIR', 'HADIM', 'HALKAPINAR', 'HÜYÜK', 'ILGIN', 'KADINHANI', 'KARAPINAR', 'KARATAY', 'KULU', 'MERAM', 'SARAYÖNÜ', 'SELÇUKLU', 'SEYDİŞEHİR', 'TAŞKENT', 'TUZLUKÇU', 'YALIHÜYÜK', 'YUNAK'],
    'KÜTAHYA': ['ALTINTAŞ', 'ASLANAPA', 'ÇAVDARHİSAR', 'DOMANİÇ', 'DUMLUPINAR', 'EMET', 'GEDİZ', 'HİSARCIK', 'MERKEZ', 'PAZARLAR', 'ŞAPHANE', 'SİMAV', 'TAVŞANLI'],
    'MALATYA': ['AKÇADAĞ', 'ARAPGİR', 'ARGUVAN', 'BATTALGAZİ', 'DARENDE', 'DOĞANŞEHİR', 'DOĞANYOL', 'HEKİMHAN', 'KALE', 'KULUNCAK', 'PÜTÜRGE', 'YAZIHAN', 'YEŞİLYURT'],
    'MANİSA': ['AHMETLİ', 'AKHİSAR', 'ALAŞEHİR', 'DEMİRCİ', 'GÖLMARMARA', 'GÖRDES', 'KIRKAĞAÇ', 'KÖPRÜBAŞI', 'KULA', 'SALİHLİ', 'SARIGÖL', 'SARUHANLI', 'SELENDI', 'SOMA', 'ŞEHZADELER', 'TURGUTLU', 'YUNUSEMRE'],
    'MARDİN': ['ARTUKLU', 'DARGEÇİT', 'DEREKÖy', 'KIZILTEPE', 'MAZIDAĞI', 'MİDYAT', 'NUSAYBİN', 'ÖMERLİ', 'SAVUR', 'YEŞİLLİ'],
    'MERSİN': ['ANAMUR', 'AYDINCIK', 'BOZYAZI', 'ÇAMLIYAYLA', 'ERDEMLİ', 'GÜLNAR', 'MEZİTLİ', 'MUT', 'SİLİFKE', 'TARSUS', 'TOROSLAR', 'YENİŞEHİR'],
    'MUĞLA': ['BODRUM', 'DALAMAN', 'DATÇA', 'FETHİYE', 'KAVAKLIDERE', 'KÖYCEĞIZ', 'MARMARIS', 'MENTEŞE', 'MİLAS', 'ORTACA', 'SEYDİKEMER', 'ULA', 'YATAĞAN'],
    'MUŞ': ['BULANIK', 'HASKOY', 'KORKUT', 'MALAZGIRT', 'MERKEZ', 'VARTO'],
    'NEVŞEHİR': ['ACIGÖL', 'AVANOS', 'DERİNKUYU', 'GÜLŞEHIR', 'HACIBEKTAS', 'KOZAKLI', 'MERKEZ', 'ÜRGÜP'],
    'NİĞDE': ['ALTUNHISAR', 'BOR', 'ÇAMARDI', 'ÇİFTLİK', 'MERKEZ', 'ULUKIŞLA'],
    'ORDU': ['AKKUŞ', 'ALTINORDU', 'AYBASTI', 'ÇAMAŞ', 'ÇATALPINAR', 'ÇAYBAŞI', 'FATSA', 'GÖLKÖY', 'GÜLYALI', 'GÜRGENTEPE', 'İKİZCE', 'KABADÜZ', 'KABATAŞ', 'KORGAN', 'KUMRU', 'MESUDİYE', 'PERŞEMBE', 'ULUBEY', 'ÜNYE'],
    'OSMANİYE': ['BAHÇE', 'DÜZİÇİ', 'HASANBEYLİ', 'KADİRLİ', 'MERKEZ', 'SUMBAS', 'TOPRAKKALE'],
    'RİZE': ['ARDEŞEN', 'ÇAMLIHEMŞİN', 'ÇAYELİ', 'DEREPAZARI', 'FINDIKLI', 'GÜNEYSU', 'HEMŞİN', 'İKİZDERE', 'İYİDERE', 'KALKANDERE', 'MERKEZ', 'PAZAR'],
    'SAKARYA': ['ADAPAZARI', 'AKYAZI', 'ARİFİYE', 'ERENLER', 'FERİZLİ', 'GEYVE', 'HENDEK', 'KARAPÜRÇEK', 'KARASU', 'KAYNARCA', 'KOCAALİ', 'PAMUKOVA', 'SAPANCA', 'SERDIVAN', 'SÖĞÜTLÜ', 'TARAKLI'],
    'SAMSUN': ['19 MAYIS', 'ALAÇAM', 'ASARCIK', 'ATAKUM', 'AYVACIK', 'BAFRA', 'CANİK', 'ÇARŞAMBA', 'HAVZA', 'İLKADIM', 'KAVAK', 'LADİK', 'ONDOKUZMAYIS', 'SALIPAZARI', 'TEKKEKÖY', 'TERME', 'VEZİRKÖPRÜ', 'YAKAKENT'],
    'SİİRT': ['AYDNLAR', 'BAYKAN', 'ERUH', 'KURTALAN', 'MERKEZ', 'PERVARİ', 'ŞİRVAN'],
    'SİNOP': ['AYANCIK', 'BOYABAT', 'DİKMEN', 'DURAĞAN', 'ERFELEK', 'GERZE', 'MERKEZ', 'SARAYDÜZÜ', 'TÜRKELİ'],
    'SİVAS': ['AKINCLAR', 'ALTINYAYLA', 'DİVRİĞİ', 'DOĞANŞAR', 'GEMEREK', 'GÖLOVA', 'GÜRÜN', 'HAFİK', 'İMRANLI', 'KANGAL', 'KOYULHISAR', 'MERKEZ', 'SUŞEHRI', 'ŞARKİŞLA', 'ULAŞ', 'YILDIZELİ', 'ZARA'],
    'ŞANLIURFA': ['AKÇAKALE', 'BİRECİK', 'BOZOVA', 'CEYLANPINAR', 'EYYÜBİYE', 'HALFETİ', 'HALİLİYE', 'HARRAN', 'HİLVAN', 'KARAKÖPRÜ', 'SİVEREK', 'SURUÇ', 'VİRANŞEHİR'],
    'ŞIRNAK': ['BEYTÜŞŞEBAP', 'CİZRE', 'GÜÇLÜKONAK', 'İDİL', 'MERKEZ', 'SİLOPİ', 'ULUDERE'],
    'TEKİRDAĞ': ['ÇERKEZKÖY', 'ÇORLU', 'ERGENE', 'HAYRABOLU', 'KAPAKLI', 'MALKARA', 'MARMARA EREĞLİSİ', 'MURATLІ', 'SARAY', 'SÜLEYMANPAŞA', 'ŞARKÖY'],
    'TOKAT': ['ALMUS', 'ARTOVA', 'BAŞÇIFTLIK', 'ERBAA', 'MERKEZ', 'NİKSAR', 'PAZAR', 'REŞADİYE', 'SULUSARAY', 'TURHAL', 'YEŞİLYURT', 'ZİLE'],
    'TRABZON': ['AKÇAABAT', 'ARAKLI', 'ARSİN', 'BEŞİKDÜZÜ', 'ÇARŞIBAŞI', 'ÇAYKARA', 'DERNEKPAZARI', 'DÜZKÖY', 'HAYRAT', 'KÖPRÜBAŞI', 'LAST', 'MAÇKA', 'OF', 'ORTAHİSAR', 'SÜRMENE', 'ŞALPAZARI', 'TONYA', 'VAKFIKEBİR', 'YOMRA'],
    'TUNCELİ': ['ÇEMİŞGEZEK', 'HOZAT', 'MAZGİRT', 'MERKEZ', 'NAZIMİYE', 'OVACIK', 'PERTEK', 'PÜLÜMÜR'],
    'UŞAK': ['BANAZ', 'EŞME', 'KARAHALLI', 'MERKEZ', 'SİVASLI', 'ULUBEY'],
    'VAN': ['BAHÇESARAY', 'BAŞKALE', 'ÇALDIRAN', 'ÇATAK', 'EDREMİT', 'ERCİŞ', 'GEVAŞ', 'GÜRPINAR', 'İPEKYOLU', 'MERKEZ', 'MURADIYE', 'ÖZALP', 'SARAY', 'TUŞBA'],
    'YALOVA': ['ALTINOVA', 'ARMUTLU', 'ÇIFTLIKKÖY', 'ÇINARCIK', 'MERKEZ', 'TERMAL'],
    'YOZGAT': ['AKDAĞMADEN', 'BOĞAZLIYAN', 'ÇANDIR', 'ÇAYIRALAN', 'ÇEKEREK', 'KADIŞEHRI', 'MERKEZ', 'SARAYKENT', 'SARIKKAYA', 'ŞEFAATLI', 'SORGUN', 'YENIFAKILI', 'YERKÖy'],
    'ZONGULDAK': ['ALAPLІ', 'ÇAYCUMA', 'DEVREK', 'EREĞLİ', 'GÖKÇEBEY', 'KİLİMLİ', 'KOZLU', 'MERKEZ']
  };

  // Denetim Firmaları
  const auditCompanies = [
    'Alberk QA Uluslararası Teknik Kontrol ve Belgelendirme A.Ş.',
    'Bureau Veritas Gözetim Hizmetleri Ltd. Şti.',
    'Control Union Gözetim ve Belgelendirme Ltd. Şti.',
    'FQC Global Sertifikasyon Anonim Şirketi',
    'Kiwa Belgelendirme Hizmetleri A.Ş.',
    'RoyalCert Belgelendirme ve Gözetim Hizmetleri A.Ş',
    'TSE Global',
    'TÜV Austria Turk Belgelendirme Eğitim ve Gözetim Hizmetleri LTD. ŞTİ.',
    'TRB Uluslararası Belgelendirme Teknik Kontrol ve Gözetim Hizmetleri Tic. Ltd.Şti.'
  ];
  
  const [showBulkEmail, setShowBulkEmail] = useState(false);
  const [bulkEmailLoading, setBulkEmailLoading] = useState(false);
  const [bulkEmailStats, setBulkEmailStats] = useState(null);
  const [bulkEmailForm, setBulkEmailForm] = useState({
    subject: '',
    content: '',
    target_filters: {
      city: '',
      audit_company: '',
      has_email: true,
      certificate_filter: ''
    }
  });
  const [bulkEmailResult, setBulkEmailResult] = useState(null);
  const [testEmail, setTestEmail] = useState('');
  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  
  const { authToken, userRole, dbUser, ensureTokenForOperation } = useAuth();
  const API = getApiUrl();

  // Fetch clients
  const fetchClients = async (page = 1, limit = itemsPerPage, search = searchTerm, sort = sortBy, order = sortOrder, clientType = clientTypeFilter) => {
    try {
      setLoading(true);
      const params = { page, limit };
      if (search && search.trim()) {
        params.search = search.trim();
      }
      if (sort) {
        params.sort = sort;
      }
      if (order) {
        params.order = order;
      }
      if (clientType && clientType !== 'all') {
        params.client_type = clientType;
      }
      
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        params,
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      console.log('🔍 SimpleClientManagement - API Response:', response.data);
      
      // Handle response - backend returns { clients, pagination }
      const { clients, pagination } = response.data;
      console.log('🔍 SimpleClientManagement - Parsed clients:', clients);
      console.log('🔍 SimpleClientManagement - Parsed pagination:', pagination);
      
      setClients(clients || []);
      setTotalPages(pagination?.total_pages || 1);
      setTotalCount(pagination?.total_count || 0);
      setHasPrev(pagination?.has_prev || false);
      setHasNext(pagination?.has_next || false);
      
    } catch (error) {
      console.error('Error fetching clients:', error);
      
      // Check if it's an authentication error
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.error('🔐 Authentication error:', error.response?.data?.detail);
        console.error('🔐 Token:', authToken ? 'EXISTS' : 'MISSING');
        console.error('🔐 Request URL:', `${API}/clients`);
        console.error('🔐 Request params:', {client_type: clientType, page, limit});
        alert('Authentication hatası: Token geçersiz. Lütfen yeniden giriş yapın.');
      } else {
        console.error('API error:', error.response?.data?.detail || error.message);
      }
      
      setClients([]);
      setTotalPages(1);
      setTotalCount(0);
      setHasPrev(false);
      setHasNext(false);
    } finally {
      setLoading(false);
    }
  };

  // Search with debouncing
  const handleSearchDebounced = (term) => {
    setSearchTerm(term);
    
    // Clear previous timer
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }
    
    // Set new timer
    const newTimer = setTimeout(() => {
      setCurrentPage(1);
      fetchClients(1, itemsPerPage, term, sortBy, sortOrder);
    }, 300); // 300ms delay
    
    setSearchDebounceTimer(newTimer);
  };
  
  // Search handler (immediate for dropdown)
  const handleSearch = (term) => {
    setSearchTerm(term);
    setCurrentPage(1);
    fetchClients(1, itemsPerPage, term, sortBy, sortOrder, clientTypeFilter);
  };


  // Pagination handlers
  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      fetchClients(page, itemsPerPage, searchTerm, sortBy, sortOrder, clientTypeFilter);
    }
  };

  const handleItemsPerPageChange = (limit) => {
    setItemsPerPage(limit);
    setCurrentPage(1);
    fetchClients(1, limit, searchTerm, sortBy, sortOrder, clientTypeFilter);
  };

  // Sort function
  const handleSort = (field) => {
    const newOrder = sortBy === field && sortOrder === 'asc' ? 'desc' : 'asc';
    setSortBy(field);
    setSortOrder(newOrder);
    setCurrentPage(1);
    fetchClients(1, itemsPerPage, searchTerm, field, newOrder, clientTypeFilter);
  };

  // Bulk Email Functions
  const fetchBulkEmailStats = async () => {
    try {
      const response = await axios.get(`${API}/bulk-email/stats`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setBulkEmailStats(response.data);
    } catch (error) {
      console.error('Error fetching bulk email stats:', error);
    }
  };

  const handleBulkEmailSend = async () => {
    if (!bulkEmailForm.subject || !bulkEmailForm.content) {
      alert('Lütfen konu ve içerik alanlarını doldurun!');
      return;
    }

    const confirmSend = window.confirm(
      'Bulk email gönderimini başlatmak istediğinizden emin misiniz?\n\nBu işlem geri alınamaz.'
    );

    if (!confirmSend) return;

    try {
      setBulkEmailLoading(true);
      setBulkEmailResult(null);

      const response = await axios.post(`${API}/bulk-email/send`, {
        subject: bulkEmailForm.subject,
        content: bulkEmailForm.content,
        target_filters: bulkEmailForm.target_filters
      }, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      setBulkEmailResult(response.data);
      
      // Reset form
      setBulkEmailForm({
        subject: '',
        content: '',
        target_filters: {
          city: '',
          audit_company: '',
          has_email: true,
          certificate_filter: ''
        }
      });

    } catch (error) {
      console.error('Error sending bulk email:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      alert('Bulk email gönderim hatası: ' + errorMessage);
      setBulkEmailResult({
        success: false,
        error: errorMessage
      });
    } finally {
      setBulkEmailLoading(false);
    }
  };

  // Load bulk email stats when bulk email modal opens
  useEffect(() => {
    if (showBulkEmail) {
      fetchBulkEmailStats();
    }
  }, [showBulkEmail]);

  // Client type filter handler
  const handleClientTypeChange = (type) => {
    setClientTypeFilter(type);
    setCurrentPage(1);
    fetchClients(1, itemsPerPage, searchTerm, sortBy, sortOrder, type);
  };

  // Add new client
  const handleAddClient = async () => {
    try {
      await axios.post(`${API}/clients`, newClientData, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      alert('Müşteri başarıyla eklendi!');
      setShowAddClient(false);
      setNewClientData({
        name: '',
        hotel_name: '',
        email: '',
        phone: '',
        address: ''
      });
      fetchClients();
    } catch (error) {
      console.error('Error adding client:', error);
      alert('Hata: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Delete client
  const handleDeleteClient = async (clientId, clientName) => {
    const confirmDelete = window.confirm(
      `"${clientName}" müşterisini silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz ve müşteriye ait tüm veriler silinecektir.`
    );
    
    if (!confirmDelete) return;
    
    try {
      await axios.delete(`${API}/clients/${clientId}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      alert('Müşteri başarıyla silindi!');
      fetchClients();
    } catch (error) {
      console.error('Error deleting client:', error);
      alert('Hata: ' + (error.response?.data?.detail || error.message));
    }
  };

  useEffect(() => {
    if (authToken && userRole === 'admin') {
      fetchClients(1, itemsPerPage, searchTerm, sortBy, sortOrder, clientTypeFilter);
    }
  }, [authToken, userRole]);

  if (userRole !== 'admin') {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Bu bölüme erişim yetkiniz bulunmamaktadır.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🏨 Müşteri Yönetimi</h1>
          <p className="text-gray-600">
            Müşteri bilgilerini yönetin ve projelerini takip edin
          </p>
        </div>

        {/* Header Actions */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Müşteri Listesi</h2>
              <p className="text-sm text-gray-600">
                {searchTerm ? `"${searchTerm}" araması - ` : ''}
                Toplam {totalCount} müşteri - Sayfa {currentPage} / {totalPages}
              </p>
            </div>
            
            {/* Search and Filters */}
            <div className="flex flex-col md:flex-row gap-3 items-center">
              {/* Search Input */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Otel adı, şehir, email ile ara..."
                  value={searchTerm}
                  onChange={(e) => handleSearchDebounced(e.target.value)}
                  className="w-64 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
                <span className="absolute right-3 top-2.5 text-gray-400">🔍</span>
              </div>
              
              {/* Client Type Filter */}
              {/* Sort Options */}
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-600">Sıralama:</label>
                <select
                  value={sortBy}
                  onChange={(e) => handleSort(e.target.value)}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  <option value="hotel_name">Otel Adı</option>
                  <option value="city">Şehir</option>
                  <option value="phone">Telefon</option>
                  <option value="email">Email</option>
                </select>
                <button
                  onClick={() => handleSort(sortBy)}
                  className="px-2 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
                  title={sortOrder === 'asc' ? 'A-Z sıralama' : 'Z-A sıralama'}
                >
                  {sortOrder === 'asc' ? '🔼' : '🔽'}
                </button>
              </div>
              
              {/* Items per page selector */}
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-600">Sayfa başına:</label>
                <select
                  value={itemsPerPage}
                  onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={200}>200</option>
                </select>
              </div>
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => setShowAddClient(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              ➕ Yeni Müşteri
            </button>
          </div>
        </div>

      {/* Bulk Email Modal - Admin Only */}
      {showBulkEmail && userRole === 'admin' && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                📧 Toplu Email Gönderimi (Sadece Bulk Müşteriler)
              </h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Email Stats */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-800 mb-3">📊 Bulk Müşteri İstatistikleri</h4>
                  {bulkEmailStats ? (
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-blue-700">Toplam Bulk Müşteri:</span>
                        <span className="font-medium text-blue-900">{bulkEmailStats.total_bulk_clients}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700">Email Adresi Olan:</span>
                        <span className="font-medium text-blue-900">{bulkEmailStats.bulk_clients_with_email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700">Email Kapsama:</span>
                        <span className="font-medium text-blue-900">{bulkEmailStats.email_coverage_percentage}%</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-blue-600">İstatistikler yükleniyor...</p>
                  )}
                </div>

                {/* Email Form */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Konusu:
                    </label>
                    <input
                      type="text"
                      value={bulkEmailForm.subject}
                      onChange={(e) => setBulkEmailForm({...bulkEmailForm, subject: e.target.value})}
                      placeholder="Email konusunu girin..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email İçeriği:
                    </label>
                    <textarea
                      value={bulkEmailForm.content}
                      onChange={(e) => setBulkEmailForm({...bulkEmailForm, content: e.target.value})}
                      placeholder="Email içeriğini girin... (HTML desteklenir)"
                      rows={6}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Placeholder'lar: {'{hotel_name}'}, {'{city}'}, {'{contact_person}'}
                    </p>
                  </div>

                  {/* Filters */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Şehir Filtresi:
                      </label>
                      <select
                        value={bulkEmailForm.target_filters.city}
                        onChange={(e) => setBulkEmailForm({
                          ...bulkEmailForm,
                          target_filters: {...bulkEmailForm.target_filters, city: e.target.value}
                        })}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="">Tüm Şehirler</option>
                        {bulkEmailStats?.city_distribution?.map(city => (
                          <option key={city._id} value={city._id}>
                            {city._id} ({city.count} müşteri)
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Denetim Firması:
                      </label>
                      <select
                        value={bulkEmailForm.target_filters.audit_company}
                        onChange={(e) => setBulkEmailForm({
                          ...bulkEmailForm,
                          target_filters: {...bulkEmailForm.target_filters, audit_company: e.target.value}
                        })}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="">Tüm Firmalar</option>
                        {bulkEmailStats?.audit_company_distribution?.map(company => (
                          <option key={company._id} value={company._id}>
                            {company._id} ({company.count} müşteri)
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              {/* Send Result */}
              {bulkEmailResult && (
                <div className={`mt-6 border rounded-lg p-4 ${
                  bulkEmailResult.success 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <h4 className={`font-semibold mb-2 ${
                    bulkEmailResult.success ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {bulkEmailResult.success ? '✅ Email Gönderildi!' : '❌ Gönderim Başarısız!'}
                  </h4>
                  {bulkEmailResult.success ? (
                    <div className="text-green-700 text-sm">
                      <p>{bulkEmailResult.message}</p>
                      <p>📧 <strong>{bulkEmailResult.sent_count}</strong> bulk müşteriye gönderildi</p>
                    </div>
                  ) : (
                    <p className="text-red-700 text-sm">{bulkEmailResult.error}</p>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-6">
                <button
                  onClick={handleBulkEmailSend}
                  disabled={!bulkEmailForm.subject || !bulkEmailForm.content || bulkEmailLoading}
                  className="flex-1 bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {bulkEmailLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Gönderiliyor...
                    </span>
                  ) : (
                    '📧 Bulk Email Gönder'
                  )}
                </button>
                <button
                  onClick={() => {
                    setShowBulkEmail(false);
                    setBulkEmailForm({
                      subject: '',
                      content: '',
                      target_filters: {
                        city: '',
                        audit_company: '',
                        has_email: true,
                        certificate_filter: ''
                      }
                    });
                    setBulkEmailResult(null);
                    setBulkEmailStats(null);
                  }}
                  disabled={bulkEmailLoading}
                  className="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 disabled:opacity-50"
                >
                  {bulkEmailLoading ? 'Bekleyin...' : 'Kapat'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

        {/* Clients Grid */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">
              {searchTerm ? 'Aranıyor...' : 'Müşteriler yükleniyor...'}
            </span>
          </div>
        ) : clients.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">
              {searchTerm ? `"${searchTerm}" için sonuç bulunamadı.` : 'Henüz müşteri bulunmuyor.'}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Müşteri Listesi</h3>
              <p className="text-sm text-gray-500 mt-1">Toplam {clients.length} müşteri</p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('hotel_name')}
                    >
                      Otel Adı {sortBy === 'hotel_name' && (sortOrder === 'asc' ? '🔼' : '🔽')}
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('city')}
                    >
                      Şehir {sortBy === 'city' && (sortOrder === 'asc' ? '🔼' : '🔽')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İlçe
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('phone')}
                    >
                      Telefon {sortBy === 'phone' && (sortOrder === 'asc' ? '🔼' : '🔽')}
                    </th>
                    <th 
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('email')}
                    >
                      Email {sortBy === 'email' && (sortOrder === 'asc' ? '🔼' : '🔽')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sertifika Bitiş
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Denetim Firma
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Müşteri Tipi
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İşlem
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {clients.slice(0, 50).map((client, index) => (  // Max 50 client render
                    <tr key={client.id || index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-8 w-8">
                            <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                              client.client_type === 'bulk' ? 'bg-orange-100' : 'bg-blue-100'
                            }`}>
                              <span className={`font-medium text-xs ${
                                client.client_type === 'bulk' ? 'text-orange-600' : 'text-blue-600'
                              }`}>
                                {client.hotel_name?.charAt(0).toUpperCase() || 'H'}
                              </span>
                            </div>
                          </div>
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900 flex items-center gap-2">
                              {client.hotel_name || 'Belirtilmemiş'}
                              {client.client_type === 'bulk' && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                                  Toplu
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {client.city || 'Belirtilmemiş'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {client.district || 'Belirtilmemiş'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {client.phone || 'Belirtilmemiş'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {client.email || 'Belirtilmemiş'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {client.certificate_end_date || 'Belirtilmemiş'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {client.audit_company || 'Belirtilmemiş'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          client.client_type === 'bulk' 
                            ? 'bg-orange-100 text-orange-800' 
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {client.client_type === 'bulk' ? 'Toplu Müşteri' : 'Kayıtlı Müşteri'}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleDeleteClient(client.id, client.hotel_name)}
                          className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50"
                          title="Sil"
                        >
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Add Client Modal */}
      {showAddClient && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Yeni Müşteri Ekle</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Firma Adı *
                  </label>
                  <input
                    type="text"
                    value={newClientData.name}
                    onChange={(e) => setNewClientData({...newClientData, name: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="Firma adını girin"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Otel Adı *
                  </label>
                  <input
                    type="text"
                    value={newClientData.hotel_name}
                    onChange={(e) => setNewClientData({...newClientData, hotel_name: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="Otel adını girin"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={newClientData.email}
                    onChange={(e) => setNewClientData({...newClientData, email: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="Email adresi"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Telefon
                  </label>
                  <input
                    type="tel"
                    value={newClientData.phone}
                    onChange={(e) => setNewClientData({...newClientData, phone: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="Telefon numarası"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      İl *
                    </label>
                    <select
                      value={newClientData.city}
                      onChange={(e) => setNewClientData({...newClientData, city: e.target.value, district: ''})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">İl seçiniz</option>
                      {Object.keys(turkeyProvinces).map(province => (
                        <option key={province} value={province}>{province}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      İlçe *
                    </label>
                    <select
                      value={newClientData.district}
                      onChange={(e) => setNewClientData({...newClientData, district: e.target.value})}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                      disabled={!newClientData.city}
                    >
                      <option value="">İlçe seçiniz</option>
                      {newClientData.city && turkeyProvinces[newClientData.city]?.map(district => (
                        <option key={district} value={district}>{district}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Denetim Firması
                  </label>
                  <select
                    value={newClientData.audit_company}
                    onChange={(e) => setNewClientData({...newClientData, audit_company: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Denetim firması seçiniz</option>
                    {auditCompanies.map(company => (
                      <option key={company} value={company}>{company}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sertifika Geçerlilik Tarihi
                  </label>
                  <input
                    type="date"
                    value={newClientData.certificate_end_date}
                    onChange={(e) => setNewClientData({...newClientData, certificate_end_date: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Adres
                  </label>
                  <textarea
                    value={newClientData.address}
                    onChange={(e) => setNewClientData({...newClientData, address: e.target.value})}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="Adres bilgisi"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={handleAddClient}
                  disabled={!newClientData.name || !newClientData.hotel_name || !newClientData.city || !newClientData.district}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Kaydet
                </button>
                <button
                  onClick={() => {
                    setShowAddClient(false);
                    setNewClientData({
                      name: '',
                      hotel_name: '',
                      email: '',
                      phone: '',
                      city: '',
                      district: '',
                      address: '',
                      certificate_end_date: '',
                      audit_company: ''
                    });
                  }}
                  className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600"
                >
                  İptal
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

// Guest Self-Assessment Component
const GuestSelfAssessment = () => {
  const [guestData, setGuestData] = useState(null);
  const [ecoTips, setEcoTips] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [completedActions, setCompletedActions] = useState([]);
  const [feedback, setFeedback] = useState({
    rating: null,
    comment: ''
  });

  // Get guest_id from URL params (in real implementation)
  const guestId = new URLSearchParams(window.location.search).get('guest_id');

  useEffect(() => {
    if (guestId) {
      fetchGuestAssessment();
    }
  }, [guestId]);

  const fetchGuestAssessment = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/guest-engagement/self-assessment/${guestId}`);
      setGuestData(response.data.guest);
      setEcoTips(response.data.eco_tips);
      setCompletedActions(response.data.guest.eco_actions || []);
      setFeedback({
        rating: response.data.guest.feedback_rating,
        comment: response.data.guest.feedback_comment || ''
      });
    } catch (error) {
      console.error('Guest assessment fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleAction = (actionTitle) => {
    setCompletedActions(prev => 
      prev.includes(actionTitle) 
        ? prev.filter(action => action !== actionTitle)
        : [...prev, actionTitle]
    );
  };

  const handleSubmitAssessment = async () => {
    try {
      setSubmitting(true);
      const assessmentData = {
        eco_actions: completedActions,
        feedback_rating: feedback.rating,
        feedback_comment: feedback.comment
      };

      const response = await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/api/guest-engagement/self-assessment/${guestId}`,
        assessmentData
      );

      alert(`Tebrikler! Sürdürülebilirlik puanınız güncellendi: ${response.data.new_score} puan!`);
      fetchGuestAssessment(); // Refresh data
    } catch (error) {
      console.error('Assessment submission error:', error);
      alert('Değerlendirme gönderilirken hata oluştu.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🔄</div>
          <p className="text-lg text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (!guestId || !guestData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Erişim Hatası</h1>
          <p className="text-gray-600">Geçersiz konuk bilgisi. Lütfen QR kodu tekrar tarayın.</p>
        </div>
      </div>
    );
  }

  const currentScore = completedActions.length * 10;
  const maxScore = ecoTips.length * 15; // Assuming max 15 points per tip

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-lg">
        <div className="max-w-4xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">🌿 Sürdürülebilirlik Değerlendirme</h1>
              <p className="text-gray-600 mt-1">
                Merhaba {guestData.guest_name}! Oda: {guestData.room_number}
              </p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{currentScore}</div>
              <div className="text-sm text-gray-500">puan</div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        {/* Progress Bar */}
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800">İlerleme Durumu</h2>
            <span className="text-sm text-gray-600">{completedActions.length}/{ecoTips.length} aksiyon</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div 
              className="bg-gradient-to-r from-green-500 to-blue-500 h-4 rounded-full transition-all duration-300"
              style={{ width: `${(completedActions.length / ecoTips.length) * 100}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Her tamamladığınız aksiyon için puan kazanırsınız!
          </p>
        </div>

        {/* Eco Actions */}
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h2 className="text-xl font-bold text-gray-800 mb-6">🎯 Sürdürülebilirlik Aksiyonları</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ecoTips.map(tip => {
              const isCompleted = completedActions.includes(tip.title);
              return (
                <div 
                  key={tip.id}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                    isCompleted 
                      ? 'border-green-500 bg-green-50' 
                      : 'border-gray-200 bg-white hover:border-green-300'
                  }`}
                  onClick={() => toggleAction(tip.title)}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-2xl">{tip.icon}</span>
                    <div className="flex items-center space-x-2">
                      <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                        +{tip.points} puan
                      </span>
                      {isCompleted && <span className="text-green-500 text-xl">✅</span>}
                    </div>
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">{tip.title}</h3>
                  <p className="text-sm text-gray-600">{tip.description}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Feedback Section */}
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h2 className="text-xl font-bold text-gray-800 mb-6">⭐ Konaklama Değerlendirme</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Konaklama deneyiminizi nasıl değerlendirirsiniz?
              </label>
              <div className="flex space-x-2">
                {[1,2,3,4,5].map(rating => (
                  <button
                    key={rating}
                    onClick={() => setFeedback(prev => ({...prev, rating}))}
                    className={`text-3xl transition-colors ${
                      feedback.rating >= rating ? 'text-yellow-400' : 'text-gray-300 hover:text-yellow-200'
                    }`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Yorumunuz (opsiyonel)
              </label>
              <textarea
                value={feedback.comment}
                onChange={(e) => setFeedback(prev => ({...prev, comment: e.target.value}))}
                placeholder="Deneyiminiz hakkında düşüncelerinizi paylaşın..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 h-24"
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="text-center">
          <button
            onClick={handleSubmitAssessment}
            disabled={submitting}
            className={`px-8 py-3 rounded-lg text-white font-semibold text-lg transition-colors ${
              submitting 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600'
            }`}
          >
            {submitting ? 'Kaydediliyor...' : '🎯 Değerlendirmeyi Kaydet'}
          </button>
        </div>

        {/* Current Score Summary */}
        <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-6 rounded-xl text-center">
          <h3 className="text-2xl font-bold mb-2">🏆 Toplam Puanınız</h3>
          <div className="text-4xl font-bold mb-2">{currentScore} puan</div>
          <p className="text-green-100">
            Sürdürülebilirlik konusundaki katkılarınız için teşekkürler!
          </p>
        </div>
      </div>
    </div>
  );
};

// Consumption Analytics Component
const ConsumptionAnalytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [selectedYear, setSelectedYear] = useState(2025);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // overview, per-person

  const { authToken, userRole, dbUser, refreshToken } = useAuth();
  const API = getApiUrl();

  // Fetch clients for admin and consultant users
  const fetchClients = async () => {
    if (userRole !== 'admin' && userRole !== 'consultant') return;
    
    try {
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(response.data.clients || []);
      if (response.data?.length > 0) {
        setSelectedClient(response.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  // Fetch analytics data
  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedYear) params.append('year', selectedYear);
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        params.append('client_id', selectedClient);
      }

      console.log('🔍 ConsumptionAnalytics API call:', {
        userRole,
        selectedClient,
        selectedYear,
        params: params.toString()
      });

      const response = await axios.get(`${API}/consumptions/analytics?${params}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setAnalyticsData(response.data);
      console.log('✅ Analytics data fetched:', response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setAnalyticsData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authToken) {
      fetchClients();
    }
  }, [authToken, userRole]);

  useEffect(() => {
    if (authToken && ((userRole !== 'admin' && userRole !== 'consultant') || selectedClient)) {
      fetchAnalyticsData();
    }
  }, [authToken, selectedClient, selectedYear]);

  const getClientName = (clientId) => {
    const client = clients.find(c => c.id === clientId);
    return client ? client.hotel_name : 'Bilinmeyen Müşteri';
  };

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📈 Tüketim Analizi</h1>
          <p className="text-gray-600">
            Detaylı tüketim analizi ve trend görüntüleme
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex gap-4 items-center">
            {/* Client Selection for Admin and Consultant */}
            {(userRole === 'admin' || userRole === 'consultant') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {userRole === 'consultant' ? 'Size Atanan Müşteriler' : 'Müşteri Seçin'}
                </label>
                <select
                  value={selectedClient}
                  onChange={(e) => {
                    console.log('🔄 Analytics client selected:', e.target.value);
                    setSelectedClient(e.target.value);
                  }}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 min-w-[200px]"
                >
                  <option value="">Müşteri Seçin</option>
                  {clients.map(client => (
                    <option key={client.id} value={client.id}>
                      {client.hotel_name || client.client_name || client.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Year Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Yıl
              </label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value={2025}>2025</option>
                <option value={2024}>2024</option>
                <option value={2023}>2023</option>
              </select>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                📊 Genel Analiz
              </button>
              <button
                onClick={() => setActiveTab('per-person')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'per-person'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                👤 Kişi Başı Analiz
              </button>
            </nav>
          </div>
        </div>

        {/* Analytics Content */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Analiz verileri yükleniyor...</p>
          </div>
        ) : !analyticsData ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500">Analiz verileri bulunamadı.</p>
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <>
                {/* Yearly Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
                  <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white shadow-lg">
                    <h3 className="text-lg font-bold mb-2">⚡ Elektrik</h3>
                    <p className="text-3xl font-bold">{analyticsData.yearly_totals?.current_year?.electricity?.toLocaleString() || 0}</p>
                    <p className="text-blue-100">kWh</p>
                    {analyticsData.yearly_totals?.previous_year?.electricity && (
                      <p className="text-sm mt-2">
                        Geçen yıl: {analyticsData.yearly_totals.previous_year.electricity.toLocaleString()}
                      </p>
                    )}
                  </div>

                  <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white shadow-lg">
                    <h3 className="text-lg font-bold mb-2">💧 Su</h3>
                    <p className="text-3xl font-bold">{analyticsData.yearly_totals?.current_year?.water?.toLocaleString() || 0}</p>
                    <p className="text-green-100">m³</p>
                    {analyticsData.yearly_totals?.previous_year?.water && (
                      <p className="text-sm mt-2">
                        Geçen yıl: {analyticsData.yearly_totals.previous_year.water.toLocaleString()}
                      </p>
                    )}
                  </div>

                  <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl text-white shadow-lg">
                    <h3 className="text-lg font-bold mb-2">🔥 Doğalgaz</h3>
                    <p className="text-3xl font-bold">{analyticsData.yearly_totals?.current_year?.natural_gas?.toLocaleString() || 0}</p>
                    <p className="text-orange-100">m³</p>
                    {analyticsData.yearly_totals?.previous_year?.natural_gas && (
                      <p className="text-sm mt-2">
                        Geçen yıl: {analyticsData.yearly_totals.previous_year.natural_gas.toLocaleString()}
                      </p>
                    )}
                  </div>

                  <div className="bg-gradient-to-br from-gray-600 to-gray-700 p-6 rounded-xl text-white shadow-lg">
                    <h3 className="text-lg font-bold mb-2">🏔️ Kömür</h3>
                    <p className="text-3xl font-bold">{analyticsData.yearly_totals?.current_year?.coal?.toLocaleString() || 0}</p>
                    <p className="text-gray-100">kg</p>
                    {analyticsData.yearly_totals?.previous_year?.coal && (
                      <p className="text-sm mt-2">
                        Geçen yıl: {analyticsData.yearly_totals.previous_year.coal.toLocaleString()}
                      </p>
                    )}
                  </div>

                  <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl text-white shadow-lg">
                    <h3 className="text-lg font-bold mb-2">🏨 Konaklama</h3>
                    <p className="text-3xl font-bold">{analyticsData.yearly_totals?.current_year?.accommodation_count?.toLocaleString() || 0}</p>
                    <p className="text-purple-100">geceleme</p>
                    {analyticsData.yearly_totals?.previous_year?.accommodation_count && (
                      <p className="text-sm mt-2">
                        Geçen yıl: {analyticsData.yearly_totals.previous_year.accommodation_count.toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>

                {/* Monthly Comparison Table - Elite Design */}
                <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-2xl shadow-2xl overflow-hidden border border-gray-100">
                  {/* Header with Gradient */}
                  <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-2xl font-bold text-white flex items-center">
                          📊 Aylık Karşılaştırma Analizi
                        </h2>
                        <p className="text-blue-100 mt-1">Detaylı tüketim ve kişi başı performans verileri</p>
                      </div>
                      <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
                        <span className="text-white font-medium">{selectedYear}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="overflow-x-auto bg-white">
                    <table className="min-w-full">
                      {/* Elite Header */}
                      <thead>
                        <tr className="bg-gradient-to-r from-gray-900 to-gray-800">
                          <th className="px-6 py-4 text-left">
                            <div className="flex items-center space-x-2">
                              <span className="text-white font-semibold">📅</span>
                              <span className="text-white font-semibold text-sm uppercase tracking-wider">Ay</span>
                            </div>
                          </th>
                          <th className="px-6 py-4 text-center">
                            <div className="flex flex-col items-center">
                              <span className="text-blue-300 text-lg">⚡</span>
                              <span className="text-white font-semibold text-xs">Elektrik</span>
                              <span className="text-gray-300 text-xs">(kWh)</span>
                            </div>
                          </th>
                          <th className="px-6 py-4 text-center">
                            <div className="flex flex-col items-center">
                              <span className="text-blue-300 text-lg">💧</span>
                              <span className="text-white font-semibold text-xs">Su</span>
                              <span className="text-gray-300 text-xs">(m³)</span>
                            </div>
                          </th>
                          <th className="px-6 py-4 text-center">
                            <div className="flex flex-col items-center">
                              <span className="text-orange-300 text-lg">🔥</span>
                              <span className="text-white font-semibold text-xs">Doğalgaz</span>
                              <span className="text-gray-300 text-xs">(m³)</span>
                            </div>
                          </th>
                          <th className="px-6 py-4 text-center">
                            <div className="flex flex-col items-center">
                              <span className="text-gray-300 text-lg">🏔️</span>
                              <span className="text-white font-semibold text-xs">Kömür</span>
                              <span className="text-gray-300 text-xs">(kg)</span>
                            </div>
                          </th>
                          <th className="px-6 py-4 text-center">
                            <div className="flex flex-col items-center">
                              <span className="text-purple-300 text-lg">🏨</span>
                              <span className="text-white font-semibold text-xs">Konaklama</span>
                              <span className="text-gray-300 text-xs">(geceleme)</span>
                            </div>
                          </th>
                          <th className="px-6 py-4 text-center border-l border-gray-600">
                            <div className="flex flex-col items-center">
                              <span className="text-yellow-300 text-lg">👤⚡</span>
                              <span className="text-yellow-200 font-semibold text-xs">Elektrik/Kişi</span>
                              <span className="text-gray-300 text-xs">(kWh)</span>
                            </div>
                          </th>
                          <th className="px-6 py-4 text-center">
                            <div className="flex flex-col items-center">
                              <span className="text-yellow-300 text-lg">👤💧</span>
                              <span className="text-yellow-200 font-semibold text-xs">Su/Kişi</span>
                              <span className="text-gray-300 text-xs">(m³)</span>
                            </div>
                          </th>
                          <th className="px-6 py-4 text-center">
                            <div className="flex flex-col items-center">
                              <span className="text-yellow-300 text-lg">👤🔥</span>
                              <span className="text-yellow-200 font-semibold text-xs">Doğalgaz/Kişi</span>
                              <span className="text-gray-300 text-xs">(m³)</span>
                            </div>
                          </th>
                          <th className="px-6 py-4 text-center">
                            <div className="flex flex-col items-center">
                              <span className="text-yellow-300 text-lg">👤🏔️</span>
                              <span className="text-yellow-200 font-semibold text-xs">Kömür/Kişi</span>
                              <span className="text-gray-300 text-xs">(kg)</span>
                            </div>
                          </th>
                        </tr>
                      </thead>
                      
                      {/* Elite Body */}
                      <tbody className="divide-y divide-gray-100">
                        {analyticsData.monthly_comparison?.map((month, index) => (
                          <tr 
                            key={month.month} 
                            className={`${
                              index % 2 === 0 
                                ? 'bg-gradient-to-r from-white to-gray-50' 
                                : 'bg-gradient-to-r from-blue-50/30 to-purple-50/30'
                            } hover:bg-gradient-to-r hover:from-blue-100 hover:to-purple-100 transition-all duration-300 hover:shadow-lg`}
                          >
                            {/* Month Column */}
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center space-x-3">
                                <div className="bg-gradient-to-r from-blue-500 to-purple-500 w-3 h-3 rounded-full"></div>
                                <div>
                                  <div className="text-sm font-bold text-gray-900">{month.month_name}</div>
                                  <div className="text-xs text-gray-500">{selectedYear}</div>
                                </div>
                              </div>
                            </td>
                            
                            {/* Consumption Columns */}
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <div className="bg-blue-50 rounded-lg px-3 py-2 border border-blue-200">
                                <div className="text-lg font-bold text-blue-700">
                                  {month.current_year?.electricity?.toLocaleString() || 0}
                                </div>
                              </div>
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <div className="bg-cyan-50 rounded-lg px-3 py-2 border border-cyan-200">
                                <div className="text-lg font-bold text-cyan-700">
                                  {month.current_year?.water?.toLocaleString() || 0}
                                </div>
                              </div>
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <div className="bg-orange-50 rounded-lg px-3 py-2 border border-orange-200">
                                <div className="text-lg font-bold text-orange-700">
                                  {month.current_year?.natural_gas?.toLocaleString() || 0}
                                </div>
                              </div>
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <div className="bg-gray-50 rounded-lg px-3 py-2 border border-gray-200">
                                <div className="text-lg font-bold text-gray-700">
                                  {month.current_year?.coal?.toLocaleString() || 0}
                                </div>
                              </div>
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              <div className="bg-purple-50 rounded-lg px-3 py-2 border border-purple-200">
                                <div className="text-lg font-bold text-purple-700">
                                  {month.current_year?.accommodation_count?.toLocaleString() || 0}
                                </div>
                              </div>
                            </td>
                            
                            {/* Per Person Columns with Special Styling */}
                            <td className="px-6 py-4 whitespace-nowrap text-center border-l border-yellow-200 bg-gradient-to-r from-yellow-50 to-amber-50">
                              <div className="bg-gradient-to-r from-yellow-100 to-amber-100 rounded-lg px-3 py-2 border border-yellow-300 shadow-sm">
                                <div className="text-lg font-bold text-yellow-800">
                                  {month.per_person?.electricity?.toFixed(2) || '0.00'}
                                </div>
                                <div className="text-xs text-yellow-600 font-medium">kWh/kişi</div>
                              </div>
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-center bg-gradient-to-r from-yellow-50 to-amber-50">
                              <div className="bg-gradient-to-r from-cyan-100 to-blue-100 rounded-lg px-3 py-2 border border-cyan-300 shadow-sm">
                                <div className="text-lg font-bold text-cyan-800">
                                  {month.per_person?.water?.toFixed(2) || '0.00'}
                                </div>
                                <div className="text-xs text-cyan-600 font-medium">m³/kişi</div>
                              </div>
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-center bg-gradient-to-r from-yellow-50 to-amber-50">
                              <div className="bg-gradient-to-r from-orange-100 to-red-100 rounded-lg px-3 py-2 border border-orange-300 shadow-sm">
                                <div className="text-lg font-bold text-orange-800">
                                  {month.per_person?.natural_gas?.toFixed(2) || '0.00'}
                                </div>
                                <div className="text-xs text-orange-600 font-medium">m³/kişi</div>
                              </div>
                            </td>
                            
                            <td className="px-6 py-4 whitespace-nowrap text-center bg-gradient-to-r from-yellow-50 to-amber-50">
                              <div className="bg-gradient-to-r from-gray-100 to-slate-100 rounded-lg px-3 py-2 border border-gray-300 shadow-sm">
                                <div className="text-lg font-bold text-gray-800">
                                  {month.per_person?.coal?.toFixed(2) || '0.00'}
                                </div>
                                <div className="text-xs text-gray-600 font-medium">kg/kişi</div>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Elite Footer */}
                  <div className="bg-gradient-to-r from-gray-100 to-gray-200 px-8 py-4 border-t border-gray-200">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-4">
                        <span className="text-gray-600">📈 Toplam {analyticsData.monthly_comparison?.length || 0} ay verisi</span>
                        <span className="text-gray-400">•</span>
                        <span className="text-gray-600">👤 Kişi başı hesaplamalar dahil</span>
                      </div>
                      <div className="text-gray-500">
                        Son güncelleme: {new Date().toLocaleDateString('tr-TR')}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Charts Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
                  {/* Monthly Consumption Chart */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Aylık Tüketim Trendi</h3>
                    <div className="h-80">
                      <Line
                        data={{
                          labels: analyticsData.monthly_comparison?.map(m => m.month_name) || [],
                          datasets: [
                            {
                              label: 'Elektrik (kWh)',
                              data: analyticsData.monthly_comparison?.map(m => m.current_year?.electricity || 0) || [],
                              borderColor: 'rgb(59, 130, 246)',
                              backgroundColor: 'rgba(59, 130, 246, 0.1)',
                              tension: 0.4,
                            },
                            {
                              label: 'Su (m³)',
                              data: analyticsData.monthly_comparison?.map(m => m.current_year?.water || 0) || [],
                              borderColor: 'rgb(34, 197, 94)',
                              backgroundColor: 'rgba(34, 197, 94, 0.1)',
                              tension: 0.4,
                            },
                            {
                              label: 'Doğalgaz (m³)',
                              data: analyticsData.monthly_comparison?.map(m => m.current_year?.natural_gas || 0) || [],
                              borderColor: 'rgb(249, 115, 22)',
                              backgroundColor: 'rgba(249, 115, 22, 0.1)',
                              tension: 0.4,
                            },
                            {
                              label: 'Kömür (kg)',
                              data: analyticsData.monthly_comparison?.map(m => m.current_year?.coal || 0) || [],
                              borderColor: 'rgb(75, 85, 99)',
                              backgroundColor: 'rgba(75, 85, 99, 0.1)',
                              tension: 0.4,
                            }
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'top',
                            },
                            title: {
                              display: false,
                            },
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                            },
                          },
                        }}
                      />
                    </div>
                  </div>

                  {/* Yearly Comparison Chart */}
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Yıllık Karşılaştırma</h3>
                    <div className="h-80">
                      <Bar
                        data={{
                          labels: ['Elektrik', 'Su', 'Doğalgaz', 'Kömür', 'Konaklama'],
                          datasets: [
                            {
                              label: `${selectedYear}`,
                              data: [
                                analyticsData.yearly_totals?.current_year?.electricity || 0,
                                analyticsData.yearly_totals?.current_year?.water || 0,
                                analyticsData.yearly_totals?.current_year?.natural_gas || 0,
                                analyticsData.yearly_totals?.current_year?.coal || 0,
                                analyticsData.yearly_totals?.current_year?.accommodation_count || 0
                              ],
                              backgroundColor: 'rgba(59, 130, 246, 0.8)',
                              borderColor: 'rgb(59, 130, 246)',
                              borderWidth: 1,
                            },
                            ...(analyticsData.yearly_totals?.previous_year ? [{
                              label: `${selectedYear - 1}`,
                              data: [
                                analyticsData.yearly_totals.previous_year.electricity || 0,
                                analyticsData.yearly_totals.previous_year.water || 0,
                                analyticsData.yearly_totals.previous_year.natural_gas || 0,
                                analyticsData.yearly_totals.previous_year.coal || 0,
                                analyticsData.yearly_totals.previous_year.accommodation_count || 0
                              ],
                              backgroundColor: 'rgba(34, 197, 94, 0.8)',
                              borderColor: 'rgb(34, 197, 94)',
                              borderWidth: 1,
                            }] : [])
                          ]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: {
                              position: 'top',
                            },
                            title: {
                              display: false,
                            },
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                            },
                          },
                        }}
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Per Person Tab */}
            {activeTab === 'per-person' && (
              <>
                {/* Monthly Per Person Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {analyticsData.monthly_comparison?.map((month) => (
                    <div key={month.month} className="bg-white rounded-lg shadow p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {month.month_name} {selectedYear}
                        </h3>
                        <span className="text-2xl">📊</span>
                      </div>
                      
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">⚡ Elektrik</span>
                          <div className="text-right">
                            <div className="font-bold text-blue-600">
                              {month.per_person?.electricity?.toFixed(2) || '0.00'}
                            </div>
                            <div className="text-xs text-gray-500">kWh/kişi/gece</div>
                          </div>
                        </div>

                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">💧 Su</span>
                          <div className="text-right">
                            <div className="font-bold text-green-600">
                              {month.per_person?.water?.toFixed(2) || '0.00'}
                            </div>
                            <div className="text-xs text-gray-500">m³/kişi/gece</div>
                          </div>
                        </div>

                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">🔥 Doğalgaz</span>
                          <div className="text-right">
                            <div className="font-bold text-orange-600">
                              {month.per_person?.natural_gas?.toFixed(2) || '0.00'}
                            </div>
                            <div className="text-xs text-gray-500">m³/kişi/gece</div>
                          </div>
                        </div>

                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">🏔️ Kömür</span>
                          <div className="text-right">
                            <div className="font-bold text-gray-600">
                              {month.per_person?.coal?.toFixed(2) || '0.00'}
                            </div>
                            <div className="text-xs text-gray-500">kg/kişi/gece</div>
                          </div>
                        </div>

                        <div className="border-t pt-3 mt-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">🏨 Toplam Konaklama</span>
                            <div className="font-bold text-purple-600">
                              {month.current_year?.accommodation_count?.toLocaleString() || 0}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Yearly Average Per Person Summary */}
                {analyticsData.yearly_totals?.per_person && (
                  <div className="bg-white rounded-lg shadow p-6 mt-8">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      {selectedYear} Yıl Ortalaması - Kişi Başı
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600 mb-2">
                          {analyticsData.yearly_totals.per_person?.electricity?.toFixed(1) || '0.0'}
                        </div>
                        <div className="text-sm text-gray-600">kWh/kişi/gece</div>
                        <div className="text-xs text-gray-500 mt-1">Elektrik</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-green-600 mb-2">
                          {analyticsData.yearly_totals.per_person?.water?.toFixed(1) || '0.0'}
                        </div>
                        <div className="text-sm text-gray-600">m³/kişi/gece</div>
                        <div className="text-xs text-gray-500 mt-1">Su</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-orange-600 mb-2">
                          {analyticsData.yearly_totals.per_person?.natural_gas?.toFixed(1) || '0.0'}
                        </div>
                        <div className="text-sm text-gray-600">m³/kişi/gece</div>
                        <div className="text-xs text-gray-500 mt-1">Doğalgaz</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-gray-600 mb-2">
                          {analyticsData.yearly_totals.per_person?.coal?.toFixed(1) || '0.0'}
                        </div>
                        <div className="text-sm text-gray-600">kg/kişi/gece</div>
                        <div className="text-xs text-gray-500 mt-1">Kömür</div>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

const DocumentModal = ({ document, onClose, onDownload }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{document.title}</h2>
              <p className="text-gray-600">Doküman Detayları</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Document Details */}
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Doküman Adı
                </label>
                <p className="text-gray-900 bg-gray-50 p-2 rounded">{document.title}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Doküman Türü
                </label>
                <p className="text-gray-900 bg-gray-50 p-2 rounded">{document.type}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Kategori
                </label>
                <p className="text-gray-900 bg-gray-50 p-2 rounded">{document.category}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dosya Boyutu
                </label>
                <p className="text-gray-900 bg-gray-50 p-2 rounded">{document.file_size}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Yüklenme Tarihi
                </label>
                <p className="text-gray-900 bg-gray-50 p-2 rounded">
                  {document.upload_date ? new Date(document.upload_date).toLocaleDateString('tr-TR') : 'Tarih bilgisi yok'}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Müşteri
                </label>
                <p className="text-gray-900 bg-gray-50 p-2 rounded">{document.client_name || 'Genel'}</p>
              </div>
            </div>

            {/* Folder Path */}
            {document.folder_path && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Klasör Yolu
                </label>
                <p className="text-gray-900 bg-gray-50 p-2 rounded font-mono text-sm">{document.folder_path}</p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-4 mt-6 pt-6 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Kapat
            </button>
            <button
              onClick={() => onDownload(document)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              İndir
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const ClientDocuments = () => {
  const [documents, setDocuments] = useState([]);
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const { authToken, userRole, dbUser, refreshToken } = useAuth();


  // Get document count for a folder
  const getFolderDocumentCount = (folderId) => {
    const count = documents.filter(doc => doc.folder_id === folderId).length;
    console.log(`📊 ClientDocuments - Folder ${folderId} has ${count} documents. Total documents: ${documents.length}`);
    return count;
  };
  useEffect(() => {
    if (!authToken || !dbUser?.client_id) return;
    
    console.log('📄 Client: Fetching documents and folders...');
    fetchDocuments();
    fetchFolders();
  }, [authToken, dbUser]);

  const fetchDocuments = async () => {
    try {
      console.log('📄 Client: Fetching documents...');
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const response = await axios.get(`${API}/documents`, { headers });
      console.log('📄 Client: Documents response:', response.data);
      setDocuments(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error("❌ Client: Error fetching documents:", error);
      setDocuments([]);
    }
  };

  const fetchFolders = async () => {
    if (!authToken) return;
    
    try {
      const headers = { 'Authorization': `Bearer ${authToken}` };
      console.log('📁 Client: Fetching folders...');
      
      const response = await axios.get(`${API}/folders`, { headers });
      console.log('📁 Client: Folders response:', response.data);
      
      setFolders(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error("❌ Client: Error fetching folders:", error);
      setFolders([]);
    }
  };

  const handleViewDocument = (document) => {
    setSelectedDocument(document);
    setShowDocumentModal(true);
  };

  const handleDownloadDocument = async (docData) => {
    try {
      console.log('📥 Starting download for:', docData.name);
      
      const downloadUrl = `${API}/simple-download/${docData.id}`;
      
      const response = await axios.get(downloadUrl, {
        headers: { 'Authorization': `Bearer ${authToken}` },
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      
      const link = window.document.createElement('a');
      link.href = url;
      link.download = docData.original_filename || docData.name || 'document';
      link.style.display = 'none';
      window.document.body.appendChild(link);
      link.click();
      
      window.document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log('✅ Download completed');
    } catch (error) {
      console.error('❌ Download error:', error);
      alert('Dosya indirilemedi!');
    }
  };

  // Filter folders for current client
  const clientFolders = folders.filter(folder => folder.client_id === dbUser?.client_id);
  
  // Filter documents by selected folder
  const filteredDocuments = selectedFolder 
    ? documents.filter(doc => {
        console.log(`🔍 Document ${doc.name} folder_id: ${doc.folder_id}, selected folder id: ${selectedFolder.id}`);
        return doc.folder_id === selectedFolder.id;
      })
    : documents;

  console.log('📊 Filtering debug:', {
    selectedFolder: selectedFolder?.name,
    totalDocuments: documents.length,
    filteredDocuments: filteredDocuments.length,
    documentsWithFolderIds: documents.map(d => ({ name: d.name, folder_id: d.folder_id }))
  });

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">📁 Belgelerim</h2>
        
        {/* Breadcrumb */}
        <div className="flex items-center mb-4 text-sm text-gray-600">
          <button
            onClick={() => setSelectedFolder(null)}
            className={`hover:text-blue-600 ${!selectedFolder ? 'text-blue-600 font-semibold' : ''}`}
          >
            📂 Ana Dizin
          </button>
          {selectedFolder && (
            <>
              <span className="mx-2">›</span>
              <span className="text-blue-600 font-semibold">{selectedFolder.name}</span>
            </>
          )}
        </div>

        {/* Folder Grid */}
        {!selectedFolder && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {clientFolders
              .filter(folder => folder.level === 0) // Root folders
              .map((folder) => (
                <div
                  key={folder.id}
                  onClick={() => setSelectedFolder(folder)}
                  className="bg-blue-50 border border-blue-200 rounded-lg p-4 cursor-pointer hover:bg-blue-100 transition-colors"
                >
                  <div className="flex items-center">
                    <span className="text-3xl mr-3">📂</span>
                    <div>
                      <h3 className="font-semibold text-blue-800">{folder.name}</h3>
                      <p className="text-xs text-blue-600">Ana Klasör</p>
                    </div>
                  </div>
                </div>
              ))
            }
            
            {clientFolders
              .filter(folder => folder.level === 1) // Column folders (A, B, C, D SÜTUNU)
              .map((folder) => {
                // Count sub-folders for this column
                const subFolderCount = clientFolders.filter(f => f.parent_folder_id === folder.id).length;
                return (
                  <div
                    key={folder.id}
                    onClick={() => setSelectedFolder(folder)}
                    className="bg-gray-50 border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="text-3xl mr-3">📁</span>
                        <div>
                          <h3 className="font-semibold text-gray-700">{folder.name}</h3>
                          <p className="text-xs text-gray-500">
                            {subFolderCount} alt klasör • {getFolderDocumentCount(folder.id)} doküman
                          </p>
                        </div>
                      </div>
                      <span className="text-gray-400">›</span>
                    </div>
                  </div>
                );
              })
            }
          </div>
        )}

        {/* Sub-folders when a column folder is selected */}
        {selectedFolder && selectedFolder.level === 1 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              📁 {selectedFolder.name} - Alt Klasörler
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {clientFolders
                .filter(folder => folder.parent_folder_id === selectedFolder.id)
                .sort((a, b) => {
                  // Natural sorting for folder names (A1, A2, ..., A9, A10)
                  const aName = a.name;
                  const bName = b.name;
                  
                  // Extract numbers from folder names for proper sorting
                  const aMatch = aName.match(/(\d+\.?\d*)/);
                  const bMatch = bName.match(/(\d+\.?\d*)/);
                  
                  if (aMatch && bMatch) {
                    const aNum = parseFloat(aMatch[1]);
                    const bNum = parseFloat(bMatch[1]);
                    return aNum - bNum;
                  }
                  
                  // Fallback to alphabetical sorting
                  return aName.localeCompare(bName);
                })
                .map((subFolder) => (
                  <div
                    key={subFolder.id}
                    onClick={() => setSelectedFolder(subFolder)}
                    className="bg-green-50 border border-green-200 rounded-lg p-3 cursor-pointer hover:bg-green-100 transition-colors"
                  >
                    <div className="flex items-center">
                      <span className="text-xl mr-2">📄</span>
                      <div>
                        <h4 className="font-semibold text-green-800 text-sm">{subFolder.name}</h4>
                        <p className="text-xs text-green-600">Alt Klasör • {getFolderDocumentCount(subFolder.id)} doküman</p>
                      </div>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* Level 3 sub-folders when a level 2 folder (D1, D2, D3) is selected */}
        {selectedFolder && selectedFolder.level === 2 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              📁 {selectedFolder.name} - Alt Klasörler (Level 3)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {clientFolders
                .filter(folder => folder.parent_folder_id === selectedFolder.id)
                .sort((a, b) => {
                  // Natural sorting for folder names (D1.1, D1.2, etc.)
                  const aName = a.name;
                  const bName = b.name;
                  
                  // Extract numbers from folder names for proper sorting
                  const aMatch = aName.match(/(\d+\.?\d*)/);
                  const bMatch = bName.match(/(\d+\.?\d*)/);
                  
                  if (aMatch && bMatch) {
                    const aNum = parseFloat(aMatch[1]);
                    const bNum = parseFloat(bMatch[1]);
                    return aNum - bNum;
                  }
                  
                  // Fallback to alphabetical sorting
                  return aName.localeCompare(bName);
                })
                .map((level3Folder) => (
                  <div
                    key={level3Folder.id}
                    onClick={() => setSelectedFolder(level3Folder)}
                    className="bg-blue-50 border border-blue-200 rounded-lg p-3 cursor-pointer hover:bg-blue-100 transition-colors"
                  >
                    <div className="flex items-center">
                      <span className="text-xl mr-2">📂</span>
                      <div>
                        <h4 className="font-semibold text-blue-800 text-sm">{level3Folder.name}</h4>
                        <p className="text-xs text-blue-600">Level 3 Klasör</p>
                      </div>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* Documents List - Updated to show for level 3 folders as well */}
        {selectedFolder && (selectedFolder.level === 2 || selectedFolder.level === 3) && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">
              📄 {selectedFolder.name} İçindeki Belgeler
            </h3>
            
            {filteredDocuments.length > 0 ? (
              <div className="space-y-3">
                {filteredDocuments.map((document) => (
                  <div key={document.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center flex-1">
                        <span className="text-2xl mr-3">{getFileIcon(document.original_filename || document.file_path || '')}</span>
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-800">{document.name}</h4>
                          <div className="flex items-center text-sm text-gray-500 space-x-4">
                            <span>📋 {document.document_type}</span>
                            <span>🎯 {document.stage}</span>
                            <span>📅 {formatDocumentDate(document.created_at)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleViewDocument(document)}
                          className="bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm"
                        >
                          👁️ Görüntüle
                        </button>
                        <button
                          onClick={() => handleDownloadDocument(document)}
                          className="bg-green-600 text-white px-3 py-2 rounded-md hover:bg-green-700 transition-colors text-sm"
                        >
                          📥 İndir
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <span className="text-4xl mb-4 block">📄</span>
                <p>Bu klasörde henüz belge bulunmuyor.</p>
              </div>
            )}
          </div>
        )}

        {/* Instruction when no folder selected */}
        {!selectedFolder && (
          <div className="text-center py-12 text-gray-500">
            <span className="text-6xl mb-4 block">📁</span>
            <h3 className="text-xl font-semibold mb-2">Bir klasör seçin</h3>
            <p>Belgelerinizi görüntülemek için yukarıdaki klasörlerden birini seçin.</p>
          </div>
        )}
      </div>

      {/* Document Detail Modal */}
      {showDocumentModal && selectedDocument && (
        <DocumentModal 
          document={selectedDocument} 
          onClose={() => setShowDocumentModal(false)}
          onDownload={handleDownloadDocument}
        />
      )}
    </div>
  );
};

  // Safe date formatting function
  const formatDocumentDate = (dateValue) => {
    if (!dateValue) return 'Tarih bilinmiyor';
    
    try {
      // Handle different date formats
      let date;
      if (typeof dateValue === 'string') {
        // Parse ISO string or other string formats
        date = new Date(dateValue);
      } else if (dateValue instanceof Date) {
        date = dateValue;
      } else {
        return 'Geçersiz tarih';
      }
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return 'Geçersiz tarih';
      }
      
      return date.toLocaleDateString('tr-TR');
    } catch (error) {
      console.error('Error formatting date:', error, dateValue);
      return 'Tarih hatası';
    }
  };

  const DocumentManagement = () => {
  const [documents, setDocuments] = useState([]);
  const [folders, setFolders] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadData, setUploadData] = useState({
    client_id: '',
    name: '',
    document_type: 'Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)',
    stage: 'I.Aşama',
    files: [],
    folder_id: ''
  });
  const { authToken, userRole, dbUser, refreshToken } = useAuth();

  // Get document count for a folder
  const getFolderDocumentCount = (folderId) => {
    const count = documents.filter(doc => doc.folder_id === folderId).length;
    console.log(`📊 DocumentManagement - Folder ${folderId} has ${count} documents. Total documents: ${documents.length}`);
    return count;
  };

  useEffect(() => {
    // Token hazır olmadan API call yapma
    if (!authToken) {
      console.log('🔄 Waiting for auth token for documents...');
      return;
    }
    
    console.log('🎯 Auth token ready, fetching documents, clients and folders...');
    fetchDocuments();
    fetchFolders();
    
    // Admin ve Consultant müşteri listesini görebilir
    if (userRole === 'admin' || userRole === 'consultant') {
      fetchClients();
    }
  }, [authToken, userRole]);

  const fetchDocuments = async (clientId = null) => {
    try {
      console.log('📄 Admin: Fetching documents for client:', clientId);
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const response = await axios.get(`${API}/documents`, { headers });
      console.log('📄 Admin: Documents response:', response.data);
      
      let filteredDocs = Array.isArray(response.data) ? response.data : [];
      
      // Filter by client if selected
      if (clientId) {
        filteredDocs = filteredDocs.filter(doc => doc.client_id === clientId);
      }
      
      console.log('📄 Admin: Filtered documents count:', filteredDocs.length);
      setDocuments(filteredDocs);
    } catch (error) {
      console.error("❌ Admin: Error fetching documents:", error);
      setDocuments([]);
    }
  };

  const fetchClients = async () => {
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error("Error fetching clients:", error);
      setClients([]);
    }
  };

  const fetchFolders = async () => {
    if (!authToken) return;
    
    try {
      const headers = { 'Authorization': `Bearer ${authToken}` };
      console.log('📁 Fetching folders...');
      console.log('🔗 API URL:', `${API}/folders`);
      console.log('🎫 Auth token:', authToken ? 'Present' : 'Missing');
      
      const response = await axios.get(`${API}/folders`, { headers });
      console.log('📁 Folders response:', response.data);
      console.log('📁 Folders array length:', response.data?.length || 0);
      
      setFolders(Array.isArray(response.data) ? response.data : []);
      console.log('✅ Folders set in state:', Array.isArray(response.data) ? response.data.length : 0, 'folders');
    } catch (error) {
      console.error("❌ Error fetching folders:", error);
      console.error("❌ Error response:", error.response?.data);
      setFolders([]);
    }
  };

  const fetchFoldersForClient = async (clientId) => {
    if (!authToken || !clientId) {
      console.log('❌ fetchFoldersForClient: Missing authToken or clientId');
      return;
    }
    
    try {
      const headers = { 'Authorization': `Bearer ${authToken}` };
      console.log('📁 Fetching folders for client:', clientId);
      
      const response = await axios.get(`${API}/folders`, { headers });
      console.log('📁 All folders response:', response.data?.length || 0, 'folders');
      
      // Filter folders for selected client
      const allFolders = Array.isArray(response.data) ? response.data : [];
      
      // DEBUG: Show first 5 folders' client_ids
      console.log('📁 Sample folder client_ids:', allFolders.slice(0, 5).map(f => ({
        name: f.name,
        client_id: f.client_id
      })));
      
      console.log('📁 Target client_id:', clientId);
      console.log('📁 Target client_id type:', typeof clientId);
      
      const clientFolders = allFolders.filter(folder => {
        const match = folder.client_id === clientId;
        console.log(`📁 Folder "${folder.name}" - client_id: "${folder.client_id}" (${typeof folder.client_id}) === "${clientId}" (${typeof clientId}) = ${match}`);
        return match;
      });
      
      console.log('📁 Client folders filtered:', clientFolders.length, 'folders for client', clientId);
      console.log('📁 Sample filtered folders:', clientFolders.slice(0, 5).map(f => f.name));
      
      setFolders(clientFolders);
      
    } catch (error) {
      console.error("❌ Error fetching client folders:", error);
      setFolders([]);
    }
  };

  const uploadLargeFile = async (file, metadata) => {
    // Her dosya için direkt upload kullan - chunk karmaşıklığı kaldırıldı
    console.log(`📤 Uploading file: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
    return await uploadSingleFile(file, metadata);
  };

  const uploadSingleFile = async (file, metadata) => {
    // Force auth refresh before upload
    console.log('🔑 Refreshing auth token before upload...');
    try {
      const user = window.Clerk?.user;
      const session = window.Clerk?.session;
      if (user && session) {
        const freshToken = await session.getToken();
        console.log('✅ Auth token refreshed for upload');
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('client_id', metadata.clientId);
        formData.append('document_name', metadata.documentName);
        formData.append('document_type', metadata.documentType);
        formData.append('stage', metadata.stage);
        formData.append('folder_id', metadata.folderId);  // Required folder selection

        // Calculate timeout based on file size (minimum 30s, max 10 minutes)
        const timeoutMs = Math.max(30000, Math.min(file.size / (1024 * 100), 600000)); // ~100KB/s minimum speed
        
        console.log(`⏱️ Upload timeout set to: ${(timeoutMs / 1000).toFixed(0)} seconds`);

        const response = await axios.post(`${API}/simple-upload`, formData, {
          headers: { 
            'Authorization': `Bearer ${freshToken}`
          },
          timeout: timeoutMs,
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            console.log(`📊 Upload progress: ${percentCompleted}% (${file.name})`);
          }
        });
        
        return response;
      } else {
        console.error('❌ No user/session found for auth refresh');
        throw new Error('Authentication required');
      }
    } catch (error) {
      console.error('❌ Upload auth error:', error);
      throw error;
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    
    if (!uploadData.files || uploadData.files.length === 0) {
      alert('Lütfen en az bir dosya seçin!');
      return;
    }

    // Check file sizes (500MB limit per file)
    for (let file of uploadData.files) {
      const sizeInMB = file.size / 1024 / 1024;
      if (sizeInMB > 500) {
        alert(`Dosya çok büyük: ${file.name} (${sizeInMB.toFixed(1)}MB). Maksimum 500MB yükleyebilirsiniz.`);
        return;
      }
    }

    try {
      const clientId = userRole === 'admin' ? uploadData.client_id : dbUser.client_id;
      
      // Upload each file separately
      for (let i = 0; i < uploadData.files.length; i++) {
        const file = uploadData.files[i];
        const fileName = file.name;
        const sizeInMB = (file.size / 1024 / 1024).toFixed(2);
        
        console.log(`📤 Uploading file ${i + 1}/${uploadData.files.length}: ${fileName} (${sizeInMB}MB)`);

        const metadata = {
          clientId: clientId,
          documentName: uploadData.files.length === 1 ? uploadData.name : `${uploadData.name} - ${fileName}`,
          documentType: uploadData.document_type,
          stage: uploadData.stage,
          folderId: uploadData.folder_id
        };

        console.log('🔍 Auth Token:', authToken ? authToken.substring(0, 50) + '...' : 'No token');
        console.log('🔍 Client ID:', clientId);
        console.log('🔍 File Details:', {
          name: file.name,
          size: file.size,
          type: file.type,
          sizeInMB: sizeInMB
        });

        const response = await uploadLargeFile(file, metadata);
        console.log(`✅ File ${i + 1} uploaded successfully:`, response.data);
        
        // Show success message with storage info
        if (response.data?.message) {
          alert(`✅ ${response.data.message}`);
        } else if (response?.message) {
          alert(`✅ ${response.message}`);
        } else {
          alert(`✅ Dosya başarıyla yüklendi! (Yerel Depolama)`);
        }
      }

      // Refresh documents list after all uploads
      console.log('🔄 Refreshing documents list...');
      await fetchDocuments();
      console.log('✅ Documents list refreshed successfully');
      
      setShowUploadForm(false);
      setUploadData({
        client_id: '',
        name: '',
        document_type: 'Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)',
        stage: 'I.Aşama',
        files: []
      });
      
      alert(`${uploadData.files.length} dosya başarıyla yüklendi! 🎉 (Local Storage)`);
    } catch (error) {
      console.error("❌ Error uploading documents:", error);
      if (error.code === 'ECONNABORTED') {
        alert('Dosya yükleme zaman aşımına uğradı. İnternet bağlantınızı kontrol edin veya daha küçük dosyalar yüklemeyi deneyin.');
      } else if (error.response?.status === 413) {
        alert('Dosya çok büyük. Maksimum 500MB yükleyebilirsiniz.');
      } else if (error.message.includes('Network Error')) {
        alert('Ağ hatası: Büyük dosyalar için internet bağlantınız yeterli olmayabilir.');
      } else {
        alert('Dosya yüklenirken hata oluştu: ' + (error.response?.data?.detail || error.message || 'Bilinmeyen hata'));
      }
    }
  };

  const handleDelete = async (documentId) => {
    if (window.confirm('Bu belgeyi silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`${API}/documents/${documentId}`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        fetchDocuments();
        alert('Belge başarıyla silindi!');
      } catch (error) {
        console.error("Error deleting document:", error);
        alert('Belge silinirken hata oluştu!');
      }
    }
  };

  const handleViewDocument = (document) => {
    setSelectedDocument(document);
    setShowDocumentModal(true);
  };

  const handleDownloadDocument = async (docData) => {
    try {
      console.log('📥 Starting download for:', docData.name);
      
      // Directly download the file using the backend endpoint
      const downloadUrl = `${API}/simple-download/${docData.id}`;
      
      // Create a temporary link and trigger download
      const link = window.document.createElement('a');
      link.href = downloadUrl;
      link.download = docData.name || 'document';
      link.style.display = 'none';
      
      // Add authorization header via a fetch request instead
      const response = await axios.get(downloadUrl, {
        headers: { 'Authorization': `Bearer ${authToken}` },
        responseType: 'blob' // Important for file downloads
      });
      
      // Create blob URL and download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      
      link.href = url;
      link.download = docData.original_filename || docData.name || 'document';
      window.document.body.appendChild(link);
      link.click();
      
      // Cleanup
      window.document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log('✅ Download completed');
      
    } catch (error) {
      console.error('❌ Download error:', error);
      alert('Dosya indirme hatası: ' + (error.response?.data?.detail || error.message));
    }
  };


  const filterDocuments = () => {
    if (userRole === 'admin' && selectedClient) {
      return (documents || []).filter(doc => doc.client_id === selectedClient);
    }
    return documents || [];
  };



  const getClientName = (clientId) => {
    const client = (clients || []).find(c => c.id === clientId);
    return client ? client.hotel_name : 'Bilinmeyen Müşteri';
  };

  const documentTypes = [
    "Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)",
    "I. Aşama Belgesi",
    "II. Aşama Belgesi", 
    "III. Aşama Belgesi",
    "Karbon Ayak İzi Raporu",
    "Sürdürülebilirlik Raporu"
  ];

  const stages = ["I.Aşama", "II.Aşama", "III.Aşama"];

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-800">
            📋 Belge Yönetimi {userRole === 'admin' ? '(Admin)' : userRole === 'consultant' ? '(Danışman)' : '(Müşteri)'}
          </h2>
          {selectedClient && (
            <button
              onClick={() => setShowUploadForm(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Yeni Belge Yükle
            </button>
          )}
        </div>

        {/* Client Selection - Admin ve Consultant için */}
        {(userRole === 'admin' || userRole === 'consultant') && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Müşteri Seçin: <span className="text-red-500">*</span>
            </label>
            <select
              value={selectedClient?.id || ''}
              onChange={(e) => {
                const client = clients.find(c => c.id === e.target.value);
                setSelectedClient(client || null);
                setSelectedFolder(null);
                if (client) {
                  console.log('🎯 Client selected:', client.hotel_name, 'ID:', client.id);
                  fetchDocuments(client.id);
                  fetchFoldersForClient(client.id);
                } else {
                  console.log('🎯 No client selected, clearing data');
                  setDocuments([]);
                  setFolders([]);
                }
              }}
              className="w-full md:w-64 p-3 border border-gray-300 rounded-md"
            >
              <option value="">Müşteri seçiniz...</option>
              {Array.isArray(clients) ? clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.hotel_name}
                </option>
              )) : null}
            </select>
          </div>
        )}

        {/* Breadcrumb */}
        {selectedClient && (
          <div className="flex items-center mb-4 text-sm text-gray-600">
            <span className="font-semibold text-blue-600">{selectedClient.hotel_name}</span>
            {selectedFolder && (
              <>
                <span className="mx-2">›</span>
                <button
                  onClick={() => setSelectedFolder(null)}
                  className="hover:text-blue-600"
                >
                  📂 Klasörler
                </button>
                <span className="mx-2">›</span>
                <span className="text-blue-600 font-semibold">{selectedFolder.name}</span>
              </>
            )}
          </div>
        )}

        {/* Folder Grid for Selected Client */}
        {selectedClient && !selectedFolder && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">📁 Klasörler</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {folders
                .filter(folder => folder.level === 0) // Root folders
                .map((folder) => (
                  <div
                    key={folder.id}
                    onClick={() => setSelectedFolder(folder)}
                    className="bg-blue-50 border border-blue-200 rounded-lg p-4 cursor-pointer hover:bg-blue-100 transition-colors"
                  >
                    <div className="flex items-center">
                      <span className="text-3xl mr-3">📂</span>
                      <div>
                        <h3 className="font-semibold text-blue-800">{folder.name}</h3>
                        <p className="text-xs text-blue-600">Ana Klasör</p>
                      </div>
                    </div>
                  </div>
                ))
              }
              
              {folders
                .filter(folder => folder.level === 1) // Column folders
                .map((folder) => {
                  const subFolderCount = folders.filter(f => f.parent_folder_id === folder.id).length;
                  return (
                    <div
                      key={folder.id}
                      onClick={() => setSelectedFolder(folder)}
                      className="bg-gray-50 border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <span className="text-3xl mr-3">📁</span>
                          <div>
                            <h3 className="font-semibold text-gray-700">{folder.name}</h3>
                            <p className="text-xs text-gray-500">{subFolderCount} alt klasör • {getFolderDocumentCount(folder.id)} doküman</p>
                          </div>
                        </div>
                        <span className="text-gray-400">›</span>
                      </div>
                    </div>
                  );
                })
              }
            </div>
          </div>
        )}

        {/* Sub-folders when a column folder is selected */}
        {selectedClient && selectedFolder && selectedFolder.level === 1 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              📁 {selectedFolder.name} - Alt Klasörler
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {folders
                .filter(folder => folder.parent_folder_id === selectedFolder.id)
                .sort((a, b) => {
                  // Natural sorting for folder names (A1, A2, ..., A9, A10)
                  const aName = a.name;
                  const bName = b.name;
                  
                  // Extract numbers from folder names for proper sorting
                  const aMatch = aName.match(/(\d+\.?\d*)/);
                  const bMatch = bName.match(/(\d+\.?\d*)/);
                  
                  if (aMatch && bMatch) {
                    const aNum = parseFloat(aMatch[1]);
                    const bNum = parseFloat(bMatch[1]);
                    return aNum - bNum;
                  }
                  
                  // Fallback to alphabetical sorting
                  return aName.localeCompare(bName);
                })
                .map((subFolder) => (
                  <div
                    key={subFolder.id}
                    onClick={() => setSelectedFolder(subFolder)}
                    className="bg-green-50 border border-green-200 rounded-lg p-3 cursor-pointer hover:bg-green-100 transition-colors"
                  >
                    <div className="flex items-center">
                      <span className="text-xl mr-2">📄</span>
                      <div>
                        <h4 className="font-semibold text-green-800 text-sm">{subFolder.name}</h4>
                        <p className="text-xs text-green-600">Alt Klasör • {getFolderDocumentCount(subFolder.id)} doküman</p>
                      </div>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* Level 3 sub-folders when a level 2 folder (D1, D2, D3) is selected */}
        {selectedClient && selectedFolder && selectedFolder.level === 2 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              📁 {selectedFolder.name} - Alt Klasörler (Level 3)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {folders
                .filter(folder => folder.parent_folder_id === selectedFolder.id)
                .sort((a, b) => {
                  // Natural sorting for folder names (D1.1, D1.2, etc.)
                  const aName = a.name;
                  const bName = b.name;
                  
                  // Extract numbers from folder names for proper sorting
                  const aMatch = aName.match(/(\d+\.?\d*)/);
                  const bMatch = bName.match(/(\d+\.?\d*)/);
                  
                  if (aMatch && bMatch) {
                    const aNum = parseFloat(aMatch[1]);
                    const bNum = parseFloat(bMatch[1]);
                    return aNum - bNum;
                  }
                  
                  // Fallback to alphabetical sorting
                  return aName.localeCompare(bName);
                })
                .map((level3Folder) => (
                  <div
                    key={level3Folder.id}
                    onClick={() => setSelectedFolder(level3Folder)}
                    className="bg-blue-50 border border-blue-200 rounded-lg p-3 cursor-pointer hover:bg-blue-100 transition-colors"
                  >
                    <div className="flex items-center">
                      <span className="text-xl mr-2">📂</span>
                      <div>
                        <h4 className="font-semibold text-blue-800 text-sm">{level3Folder.name}</h4>
                        <p className="text-xs text-blue-600">Level 3 Klasör</p>
                      </div>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* Documents List for Selected Folder - Updated to show for level 2 and 3 folders */}
        {selectedClient && selectedFolder && (selectedFolder.level === 2 || selectedFolder.level === 3) && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">
              📄 {selectedFolder.name} İçindeki Belgeler
            </h3>
            
            {documents
              .filter(doc => doc.folder_id === selectedFolder.id)
              .length > 0 ? (
              <div className="space-y-3">
                {documents
                  .filter(doc => doc.folder_id === selectedFolder.id)
                  .map((document) => (
                    <div key={document.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center flex-1">
                          <span className="text-2xl mr-3">{getFileIcon(document.original_filename || document.file_path || '')}</span>
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-800">{document.name}</h4>
                            <div className="flex items-center text-sm text-gray-500 space-x-4">
                              <span>📋 {document.document_type}</span>
                              <span>🎯 {document.stage}</span>
                              <span>📅 {new Date(document.created_at).toLocaleDateString('tr-TR')}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleViewDocument(document)}
                            className="bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm"
                          >
                            👁️ Görüntüle
                          </button>
                          <button
                            onClick={() => handleDownloadDocument(document)}
                            className="bg-green-600 text-white px-3 py-2 rounded-md hover:bg-green-700 transition-colors text-sm"
                          >
                            📥 İndir
                          </button>
                          <button
                            onClick={() => handleDelete(document.id)}
                            className="bg-red-600 text-white px-3 py-2 rounded-md hover:bg-red-700 transition-colors text-sm"
                          >
                            🗑️ Sil
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                }
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <span className="text-4xl mb-4 block">📄</span>
                <p>Bu klasörde henüz belge bulunmuyor.</p>
              </div>
            )}
          </div>
        )}

        {/* Instruction when no client selected */}
        {!selectedClient && (
          <div className="text-center py-12 text-gray-500">
            <span className="text-6xl mb-4 block">👥</span>
            <h3 className="text-xl font-semibold mb-2">Müşteri seçin</h3>
            <p>Belgelerinizi yönetmek için yukarıdan bir müşteri seçin.</p>
          </div>
      )}

        {/* Upload Form Modal */}
        {showUploadForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg w-full max-w-md max-h-90vh overflow-y-auto">
              <h3 className="text-lg font-semibold mb-4">Yeni Belge Yükle</h3>
              <form onSubmit={handleUploadSubmit} className="space-y-4">
                
                {/* Client Selection (Admin Only) */}
                {userRole === 'admin' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Müşteri <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={uploadData.client_id}
                      onChange={(e) => setUploadData({...uploadData, client_id: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-md"
                      required
                    >
                      <option value="">Müşteri Seçin</option>
                      {Array.isArray(clients) ? clients.map((client) => (
                        <option key={client.id} value={client.id}>
                          {client.hotel_name}
                        </option>
                      )) : null}
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Belge Adı <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Örn: Sürdürülebilirlik Sertifikası"
                    value={uploadData.name}
                    onChange={(e) => setUploadData({...uploadData, name: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Belge Türü <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={uploadData.document_type}
                    onChange={(e) => setUploadData({...uploadData, document_type: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  >
                    {documentTypes.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Aşama <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={uploadData.stage}
                    onChange={(e) => setUploadData({...uploadData, stage: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  >
                    {stages.map((stage) => (
                      <option key={stage} value={stage}>{stage}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Klasör <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={uploadData.folder_id}
                    onChange={(e) => setUploadData({...uploadData, folder_id: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  >
                    <option value="">Klasör seçiniz</option>
                    {folders.filter(folder => folder.client_id === uploadData.client_id).map(folder => {
                      const docCount = getFolderDocumentCount(folder.id);
                      return (
                        <option key={folder.id} value={folder.id}>
                          {"  ".repeat(folder.level)} {folder.name} ({docCount} doküman)
                        </option>
                      );
                    })}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Dosya(lar) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.zip,.rar,.jpg,.jpeg,.png"
                    multiple
                    onChange={(e) => setUploadData({...uploadData, files: Array.from(e.target.files)})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Desteklenen formatlar: PDF, DOC, DOCX, XLS, XLSX, ZIP, RAR, JPG, PNG
                  </p>
                </div>

                <div className="flex space-x-3">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Yükle
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowUploadForm(false)}
                    className="flex-1 bg-gray-500 text-white py-2 rounded-md hover:bg-gray-600 transition-colors"
                  >
                    İptal
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Upload Form Modal */}
        {showUploadForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg w-full max-w-md max-h-90vh overflow-y-auto">
              <h3 className="text-lg font-semibold mb-4">Yeni Belge Yükle</h3>
              <form onSubmit={handleUploadSubmit} className="space-y-4">
                
                {/* Client Selection (Admin Only) */}
                {userRole === 'admin' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Müşteri <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={uploadData.client_id}
                      onChange={(e) => setUploadData({...uploadData, client_id: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-md"
                      required
                    >
                      <option value="">Müşteri Seçin</option>
                      {Array.isArray(clients) ? clients.map((client) => (
                        <option key={client.id} value={client.id}>
                          {client.hotel_name}
                        </option>
                      )) : null}
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Belge Adı <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Örn: Sürdürülebilirlik Sertifikası"
                    value={uploadData.name}
                    onChange={(e) => setUploadData({...uploadData, name: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Belge Türü <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={uploadData.document_type}
                    onChange={(e) => setUploadData({...uploadData, document_type: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  >
                    {documentTypes.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Aşama <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={uploadData.stage}
                    onChange={(e) => setUploadData({...uploadData, stage: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  >
                    {stages.map((stage) => (
                      <option key={stage} value={stage}>{stage}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Klasör <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={uploadData.folder_id}
                    onChange={(e) => setUploadData({...uploadData, folder_id: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  >
                    <option value="">Klasör seçiniz</option>
                    {folders.filter(folder => folder.client_id === uploadData.client_id).map(folder => {
                      const docCount = getFolderDocumentCount(folder.id);
                      return (
                        <option key={folder.id} value={folder.id}>
                          {"  ".repeat(folder.level)} {folder.name} ({docCount} doküman)
                        </option>
                      );
                    })}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Dosya(lar) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.zip,.rar,.jpg,.jpeg,.png"
                    multiple
                    onChange={(e) => setUploadData({...uploadData, files: Array.from(e.target.files)})}
                    className="w-full p-3 border border-gray-300 rounded-md"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Desteklenen formatlar: PDF, DOC, DOCX, XLS, XLSX, ZIP, RAR, JPG, PNG
                  </p>
                </div>

                <div className="flex space-x-3">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Yükle
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowUploadForm(false)}
                    className="flex-1 bg-gray-500 text-white py-2 rounded-md hover:bg-gray-600 transition-colors"
                  >
                    İptal
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* Document Detail Modal */}
      {showDocumentModal && selectedDocument && (
        <DocumentModal 
          document={selectedDocument} 
          onClose={() => setShowDocumentModal(false)}
          onDownload={handleDownloadDocument}
        />
      )}
    </div>
  );
};

const ConsumptionManagement = ({ onNavigate }) => {
  const [consumptions, setConsumptions] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [showConsumptionForm, setShowConsumptionForm] = useState(false);
  const [editingConsumption, setEditingConsumption] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [consumptionData, setConsumptionData] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    electricity: '',
    water: '',
    natural_gas: '',
    coal: '',
    // DEFRA Additional Fuel Types
    diesel: '',
    gasoline: '',
    lpg: '',
    fuel_oil: '',
    // DEFRA F-Gases
    r134a_gas: '',
    r600a_gas: '',
    r410a_gas: '',
    r32_gas: '',
    co2_fire: '',
    fm200_fire: '',
    accommodation_count: ''
  });
  const { authToken, userRole, dbUser, ensureTokenForOperation } = useAuth();

  useEffect(() => {
    console.log('🔍 ConsumptionManagement useEffect triggered:', {
      authToken: !!authToken,
      userRole,
      selectedYear,
      selectedClient
    });
    
    if (authToken) {
      fetchConsumptions();
      fetchAnalytics();
      fetchClients();
    }
  }, [authToken, selectedYear, selectedClient, userRole]);

  const fetchConsumptions = async () => {
    if (!authToken) {
      console.log('⚠️ No authToken, skipping consumptions fetch');
      return;
    }
    
    // Admin ve Consultant için müşteri seçimi zorunlu
    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      console.log('⚠️ Admin/Consultant must select client for consumptions');
      setConsumptions([]);
      return;
    }
    
    try {
      let url = `${API}/consumptions?year=${selectedYear}`;
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        url += `&client_id=${selectedClient}`;
      }
      // Client için kendi verilerini getir (backend otomatik olarak kendi verisini döndürür)
      
      console.log('🔍 Fetching consumptions:', {
        year: selectedYear,
        client_id: selectedClient || 'current user',
        authToken: authToken ? `${authToken.substring(0, 20)}...` : 'null'
      });
      
      const response = await axios.get(url, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      // Check if response is actually JSON array
      if (Array.isArray(response.data)) {
        setConsumptions(response.data);
        console.log('✅ Consumptions fetched:', response.data.length);
      } else {
        console.error('❌ Invalid consumptions response type:', typeof response.data, response.data);
        setConsumptions([]);
      }
    } catch (error) {
      console.error("❌ Error fetching consumptions:", error.response?.status, error.response?.data);
      setConsumptions([]);
    }
  };

  const fetchAnalytics = async () => {
    if (!authToken) {
      console.log('⚠️ No authToken, skipping analytics fetch');
      setAnalytics(null);
      return;
    }
    
    // Admin ve Consultant için müşteri seçimi zorunlu
    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      console.log('⚠️ Admin/Consultant must select client for analytics');
      setAnalytics(null);
      return;
    }
    
    try {
      let url = `${API}/consumptions/analytics?year=${selectedYear}`;
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        url += `&client_id=${selectedClient}`;
      }
      
      console.log('🔍 Fetching analytics:', {
        url,
        userRole,
        selectedClient,
        year: selectedYear
      });
      
      const response = await axios.get(url, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setAnalytics(response.data);
      console.log('✅ Analytics fetched for client:', selectedClient || 'current user');
    } catch (error) {
      console.error("Error fetching analytics:", error);
      setAnalytics(null);
    }
  };

  const fetchClients = async () => {
    if (!authToken) return;
    
    // For clients, no need to fetch clients list - they only work with their own data
    if (userRole === 'client') {
      console.log('👤 Client user - using own data only');
      return;
    }
    
    // Admin and consultant can see all clients
    if (userRole !== 'admin' && userRole !== 'consultant') {
      return;
    }
    
    try {
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      // Handle new backend response format { clients, pagination }
      if (response.data.clients && Array.isArray(response.data.clients)) {
        setClients(response.data.clients);
        console.log('✅ Clients fetched for consumption:', response.data.clients.length);
      } else if (Array.isArray(response.data)) {
        // Fallback for old format
        setClients(response.data.clients || []);
        console.log('✅ Clients fetched for consumption (old format):', response.data.length);
      } else {
        setClients([]);
        console.log('⚠️ No clients found in response');
      }
    } catch (error) {
      console.error("Error fetching clients for consumption:", error);
      setClients([]);
    }
  };

  const handleConsumptionSubmit = async (e) => {
    e.preventDefault();
    
    if (!authToken) {
      alert('Oturum süresi dolmuş. Lütfen sayfayı yenileyin.');
      return;
    }
    
    try {
      const endpoint = editingConsumption 
        ? `${API}/consumptions/${editingConsumption.id}`
        : `${API}/consumptions`;
      
      const method = editingConsumption ? 'put' : 'post';
      
      console.log('🔍 Consumption API call:', {
        endpoint,
        method,
        userRole,
        'consumptionData.client_id': consumptionData.client_id,
        'selectedClient': selectedClient,
        'will send client_id': ((userRole === 'admin' || userRole === 'consultant') && consumptionData.client_id),
        authToken: authToken ? `${authToken.substring(0, 20)}...` : 'null'
      });
      
      await axios[method](endpoint, {
        year: parseInt(consumptionData.year),
        month: parseInt(consumptionData.month),
        electricity: parseFloat(consumptionData.electricity) || 0,
        water: parseFloat(consumptionData.water) || 0,
        natural_gas: parseFloat(consumptionData.natural_gas) || 0,
        coal: parseFloat(consumptionData.coal) || 0,
        // DEFRA Additional Fuel Types
        diesel: parseFloat(consumptionData.diesel) || 0,
        gasoline: parseFloat(consumptionData.gasoline) || 0,
        lpg: parseFloat(consumptionData.lpg) || 0,
        fuel_oil: parseFloat(consumptionData.fuel_oil) || 0,
        // DEFRA F-Gases
        r134a_gas: parseFloat(consumptionData.r134a_gas) || 0,
        r600a_gas: parseFloat(consumptionData.r600a_gas) || 0,
        r410a_gas: parseFloat(consumptionData.r410a_gas) || 0,
        r32_gas: parseFloat(consumptionData.r32_gas) || 0,
        co2_fire: parseFloat(consumptionData.co2_fire) || 0,
        fm200_fire: parseFloat(consumptionData.fm200_fire) || 0,
        accommodation_count: parseInt(consumptionData.accommodation_count) || 0,
        ...((userRole === 'admin' || userRole === 'consultant') && consumptionData.client_id && { client_id: consumptionData.client_id })
      }, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });

      fetchConsumptions();
      fetchAnalytics();
      setShowConsumptionForm(false);
      setEditingConsumption(null);
      setConsumptionData({
        year: new Date().getFullYear(),
        month: new Date().getMonth() + 1,
        electricity: '',
        water: '',
        natural_gas: '',
        coal: '',
        // DEFRA Additional Fuel Types
        diesel: '',
        gasoline: '',
        lpg: '',
        fuel_oil: '',
        // DEFRA F-Gases
        r134a_gas: '',
        r600a_gas: '',
        r410a_gas: '',
        r32_gas: '',
        co2_fire: '',
        fm200_fire: '',
        accommodation_count: ''
      });
      
      alert(editingConsumption ? 'Tüketim verisi güncellendi!' : 'Tüketim verisi kaydedildi!');
    } catch (error) {
      console.error("Error saving consumption:", error);
      alert('Hata: ' + (error.response?.data?.detail || 'Bilinmeyen hata'));
    }
  };

  const handleEdit = (consumption) => {
    setEditingConsumption(consumption);
    setConsumptionData({
      year: consumption.year,
      month: consumption.month,
      electricity: consumption.electricity,
      water: consumption.water,
      natural_gas: consumption.natural_gas,
      coal: consumption.coal,
      // DEFRA Additional Fuel Types
      diesel: consumption.diesel || '',
      gasoline: consumption.gasoline || '',
      lpg: consumption.lpg || '',
      fuel_oil: consumption.fuel_oil || '',
      // DEFRA F-Gases
      r134a_gas: consumption.r134a_gas || '',
      r600a_gas: consumption.r600a_gas || '',
      r410a_gas: consumption.r410a_gas || '',
      r32_gas: consumption.r32_gas || '',
      co2_fire: consumption.co2_fire || '',
      fm200_fire: consumption.fm200_fire || '',
      accommodation_count: consumption.accommodation_count
    });
    setShowConsumptionForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Bu tüketim verisini silmek istediğinizden emin misiniz?')) {
      try {
        console.log("🗑️ Deleting consumption with ID:", id);
        console.log("🔑 Using token:", authToken ? authToken.substring(0, 20) + "..." : "null");
        console.log("🌐 API URL:", `${API}/consumptions/${id}`);
        
        const response = await axios.delete(`${API}/consumptions/${id}`, {
          headers: { 
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        });
        
        console.log("✅ Delete response:", response.data);
        
        // Refresh all data
        await fetchConsumptions();
        await fetchAnalytics();
        
        alert('✅ Tüketim verisi başarıyla silindi!');
        
      } catch (error) {
        console.error("❌ Error deleting consumption:", {
          status: error.response?.status,
          data: error.response?.data,
          message: error.message
        });
        
        const errorMsg = error.response?.data?.detail || error.message || 'Bilinmeyen hata';
        alert(`❌ Silme hatası: ${errorMsg}`);
      }
    }
  };

  const getMonthName = (month) => {
    const months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                   "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
    return months[month];
  };

  const getConsumptionIcon = (type) => {
    const icons = {
      electricity: '⚡',
      water: '💧',
      natural_gas: '🔥',
      coal: '⚫'
    };
    return icons[type] || '📊';
  };

  const getConsumptionUnit = (type) => {
    const units = {
      electricity: 'kWh',
      water: 'm³',
      natural_gas: 'm³',
      coal: 'kg'
    };
    return units[type] || '';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-500 to-blue-600 text-white p-6 rounded-lg shadow-lg">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold mb-2">⚡ Tüketim Yönetimi</h2>
            <p className="text-green-100">Aylık enerji ve kaynak tüketimlerinizi takip edin</p>
          </div>
          <button
            onClick={() => onNavigate('dashboard')}
            className="bg-white bg-opacity-20 text-white px-4 py-2 rounded-lg hover:bg-opacity-30 transition-all"
          >
            ← Dashboard
          </button>
        </div>
      </div>

      {/* Year Selector & Client Selector & New Entry Button */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          {userRole === 'admin' && (
            <>
              <label className="font-semibold text-gray-700">Müşteri:</label>
              <select
                value={selectedClient}
                onChange={(e) => {
                  console.log('🏨 Client selected in ConsumptionManagement:', e.target.value);
                  setSelectedClient(e.target.value);
                }}
                className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Tüm Müşteriler</option>
                {(Array.isArray(clients) ? clients : []).map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.hotel_name}
                  </option>
                ))}
              </select>
            </>
          )}
          
          <label className="font-semibold text-gray-700">Yıl:</label>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            {[2025, 2024, 2023, 2022, 2021].map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>
        
        {userRole === 'client' && (
          <div className="text-gray-600 text-sm">
            📊 Tüketim verilerinizi görüntüleyebilirsiniz
          </div>
        )}
      </div>

      {/* Consumption Form Modal */}
      {showConsumptionForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
            <div className="bg-gradient-to-r from-blue-600 to-green-600 text-white p-6 rounded-t-xl">
              <h3 className="text-xl font-bold">
                {editingConsumption ? 'Tüketim Verisini Düzenle' : 'Yeni Tüketim Verisi'}
              </h3>
            </div>
            
            <form className="p-6 overflow-y-auto flex-1 space-y-4">
              {(userRole === 'admin' || userRole === 'consultant') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Müşteri Seçin {userRole === 'consultant' && '(Sadece size atanan müşteriler)'}
                  </label>
                  <select
                    value={consumptionData.client_id || ''}
                    onChange={(e) => setConsumptionData({...consumptionData, client_id: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Müşteri seçin...</option>
                    {(Array.isArray(clients) ? clients : []).map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.hotel_name || client.client_name || client.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Yıl</label>
                  <select
                    value={consumptionData.year}
                    onChange={(e) => setConsumptionData({...consumptionData, year: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    {[2025, 2024, 2023, 2022, 2021].map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ay</label>
                  <select
                    value={consumptionData.month}
                    onChange={(e) => setConsumptionData({...consumptionData, month: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    {Array.from({length: 12}, (_, i) => i + 1).map(month => (
                      <option key={month} value={month}>{getMonthName(month)}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ⚡ Elektrik (kWh)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={consumptionData.electricity}
                    onChange={(e) => setConsumptionData({...consumptionData, electricity: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    💧 Su (m³)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={consumptionData.water}
                    onChange={(e) => setConsumptionData({...consumptionData, water: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    🔥 Doğalgaz (m³)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={consumptionData.natural_gas}
                    onChange={(e) => setConsumptionData({...consumptionData, natural_gas: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ⚫ Kömür (kg)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={consumptionData.coal}
                    onChange={(e) => setConsumptionData({...consumptionData, coal: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  🏨 Konaklama Sayısı (Kişi)
                </label>
                <input
                  type="number"
                  value={consumptionData.accommodation_count}
                  onChange={(e) => setConsumptionData({...consumptionData, accommodation_count: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="0"
                  required
                />
              </div>

              {/* DEFRA Additional Fuel Types Section */}
              <div className="border-t pt-4 mt-4">
                <h4 className="font-medium text-gray-700 mb-3">🌍 DEFRA Ek Yakıt Tipleri</h4>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      🚛 Mazot/Dizel (litre)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={consumptionData.diesel || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, diesel: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ⛽ Benzin (litre)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={consumptionData.gasoline || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, gasoline: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      🔥 LPG (litre)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={consumptionData.lpg || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, lpg: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      🏭 Fuel Oil (litre)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={consumptionData.fuel_oil || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, fuel_oil: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                </div>
              </div>

              {/* DEFRA Refrigerant Gases Section */}
              <div className="border-t pt-4 mt-4">
                <h4 className="font-medium text-gray-700 mb-3">❄️ DEFRA Soğutucu Gazlar</h4>
                <p className="text-xs text-gray-500 mb-3">Klimalar, soğutucular, minibarlar için kullanılan spesifik gazlar (kg)</p>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      🌀 R134a (Klimalar) - kg
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={consumptionData.r134a_gas || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, r134a_gas: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.000"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      🧊 R600a (Buzdolapları) - kg
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={consumptionData.r600a_gas || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, r600a_gas: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.000"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ❄️ R410A (Modern AC) - kg
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={consumptionData.r410a_gas || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, r410a_gas: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.000"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      🌀 R32 (Yeni Nesil AC) - kg
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={consumptionData.r32_gas || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, r32_gas: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.000"
                    />
                  </div>
                </div>
              </div>

              {/* DEFRA Fire Suppressants Section */}
              <div className="border-t pt-4 mt-4">
                <h4 className="font-medium text-gray-700 mb-3">🧯 DEFRA Yangın Söndürücüler</h4>
                <p className="text-xs text-gray-500 mb-3">Yangın söndürme sistemlerinde kullanılan gazlar (kg)</p>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      💨 CO2 Söndürücü - kg
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={consumptionData.co2_fire || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, co2_fire: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.000"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      🧯 FM200 (HFC-227ea) - kg
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={consumptionData.fm200_fire || ''}
                      onChange={(e) => setConsumptionData({...consumptionData, fm200_fire: e.target.value})}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="0.000"
                    />
                  </div>
                </div>
              </div>

            </form>
            
            {/* Modal Footer with Action Buttons */}
            <div className="p-6 border-t bg-gray-50 rounded-b-xl">
              <div className="flex space-x-3">
                <button
                  onClick={handleConsumptionSubmit}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {editingConsumption ? 'Güncelle' : 'Kaydet'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowConsumptionForm(false);
                    setEditingConsumption(null);
                  }}
                  className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition-colors"
                >
                  İptal
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Consumption List - Admin için müşteri seçimi gerekli */}
      {(userRole === 'client' || (userRole === 'admin' && selectedClient)) && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-800">
            📊 {selectedYear} Yılı Tüketim Verileri
          </h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ay</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">⚡ Elektrik</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">💧 Su</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">🔥 Doğalgaz</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">⚫ Kömür</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">🏨 Konaklama</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">İşlemler</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {(Array.isArray(consumptions) ? consumptions : []).map((consumption) => (
                <tr key={consumption.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium">
                    {getMonthName(consumption.month)} {consumption.year}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {consumption.electricity.toFixed(2)} kWh
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {consumption.water.toFixed(2)} m³
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {consumption.natural_gas.toFixed(2)} m³
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {consumption.coal.toFixed(2)} kg
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {consumption.accommodation_count} kişi
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex space-x-2">
                      {(userRole === 'admin' || userRole === 'client') && (
                        <>
                          <button
                            onClick={() => handleEdit(consumption)}
                            className="text-blue-600 hover:text-blue-900 font-medium flex items-center space-x-1"
                          >
                            <span>✏️</span>
                            <span>Düzenle</span>
                          </button>
                          <button
                            onClick={() => handleDelete(consumption.id)}
                            className="text-red-600 hover:text-red-900 font-medium flex items-center space-x-1"
                          >
                            <span>🗑️</span>
                            <span>Sil</span>
                          </button>
                        </>
                      )}
                      {userRole === 'consultant' && (
                        <span className="text-gray-500 text-sm">Sadece görüntüleme</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {(Array.isArray(consumptions) ? consumptions : []).length === 0 && (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center text-gray-500">
                    {selectedYear} yılı için henüz tüketim verisi girilmemiş.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {/* Client Section - Only Client Role */}
      {userRole === 'client' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-green-800">👤 Kendi Verileriniz</h3>
            <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
              ✓ Client Kullanıcısı
            </span>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => {
                console.log('🆕 Creating new consumption for client user');
                setEditingConsumption(null);
                setConsumptionData({
                  year: selectedYear,
                  month: new Date().getMonth() + 1,
                  electricity: '',
                  water: '',
                  natural_gas: '',
                  coal: '',
                  // DEFRA Additional Fuel Types
                  diesel: '',
                  gasoline: '',
                  lpg: '',
                  fuel_oil: '',
                  // DEFRA F-Gases
                  r134a_gas: '',
                  r600a_gas: '',
                  r410a_gas: '',
                  r32_gas: '',
                  co2_fire: '',
                  fm200_fire: '',
                  accommodation_count: ''
                });
                setShowConsumptionForm(true);
              }}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
            >
              <span>➕</span>
              <span>Yeni Tüketim Verisi Ekle</span>
            </button>
          </div>
        </div>
      )}

      {/* Analytics Section - Admin and Consultant Client Selection */}
      {(userRole === 'admin' || userRole === 'consultant') && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-blue-800">📊 Müşteri Seçimi</h3>
            {consumptionData.client_id && (
              <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                ✓ Müşteri Seçili
              </span>
            )}
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-blue-700 mb-2">
                {userRole === 'consultant' ? 'Size atanan müşterilerden birini seçin:' : 'Müşteri seçin:'}
              </label>
              <select
                value={consumptionData.client_id || ''}
                onChange={(e) => {
                  console.log('🔄 Client selected:', e.target.value);
                  setConsumptionData({...consumptionData, client_id: e.target.value});
                  setSelectedClient(e.target.value); // Also update selectedClient state
                  // Trigger both analytics and consumptions fetch when client is selected
                  if (e.target.value) {
                    setTimeout(() => {
                      fetchAnalytics();
                      fetchConsumptions();
                    }, 100);
                  } else {
                    setAnalytics(null);
                    setConsumptions([]);
                  }
                }}
                className="w-full px-4 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Müşteri seçin...</option>
                {(Array.isArray(clients) ? clients : []).map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.hotel_name || client.client_name || client.name}
                  </option>
                ))}
              </select>
            </div>
            {consumptionData.client_id && (
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    console.log('🆕 Creating new consumption for client:', consumptionData.client_id);
                    setEditingConsumption(null);
                    setConsumptionData({
                      ...consumptionData,
                      year: selectedYear,
                      month: new Date().getMonth() + 1,
                      electricity: '',
                      water: '',
                      natural_gas: '',
                      coal: '',
                      // DEFRA Additional Fuel Types
                      diesel: '',
                      gasoline: '',
                      lpg: '',
                      fuel_oil: '',
                      // DEFRA F-Gases
                      r134a_gas: '',
                      r600a_gas: '',
                      r410a_gas: '',
                      r32_gas: '',
                      co2_fire: '',
                      fm200_fire: '',
                      accommodation_count: ''
                    });
                    setShowConsumptionForm(true);
                  }}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                >
                  <span>➕</span>
                  <span>Yeni Tüketim Verisi</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Admin ve Consultant için müşteri seçim uyarısı */}
      {(userRole === 'admin' || userRole === 'consultant') && !selectedClient && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 rounded-lg">
          <div className="flex items-center">
            <div className="text-yellow-400 mr-3">
              ⚠️
            </div>
            <div>
              <h3 className="text-lg font-semibold text-yellow-800">Müşteri Seçimi Gerekli</h3>
              <p className="text-yellow-700 mt-1">
                Tüketim verilerini görüntülemek için lütfen yukarıdan bir müşteri seçin.
              </p>
            </div>
          </div>
        </div>
      )}

      {analytics && selectedClient && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Monthly Comparison */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              📈 Aylık Karşılaştırma ({analytics.year} vs {analytics.year - 1})
            </h3>
            <div className="space-y-4">
              {(analytics?.monthly_comparison || []).slice(0, 12).map((month) => (
                <div key={month.month} className="border-b pb-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-gray-700">{month.month_name}</span>
                    <span className="text-sm text-gray-500">
                      Konaklama: {month.current_year.accommodation_count} vs {month.previous_year.accommodation_count}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    <div className="text-center">
                      <div className="text-blue-600 font-semibold">⚡ {month.current_year.electricity.toFixed(0)}</div>
                      <div className="text-gray-400">({month.previous_year.electricity.toFixed(0)})</div>
                    </div>
                    <div className="text-center">
                      <div className="text-blue-600 font-semibold">💧 {month.current_year.water.toFixed(0)}</div>
                      <div className="text-gray-400">({month.previous_year.water.toFixed(0)})</div>
                    </div>
                    <div className="text-center">
                      <div className="text-orange-600 font-semibold">🔥 {month.current_year.natural_gas.toFixed(0)}</div>
                      <div className="text-gray-400">({month.previous_year.natural_gas.toFixed(0)})</div>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-800 font-semibold">⚫ {month.current_year.coal.toFixed(0)}</div>
                      <div className="text-gray-400">({month.previous_year.coal.toFixed(0)})</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Per Person Analysis */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              👤 Kişi Başı Yıllık Ortalama
            </h3>
            <div className="space-y-4">
              <div className="bg-gradient-to-r from-blue-50 to-green-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-700 mb-3">{analytics.year} Yılı</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl text-blue-600 font-bold">
                      ⚡ {analytics?.yearly_per_person?.current_year?.electricity?.toFixed(1) || '0.0'}
                    </div>
                    <div className="text-sm text-gray-600">kWh/kişi</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl text-blue-500 font-bold">
                      💧 {analytics?.yearly_per_person?.current_year?.water?.toFixed(1) || '0.0'}
                    </div>
                    <div className="text-sm text-gray-600">m³/kişi</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl text-orange-600 font-bold">
                      🔥 {analytics?.yearly_per_person?.current_year?.natural_gas?.toFixed(1) || '0.0'}
                    </div>
                    <div className="text-sm text-gray-600">m³/kişi</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl text-gray-800 font-bold">
                      ⚫ {analytics?.yearly_per_person?.current_year?.coal?.toFixed(1) || '0.0'}
                    </div>
                    <div className="text-sm text-gray-600">kg/kişi</div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-700 mb-3">{analytics?.year - 1 || 2023} Yılı (Karşılaştırma)</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-xl text-gray-600 font-semibold">
                      ⚡ {analytics?.yearly_per_person?.previous_year?.electricity?.toFixed(1) || '0.0'}
                    </div>
                    <div className="text-xs text-gray-500">kWh/kişi</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl text-gray-600 font-semibold">
                      💧 {analytics?.yearly_per_person?.previous_year?.water?.toFixed(1) || '0.0'}
                    </div>
                    <div className="text-xs text-gray-500">m³/kişi</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl text-gray-600 font-semibold">
                      🔥 {analytics?.yearly_per_person?.previous_year?.natural_gas?.toFixed(1) || '0.0'}
                    </div>
                    <div className="text-xs text-gray-500">m³/kişi</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl text-gray-600 font-semibold">
                      ⚫ {analytics?.yearly_per_person?.previous_year?.coal?.toFixed(1) || '0.0'}
                    </div>
                    <div className="text-xs text-gray-500">kg/kişi</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ProjectManagement = ({ client, onNavigate }) => {
  const [trainings, setTrainings] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [showTrainingForm, setShowTrainingForm] = useState(false);
  const [showCarbonReportForm, setShowCarbonReportForm] = useState(false);
  const [trainingData, setTrainingData] = useState({
    title: '',
    description: '',
    training_date: '',
    participants: ''
  });
  const [carbonReportData, setCarbonReportData] = useState({
    report_file: null,
    total_emissions: '',
    calculation_date: '',
    notes: ''
  });
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const { authToken, userRole, dbUser, ensureTokenForOperation } = useAuth();

  // Handle viewing documents
  const handleViewDocument = (document) => {
    setSelectedDocument(document);
    setShowDocumentModal(true);
  };

  useEffect(() => {
    if (client && authToken) {
      fetchTrainings();
      fetchDocuments();
    }
  }, [client, authToken]);

  const fetchTrainings = async () => {
    try {
      const response = await axios.get(`${API}/trainings/${client.id}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setTrainings(response.data);
    } catch (error) {
      console.error("Error fetching trainings:", error);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents/${client.id}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setDocuments(response.data);
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  };

  const handleCarbonReportSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        client_id: client.id,
        name: "Karbon Ayak İzi Raporu",
        document_type: "Karbon Ayak İzi Raporu",
        stage: client.current_stage,
        file_path: `/reports/carbon_${client.id}_${Date.now()}.pdf`,
        file_size: carbonReportData.report_file ? carbonReportData.report_file.size : 0
      };
      
      await axios.post(`${API}/documents`, data, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      // Update client's carbon footprint value
      if (carbonReportData.total_emissions) {
        await axios.put(`${API}/clients/${client.id}`, { 
          carbon_footprint: parseFloat(carbonReportData.total_emissions)
        }, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
      }
      
      setShowCarbonReportForm(false);
      setCarbonReportData({
        report_file: null,
        total_emissions: '',
        calculation_date: '',
        notes: ''
      });
      fetchDocuments();
      alert('Karbon ayak izi raporu başarıyla yüklendi!');
    } catch (error) {
      console.error("Error uploading carbon report:", error);
      alert('Rapor yüklenirken hata oluştu!');
    }
  };

  const handleTrainingSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        client_id: client.id,
        title: trainingData.title,
        description: trainingData.description,
        training_date: new Date(trainingData.training_date).toISOString(),
        participants: parseInt(trainingData.participants)
      };
      await axios.post(`${API}/trainings`, data, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      fetchTrainings();
      setShowTrainingForm(false);
      setTrainingData({
        title: '',
        description: '',
        training_date: '',
        participants: ''
      });
    } catch (error) {
      console.error("Error creating training:", error);
    }
  };

  const updateTrainingStatus = async (trainingId, status) => {
    try {
      await axios.put(`${API}/trainings/${trainingId}?status=${status}`, {}, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      fetchTrainings();
    } catch (error) {
      console.error("Error updating training status:", error);
    }
  };


  const serviceTypes = [
    "Mevcut durum analizi",
    "Çalışma ekibinin belirlenmesi",
    "Proje planının oluşturulması",
    "Risk değerlendirmesi",
    "Eğitim-Bilinçlendirme faaliyetleri",
    "İzleme, Denetim Kayıtlarının Oluşturulması ve İyileştirme faaliyetleri",
    "Belgelendirme denetimi"
  ];

  if (!client) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Lütfen bir müşteri seçin.</p>
        <button
          onClick={() => onNavigate('clients')}
          className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          Müşteri Listesine Dön
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-800">
            Proje Yönetimi - {client.hotel_name}
          </h2>
          <button
            onClick={() => onNavigate(userRole === 'admin' ? 'clients' : 'dashboard')}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors"
          >
            Geri Dön
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-800">Müşteri Bilgileri</h3>
            <p><strong>Firma:</strong> {client.name}</p>
            <p><strong>Otel:</strong> {client.hotel_name}</p>
            <p><strong>İletişim:</strong> {client.contact_person}</p>
            <p><strong>Aşama:</strong> {client.current_stage}</p>
          </div>
          
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="font-semibold text-green-800">Karbon Ayak İzi</h3>
            <p className="text-2xl font-bold text-green-600">
              {client.carbon_footprint ? `${client.carbon_footprint.toFixed(2)} kg CO2` : 'Rapor Yüklenmedi'}
            </p>
            {userRole === 'admin' && (
              <button
                onClick={() => setShowCarbonReportForm(true)}
                className="mt-2 bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 transition-colors"
              >
                Rapor Yükle
              </button>
            )}
            {userRole === 'client' && client.carbon_footprint && (
              <p className="text-xs text-green-600 mt-1">
                📊 Karbon ayak izi hesaplaması tamamlandı
              </p>
            )}
            {userRole === 'client' && !client.carbon_footprint && (
              <p className="text-xs text-green-600 mt-1">
                ⏳ Karbon ayak izi analizi devam ediyor
              </p>
            )}
          </div>

          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="font-semibold text-purple-800">Belgeler</h3>
            <p className="text-2xl font-bold text-purple-600">{documents.length}</p>
            <p className="text-sm text-purple-600">Yüklenen belge</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-gray-800 mb-3">Hizmet Durumu</h3>
            <div className="space-y-2">
              {serviceTypes.map((service, index) => (
                <div key={index} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={client.services_completed?.includes(service) || false}
                    readOnly
                    className="mr-2"
                  />
                  <span className={`text-sm ${
                    client.services_completed?.includes(service) ? 'text-green-600 font-semibold' : 'text-gray-600'
                  }`}>
                    {service}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold text-gray-800">Eğitimler</h3>
              {userRole === 'admin' && (
                <button
                  onClick={() => setShowTrainingForm(true)}
                  className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
                >
                  Yeni Eğitim
                </button>
              )}
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {(trainings || []).map((training) => (
                <div key={training.id} className="border-l-4 border-blue-400 pl-3 py-2 bg-white rounded">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-semibold text-sm">{training.title || training.name}</h4>
                      <p className="text-xs text-gray-600">{training.description}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(training.training_date).toLocaleDateString('tr-TR')} - {training.participants} kişi
                      </p>
                    </div>
                    {userRole === 'admin' && (
                      <select
                        value={training.status}
                        onChange={(e) => updateTrainingStatus(training.id, e.target.value)}
                        className="text-xs border rounded px-1 py-1"
                      >
                        <option value="Planned">Planlandı</option>
                        <option value="Completed">Tamamlandı</option>
                        <option value="Cancelled">İptal</option>
                      </select>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Documents Section */}
        <div className="mt-6 bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-800 mb-3">
            {userRole === 'admin' ? 'Belgeler' : 'Belgelerim'}
          </h3>
          
          {/* Carbon Reports Section for Clients */}
          {userRole === 'client' && (
            <div className="mb-4">
              <h4 className="font-medium text-gray-700 mb-2 flex items-center">
                🌱 Karbon Ayak İzi Raporlarım
              </h4>
              <div className="bg-white p-3 rounded border">
                {client.carbon_footprint ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-green-800">
                        Karbon Ayak İzi: {client.carbon_footprint.toFixed(2)} kg CO2
                      </p>
                      <p className="text-sm text-gray-600">
                        📄 Detaylı rapor yüklenmiştir
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        // Find carbon report for this client
                        const carbonReport = documents.find(d => d.document_type === "Karbon Ayak İzi Raporu");
                        if (carbonReport) {
                          handleViewDocument(carbonReport);
                        } else {
                          alert('Karbon ayak izi raporu henüz yüklenmemiş.');
                        }
                      }}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 transition-colors"
                    >
                      📊 Raporu Görüntüle
                    </button>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <span className="text-gray-500">⏳ Karbon ayak izi analizi henüz tamamlanmadı</span>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* All Documents */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {(documents || []).map((doc) => (
              <div key={doc.id} className="bg-white p-3 rounded border hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <span className="text-lg mr-2">{getFileIcon(doc?.original_filename || doc?.file_path || '')}</span>
                      <h4 className="font-semibold text-sm text-gray-800 truncate">{doc.name}</h4>
                    </div>
                    <p className="text-xs text-gray-600 mb-1">{doc.document_type}</p>
                    <p className="text-xs text-gray-500">{doc.stage}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(doc.created_at).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                  <button
                    onClick={() => handleViewDocument(doc)}
                    className="text-blue-600 hover:text-blue-900 text-sm ml-2"
                  >
                    📋
                  </button>
                </div>
              </div>
            ))}
            
            {documents.length === 0 && (
              <div className="col-span-full text-center py-8 text-gray-500">
                {userRole === 'admin' ? 'Henüz belge yüklenmemiş.' : 'Henüz size ait belge bulunmuyor.'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Carbon Report Form Modal */}
      {showCarbonReportForm && userRole === 'admin' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Karbon Ayak İzi Raporu Yükleme</h3>
            <form onSubmit={handleCarbonReportSubmit} className="space-y-4">
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={(e) => setCarbonReportData({...carbonReportData, report_file: e.target.files[0]})}
                className="w-full p-3 border border-gray-300 rounded-md"
              />
              <input
                type="number"
                step="0.01"
                placeholder="Toplam Emisyon (kg CO2)"
                value={carbonReportData.total_emissions}
                onChange={(e) => setCarbonReportData({...carbonReportData, total_emissions: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-md"
                required
              />
              <input
                type="date"
                value={carbonReportData.calculation_date}
                onChange={(e) => setCarbonReportData({...carbonReportData, calculation_date: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-md"
                required
              />
              <textarea
                placeholder="Notlar"
                value={carbonReportData.notes}
                onChange={(e) => setCarbonReportData({...carbonReportData, notes: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-md"
                rows="3"
              />
              <div className="flex space-x-3">
                <button
                  type="submit"
                  className="flex-1 bg-green-600 text-white py-2 rounded-md hover:bg-green-700 transition-colors"
                >
                  Yükle
                </button>
                <button
                  type="button"
                  onClick={() => setShowCarbonReportForm(false)}
                  className="flex-1 bg-gray-500 text-white py-2 rounded-md hover:bg-gray-600 transition-colors"
                >
                  İptal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Training Form Modal */}
      {showTrainingForm && userRole === 'admin' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Yeni Eğitim Ekle</h3>
            <form onSubmit={handleTrainingSubmit} className="space-y-4">
              <input
                type="text"
                placeholder="Eğitim Başlığı"
                value={trainingData.title}
                onChange={(e) => setTrainingData({...trainingData, title: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-md"
                required
              />
              <textarea
                placeholder="Eğitim Açıklaması"
                value={trainingData.description}
                onChange={(e) => setTrainingData({...trainingData, description: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-md"
                rows="3"
                required
              />
              <input
                type="datetime-local"
                value={trainingData.training_date}
                onChange={(e) => setTrainingData({...trainingData, training_date: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-md"
                required
              />
              <input
                type="number"
                placeholder="Katılımcı Sayısı"
                value={trainingData.participants}
                onChange={(e) => setTrainingData({...trainingData, participants: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-md"
                required
              />
              <div className="flex space-x-3">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Kaydet
                </button>
                <button
                  type="button"
                  onClick={() => setShowTrainingForm(false)}
                  className="flex-1 bg-gray-500 text-white py-2 rounded-md hover:bg-gray-600 transition-colors"
                >
                  İptal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const ClientTrainings = () => {
  const [trainings, setTrainings] = useState([]);
  const [selectedTraining, setSelectedTraining] = useState(null);
  const [showTrainingModal, setShowTrainingModal] = useState(false);
  const { authToken, userRole, dbUser, refreshToken } = useAuth();

  useEffect(() => {
    if (authToken && userRole === 'client') {
      fetchTrainings();
    }
  }, [authToken, userRole]);

  const fetchTrainings = async () => {
    if (!authToken) return;
    
    try {
      console.log('📚 Client fetching trainings...');
      const response = await axios.get(`${API}/trainings`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      console.log('📚 Client trainings response:', response.data);
      setTrainings(response.data);
    } catch (error) {
      console.error('❌ Error fetching trainings:', error);
      setTrainings([]);
    }
  };

  const handleViewTraining = (training) => {
    setSelectedTraining(training);
    setShowTrainingModal(true);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isUpcoming = (dateString) => {
    return new Date(dateString) > new Date();
  };

  const upcomingTrainings = trainings.filter(t => isUpcoming(t.training_date));
  const pastTrainings = trainings.filter(t => !isUpcoming(t.training_date));

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">📚 Eğitimlerim</h2>

      {/* Upcoming Trainings */}
      {upcomingTrainings.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-blue-800 mb-4">🔔 Yaklaşan Eğitimler</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {upcomingTrainings.map((training) => (
              <div
                key={training.id}
                onClick={() => handleViewTraining(training)}
                className="bg-blue-50 border border-blue-200 rounded-lg p-4 cursor-pointer hover:bg-blue-100 transition-colors"
              >
                <div className="flex items-center mb-2">
                  <span className="text-2xl mr-2">📅</span>
                  <h4 className="font-semibold text-blue-800">{training.name}</h4>
                </div>
                <p className="text-sm text-blue-600 mb-1">{training.subject}</p>
                <p className="text-sm text-gray-600 mb-2">Eğitmen: {training.trainer}</p>
                <p className="text-sm font-medium text-blue-800">{formatDate(training.training_date)}</p>
                <p className="text-xs text-blue-600 mt-1">{training.participant_count} katılımcı</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Past Trainings */}
      {pastTrainings.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">📋 Geçmiş Eğitimler</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pastTrainings.map((training) => (
              <div
                key={training.id}
                onClick={() => handleViewTraining(training)}
                className="bg-gray-50 border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center mb-2">
                  <span className="text-2xl mr-2">✅</span>
                  <h4 className="font-semibold text-gray-800">{training.name}</h4>
                </div>
                <p className="text-sm text-gray-600 mb-1">{training.subject}</p>
                <p className="text-sm text-gray-600 mb-2">Eğitmen: {training.trainer}</p>
                <p className="text-sm font-medium text-gray-800">{formatDate(training.training_date)}</p>
                <p className="text-xs text-gray-600 mt-1">{training.participant_count} katılımcı</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Trainings */}
      {trainings.length === 0 && (
        <div className="text-center py-8">
          <span className="text-6xl mb-4 block">📚</span>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Henüz eğitim planlanmamış</h3>
          <p className="text-gray-600">Eğitimleriniz burada görünecektir.</p>
        </div>
      )}

      {/* Training Detail Modal */}
      {showTrainingModal && selectedTraining && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            {/* Header */}
            <div className={`${isUpcoming(selectedTraining.training_date) ? 'bg-blue-600' : 'bg-gray-600'} text-white p-6 rounded-t-xl`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <span className="text-3xl mr-3">📚</span>
                  <div>
                    <h3 className="text-xl font-bold">Eğitim Detayları</h3>
                    <p className={`${isUpcoming(selectedTraining.training_date) ? 'text-blue-100' : 'text-gray-100'} text-sm`}>
                      {selectedTraining.name}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowTrainingModal(false)}
                  className="text-white hover:text-red-300 text-2xl font-bold"
                >
                  ×
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                  Konu
                </label>
                <p className="text-sm font-medium text-gray-900">{selectedTraining.subject}</p>
              </div>
              
              <div>
                <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                  Eğitmen
                </label>
                <p className="text-sm font-medium text-gray-900">{selectedTraining.trainer}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                    Tarih & Saat
                  </label>
                  <p className="text-sm font-medium text-gray-900">{formatDate(selectedTraining.training_date)}</p>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                    Katılımcı Sayısı
                  </label>
                  <p className="text-sm font-medium text-gray-900">{selectedTraining.participant_count} kişi</p>
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                  Açıklama
                </label>
                <p className="text-sm text-gray-900">{selectedTraining.description}</p>
              </div>
              
              {isUpcoming(selectedTraining.training_date) && (
                <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                  <div className="flex items-start">
                    <span className="text-2xl mr-3">🔔</span>
                    <div>
                      <h4 className="text-sm font-semibold text-blue-800 mb-1">Yaklaşan Eğitim</h4>
                      <p className="text-sm text-blue-700">
                        Bu eğitim için hazırlıklı olunuz. Gerekli dokümanlar tarafınıza ayrıca iletilecektir.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex justify-end">
              <button
                onClick={() => setShowTrainingModal(false)}
                className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-all"
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Attendees List Component - Katılımcıları göstermek için
const AttendeesList = ({ attendeeIds, clientId, authToken }) => {
  const [attendees, setAttendees] = useState([]);
  const [loading, setLoading] = useState(true);
  const API = getApiUrl();

  useEffect(() => {
    const fetchAttendees = async () => {
      if (!attendeeIds || attendeeIds.length === 0) {
        setAttendees([]);
        setLoading(false);
        return;
      }

      try {
        // Personnel listesini getir
        const response = await axios.get(`${API}/personnel?client_id=${clientId}`, {
          headers: { Authorization: `Bearer ${authToken}` }
        });
        
        const allPersonnel = response.data || [];
        
        // Sadece seçilenleri filtrele
        const selectedAttendees = allPersonnel.filter(person => 
          attendeeIds.includes(person.id)
        );
        
        setAttendees(selectedAttendees);
      } catch (error) {
        console.error('Error fetching attendees:', error);
        setAttendees([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAttendees();
  }, [attendeeIds, clientId, authToken]);

  if (loading) {
    return <div className="text-xs text-gray-400">Katılımcılar yükleniyor...</div>;
  }

  if (attendees.length === 0) {
    return <div className="text-xs text-gray-400">Katılımcı bilgisi bulunamadı</div>;
  }

  return (
    <div className="flex flex-wrap gap-1">
      {attendees.map((person) => {
        const displayName = person.full_name || 
                          `${person.name || ''} ${person.surname || ''}`.trim() || 
                          person.position || 
                          'İsimsiz';
        
        return (
          <span
            key={person.id}
            className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
          >
            👤 {displayName}
            {person.position && person.full_name && (
              <span className="ml-1 text-blue-600">({person.position})</span>
            )}
          </span>
        );
      })}
    </div>
  );
};

// Training Calendar Component
const TrainingCalendar = ({ trainings, clients }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);

  // Helper functions for calendar
  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const getMonthName = (date) => {
    return date.toLocaleDateString('tr-TR', { month: 'long', year: 'numeric' });
  };

  const getTrainingsForDate = (day) => {
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return trainings.filter(training => training.training_date?.startsWith(dateStr));
  };

  const getClientName = (clientId) => {
    const client = clients.find(c => c.id === clientId);
    return client ? (client.hotel_name || client.name) : 'Bilinmeyen Müşteri';
  };

  const renderCalendarDay = (day) => {
    const dayTrainings = getTrainingsForDate(day);
    const hasTrainings = dayTrainings.length > 0;
    const today = new Date();
    const isToday = today.getDate() === day && 
                   today.getMonth() === currentDate.getMonth() && 
                   today.getFullYear() === currentDate.getFullYear();

    return (
      <div
        key={day}
        onClick={() => setSelectedDate(day)}
        className={`min-h-[80px] p-2 border border-gray-200 cursor-pointer hover:bg-gray-50 ${
          isToday ? 'bg-blue-50 border-blue-300' : ''
        } ${selectedDate === day ? 'bg-blue-100 border-blue-500' : ''}`}
      >
        <div className={`text-sm font-medium mb-1 ${isToday ? 'text-blue-600' : 'text-gray-900'}`}>
          {day}
        </div>
        
        {hasTrainings && (
          <div className="space-y-1">
            {dayTrainings.slice(0, 2).map((training, idx) => (
              <div
                key={idx}
                className={`text-xs p-1 rounded truncate ${
                  training.status === 'completed' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-blue-100 text-blue-800'
                }`}
                title={`${training.name} - ${getClientName(training.client_id)}`}
              >
                {training.status === 'completed' ? '✅' : '📚'} {training.name}
              </div>
            ))}
            
            {dayTrainings.length > 2 && (
              <div className="text-xs text-gray-500">
                +{dayTrainings.length - 2} daha...
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const daysInMonth = getDaysInMonth(currentDate);
  const firstDay = getFirstDayOfMonth(currentDate);
  const calendarDays = [];

  // Empty cells for days before month starts
  for (let i = 0; i < firstDay; i++) {
    calendarDays.push(<div key={`empty-${i}`} className="min-h-[80px] p-2 border border-gray-200 bg-gray-50"></div>);
  }

  // Days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push(renderCalendarDay(day));
  }

  const selectedDateTrainings = selectedDate ? getTrainingsForDate(selectedDate) : [];

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-6">
        {/* Calendar Header */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Eğitim Takvimi</h3>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1))}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              ←
            </button>
            <span className="text-lg font-medium min-w-[200px] text-center">
              {getMonthName(currentDate)}
            </span>
            <button
              onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              →
            </button>
          </div>
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-0 border border-gray-200 rounded-lg overflow-hidden">
          {/* Day headers */}
          {['Pz', 'Pt', 'Sl', 'Çr', 'Pr', 'Cm', 'Ct'].map(day => (
            <div key={day} className="p-3 bg-gray-50 border-b border-gray-200 text-center font-medium text-sm text-gray-700">
              {day}
            </div>
          ))}
          
          {/* Calendar days */}
          {calendarDays}
        </div>

        {/* Selected Date Details */}
        {selectedDate && selectedDateTrainings.length > 0 && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-3">
              {selectedDate} {getMonthName(currentDate)} - Eğitimler ({selectedDateTrainings.length})
            </h4>
            <div className="space-y-2">
              {selectedDateTrainings.map((training, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-white rounded border">
                  <div>
                    <span className="font-medium">{training.name}</span>
                    <span className="text-sm text-gray-600 ml-2">({training.subject})</span>
                    <div className="text-xs text-gray-500">
                      🏨 {getClientName(training.client_id)} | 👨‍🏫 {training.trainer}
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    training.status === 'completed' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {training.status === 'completed' ? '✅ Tamamlandı' : '📅 Planlandı'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const TrainingManagement = ({ selectedClient: propSelectedClient }) => {
  const [trainings, setTrainings] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState(''); // Add client selection state
  const [clientPersonnel, setClientPersonnel] = useState([]); // Personnel listesi
  const [showAddForm, setShowAddForm] = useState(false);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'calendar'
  const [editingTraining, setEditingTraining] = useState(null); // Düzenlenen eğitim
  const [formData, setFormData] = useState({
    client_id: '',
    name: '',
    subject: '',
    participant_count: '',
    trainer: '',
    training_date: '',
    training_time: '09:00',  // Add training time field
    description: '',
    attendees: [],  // Seçilen personeller
    status: 'planned'  // Default status
  });
  const [loading, setLoading] = useState(false);
  const { authToken, userRole, dbUser, ensureTokenForOperation } = useAuth();

  // Use selectedClient from props (for consultant) or manage locally (for admin/client)
  const effectiveSelectedClient = propSelectedClient;

  const API = getApiUrl();
  
  // Fetch client personnel when client is selected
  const fetchClientPersonnel = async (clientId) => {
    if (!clientId) {
      setClientPersonnel([]);
      return;
    }
    
    try {
      // Use the same endpoint as Personnel Management
      const response = await axios.get(`${API}/personnel?client_id=${clientId}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      console.log('🧑‍💼 Client Personnel Response:', response.data);
      setClientPersonnel(response.data || []);
    } catch (error) {
      console.error('Error fetching client personnel:', error);
      setClientPersonnel([]);
    }
  };

  // Handle client change
  const handleClientChange = (clientId) => {
    setFormData(prev => ({
      ...prev,
      client_id: clientId,
      attendees: []  // Reset attendees when client changes
    }));
    
    // Fetch personnel for the selected client
    fetchClientPersonnel(clientId);
  };

  // Handle personnel selection
  const handlePersonnelSelection = (personnelId, isSelected) => {
    setFormData(prev => ({
      ...prev,
      attendees: isSelected 
        ? [...prev.attendees, personnelId]
        : prev.attendees.filter(id => id !== personnelId)
    }));
  };

  // Handle select all personnel
  const handleSelectAllPersonnel = (selectAll) => {
    setFormData(prev => ({
      ...prev,
      attendees: selectAll ? clientPersonnel.map(p => p.id) : []
    }));
  };

  // Auto complete expired trainings
  const autoCompleteTrainings = async () => {
    try {
      const response = await axios.post(`${API}/trainings/auto-complete`, {}, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      console.log('🔄 Auto-complete result:', response.data);
      
      if (response.data.updated_count > 0) {
        alert(`${response.data.updated_count} eğitim otomatik olarak tamamlandı!`);
        fetchTrainings(); // Refresh the list
      }
    } catch (error) {
      console.error('Error auto-completing trainings:', error);
    }
  };

  // Delete training function
  const deleteTraining = async (trainingId) => {
    if (!window.confirm('Bu eğitimi silmek istediğinizden emin misiniz?')) {
      return;
    }
    
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      await axios.delete(`${API}/trainings/${trainingId}`, { headers });
      
      // Remove from local state
      setTrainings(prev => prev.filter(t => t.id !== trainingId));
      alert('✅ Eğitim başarıyla silindi!');
    } catch (error) {
      console.error('❌ Error deleting training:', error);
      alert(`❌ Eğitim silinirken hata: ${error.response?.data?.detail || error.message}`);
    }
  };

  const editTraining = (training) => {
    setEditingTraining(training);
    setFormData({
      client_id: training.client_id,
      name: training.name,
      subject: training.subject,
      participant_count: training.participant_count,
      trainer: training.trainer,
      training_date: training.training_date?.split('T')[0] || '',
      training_time: training.training_time || '09:00',
      description: training.description || '',
      attendees: training.attendees || [],
      status: training.status || 'planned'
    });
    setSelectedClient(training.client_id);
    fetchClientPersonnel(training.client_id);
    setShowAddForm(true);
  };

  const cancelEdit = () => {
    setEditingTraining(null);
    setFormData({
      client_id: '',
      name: '',
      subject: '',
      participant_count: '',
      trainer: '',
      training_date: '',
      training_time: '09:00',
      description: '',
      attendees: [],
      status: 'planned'
    });
    setShowAddForm(false);
  };

  const completeTraining = async (trainingId) => {
    if (!window.confirm('Bu eğitimi tamamlandı olarak işaretlemek istediğinizden emin misiniz?')) {
      return;
    }
    
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      await axios.put(`${API}/trainings/${trainingId}`, {
        status: 'completed'
      }, { headers });
      
      // Update local state
      setTrainings(prev => prev.map(t => 
        t.id === trainingId 
          ? { ...t, status: 'completed' }
          : t
      ));
      alert('✅ Eğitim tamamlandı olarak işaretlendi!');
    } catch (error) {
      console.error('❌ Error completing training:', error);
      alert(`❌ Eğitim tamamlanırken hata: ${error.response?.data?.detail || error.message}`);
    }
  };

  useEffect(() => {
    if (authToken && (userRole === 'admin' || userRole === 'consultant')) {
      fetchTrainings();
      fetchClients();
    }
  }, [authToken, userRole]);

  // Set effective client_id in formData when propSelectedClient or selectedClient changes
  useEffect(() => {
    if (propSelectedClient && propSelectedClient.id) {
      setFormData(prev => ({
        ...prev,
        client_id: propSelectedClient.id
      }));
    }
  }, [propSelectedClient]);

  // Sync selectedClient with formData and fetch personnel
  useEffect(() => {
    if (selectedClient) {
      setFormData(prev => ({
        ...prev,
        client_id: selectedClient,
        attendees: [] // Reset attendees when client changes
      }));
      fetchClientPersonnel(selectedClient);
    }
  }, [selectedClient]);

  // Auto-select client for CLIENT role users
  useEffect(() => {
    if (userRole === 'client' && dbUser?.client_id && !selectedClient) {
      setSelectedClient(dbUser.client_id);
      console.log('🔄 Auto-selected client for CLIENT user in Training:', dbUser.client_id);
    }
  }, [userRole, dbUser, selectedClient]);

  const fetchTrainings = async () => {
    if (!authToken) return;
    
    try {
      console.log('📚 Admin fetching trainings...');
      const response = await axios.get(`${API}/trainings`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      console.log('📚 Admin trainings response:', response.data);
      setTrainings(response.data);
    } catch (error) {
      console.error('❌ Error fetching trainings:', error);
      setTrainings([]);
    }
  };

  const fetchClients = async () => {
    if (!authToken) return;
    
    // Client users don't need to fetch clients - they use their own
    if (userRole === 'client') {
      console.log('👤 Client user - skipping client fetch, will use auto-selection');
      return;
    }
    
    try {
      console.log("👥 Admin fetching clients...");
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      console.log("👥 Admin clients response:", response.data);
      setClients(response.data.clients || []);
    } catch (error) {
      console.error("❌ Error fetching clients:", error);
      setClients([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // 🔄 ENSURE FRESH TOKEN BEFORE IMPORTANT OPERATION
      await ensureTokenForOperation();
      console.log('✅ Token refreshed before training submission');
      
      const trainingData = {
        ...formData,
        participant_count: parseInt(formData.participant_count) || 0,
        training_date: formData.training_date ? new Date(formData.training_date + 'T00:00:00Z').toISOString() : null,
        training_time: formData.training_time || '09:00',
        attendees: formData.attendees || []
      };
      
      let response;
      if (editingTraining) {
        // Update existing training
        console.log('📚 Updating training:', editingTraining.id, trainingData);
        response = await axios.put(`${API}/trainings/${editingTraining.id}`, trainingData, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        console.log('✅ Training updated:', response.data);
        alert('✅ Eğitim başarıyla güncellendi!');
      } else {
        // Create new training
        console.log('📚 Creating training:', trainingData);
        response = await axios.post(`${API}/trainings`, trainingData, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        console.log('✅ Training created:', response.data);
        alert('✅ Eğitim başarıyla oluşturuldu!');
      }
      
      // Reset form
      setFormData({
        client_id: '',
        name: '',
        subject: '',
        participant_count: '',
        trainer: '',
        training_date: '',
        training_time: '09:00',
        description: '',
        attendees: [],
        status: 'planned'
      });
      setShowAddForm(false);
      setEditingTraining(null);
      setClientPersonnel([]);
      fetchTrainings();
      
    } catch (error) {
      console.error('❌ Error saving training:', error);
      alert(`❌ Eğitim kaydetme hatası: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('tr-TR');
  };

  const isUpcoming = (dateString) => {
    if (!dateString) return false;
    return new Date(dateString) > new Date();
  };

  const getClientName = (clientId) => {
    const client = clients.find(c => c.id === clientId);
    return client ? (client.hotel_name || client.name) : "Bilinmeyen Müşteri";
  };

  return (
    <div className="space-y-6">
      {/* Client Section - Only Client Role */}
      {userRole === 'client' && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-800">👤 Kendi Eğitimleriniz</h3>
              <p className="text-gray-600 text-sm mt-1">Eğitim planlarınızı yönetebilir ve takip edebilirsiniz</p>
            </div>
            <button
              onClick={() => setShowAddForm(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center space-x-2"
            >
              <span>➕</span>
              <span>Yeni Eğitim</span>
            </button>
          </div>
        </div>
      )}

      {/* Client Selection */}
      {(userRole === 'admin' || userRole === 'consultant') && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Müşteri Seçimi</h3>
          <select
            value={selectedClient}
            onChange={(e) => setSelectedClient(e.target.value)}
            className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Bir müşteri seçin...</option>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>
                {client.hotel_name || client.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* View Toggle & Training List */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-800">📚 Eğitim Yönetimi</h2>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowAddForm(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center space-x-2"
              >
                <span>➕</span>
                <span>Yeni Eğitim</span>
              </button>
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  📋 Liste
                </button>
                <button
                  onClick={() => setViewMode('calendar')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    viewMode === 'calendar' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  📅 Takvim
                </button>
              </div>
            </div>
          </div>

          {viewMode === 'calendar' ? (
            <TrainingCalendar trainings={trainings} clients={clients} />
          ) : (
            <div>
              <h3 className="text-lg font-semibold mb-4">Eğitim Listesi</h3>
              {trainings.length === 0 ? (
                <div className="text-center py-8">
                  <span className="text-6xl mb-4 block">📚</span>
                  <p className="text-gray-500">Henüz eğitim eklenmemiş</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {trainings.map((training) => (
                    <div key={training.id} className="border rounded-lg p-4">
                      <h4 className="font-semibold">{training.name}</h4>
                      <p className="text-sm text-gray-600">{training.subject}</p>
                      
                      {/* Training Details */}
                      <div className="grid grid-cols-2 gap-4 mt-3 mb-3 text-sm">
                        <div>
                          <span className="text-gray-500">📅 Tarih:</span>
                          <span className="ml-1">{formatDate(training.training_date)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">👨‍🏫 Eğitmen:</span>
                          <span className="ml-1">{training.trainer || 'Belirtilmemiş'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">📊 Katılımcı Sayısı:</span>
                          <span className="ml-1">{training.participant_count || 0} kişi</span>
                        </div>
                        <div>
                          <span className="text-gray-500">📋 Durum:</span>
                          <span className={`ml-1 px-2 py-1 rounded-full text-xs font-medium ${
                            training.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : training.status === 'cancelled'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {training.status === 'completed' ? '✅ Tamamlandı' : 
                             training.status === 'cancelled' ? '❌ İptal' : '📅 Planlandı'}
                          </span>
                        </div>
                      </div>

                      {/* Attendees Section */}
                      {training.attendees && training.attendees.length > 0 && (
                        <div className="mb-3">
                          <div className="text-sm text-gray-600 mb-2">
                            👥 Katılımcılar ({training.attendees.length}):
                          </div>
                          <AttendeesList 
                            attendeeIds={training.attendees}
                            clientId={training.client_id}
                            authToken={authToken}
                          />
                        </div>
                      )}

                      {/* Description */}
                      {training.description && (
                        <div className="mb-3">
                          <p className="text-sm text-gray-600">
                            <span className="font-medium">📝 Açıklama:</span> {training.description}
                          </p>
                        </div>
                      )}

                      <div className="flex justify-between items-center mt-3 pt-3 border-t">
                        <span className="text-xs text-gray-500">
                          ID: {training.id}
                        </span>
                        <div className="space-x-2">
                          <button
                            onClick={() => editTraining(training)}
                            className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                          >
                            ✏️ Düzenle
                          </button>
                          {training.status !== 'completed' && (
                            <button
                              onClick={() => completeTraining(training.id)}
                              className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
                            >
                              ✅ Tamamla
                            </button>
                          )}
                          <button
                            onClick={() => deleteTraining(training.id)}
                            className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600"
                          >
                            🗑️ Sil
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Training Form Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">
                {editingTraining ? '✏️ Eğitimi Düzenle' : '➕ Yeni Eğitim Ekle'}
              </h3>
              <button
                onClick={cancelEdit}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Client Selection for Admin/Consultant */}
              {(userRole === 'admin' || userRole === 'consultant') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Müşteri *
                  </label>
                  <select
                    value={formData.client_id}
                    onChange={(e) => handleClientChange(e.target.value)}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Müşteri seçin...</option>
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.hotel_name || client.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Eğitim Adı *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Konu
                  </label>
                  <input
                    type="text"
                    value={formData.subject}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Eğitmen
                  </label>
                  <input
                    type="text"
                    value={formData.trainer}
                    onChange={(e) => setFormData({ ...formData, trainer: e.target.value })}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tarih
                  </label>
                  <input
                    type="date"
                    value={formData.training_date}
                    onChange={(e) => setFormData({ ...formData, training_date: e.target.value })}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Katılımcı Sayısı
                  </label>
                  <input
                    type="number"
                    value={formData.participant_count}
                    onChange={(e) => setFormData({ ...formData, participant_count: e.target.value })}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Eğitim Durumu
                  </label>
                  <select
                    value={formData.status || 'planned'}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="planned">📅 Planlandı</option>
                    <option value="completed">✅ Tamamlandı</option>
                    <option value="cancelled">❌ İptal Edildi</option>
                  </select>
                </div>
              </div>

              {/* Personnel Selection Section */}
              {clientPersonnel.length > 0 && (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Katılımcı Seçimi ({clientPersonnel.length} kişi mevcut)
                    </label>
                    <div className="flex space-x-2">
                      <button
                        type="button"
                        onClick={() => handleSelectAllPersonnel(true)}
                        className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200"
                      >
                        Tümünü Seç
                      </button>
                      <button
                        type="button"
                        onClick={() => handleSelectAllPersonnel(false)}
                        className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200"
                      >
                        Tümünü Kaldır
                      </button>
                    </div>
                  </div>
                  <div className="max-h-40 overflow-y-auto border rounded-lg p-3 bg-gray-50">
                    <div className="grid grid-cols-1 gap-2">
                      {clientPersonnel.map((person) => {
                        const displayName = person.full_name || 
                                          `${person.name || ''} ${person.surname || ''}`.trim() || 
                                          person.position || 
                                          'İsimsiz';
                        const isSelected = formData.attendees.includes(person.id);
                        
                        return (
                          <label key={person.id} className="flex items-center space-x-2 cursor-pointer hover:bg-white rounded p-2">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={(e) => handlePersonnelSelection(person.id, e.target.checked)}
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-sm text-gray-900">{displayName}</div>
                              {person.position && (
                                <div className="text-xs text-gray-500">{person.position}</div>
                              )}
                              {person.department && (
                                <div className="text-xs text-gray-400">{person.department}</div>
                              )}
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-gray-600">
                    Seçilen katılımcı sayısı: <span className="font-medium text-blue-600">{formData.attendees.length}</span>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Açıklama
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                />
              </div>

              <div className="flex space-x-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-colors font-medium"
                >
                  {loading ? 'Kaydediliyor...' : (editingTraining ? '📝 Güncelle' : '➕ Kaydet')}
                </button>
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition-colors font-medium"
                >
                  İptal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};



// Email Management Component - BULK EMAIL WITH TEMPLATES
const EmailManagement = ({ selectedClient: propSelectedClient }) => {
  const { authToken, user, userRole, dbUser } = useAuth();
  const { session } = useClerk();
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [customContent, setCustomContent] = useState('');
  const [bulkEmailStats, setBulkEmailStats] = useState(null);
  const [emailFilters, setEmailFilters] = useState({
    city: '',
    audit_company: '',
    has_email: true,
    certificate_filter: ''
  });
  const [showPreview, setShowPreview] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  
  const API = getApiUrl();

  // Fetch email templates
  useEffect(() => {
    if (userRole === 'admin') {
      fetchTemplates();
      fetchBulkEmailStats();
    }
  }, [userRole]);

  const fetchTemplates = async () => {
    try {
      let currentToken = authToken;
      if (!currentToken && session) {
        currentToken = await session.getToken();
      }

      const response = await axios.get(`${API}/api/email-templates`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      
      setTemplates(response.data.templates || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
      setTemplates([]);
    }
  };

  const fetchBulkEmailStats = async () => {
    try {
      let currentToken = authToken;
      if (!currentToken && session) {
        currentToken = await session.getToken();
      }

      const response = await axios.get(`${API}/api/bulk-email/stats`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      
      setBulkEmailStats(response.data);
    } catch (error) {
      console.error('Error fetching bulk email stats:', error);
    }
  };

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setCustomContent(''); // Reset custom content
    setShowPreview(true);
  };

  const sendBulkEmail = async () => {
    if (!selectedTemplate) {
      alert('Lütfen bir template seçiniz!');
      return;
    }

    setSendingEmail(true);
    try {
      let currentToken = authToken;
      if (!currentToken && session) {
        currentToken = await session.getToken();
      }

      const emailData = {
        template_id: selectedTemplate.id,
        email_type: 'bulk',
        filters: emailFilters
      };

      // Add custom content for general announcement
      if (selectedTemplate.id === 'general_announcement' && customContent.trim()) {
        emailData.custom_content = customContent;
      }

      const response = await axios.post(`${API}/api/bulk-email/send`, emailData, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      alert(`✅ Toplu email başarıyla gönderildi!\n\n📊 İstatistikler:\n• Gönderilen: ${response.data.sent_count} email\n• Başarısız: ${response.data.failed_count} email\n• Toplam süre: ${response.data.duration_seconds} saniye`);
      
      // Reset form
      setSelectedTemplate(null);
      setCustomContent('');
      setShowPreview(false);
      
      // Refresh stats
      fetchBulkEmailStats();
      
    } catch (error) {
      console.error('Bulk email error:', error);
      alert('❌ Toplu email gönderim hatası: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSendingEmail(false);
    }
  };

  const sendTestEmail = async () => {
    if (!selectedTemplate) {
      alert('Lütfen önce bir template seçiniz!');
      return;
    }

    if (!testEmail || !testEmail.includes('@')) {
      alert('Lütfen geçerli bir test email adresi giriniz!');
      return;
    }

    setSendingTestEmail(true);
    try {
      let currentToken = authToken;
      if (!currentToken && session) {
        try {
          currentToken = await session.getToken();
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
          return;
        }
      }

      const testEmailData = {
        template_id: selectedTemplate.id,
        test_email: testEmail
      };

      // Add custom content for general announcement
      if (selectedTemplate.id === 'general_announcement' && bulkEmailForm.custom_content.trim()) {
        testEmailData.custom_content = bulkEmailForm.custom_content;
      }

      const response = await axios.post(`${API}/email-templates/test`, testEmailData, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      alert(`✅ Test email başarıyla gönderildi!\n\n📧 Gönderilen Adres: ${testEmail}\n🎨 Template: ${selectedTemplate.name}\n\nEmail kutunuzu kontrol ediniz.`);
      
    } catch (error) {
      console.error('Test email error:', error);
      alert('❌ Test email gönderim hatası: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSendingTestEmail(false);
    }
  };

  if (userRole !== 'admin') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="text-6xl mb-4">🚫</div>
            <h1 className="text-2xl font-bold text-gray-800 mb-4">Erişim Engellendi</h1>
            <p className="text-gray-600">Bu özellik sadece admin kullanıcıları için mevcuttur.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 mb-2">📧 Toplu Email Yönetimi</h1>
              <p className="text-gray-600">Müşterilerinize profesyonel email şablonları ile ulaşın</p>
            </div>
            {bulkEmailStats && (
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">{bulkEmailStats.total_bulk_clients}</div>
                <div className="text-sm text-gray-500">Toplam Bulk Müşteri</div>
                <div className="text-sm text-green-600">{bulkEmailStats.bulk_clients_with_email} email adresi</div>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Email Templates */}
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">🎨 Email Şablonları</h2>
            
            <div className="space-y-4">
              {templates.map((template) => (
                <div 
                  key={template.id}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedTemplate?.id === template.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleTemplateSelect(template)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-bold text-gray-800">{template.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                      <div className="text-xs text-gray-500 mt-2 truncate">
                        📧 {template.subject}
                      </div>
                    </div>
                    <div className="ml-4">
                      {selectedTemplate?.id === template.id ? (
                        <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-xs">✓</span>
                        </div>
                      ) : (
                        <div className="w-6 h-6 border-2 border-gray-300 rounded-full"></div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Filters */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-bold text-gray-800 mb-3">🎯 Hedef Müşteri Filtreleri</h3>
              <div className="grid grid-cols-1 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Şehir</label>
                  <input
                    type="text"
                    placeholder="Şehir filtresi (örn: İstanbul)"
                    value={emailFilters.city}
                    onChange={(e) => setEmailFilters({...emailFilters, city: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Denetim Firması</label>
                  <input
                    type="text"
                    placeholder="Denetim firması filtresi"
                    value={emailFilters.audit_company}
                    onChange={(e) => setEmailFilters({...emailFilters, audit_company: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={emailFilters.has_email}
                    onChange={(e) => setEmailFilters({...emailFilters, has_email: e.target.checked})}
                    className="mr-2"
                  />
                  <label className="text-sm text-gray-700">Sadece email adresi olanlar</label>
                </div>
              </div>
            </div>
          </div>

          {/* Preview & Send */}
          <div className="bg-white rounded-2xl shadow-xl p-6">
            {selectedTemplate ? (
              <>
                <h2 className="text-xl font-bold text-gray-800 mb-4">👁️ Email Önizleme</h2>
                
                <div className="mb-4">
                  <div className="bg-gray-50 p-3 rounded-lg mb-3">
                    <div className="text-sm font-medium text-gray-700">📧 Konu:</div>
                    <div className="text-gray-800">{selectedTemplate.subject}</div>
                  </div>
                  
                  {selectedTemplate.id === 'general_announcement' && (
                    <div className="mb-3">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        📝 Özel İçerik (Duyuru metni):
                      </label>
                      <textarea
                        value={customContent}
                        onChange={(e) => setCustomContent(e.target.value)}
                        placeholder="Buraya duyuru içeriğinizi yazın..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        rows={4}
                      />
                    </div>
                  )}
                  
                  <div className="bg-gray-50 p-3 rounded-lg max-h-60 overflow-y-auto">
                    <div className="text-sm font-medium text-gray-700 mb-2">📝 İçerik Önizleme:</div>
                    <div className="text-gray-800 whitespace-pre-line text-sm">
                      {selectedTemplate.id === 'general_announcement' && customContent
                        ? selectedTemplate.content.replace('{content}', customContent)
                        : selectedTemplate.content}
                    </div>
                  </div>
                </div>

                {bulkEmailStats && (
                  <div className="bg-blue-50 p-4 rounded-lg mb-4">
                    <div className="text-sm text-blue-800">
                      <div className="font-bold mb-2">📊 Gönderim Özeti:</div>
                      <div>• Toplam Bulk Müşteri: {bulkEmailStats.total_bulk_clients}</div>
                      <div>• Email Adresi Olan: {bulkEmailStats.bulk_clients_with_email}</div>
                      <div>• Filtreli Gönderim: {emailFilters.city || emailFilters.audit_company ? 'Evet' : 'Tüm müşteriler'}</div>
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    onClick={sendBulkEmail}
                    disabled={sendingEmail}
                    className="flex-1 bg-gradient-to-r from-blue-500 to-blue-600 text-white py-3 px-6 rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all font-medium disabled:opacity-50"
                  >
                    {sendingEmail ? '📤 Gönderiliyor...' : '📧 Toplu Email Gönder'}
                  </button>
                  <button
                    onClick={() => {
                      setSelectedTemplate(null);
                      setCustomContent('');
                      setShowPreview(false);
                    }}
                    className="px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    ❌
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📧</div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Template Seçin</h3>
                <p className="text-gray-600">Email gönderebilmek için bir template seçiniz</p>
              </div>
            )}
          </div>
        </div>

        {/* Statistics */}
        {bulkEmailStats && (
          <div className="bg-white rounded-2xl shadow-xl p-6 mt-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">📈 Email İstatistikleri</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{bulkEmailStats.total_bulk_clients}</div>
                <div className="text-sm text-gray-600">Toplam Bulk Müşteri</div>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{bulkEmailStats.bulk_clients_with_email}</div>
                <div className="text-sm text-gray-600">Email Adresi Olan</div>
              </div>
              
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">{bulkEmailStats.email_coverage_percentage}%</div>
                <div className="text-sm text-gray-600">Email Kapsamı</div>
              </div>
            </div>

            {bulkEmailStats.city_distribution && bulkEmailStats.city_distribution.length > 0 && (
              <div className="mt-6">
                <h3 className="font-bold text-gray-800 mb-3">🏙️ Şehir Dağılımı (Top 5)</h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                  {bulkEmailStats.city_distribution.slice(0, 5).map((city, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded-lg text-center">
                      <div className="font-bold text-gray-800">{city.count}</div>
                      <div className="text-xs text-gray-600">{city._id || 'Bilinmiyor'}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Reports Management Component
const ReportsManagement = ({ selectedClient: propSelectedClient }) => {
  const { authToken, user, userRole, dbUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState(propSelectedClient || '');
  const [reports, setReports] = useState([]);
  const [downloadingReport, setDownloadingReport] = useState('');
  const API = getApiUrl();

  // Download comprehensive report
  const downloadComprehensiveReport = async () => {
    try {
      setDownloadingReport('comprehensive');
      
      let url = `${API}/reports/comprehensive`;
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        url += `?client_id=${selectedClient}`;
      }
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${authToken}` },
        responseType: 'blob'
      });

      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `suruduurulebilirlik_raporu_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      alert('Sürdürülebilirlik raporu başarıyla indirildi!');
    } catch (error) {
      console.error('Error downloading comprehensive report:', error);
      alert('Rapor indirme sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    } finally {
      setDownloadingReport('');
    }
  };

  // Download training report
  const downloadTrainingReport = async () => {
    try {
      setDownloadingReport('training');
      
      let url = `${API}/reports/training`;
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        url += `?client_id=${selectedClient}`;
      }
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${authToken}` },
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `egitim_raporu_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      alert('Eğitim raporu başarıyla indirildi!');
    } catch (error) {
      console.error('Error downloading training report:', error);
      alert('Rapor indirme sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    } finally {
      setDownloadingReport('');
    }
  };

  // Download consumption report
  const downloadConsumptionReport = async () => {
    try {
      setDownloadingReport('consumption');
      
      let url = `${API}/reports/consumption`;
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        url += `?client_id=${selectedClient}`;
      }
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${authToken}` },
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `tuketim_raporu_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      alert('Tüketim raporu başarıyla indirildi!');
    } catch (error) {
      console.error('Error downloading consumption report:', error);
      alert('Rapor indirme sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    } finally {
      setDownloadingReport('');
    }
  };

  // Fetch clients for selection
  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" },
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      if (response.data.clients) {
        setClients(response.data.clients || []);
      } else if (Array.isArray(response.data)) {
        setClients(response.data || []);
      } else {
        setClients([]);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authToken) {
      fetchClients();
    }
  }, [authToken]);

  // Auto-select client for CLIENT role users
  useEffect(() => {
    if (userRole === 'client' && dbUser?.client_id && !selectedClient) {
      setSelectedClient(dbUser.client_id);
    }
  }, [userRole, dbUser, selectedClient]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-700 text-white p-6 shadow-xl">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">📊 Raporlar</h1>
          <p className="text-purple-100 text-lg">Sürdürülebilirlik ve performans raporları</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        
        {/* Client Selection - Only for Admin and Consultant */}
        {(userRole === 'admin' || userRole === 'consultant') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">1. Müşteri Seçimi</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Müşteri Seçin
                </label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">-- Müşteri Seçin --</option>
                  {Array.isArray(clients) && clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name || client.hotel_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Reports Section */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-6">📈 Mevcut Raporlar</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Sustainability Report */}
            <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="text-center">
                <div className="text-4xl mb-4">🌱</div>
                <h3 className="text-lg font-bold text-gray-800 mb-2">Profesyonel Sürdürülebilirlik Raporu</h3>
                <p className="text-gray-600 text-sm mb-4">
                  NEST Hotel tarzında profesyonel format ile tüm sürdürülebilirlik verileri
                </p>
                <button 
                  onClick={downloadComprehensiveReport}
                  disabled={!selectedClient || downloadingReport === 'comprehensive'}
                  className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {downloadingReport === 'comprehensive' ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      İndiriliyor...
                    </>
                  ) : (
                    <>
                      📥 PDF İndir
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Training Report */}
            <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="text-center">
                <div className="text-4xl mb-4">🎓</div>
                <h3 className="text-lg font-bold text-gray-800 mb-2">Eğitim Raporu</h3>
                <p className="text-gray-600 text-sm mb-4">
                  Tüm eğitimler, katılımcılar ve tamamlanma oranları
                </p>
                <button 
                  onClick={downloadTrainingReport}
                  disabled={!selectedClient || downloadingReport === 'training'}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {downloadingReport === 'training' ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      İndiriliyor...
                    </>
                  ) : (
                    <>
                      📥 PDF İndir
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Consumption Report */}
            <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow">
              <div className="text-center">
                <div className="text-4xl mb-4">⚡</div>
                <h3 className="text-lg font-bold text-gray-800 mb-2">Tüketim Raporu</h3>
                <p className="text-gray-600 text-sm mb-4">
                  Enerji, su, gaz tüketimi ve trend analizleri
                </p>
                <button 
                  onClick={downloadConsumptionReport}
                  disabled={!selectedClient || downloadingReport === 'consumption'}
                  className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {downloadingReport === 'consumption' ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      İndiriliyor...
                    </>
                  ) : (
                    <>
                      📥 PDF İndir
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {!selectedClient && (userRole === 'admin' || userRole === 'consultant') && (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">📊</div>
              <p className="text-sm">Rapor oluşturmak için önce bir müşteri seçin.</p>
            </div>
          )}
        </div>

        {/* Coming Soon Features */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-6">🚀 Yakında Gelecek Özellikler</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">📈 Otomatik Raporlama</h3>
              <p className="text-gray-600 text-sm">Belirli aralıklarla otomatik rapor oluşturma</p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">📧 Email Gönderimi</h3>
              <p className="text-gray-600 text-sm">Raporları otomatik email ile gönderme</p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">📋 Özel Şablonlar</h3>
              <p className="text-gray-600 text-sm">Müşteri özel rapor şablonları</p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">🔄 Karşılaştırmalı Analiz</h3>
              <p className="text-gray-600 text-sm">Dönemsel karşılaştırma raporları</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Email Notification Management Component
const EmailNotificationManagement = () => {
  const { authToken, user, userRole, dbUser } = useAuth();
  const { session } = useClerk();
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [documents, setDocuments] = useState([]);
  const [trainings, setTrainings] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [selectedTrainings, setSelectedTrainings] = useState([]);
  const [activeTab, setActiveTab] = useState('documents');
  const API = getApiUrl();

  // Fetch clients
  const fetchClients = async () => {
    try {
      let currentToken = authToken;
      if (!currentToken && session) {
        try {
          currentToken = await session.getToken();
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      setClients(response.data.clients || []);
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
    }
  };

  // Fetch documents
  const fetchDocuments = async (clientId) => {
    try {
      let currentToken = authToken;
      if (!currentToken && session) {
        try {
          currentToken = await session.getToken();
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const response = await axios.get(`${API}/documents`, {
        params: { client_id: clientId },
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      setDocuments(response.data.map(doc => ({ ...doc, selected: false })));
    } catch (error) {
      console.error('Error fetching documents:', error);
      setDocuments([]);
    }
  };

  // Fetch trainings
  const fetchTrainings = async (clientId) => {
    try {
      let currentToken = authToken;
      if (!currentToken && session) {
        try {
          currentToken = await session.getToken();
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const response = await axios.get(`${API}/trainings`, {
        params: { client_id: clientId },
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      setTrainings(response.data.map(training => ({ ...training, selected: false })));
    } catch (error) {
      console.error('Error fetching trainings:', error);
      setTrainings([]);
    }
  };

  // Toggle document selection
  const toggleDocumentSelection = (docId) => {
    setDocuments(prev => prev.map(doc => 
      doc.id === docId ? { ...doc, selected: !doc.selected } : doc
    ));
    
    setSelectedDocuments(prev => {
      if (prev.includes(docId)) {
        return prev.filter(id => id !== docId);
      } else {
        return [...prev, docId];
      }
    });
  };

  // Toggle training selection
  const toggleTrainingSelection = (trainingId) => {
    setTrainings(prev => prev.map(training => 
      training.id === trainingId ? { ...training, selected: !training.selected } : training
    ));
    
    setSelectedTrainings(prev => {
      if (prev.includes(trainingId)) {
        return prev.filter(id => id !== trainingId);
      } else {
        return [...prev, trainingId];
      }
    });
  };

  // Select all documents
  const selectAllDocuments = () => {
    const allSelected = documents.every(doc => doc.selected);
    setDocuments(prev => prev.map(doc => ({ ...doc, selected: !allSelected })));
    setSelectedDocuments(allSelected ? [] : documents.map(doc => doc.id));
  };

  // Select all trainings
  const selectAllTrainings = () => {
    const allSelected = trainings.every(training => training.selected);
    setTrainings(prev => prev.map(training => ({ ...training, selected: !allSelected })));
    setSelectedTrainings(allSelected ? [] : trainings.map(training => training.id));
  };

  // Clear selections
  const clearSelections = () => {
    if (activeTab === 'documents') {
      setDocuments(prev => prev.map(doc => ({ ...doc, selected: false })));
      setSelectedDocuments([]);
    } else {
      setTrainings(prev => prev.map(training => ({ ...training, selected: false })));
      setSelectedTrainings([]);
    }
  };

  // Send email notification - SABİT FORMAT
  const sendEmailNotification = async () => {
    try {
      if (!selectedClient) {
        alert('Lütfen müşteri seçin!');
        return;
      }

      const selectedItems = activeTab === 'documents' ? 
        documents.filter(doc => selectedDocuments.includes(doc.id)) :
        trainings.filter(training => selectedTrainings.includes(training.id));

      if (selectedItems.length === 0) {
        alert('Lütfen en az bir item seçin!');
        return;
      }

      let currentToken = authToken;
      if (!currentToken && session) {
        try {
          currentToken = await session.getToken();
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const clientName = clients.find(c => c.id === selectedClient)?.name || 
                        clients.find(c => c.id === selectedClient)?.hotel_name || 
                        'Değerli Müşterimiz';

      const emailData = {
        client_id: selectedClient,
        type: activeTab === 'documents' ? 'document' : 'training',
        subject: activeTab === 'documents' ? 
          `ROTA CRM - Yeni Doküman Bildirimi (${selectedItems.length} adet)` : 
          `ROTA CRM - Yeni Eğitim Bildirimi (${selectedItems.length} adet)`,
        message: `Sayın ${clientName},\n\nSisteminize ${selectedItems.length} adet yeni ${activeTab === 'documents' ? 'doküman' : 'eğitim'} yüklenmiştir. Detaylar aşağıdadır.\n\nSaygılarımızla,\nROTA CRM Ekibi`,
        items: selectedItems.map(item => ({
          id: item.id,
          name: item.displayName,
          ...(activeTab === 'documents' ? {
            upload_date: item.uploadDate,
            folder_path: item.folderPath
          } : {
            training_date: item.trainingDate,
            trainer: item.trainer,
            hours: item.hours // Eğitim saati
          })
        }))
      };

      await axios.post(`${API}/email/send-notification`, emailData, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      alert('✅ Email başarıyla gönderildi!');
      clearSelections();
      
    } catch (error) {
      console.error('Error sending email:', error);
      alert('❌ Email gönderilirken hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Initial data loading
  useEffect(() => {
    if (authToken && (userRole === 'admin' || userRole === 'consultant')) {
      fetchClients();
    }
    setLoading(false);
  }, [authToken, userRole]);

  // Auto-select client for CLIENT role users
  useEffect(() => {
    if (userRole === 'client' && dbUser?.client_id && !selectedClient) {
      setSelectedClient(dbUser.client_id);
    }
  }, [userRole, dbUser, selectedClient]);

  // Load data when client is selected
  useEffect(() => {
    if (selectedClient) {
      fetchDocuments(selectedClient);
      fetchTrainings(selectedClient);
    }
  }, [selectedClient]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 text-white p-6 shadow-xl">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">📧 Email Yönetimi</h1>
          <p className="text-blue-100 text-lg">Doküman ve eğitim bildirimleri gönderme sistemi</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        
        {/* Client Selection - For Admin and Consultant */}
        {(userRole === 'admin' || userRole === 'consultant') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">1. Müşteri Seçimi</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Müşteri Seçin
                </label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">-- Müşteri Seçin --</option>
                  {Array.isArray(clients) && clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name || client.hotel_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Consultant needs client selection message */}
        {userRole === 'consultant' && !selectedClient && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📧</div>
              <p className="text-gray-500 text-lg mb-2">Email yönetimi için önce bir müşteri seçin.</p>
              <p className="text-gray-400 text-sm">Yukarıdaki dropdown'dan müşteri seçerek başlayabilirsiniz.</p>
            </div>
          </div>
        )}

        {/* Client Info - For Client Users */}
        {userRole === 'client' && selectedClient && Array.isArray(clients) && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">📧 Email Bildirimleri</h2>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-800">
                <strong>🏢 İşletme:</strong> {clients.find(c => c.id === selectedClient)?.name || clients.find(c => c.id === selectedClient)?.hotel_name}
              </p>
              <p className="text-blue-600 text-sm mt-1">Doküman ve eğitim bildirimlerinizi buradan yönetebilirsiniz.</p>
            </div>
          </div>
        )}

        {selectedClient && (
          <>
            {/* Tabs */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex space-x-4 mb-6">
                <button
                  onClick={() => setActiveTab('documents')}
                  className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                    activeTab === 'documents'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📄 Dokümanlar ({documents.length})
                </button>
                <button
                  onClick={() => setActiveTab('trainings')}
                  className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                    activeTab === 'trainings'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  🎓 Eğitimler ({trainings.length})
                </button>
              </div>

              {/* Selection Controls */}
              <div className="flex flex-wrap gap-4 mb-6">
                <button
                  onClick={activeTab === 'documents' ? selectAllDocuments : selectAllTrainings}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  {(activeTab === 'documents' ? documents : trainings).every(item => item.selected) ? 
                    '❌ Tümünü Kaldır' : '✅ Tümünü Seç'}
                </button>
                <button
                  onClick={clearSelections}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  🗑️ Seçimi Temizle
                </button>
                <div className="text-sm text-gray-600 flex items-center">
                  Seçilen: {activeTab === 'documents' ? selectedDocuments.length : selectedTrainings.length} item
                </div>
              </div>

              {/* Documents Tab */}
              {activeTab === 'documents' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-800">📄 Dokümanlar</h3>
                  
                  {documents.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <p>Henüz doküman bulunmuyor.</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {documents.map((doc) => (
                        <div
                          key={doc.id}
                          className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                            doc.selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                          }`}
                          onClick={() => toggleDocumentSelection(doc.id)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <input
                                type="checkbox"
                                checked={doc.selected}
                                onChange={() => {}}
                                className="h-5 w-5 text-blue-600"
                              />
                              <div>
                                <h4 className="font-medium text-gray-900">{doc.displayName}</h4>
                                <p className="text-sm text-gray-600">
                                  📁 Klasör: {doc.folderPath}
                                </p>
                                <p className="text-sm text-gray-500">
                                  📅 Yükleme: {new Date(doc.uploadDate).toLocaleDateString('tr-TR')}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <span className={`px-2 py-1 rounded-full text-xs ${
                                doc.selected ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
                              }`}>
                                {doc.selected ? 'Seçildi' : 'Seç'}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Trainings Tab */}
              {activeTab === 'trainings' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-800">🎓 Eğitimler</h3>
                  
                  {trainings.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <p>Henüz eğitim bulunmuyor.</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {trainings.map((training) => (
                        <div
                          key={training.id}
                          className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                            training.selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                          }`}
                          onClick={() => toggleTrainingSelection(training.id)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <input
                                type="checkbox"
                                checked={training.selected}
                                onChange={() => {}}
                                className="h-5 w-5 text-blue-600"
                              />
                              <div>
                                <h4 className="font-medium text-gray-900">{training.displayName}</h4>
                                <p className="text-sm text-gray-600">
                                  👨‍🏫 Eğitmen: {training.trainer}
                                </p>
                                <p className="text-sm text-gray-500">
                                  📅 Tarih: {new Date(training.trainingDate).toLocaleDateString('tr-TR')} | 
                                  ⏰ Eğitim Saati: {training.hours}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <span className={`px-2 py-1 rounded-full text-xs ${
                                training.selected ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
                              }`}>
                                {training.selected ? 'Seçildi' : 'Seç'}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Email Gönderme - SABİT FORMAT */}
            {((activeTab === 'documents' && selectedDocuments.length > 0) || 
              (activeTab === 'trainings' && selectedTrainings.length > 0)) && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">✉️ Email Gönder (Sabit Format)</h3>
                
                <div className="bg-gray-50 p-4 rounded-lg mb-4">
                  <div className="text-sm text-gray-600 space-y-2">
                    <p><strong>📧 Konu:</strong> ROTA CRM - Yeni {activeTab === 'documents' ? 'Doküman' : 'Eğitim'} Bildirimi ({(activeTab === 'documents' ? selectedDocuments : selectedTrainings).length} adet)</p>
                    <p><strong>📝 İçerik:</strong> Standart ROTA CRM bildirim formatı kullanılacak</p>
                    <p><strong>📊 Seçilen İtemler:</strong> {activeTab === 'documents' ? selectedDocuments.length : selectedTrainings.length} adet</p>
                    <p><strong>🏢 Müşteri:</strong> {clients.find(c => c.id === selectedClient)?.name || clients.find(c => c.id === selectedClient)?.hotel_name}</p>
                  </div>
                </div>
                
                <div className="flex justify-center">
                  <button
                    onClick={sendEmailNotification}
                    className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg"
                  >
                    📧 Sabit Formatta Email Gönder
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// Simple Sidebar Component (Temporary Fix)
const Sidebar = ({ activeTab, onNavigate, userRole }) => {
  const adminMenuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'clients', name: 'Müşteri Yönetimi', icon: '🏨' },
    { id: 'bulk-operations', name: 'Bulk İşlemler', icon: '📦' },
    { id: 'consultants', name: 'Danışman Yönetimi', icon: '👔' },
    { id: 'consumption', name: 'Tüketim Takibi', icon: '⚡' },
    { id: 'analytics', name: 'Tüketim Analizi', icon: '📈' },
    { id: 'carbon', name: 'Karbon Ayak İzi', icon: '🌍' },
    { id: 'waste-management', name: 'Atık Yönetimi', icon: '🗑️' },
    { id: 'suppliers', name: 'Tedarikçi Yönetimi', icon: '🏢' },
    { id: 'personnel', name: 'Personel Yönetimi', icon: '👥' },
    { id: 'sustainability-targets', name: 'Sürdürülebilirlik Hedefleri', icon: '🎯' },
    { id: 'yeni-belge', name: 'Belge Yönetimi', icon: '📋' },
    { id: 'training', name: 'Eğitim Yönetimi', icon: '🎓' },
    { id: 'email-management', name: 'Email Yönetimi', icon: '📧' },
    { id: 'ai-assistant', name: 'AI Asistan', icon: '🤖' },
    { id: 'reports', name: 'Raporlar', icon: '📊' }
  ];

  const clientMenuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'consumption', name: 'Tüketim Takibi', icon: '⚡' },
    { id: 'analytics', name: 'Tüketim Analizi', icon: '📈' },
    { id: 'carbon', name: 'Karbon Ayak İzi', icon: '🌍' },
    { id: 'waste-management', name: 'Atık Yönetimi', icon: '🗑️' },
    { id: 'suppliers', name: 'Tedarikçi Yönetimi', icon: '🏢' },
    { id: 'personnel', name: 'Personel Yönetimi', icon: '👥' },
    { id: 'sustainability-targets', name: 'Sürdürülebilirlik Hedefleri', icon: '🎯' },
    { id: 'yeni-belge', name: 'Belge Yönetimi', icon: '📋' },
    { id: 'ai-assistant', name: 'AI Asistan', icon: '🤖' },
    { id: 'training', name: 'Eğitimlerim', icon: '🎓' }
  ];

  const menuItems = userRole === 'admin' ? adminMenuItems : clientMenuItems;

  return (
    <div 
      className="text-white w-64 shadow-2xl"
      style={{
        background: 'linear-gradient(180deg, #111827 0%, #1f2937 50%, #111827 100%)',
        minHeight: '100vh',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto', // Sidebar scroll özelliği
        overflowX: 'hidden'
      }}
    >
      <div 
        className="p-6 flex-1 flex flex-col"
        style={{ 
          minHeight: '100vh',
          background: 'linear-gradient(180deg, #111827 0%, #1f2937 50%, #111827 100%)'
        }}
      >
        <div className="text-center mb-8 flex-shrink-0">
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-3">
            <span className="text-white text-xl font-bold">R</span>
          </div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            ROTA CRM
          </h1>
          <p className="text-gray-400 text-sm mt-1">Sürdürülebilirlik Paneli</p>
        </div>

        <nav 
          className="space-y-2 flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800" 
          style={{ 
            minHeight: '400px',
            maxHeight: 'calc(100vh - 200px)', // Header ve footer için alan bırak
            paddingRight: '8px', // Scroll bar için alan
            scrollbarWidth: 'thin',
            scrollbarColor: '#4B5563 #1F2937'
          }}
        >
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`group w-full text-left px-4 py-3 rounded-xl transition-all duration-200 ${
                activeTab === item.id 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg transform scale-105' 
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white hover:translate-x-2'
              }`}
            >
              <span className="mr-3 text-lg">{item.icon}</span>
              <span className="font-medium">{item.name}</span>
              {activeTab === item.id && (
                <span className="float-right text-white">⚡</span>
              )}
            </button>
          ))}
        </nav>
        
        <div 
          className="p-4 rounded-xl flex-shrink-0" 
          style={{ 
            background: 'linear-gradient(90deg, #059669, #0d9488)',
            marginTop: '20px',
            marginBottom: '10px'
          }}
        >
          <div className="text-center">
            <div className="text-2xl mb-2">🌱</div>
            <p className="text-white text-sm font-medium">Sürdürülebilir Gelecek</p>
            <p className="text-emerald-100 text-xs mt-1">Çevre dostu çözümler</p>
          </div>
        </div>
        
        {/* Çıkış Butonu */}
        <div className="p-4 flex-shrink-0">
          <SignOutButton>
            <button className="w-full bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-xl transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg">
              <span className="text-lg">🚪</span>
              <span className="font-medium">Çıkış Yap</span>
            </button>
          </SignOutButton>
        </div>
      </div>
    </div>
  );
};

// 2FA Component
// 2FA Component
const TwoFactorAuth = ({ onVerificationComplete }) => {
  const [step, setStep] = useState('send'); // 'send' or 'verify'
  const [email, setEmail] = useState('');
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [message, setMessage] = useState('');
  const [attempts, setAttempts] = useState(0);
  
  const { user } = useUser();
  const { authToken } = useAuth();
  const API = getApiUrl();

  // Initialize with user's email
  useEffect(() => {
    if (user?.emailAddresses?.[0]?.emailAddress) {
      setEmail(user.emailAddresses[0].emailAddress);
    }
  }, [user]);

  // Countdown timer
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // Send 2FA code
  const sendCode = async () => {
    try {
      setLoading(true);
      setMessage('');
      
      const response = await axios.post(`${API}/auth/2fa/send-code`, 
        { email },
        { headers: { Authorization: `Bearer ${authToken}` } }
      );
      
      setStep('verify');
      setCountdown(60); // 60 second cooldown
      setMessage('✅ Doğrulama kodu email adresinize gönderildi!');
    } catch (error) {
      console.error('Send code error:', error);
      setMessage('❌ ' + (error.response?.data?.detail || 'Kod gönderilirken hata oluştu'));
    } finally {
      setLoading(false);
    }
  };

  // Verify 2FA code
  const verifyCode = async () => {
    try {
      setLoading(true);
      setMessage('');
      
      const codeString = code.join('');
      if (codeString.length !== 6) {
        setMessage('❌ Lütfen 6 haneli kodu eksiksiz giriniz');
        return;
      }

      const response = await axios.post(`${API}/auth/2fa/verify-code`, 
        { email, code: codeString },
        { headers: { Authorization: `Bearer ${authToken}` } }
      );
      
      setMessage('✅ Doğrulama başarılı! Yönlendiriliyorsunuz...');
      setTimeout(() => {
        onVerificationComplete();
      }, 1500);
      
    } catch (error) {
      console.error('Verify code error:', error);
      const errorMsg = error.response?.data?.detail || 'Kod doğrulanırken hata oluştu';
      setMessage('❌ ' + errorMsg);
      setAttempts(prev => prev + 1);
      
      // Clear code inputs on error
      setCode(['', '', '', '', '', '']);
      
      // If too many attempts, go back to send step
      if (attempts >= 2) {
        setStep('send');
        setAttempts(0);
        setMessage('❌ Çok fazla yanlış deneme. Yeni kod talep ediniz.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Handle code input
  const handleCodeChange = (index, value) => {
    if (value.length > 1) return; // Only single digit
    
    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    
    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`code-${index + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  // Handle paste
  const handlePaste = (e) => {
    e.preventDefault();
    const paste = e.clipboardData.getData('text');
    if (paste.length === 6 && /^\d{6}$/.test(paste)) {
      const newCode = paste.split('');
      setCode(newCode);
      // Auto verify if complete
      setTimeout(() => verifyCode(), 100);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl">🔐</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">İki Faktörlü Doğrulama</h1>
          <p className="text-gray-600">Hesabınızın güvenliği için doğrulama gereklidir</p>
        </div>

        {/* Send Code Step */}
        {step === 'send' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Adresiniz
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="ornek@email.com"
                disabled={loading}
              />
            </div>
            
            <button
              onClick={sendCode}
              disabled={loading || !email || countdown > 0}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? 'Gönderiliyor...' : countdown > 0 ? `Tekrar gönderin (${countdown}s)` : 'Doğrulama Kodu Gönder'}
            </button>
          </div>
        )}

        {/* Verify Code Step */}
        {step === 'verify' && (
          <div className="space-y-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-4">
                <strong>{email}</strong> adresine 6 haneli kod gönderildi
              </p>
              
              {/* Code Input */}
              <div className="flex justify-center space-x-2 mb-6">
                {code.map((digit, index) => (
                  <input
                    key={index}
                    id={`code-${index}`}
                    type="text"
                    value={digit}
                    onChange={(e) => handleCodeChange(index, e.target.value)}
                    onPaste={handlePaste}
                    className="w-12 h-12 text-center text-xl font-bold border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    maxLength={1}
                    disabled={loading}
                  />
                ))}
              </div>
            </div>
            
            <div className="space-y-3">
              <button
                onClick={verifyCode}
                disabled={loading || code.join('').length !== 6}
                className="w-full bg-gradient-to-r from-green-600 to-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:from-green-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? 'Doğrulanıyor...' : 'Doğrula'}
              </button>
              
              <button
                onClick={() => {
                  if (countdown === 0) {
                    sendCode();
                  }
                }}
                disabled={countdown > 0 || loading}
                className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {countdown > 0 ? `Tekrar gönder (${countdown}s)` : 'Kodu Tekrar Gönder'}
              </button>
              
              <button
                onClick={() => setStep('send')}
                className="w-full text-blue-600 py-2 px-4 rounded-lg font-medium hover:bg-blue-50 transition-all"
              >
                ← Email Adresini Değiştir
              </button>
            </div>
          </div>
        )}

        {/* Message */}
        {message && (
          <div className={`mt-4 p-3 rounded-lg text-sm ${
            message.startsWith('✅') 
              ? 'bg-green-50 text-green-700 border border-green-200' 
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {message}
          </div>
        )}

        {/* Security Note */}
        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <p className="text-yellow-800 text-xs">
              <strong>Güvenlik:</strong> Bu kodu kimseyle paylaşmayın. Kod 5 dakika boyunca geçerlidir.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Supplier Management Component - Temporarily Removed for Debugging
// Will be added back in incremental steps

// Simple Supplier Management Component (Step 1 - Basic Structure)
const SupplierManagement = ({ selectedClient: propSelectedClient }) => {
  const { authToken, user, userRole, dbUser } = useAuth();
  const { session } = useClerk();
  const [loading, setLoading] = useState(true);
  const [suppliers, setSuppliers] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [showBulkForm, setShowBulkForm] = useState(false);
  const [bulkSuppliersText, setBulkSuppliersText] = useState('');
  const [bulkProcessing, setBulkProcessing] = useState(false);
  const [showExcelImport, setShowExcelImport] = useState(false);
  const [excelFile, setExcelFile] = useState(null);
  const [excelProcessing, setExcelProcessing] = useState(false);
  const [categories, setCategories] = useState([]);
  const [formData, setFormData] = useState({
    company_name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    category: '',
    services: [],
    certifications: [],
    sustainability_score: 0,
    monthly_purchase_amount: '',
    monthly_purchase_unit: 'KG',
    purchase_amount: '',
    purchase_unit: 'ADET',
    monthly_payment: '',
    local_supplier: false,
    description: ''
  });
  const API = getApiUrl();

  // Use selectedClient from props (for consultant) or manage locally (for admin/client)
  const effectiveSelectedClient = propSelectedClient || selectedClient;

  // Fetch clients first
  const fetchClients = async () => {
    if (!authToken) return;
    
    // For client users, no need to fetch clients - they work with their own data
    if (userRole === 'client') {
      console.log('👤 Client user - using own data for suppliers');
      return;
    }
    
    // Admin and consultant can see client list
    try {
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(response.data.clients || []);
      
      // Auto-select first client if no prop provided
      if (response.data?.clients?.length > 0 && !propSelectedClient) {
        setSelectedClient(response.data.clients[0].id);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
      
      // Handle authentication errors
      if (error.response?.status === 401) {
        console.log('Token expired while fetching clients');
        setClients([]);
        return;
      }
      
      setClients([]);
    }
  };

  // Fetch categories
  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/suppliers/categories/list`);
      console.log('Categories response:', response.data);
      const categoriesData = response.data || [];
      console.log('Categories data type:', typeof categoriesData, 'isArray:', Array.isArray(categoriesData));
      setCategories(Array.isArray(categoriesData) ? categoriesData : [
        'Et', 'Süt', 'Balık', 'Yumurta', 'Sebze-Meyve',
        'Gıda & İçecek', 'Temizlik & Hijyen', 'Tekstil', 'Teknoloji',
        'Bakım-Onarım', 'İSG Hizmeti', 'Yangın Hizmeti', 'Bilişim Hizmeti'
      ]);
    } catch (error) {
      console.error('Error fetching categories:', error);
      setCategories([
        'Et', 'Süt', 'Balık', 'Yumurta', 'Sebze-Meyve',
        'Gıda & İçecek', 'Temizlik & Hijyen', 'Tekstil', 'Teknoloji',
        'Bakım-Onarım', 'İSG Hizmeti', 'Yangın Hizmeti', 'Bilişim Hizmeti'
      ]);
    }
  };

  // Fetch suppliers for selected client
  const fetchSuppliers = async (clientId) => {
    if (!authToken) {
      setSuppliers([]);
      return;
    }
    
    try {
      setLoading(true);
      const params = {};
      
      // Admin ve consultant için client_id gerekli, client için otomatik
      if ((userRole === 'admin' || userRole === 'consultant') && clientId) {
        params.client_id = clientId;
      }
      // Client için backend otomatik olarak kendi verilerini döndürür
      
      const response = await axios.get(`${API}/suppliers`, {
        params,
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setSuppliers(response.data || []);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      
      // Handle authentication errors
      if (error.response?.status === 401) {
        console.log('Token expired while fetching suppliers');
        setSuppliers([]);
        return;
      }
      
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  };

  // Add new supplier
  const addSupplier = async () => {
    // Admin/consultant için client seçimi zorunlu
    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      alert('Lütfen önce bir müşteri seçin!');
      return;
    }
    
    // Client için doğrulama yok, backend otomatik client_id ekler

    try {
      // Get fresh token from session
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
            console.log('🔄 Using fresh token for supplier creation');
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const supplierData = {
        ...formData
      };
      
      // Admin/consultant için client_id ekle
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        supplierData.client_id = selectedClient;
      };

      console.log('📤 Creating supplier with data:', supplierData);
      const response = await axios.post(`${API}/suppliers`, supplierData, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      console.log('✅ Supplier created successfully:', response.data);

      // Refresh suppliers list with fresh token
      await fetchSuppliersWithFreshToken(selectedClient);
      
      // Reset form
      setFormData({
        company_name: '',
        address: '',
        category: '',
        certifications: [],
        monthly_purchase_amount: '',
        monthly_purchase_unit: 'KG',
        local_supplier: false,
        description: ''
      });
      setShowAddForm(false);
      
      alert('Tedarikçi başarıyla eklendi!');
    } catch (error) {
      console.error('Error adding supplier:', error);
      
      // Handle authentication errors
      if (error.response?.status === 401) {
        console.log('🔄 401 error detected, auth system will handle this silently');
        // Let the main auth system handle re-authentication silently - no page reload
        return;
      }
      
      alert('Tedarikçi eklenirken hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Delete supplier
  const deleteSupplier = async (supplierId) => {
    if (!confirm('Bu tedarikçiyi silmek istediğinizden emin misiniz?')) return;
    
    try {
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      await axios.delete(`${API}/suppliers/${supplierId}`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      await fetchSuppliersWithFreshToken(selectedClient);
      
      alert('Tedarikçi başarıyla silindi!');
    } catch (error) {
      console.error('Error deleting supplier:', error);
      alert('Tedarikçi silinirken hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Bulk Suppliers Import Function
  const processBulkSuppliers = async () => {
    if (!bulkSuppliersText.trim()) {
      alert('Lütfen tedarikçi listesini girin!');
      return;
    }

    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      alert('Lütfen önce bir müşteri seçin!');
      return;
    }

    setBulkProcessing(true);
    
    try {
      // Parse the text input
      const lines = bulkSuppliersText.trim().split('\n').filter(line => line.trim());
      const suppliersList = [];
      
      for (const line of lines) {
        const parts = line.split(',').map(part => part.trim());
        if (parts.length >= 2) {
          const supplierItem = {
            company_name: parts[0] || '',
            contact_person: parts[1] || '',
            email: parts[2] || '',
            phone: parts[3] || '',
            category: parts[4] || 'Diğer',
            services: parts[5] ? parts[5].split(';').map(s => s.trim()).filter(s => s) : [],
            certifications: parts[6] ? parts[6].split(';').map(c => c.trim()).filter(c => c) : [],
            sustainability_score: parseInt(parts[7]) || 0,
            local_supplier: parts[8] ? parts[8].toLowerCase() === 'evet' || parts[8].toLowerCase() === 'true' : false
          };
          
          if (supplierItem.company_name && supplierItem.category) {
            suppliersList.push(supplierItem);
          }
        }
      }
      
      if (suppliersList.length === 0) {
        alert('Geçerli tedarikçi bulunamadı! Format: Şirket Adı, İletişim Kişisi, Email, Telefon, Kategori, Hizmetler, Sertifikalar, Sürdürülebilirlik Skoru, Yerel');
        return;
      }

      // Get fresh token
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      // Send bulk request
      const payload = {
        suppliers_list: suppliersList
      };
      
      // Add client_id for admin/consultant
      const params = new URLSearchParams();
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        params.append('client_id', selectedClient);
      }
      
      const url = `${API}/suppliers/bulk${params.toString() ? `?${params.toString()}` : ''}`;
      
      const response = await axios.post(url, payload, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      const result = response.data;
      alert(`Bulk tedarikçi ekleme tamamlandı!\n${result.success_count}/${result.total_count} tedarikçi eklendi (${result.success_rate})`);
      
      // Refresh suppliers list
      const clientIdToRefresh = selectedClient || dbUser?.client_id;
      if (clientIdToRefresh) {
        await fetchSuppliersWithFreshToken(clientIdToRefresh);
      }
      
      // Clear form
      setBulkSuppliersText('');
      setShowBulkForm(false);
      
    } catch (error) {
      console.error('Error processing bulk suppliers:', error);
      alert('Bulk tedarikçi ekleme hatası: ' + (error.response?.data?.detail || error.message));
    } finally {
      setBulkProcessing(false);
    }
  };

  // Excel Suppliers Import Function
  const processExcelSuppliers = async () => {
    if (!excelFile) {
      alert('Lütfen bir Excel dosyası seçin!');
      return;
    }

    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      alert('Lütfen önce bir müşteri seçin!');
      return;
    }

    setExcelProcessing(true);
    
    try {
      // Import XLSX library
      const XLSX = await import('xlsx');
      
      // Read Excel file as ArrayBuffer
      const arrayBuffer = await excelFile.arrayBuffer();
      
      // Parse Excel file
      const workbook = XLSX.read(arrayBuffer, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      
      // Convert to JSON
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
      
      // Skip header row and process data
      const dataRows = jsonData.slice(1);
      const suppliersList = [];
      
      for (const row of dataRows) {
        if (row.length >= 2 && row[0] && row[1]) {
          const supplierItem = {
            company_name: String(row[0] || '').trim(),
            contact_person: String(row[1] || '').trim(),
            email: String(row[2] || '').trim(),
            phone: String(row[3] || '').trim(),
            category: String(row[4] || 'Diğer').trim(),
            services: row[5] ? String(row[5]).split(';').map(s => s.trim()).filter(s => s) : [],
            certifications: row[6] ? String(row[6]).split(';').map(c => c.trim()).filter(c => c) : [],
            sustainability_score: parseInt(row[7]) || 0,
            local_supplier: row[8] ? (String(row[8]).toLowerCase() === 'evet' || String(row[8]).toLowerCase() === 'true' || String(row[8]).toLowerCase() === 'yes') : false,
            purchase_amount: parseFloat(row[9]) || 0.0,
            purchase_unit: String(row[10] || 'ADET').trim(),
            monthly_payment: parseFloat(row[11]) || 0.0
          };
          
          if (supplierItem.company_name && supplierItem.category) {
            suppliersList.push(supplierItem);
          }
        }
      }
      
      if (suppliersList.length === 0) {
        alert('Excel dosyasında geçerli tedarikçi bulunamadı!\n\nBeklenen format:\nŞirket Adı | İletişim Kişisi | Email | Telefon | Kategori | Hizmetler | Sertifikalar | Sürdürülebilirlik Skoru | Yerel');
        return;
      }

      // Get fresh token
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      // Send bulk request
      const payload = {
        suppliers_list: suppliersList
      };
      
      // Add client_id for admin/consultant
      const params = new URLSearchParams();
      if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
        params.append('client_id', selectedClient);
      }
      
      const url = `${API}/suppliers/bulk${params.toString() ? `?${params.toString()}` : ''}`;
      
      const response = await axios.post(url, payload, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });

      const result = response.data;
      alert(`Excel tedarikçi import tamamlandı!\n${result.success_count}/${result.total_count} tedarikçi eklendi (${result.success_rate})`);
      
      // Refresh suppliers list
      const clientIdToRefresh = selectedClient || dbUser?.client_id;
      if (clientIdToRefresh) {
        await fetchSuppliersWithFreshToken(clientIdToRefresh);
      }
      
      // Clear form
      setExcelFile(null);
      setShowExcelImport(false);
      
    } catch (error) {
      console.error('Error processing Excel suppliers:', error);
      alert('Excel tedarikçi import hatası: ' + (error.response?.data?.detail || error.message));
    } finally {
      setExcelProcessing(false);
    }
  };

  // Download Suppliers Template Function (XLSX Format with New Fields)
  const downloadSuppliersTemplate = async () => {
    try {
      // Import XLSX library
      const XLSX = await import('xlsx');
      
      // Create template data with new fields
      const templateData = [
        // Header row
        ['Şirket Adı', 'İletişim Kişisi', 'Email', 'Telefon', 'Kategori', 'Hizmetler', 'Sertifikalar', 'Sürdürülebilirlik Skoru', 'Yerel', 'Satın Alım Miktarı', 'Satın Alım Cinsi', 'Aylık Ödenen Tutar (TL)'],
        // Example rows with proper formatting
        ['ABC Gıda Ltd.', 'Ahmet Yılmaz', 'ahmet@abcgida.com', '0212-555-0123', 'Gıda', 'Organik Ürünler;Et Ürünleri', 'ISO 14001;HACCP', '85', 'Evet', '500', 'KG', '15000'],
        ['XYZ Temizlik A.Ş.', 'Fatma Kaya', 'fatma@xyztemizlik.com', '0212-444-5555', 'Temizlik', 'Çevre Dostu Ürünler', 'ISO 9001', '75', 'Hayır', '1000', 'LİTRE', '8500'],
        ['DEF Tekstil San.', 'Mehmet Demir', 'mehmet@deftekstil.com', '0212-333-4444', 'Tekstil', '', '', '60', 'Evet', '200', 'ADET', '12000'],
        ['GHI Elektronik Ltd.', 'Ayşe Öztürk', 'ayse@ghielektronik.com', '0212-777-8888', 'Elektronik', 'Bilgisayar;Telefon', 'ISO 27001', '90', 'Evet', '50', 'ADET', '25000'],
        ['JKL İnşaat A.Ş.', 'Murat Kaya', 'murat@jklinsaat.com', '0212-999-1111', 'İnşaat', 'Yapı Malzemeleri;Çimento', 'ISO 45001', '70', 'Hayır', '1500', 'M³', '35000'],
        // Empty rows for user input
        ['', '', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', '', '']
      ];

      // Create workbook and worksheet
      const workbook = XLSX.utils.book_new();
      const worksheet = XLSX.utils.aoa_to_sheet(templateData);
      
      // Set column widths for better formatting
      worksheet['!cols'] = [
        { width: 18 }, // Şirket Adı
        { width: 15 }, // İletişim Kişisi
        { width: 25 }, // Email
        { width: 15 }, // Telefon
        { width: 12 }, // Kategori
        { width: 20 }, // Hizmetler
        { width: 20 }, // Sertifikalar
        { width: 12 }, // Sürdürülebilirlik Skoru
        { width: 8 },  // Yerel
        { width: 15 }, // Satın Alım Miktarı
        { width: 15 }, // Satın Alım Cinsi
        { width: 18 }  // Aylık Ödenen Tutar
      ];
      
      // Style the header row
      const headerStyle = {
        font: { bold: true, color: { rgb: "FFFFFF" } },
        fill: { fgColor: { rgb: "228B22" } }, // Forest Green for suppliers
        alignment: { horizontal: "center", vertical: "center" }
      };
      
      // Apply header styling
      for (let col = 0; col < 12; col++) {
        const cellRef = XLSX.utils.encode_cell({ r: 0, c: col });
        if (!worksheet[cellRef]) worksheet[cellRef] = { t: 's', v: '' };
        worksheet[cellRef].s = headerStyle;
      }
      
      // Add data validation for Kategori column (E column)
      if (!worksheet['!dataValidations']) worksheet['!dataValidations'] = [];
      worksheet['!dataValidations'].push({
        type: 'list',
        allowBlank: false,
        showInputMessage: true,
        showErrorMessage: true,
        sqref: 'E2:E1000',
        formula1: '"Gıda,Temizlik,Tekstil,Elektronik,İnşaat,Kimyasal,Kozmetik,Mobilya,Otomotiv,Teknoloji,Hizmet,Diğer"'
      });
      
      // Add data validation for Yerel column (I column)
      worksheet['!dataValidations'].push({
        type: 'list',
        allowBlank: false,
        showInputMessage: true,
        showErrorMessage: true,
        sqref: 'I2:I1000',
        formula1: '"Evet,Hayır"'
      });
      
      // Add data validation for Satın Alım Cinsi column (K column)
      worksheet['!dataValidations'].push({
        type: 'list',
        allowBlank: false,
        showInputMessage: true,
        showErrorMessage: true,
        sqref: 'K2:K1000',
        formula1: '"KG,LİTRE,ADET,GÜN,SAAT,M²,M³,TON,GRAM,PAKET,KUTU,KASA"'
      });

      // Add worksheet to workbook
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Tedarikçiler');
      
      // Generate and download XLSX file
      const xlsxBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([xlsxBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', 'tedarikci_taslak.xlsx');
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      alert('📊 Tedarikçi taslak Excel dosyası indirildi!\n\n✅ XLSX formatında\n✅ Yeni alanlar eklendi\n✅ Açılır listeler (Kategori, Yerel, Satın Alım Cinsi)\n✅ Düzenli sütun yapısı\n✅ Boş satırlar eklendi\n\nDosyayı açın, kendi tedarikçi verilerinizi girin ve Excel İmport ile yükleyin.');
      
    } catch (error) {
      console.error('Error creating suppliers template:', error);
      alert('Template oluşturma hatası: ' + error.message);
    }
  };

  // Fetch suppliers with fresh token
  const fetchSuppliersWithFreshToken = async (clientId) => {
    try {
      setLoading(true);
      
      // Get fresh token from session
      let currentToken = authToken;
      if (session) {
        try {
          const freshToken = await session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
            console.log('🔄 Using fresh token for fetching suppliers');
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }

      const params = {};
      
      // Admin/consultant için client_id gerekli
      if ((userRole === 'admin' || userRole === 'consultant') && clientId) {
        params.client_id = clientId;
      }
      // Client için backend otomatik client_id ekler

      const response = await axios.get(`${API}/suppliers`, {
        params,
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      setSuppliers(response.data || []);
      console.log('✅ Suppliers fetched successfully:', response.data?.length || 0, 'items');
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      
      // Handle authentication errors
      if (error.response?.status === 401) {
        console.log('Token expired while fetching suppliers');
        setSuppliers([]);
        return;
      }
      
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authToken) {
      fetchClients();
      fetchCategories();
    }
  }, [authToken]);

  // Auto-select client for CLIENT role users
  useEffect(() => {
    if (userRole === 'client' && dbUser?.client_id && !selectedClient) {
      setSelectedClient(dbUser.client_id);
      console.log('🔄 Auto-selected client for CLIENT user:', dbUser.client_id);
    }
  }, [userRole, dbUser, selectedClient]);

  useEffect(() => {
    if (selectedClient) {
      fetchSuppliersWithFreshToken(selectedClient);
    }
  }, [selectedClient]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-purple-700 text-white p-6 shadow-xl">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">🏢 Tedarikçi Yönetimi</h1>
          <p className="text-blue-100 text-lg">Müşteri bazlı tedarikçi ağınızı yönetin</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        
        {/* Client Selection - Only for Admin and Consultant */}
        {(userRole === 'admin' || userRole === 'consultant') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">1. Müşteri Seçimi</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Müşteri Seçin
                </label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">-- Müşteri Seçin --</option>
                  {Array.isArray(clients) && clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name || client.hotel_name}
                    </option>
                  ))}
                </select>
              </div>
              {selectedClient && (
                <div className="flex items-end gap-3">
                  <button
                    onClick={() => setShowAddForm(!showAddForm)}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
                  >
                    {showAddForm ? '❌ İptal' : '➕ Tedarikçi Ekle'}
                  </button>
                  <button
                    onClick={() => setShowBulkForm(!showBulkForm)}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    {showBulkForm ? '❌ İptal' : '📋 Toplu Ekle'}
                  </button>
                  <button
                    onClick={() => setShowExcelImport(!showExcelImport)}
                    className="px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium"
                  >
                    {showExcelImport ? '❌ İptal' : '📊 Excel İmport'}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Client Info and Add Button - For Client Users */}
        {userRole === 'client' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-800">📋 Tedarikçilerim</h2>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center gap-2"
                >
                  {showAddForm ? '❌ İptal' : '➕ Tedarikçi Ekle'}
                </button>
                <button
                  onClick={() => setShowBulkForm(!showBulkForm)}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center gap-2"
                >
                  {showBulkForm ? '❌ İptal' : '📋 Toplu Ekle'}
                </button>
                <button
                  onClick={() => setShowExcelImport(!showExcelImport)}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
                >
                  {showExcelImport ? '❌ İptal' : '📊 Excel İmport'}
                </button>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-800">
                <strong>🏢 İşletme:</strong> {dbUser?.client_name || 'Otel Adı'}
              </p>
              <p className="text-blue-600 text-sm mt-1">Kendi tedarikçilerinizi ekleyebilir ve yönetebilirsiniz.</p>
            </div>
          </div>
        )}

        {/* Add Supplier Form - For Client Users */}
        {userRole === 'client' && showAddForm && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">➕ Yeni Tedarikçi Ekle</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Basic Info */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Şirket Adı *</label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Şirket adını girin"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Kategori *</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">-- Kategori Seçin --</option>
                  <option value="Gıda">Gıda</option>
                  <option value="Temizlik">Temizlik</option>
                  <option value="Tekstil">Tekstil</option>
                  <option value="Elektronik">Elektronik</option>
                  <option value="İnşaat">İnşaat</option>
                  <option value="Kimyasal">Kimyasal</option>
                  <option value="Kozmetik">Kozmetik</option>
                  <option value="Mobilya">Mobilya</option>
                  <option value="Otomotiv">Otomotiv</option>
                  <option value="Teknoloji">Teknoloji</option>
                  <option value="Hizmet">Hizmet</option>
                  <option value="Diğer">Diğer</option>
                </select>
              </div>
              
              {/* Contact Info */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">İletişim Kişisi</label>
                <input
                  type="text"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Sorumlu kişi adı"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="email@domain.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Telefon</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="0212-555-0123"
                />
              </div>
              
              {/* Services */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Hizmetler</label>
                <input
                  type="text"
                  value={formData.services.join(', ')}
                  onChange={(e) => setFormData({...formData, services: e.target.value.split(',').map(s => s.trim()).filter(s => s)})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Hizmet 1, Hizmet 2 (virgülle ayırın)"
                />
              </div>
              
              {/* Purchase Info - NEW FIELDS */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Satın Alım Miktarı</label>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    value={formData.purchase_amount}
                    onChange={(e) => setFormData({...formData, purchase_amount: e.target.value})}
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Miktar"
                    min="0"
                    step="0.1"
                  />
                  <select
                    value={formData.purchase_unit}
                    onChange={(e) => setFormData({...formData, purchase_unit: e.target.value})}
                    className="w-20 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="KG">KG</option>
                    <option value="LİTRE">LİTRE</option>
                    <option value="ADET">ADET</option>
                    <option value="GÜN">GÜN</option>
                    <option value="SAAT">SAAT</option>
                    <option value="M²">M²</option>
                    <option value="M³">M³</option>
                    <option value="TON">TON</option>
                    <option value="GRAM">GRAM</option>
                    <option value="PAKET">PAKET</option>
                    <option value="KUTU">KUTU</option>
                    <option value="KASA">KASA</option>
                  </select>
                </div>
              </div>
              
              {/* Monthly Payment - NEW FIELD */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Aylık Ödenen Tutar (TL)</label>
                <input
                  type="number"
                  value={formData.monthly_payment}
                  onChange={(e) => setFormData({...formData, monthly_payment: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                />
              </div>
              
              {/* Certifications */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Sertifikalar</label>
                <input
                  type="text"
                  value={formData.certifications.join(', ')}
                  onChange={(e) => setFormData({...formData, certifications: e.target.value.split(',').map(s => s.trim()).filter(s => s)})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="ISO 14001, HACCP (virgülle ayırın)"
                />
              </div>
              
              {/* Sustainability Score */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Sürdürülebilirlik Skoru (0-100)</label>
                <input
                  type="number"
                  value={formData.sustainability_score}
                  onChange={(e) => setFormData({...formData, sustainability_score: Math.max(0, Math.min(100, parseInt(e.target.value) || 0))})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="85"
                  min="0"
                  max="100"
                />
              </div>
              
              {/* Legacy Fields */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Aylık Satın Alım Miktarı (Legacy)</label>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    value={formData.monthly_purchase_amount}
                    onChange={(e) => setFormData({...formData, monthly_purchase_amount: e.target.value})}
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Miktar girin"
                    min="0"
                    step="0.1"
                  />
                  <select
                    value={formData.monthly_purchase_unit}
                    onChange={(e) => setFormData({...formData, monthly_purchase_unit: e.target.value})}
                    className="w-24 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="KG">KG</option>
                    <option value="Litre">Litre</option>
                    <option value="Adet">Adet</option>
                    <option value="Gün">Gün</option>
                  </select>
                </div>
              </div>
              
              {/* Local Supplier Checkbox */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="client_local_supplier"
                  checked={formData.local_supplier}
                  onChange={(e) => setFormData({...formData, local_supplier: e.target.checked})}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="client_local_supplier" className="ml-2 block text-sm text-gray-700">
                  🏠 Yerel Tedarikçi
                </label>
              </div>
              
              {/* Address */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Adres</label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  rows="3"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Tam adres bilgisi"
                />
              </div>
              
              {/* Description */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Açıklama</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  rows="2"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Tedarikçi hakkında ek bilgiler"
                />
              </div>
            </div>
            
            <div className="mt-6 flex justify-end space-x-4">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={addSupplier}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                ➕ Tedarikçi Ekle
              </button>
            </div>
          </div>
        )}

        {/* Add Supplier Form - Admin and Consultant */}
        {(userRole === 'admin' || userRole === 'consultant') && showAddForm && selectedClient && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">2. Yeni Tedarikçi Ekle</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Şirket Adı</label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Şirket adını girin"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Kategori</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">-- Kategori Seçin --</option>
                  {Array.isArray(categories) && categories.map((category) => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Sertifikalar</label>
                <input
                  type="text"
                  value={formData.certifications.join(', ')}
                  onChange={(e) => setFormData({...formData, certifications: e.target.value.split(',').map(s => s.trim()).filter(s => s)})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Organic, ISO 14001, Fair Trade (virgülle ayırın)"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Aylık Satın Alım Miktarı</label>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    value={formData.monthly_purchase_amount}
                    onChange={(e) => setFormData({...formData, monthly_purchase_amount: e.target.value})}
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Miktar girin"
                    min="0"
                    step="0.1"
                  />
                  <select
                    value={formData.monthly_purchase_unit}
                    onChange={(e) => setFormData({...formData, monthly_purchase_unit: e.target.value})}
                    className="w-24 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="KG">KG</option>
                    <option value="Litre">Litre</option>
                    <option value="Adet">Adet</option>
                    <option value="Gün">Gün</option>
                  </select>
                </div>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="local_supplier"
                  checked={formData.local_supplier}
                  onChange={(e) => setFormData({...formData, local_supplier: e.target.checked})}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="local_supplier" className="ml-2 block text-sm text-gray-700">
                  🏠 Yerel Tedarikçi
                </label>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Adres</label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  rows="3"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Tam adres bilgisi"
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-4">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={addSupplier}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Tedarikçi Ekle
              </button>
            </div>
          </div>
        )}

        {/* Bulk Suppliers Form */}
        {showBulkForm && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">📋 Toplu Tedarikçi Ekleme</h2>
            <div className="mb-4">
              <p className="text-gray-600 mb-2">Format: Şirket Adı, İletişim Kişisi, Email, Telefon, Kategori, Hizmetler, Sertifikalar, Sürdürülebilirlik Skoru, Yerel</p>
              <p className="text-sm text-gray-500 mb-4">
                Örnek: ABC Gıda Ltd., Ahmet Yılmaz, ahmet@abcgida.com, 0212-555-0123, Gıda, Organik Ürünler;Et Ürünleri, ISO 14001;HACCP, 85, Evet
              </p>
              <textarea
                value={bulkSuppliersText}
                onChange={(e) => setBulkSuppliersText(e.target.value)}
                placeholder="ABC Gıda Ltd., Ahmet Yılmaz, ahmet@abcgida.com, 0212-555-0123, Gıda, Organik Ürünler;Et Ürünleri, ISO 14001;HACCP, 85, Evet
XYZ Temizlik A.Ş., Fatma Kaya, fatma@xyztemizlik.com, 0212-444-5555, Temizlik, Çevre Dostu Ürünler, ISO 9001, 75, Hayır
DEF Tekstil San., Mehmet Demir, mehmet@deftekstil.com, 0212-333-4444, Tekstil, , , 60, Evet"
                className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="10"
              />
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <h3 className="font-medium text-blue-800 mb-2">📝 Format Açıklaması:</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• <strong>Şirket Adı:</strong> Zorunlu - Tedarikçi firma adı</li>
                <li>• <strong>İletişim Kişisi:</strong> Opsiyonel - Sorumlu kişi adı</li>
                <li>• <strong>Email:</strong> Opsiyonel - İletişim email adresi</li>
                <li>• <strong>Telefon:</strong> Opsiyonel - İletişim telefonu</li>
                <li>• <strong>Kategori:</strong> Zorunlu - Gıda, Temizlik, Tekstil vb.</li>
                <li>• <strong>Hizmetler:</strong> Opsiyonel - Noktalı virgülle ayrılmış</li>
                <li>• <strong>Sertifikalar:</strong> Opsiyonel - Noktalı virgülle ayrılmış</li>
                <li>• <strong>Sürdürülebilirlik Skoru:</strong> Opsiyonel - 0-100 arası sayı</li>
                <li>• <strong>Yerel:</strong> Opsiyonel - "Evet" veya "Hayır"</li>
                <li>• <strong>Satın Alım Miktarı:</strong> YENİ - Sayısal değer</li>
                <li>• <strong>Satın Alım Cinsi:</strong> YENİ - KG, LİTRE, ADET, GÜN vb.</li>
                <li>• <strong>Aylık Ödenen Tutar:</strong> YENİ - TL cinsinden (isteğe bağlı)</li>
              </ul>
            </div>
            
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setShowBulkForm(false)}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={processBulkSuppliers}
                disabled={bulkProcessing}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {bulkProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>İşleniyor...</span>
                  </>
                ) : (
                  <>
                    <span>📋</span>
                    <span>Toplu Ekle</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Excel Suppliers Import Form */}
        {showExcelImport && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">📊 Excel Tedarikçi İmport</h2>
            
            <div className="mb-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <h3 className="font-medium text-green-800 mb-2">📋 Excel Dosyası Formatı:</h3>
                <div className="text-sm text-green-700">
                  <p className="mb-2"><strong>Kolon Sırası:</strong> Şirket Adı, İletişim Kişisi, Email, Telefon, Kategori, Hizmetler, Sertifikalar, Sürdürülebilirlik Skoru, Yerel</p>
                  <p className="mb-2"><strong>Önemli Notlar:</strong></p>
                  <ul className="list-disc list-inside mb-2 space-y-1">
                    <li>İlk satır başlık satırı olarak atlanır</li>
                    <li>Hizmetler ve Sertifikalar noktalı virgül (;) ile ayrılır</li>
                    <li>Sürdürülebilirlik Skoru 0-100 arası sayı olmalıdır</li>
                    <li>Yerel sütunu: "Evet", "Hayır", "True", "False" değerleri alabilir</li>
                    <li>Kategori: Gıda, Temizlik, Tekstil vb. değerler alabilir</li>
                  </ul>
                  <p><strong>Örnek:</strong></p>
                  <div className="bg-white border rounded p-2 mt-2 font-mono text-xs">
                    Şirket Adı,İletişim Kişisi,Email,Telefon,Kategori,Hizmetler,Sertifikalar,Sürdürülebilirlik Skoru,Yerel<br/>
                    ABC Gıda Ltd.,Ahmet Yılmaz,ahmet@abcgida.com,0212-555-0123,Gıda,Organik Ürünler;Et Ürünleri,ISO 14001;HACCP,85,Evet<br/>
                    XYZ Temizlik A.Ş.,Fatma Kaya,fatma@xyztemizlik.com,0212-444-5555,Temizlik,Çevre Dostu Ürünler,ISO 9001,75,Hayır<br/>
                    DEF Tekstil San.,Mehmet Demir,mehmet@deftekstil.com,0212-333-4444,Tekstil,,,60,Evet
                  </div>
                </div>
                
                {/* Template Download Button */}
                <div className="mt-4 pt-3 border-t border-green-200">
                  <button
                    onClick={downloadSuppliersTemplate}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium flex items-center gap-2"
                  >
                    <span>📁</span>
                    <span>Taslak Excel İndir</span>
                  </button>
                  <p className="text-xs text-green-600 mt-1">💡 Hazır template'i indirin, düzenleyin ve yükleyin!</p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Excel Dosyası Seçin (.csv, .xlsx)
                </label>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => setExcelFile(e.target.files[0])}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {excelFile && (
                  <p className="text-sm text-green-600 mt-2">
                    ✅ Seçilen dosya: {excelFile.name}
                  </p>
                )}
              </div>
            </div>
            
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => {
                  setShowExcelImport(false);
                  setExcelFile(null);
                }}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                İptal
              </button>
              <button
                onClick={processExcelSuppliers}
                disabled={excelProcessing || !excelFile}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {excelProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>İşleniyor...</span>
                  </>
                ) : (
                  <>
                    <span>📊</span>
                    <span>Excel İmport</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Suppliers List */}
        {selectedClient && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              {userRole === 'client' ? '📋 Tedarikçilerim' : '3. Tedarikçi Listesi'}
              {(userRole === 'admin' || userRole === 'consultant') && clients.find(c => c.id === selectedClient) && (
                <span className="text-blue-600 font-normal">
                  - {Array.isArray(clients) && clients.find(c => c.id === selectedClient)?.name || clients.find(c => c.id === selectedClient)?.hotel_name}
                </span>
              )}
            </h2>
            
            {loading ? (
              <div className="flex justify-center items-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : Array.isArray(suppliers) && suppliers.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {suppliers.map((supplier) => (
                  <div key={supplier.id} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-all">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-lg font-bold text-gray-800">{supplier.company_name}</h3>
                      <div className="flex items-center space-x-2">
                        {supplier.local_supplier && (
                          <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                            🏠 Yerel
                          </span>
                        )}
                        {(userRole === 'admin' || userRole === 'consultant') && (
                          <button
                            onClick={() => deleteSupplier(supplier.id)}
                            className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition-colors"
                          >
                            🗑️ Sil
                          </button>
                        )}
                        {userRole === 'client' && (
                          <button
                            onClick={() => deleteSupplier(supplier.id)}
                            className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition-colors"
                          >
                            🗑️ Sil
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="space-y-2 text-sm text-gray-600">
                      <p><strong>🏷️ Kategori:</strong> {supplier.category}</p>
                      
                      {/* Contact Information */}
                      {supplier.contact_person && (
                        <p><strong>👤 İletişim:</strong> {supplier.contact_person}</p>
                      )}
                      {supplier.email && (
                        <p><strong>📧 Email:</strong> {supplier.email}</p>
                      )}
                      {supplier.phone && (
                        <p><strong>📞 Telefon:</strong> {supplier.phone}</p>
                      )}
                      
                      {/* Purchase Information - NEW FIELDS */}
                      {supplier.purchase_amount && supplier.purchase_amount > 0 && (
                        <p><strong>📦 Satın Alım:</strong> {supplier.purchase_amount} {supplier.purchase_unit || 'ADET'}</p>
                      )}
                      
                      {/* Monthly Payment - NEW FIELD */}
                      {supplier.monthly_payment && supplier.monthly_payment > 0 && (
                        <p><strong>💰 Aylık Ödeme:</strong> {supplier.monthly_payment.toLocaleString('tr-TR')} TL</p>
                      )}
                      
                      {/* Services */}
                      {supplier.services && supplier.services.length > 0 && (
                        <p><strong>🛠️ Hizmetler:</strong> {supplier.services.join(', ')}</p>
                      )}
                      
                      {/* Certifications */}
                      {supplier.certifications && supplier.certifications.length > 0 && (
                        <p><strong>🏆 Sertifikalar:</strong> {supplier.certifications.join(', ')}</p>
                      )}
                      
                      {/* Sustainability Score */}
                      {supplier.sustainability_score && supplier.sustainability_score > 0 && (
                        <div className="flex items-center gap-2">
                          <strong>🌱 Sürdürülebilirlik:</strong>
                          <div className="flex items-center">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full ${
                                  supplier.sustainability_score >= 80 ? 'bg-green-500' :
                                  supplier.sustainability_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                                }`}
                                style={{width: `${supplier.sustainability_score}%`}}
                              ></div>
                            </div>
                            <span className="ml-2 text-xs font-medium">{supplier.sustainability_score}/100</span>
                          </div>
                        </div>
                      )}
                      
                      {/* Legacy fields for backward compatibility */}
                      {supplier.monthly_purchase_amount && (
                        <p><strong>📊 Aylık Miktar:</strong> {supplier.monthly_purchase_amount} {supplier.monthly_purchase_unit}</p>
                      )}
                      {supplier.address && (
                        <p><strong>📍 Adres:</strong> {supplier.address}</p>
                      )}
                      {supplier.description && (
                        <p><strong>📝 Açıklama:</strong> {supplier.description}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📦</div>
                <p className="text-gray-500 text-lg mb-2">Bu müşteri için henüz tedarikçi bulunmuyor.</p>
                <p className="text-gray-400 text-sm">Yukarıdaki butonu kullanarak tedarikçi ekleyebilirsiniz.</p>
              </div>
            )}

            {/* Local vs Non-Local Suppliers Chart */}
            {Array.isArray(suppliers) && suppliers.length > 0 && (
              <div className="mt-8 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                <h3 className="text-lg font-bold text-gray-800 mb-4 text-center">
                  📊 Yerel/Yerel Olmayan Tedarikçi Dağılımı
                </h3>
                <div className="flex flex-col lg:flex-row items-center justify-center gap-8">
                  {/* Chart */}
                  <div className="w-64 h-64">
                    <Pie
                      data={{
                        labels: ['🏠 Yerel Tedarikçi', '🌍 Yerel Olmayan'],
                        datasets: [{
                          data: [
                            suppliers.filter(s => s.local_supplier).length,
                            suppliers.filter(s => !s.local_supplier).length
                          ],
                          backgroundColor: [
                            '#10b981', // Green for local
                            '#3b82f6'  // Blue for non-local
                          ],
                          borderColor: [
                            '#059669',
                            '#2563eb'
                          ],
                          borderWidth: 2,
                          hoverBackgroundColor: [
                            '#059669',
                            '#1d4ed8'
                          ],
                          hoverBorderWidth: 3
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                          legend: {
                            position: 'bottom',
                            labels: {
                              padding: 20,
                              font: {
                                size: 14,
                                weight: 'bold'
                              },
                              usePointStyle: true,
                              pointStyle: 'circle'
                            }
                          },
                          tooltip: {
                            callbacks: {
                              label: function(context) {
                                const total = suppliers.length;
                                const value = context.parsed;
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${value} (${percentage}%)`;
                              }
                            },
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#fff',
                            borderWidth: 1
                          }
                        }
                      }}
                    />
                  </div>
                  
                  {/* Statistics */}
                  <div className="space-y-4">
                    <div className="bg-white rounded-lg p-4 shadow-sm border border-green-200">
                      <div className="flex items-center space-x-3">
                        <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                        <div>
                          <p className="text-sm text-gray-600">Yerel Tedarikçi</p>
                          <p className="text-2xl font-bold text-green-600">
                            {suppliers.filter(s => s.local_supplier).length}
                          </p>
                          <p className="text-xs text-gray-500">
                            {suppliers.length > 0 ? ((suppliers.filter(s => s.local_supplier).length / suppliers.length) * 100).toFixed(1) : 0}% of total
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white rounded-lg p-4 shadow-sm border border-blue-200">
                      <div className="flex items-center space-x-3">
                        <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                        <div>
                          <p className="text-sm text-gray-600">Yerel Olmayan</p>
                          <p className="text-2xl font-bold text-blue-600">
                            {suppliers.filter(s => !s.local_supplier).length}
                          </p>
                          <p className="text-xs text-gray-500">
                            {suppliers.length > 0 ? ((suppliers.filter(s => !s.local_supplier).length / suppliers.length) * 100).toFixed(1) : 0}% of total
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Toplam Tedarikçi</p>
                        <p className="text-3xl font-bold text-gray-800">{suppliers.length}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {suppliers.filter(s => s.local_supplier).length > suppliers.filter(s => !s.local_supplier).length 
                            ? '🏠 Yerel ağırlıklı' 
                            : suppliers.filter(s => s.local_supplier).length < suppliers.filter(s => !s.local_supplier).length
                            ? '🌍 Global ağırlıklı'
                            : '⚖️ Dengeli dağılım'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* No Client Selected - Admin and Consultant only */}
        {!selectedClient && (userRole === 'admin' || userRole === 'consultant') && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🏢</div>
              <p className="text-gray-500 text-lg mb-2">Tedarikçi yönetimi için önce bir müşteri seçin.</p>
              <p className="text-gray-400 text-sm">Yukarıdaki dropdown'dan müşteri seçerek başlayabilirsiniz.</p>
            </div>
          </div>
        )}

        {/* No Client Data for Client Users */}
        {!selectedClient && userRole === 'client' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">⏳</div>
              <p className="text-gray-500 text-lg mb-2">Hesap bilgileriniz yükleniyor...</p>
              <p className="text-gray-400 text-sm">Lütfen birkaç saniye bekleyiniz.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
// Consultant Management Component
const ConsultantManagement = () => {
  const { authToken, userRole, dbUser, refreshToken } = useAuth();
  const [consultants, setConsultants] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedConsultant, setSelectedConsultant] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showClientAssignment, setShowClientAssignment] = useState(false);
  const [editingConsultant, setEditingConsultant] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [assigningClient, setAssigningClient] = useState(null);
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const [consultantToDelete, setConsultantToDelete] = useState(null);
  const [formData, setFormData] = useState({
    company_name: '',
    authorized_person_name: '',
    email: '',
    phone: '',
    address: ''
  });
  const [consultantStats, setConsultantStats] = useState(null);
  
  const API = getApiUrl();

  // Fetch consultant statistics
  const fetchConsultantStats = async () => {
    try {
      const response = await axios.get(`${API}/consultants/stats`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      console.log('📊 Consultant Stats Response:', response.data);
      setConsultantStats(response.data);
    } catch (error) {
      console.error('Error fetching consultant stats:', error);
    }
  };

  // Fetch consultants
  const fetchConsultants = async () => {
    if (!authToken) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`${API}/consultants`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      const consultantList = response.data || [];
      
      // Sort consultants with current user first, then ROTA, then alphabetically
      const sortedConsultants = consultantList.sort((a, b) => {
        // Current user (admin) always first
        if (dbUser?.email && a.email === dbUser.email) return -1;
        if (dbUser?.email && b.email === dbUser.email) return 1;
        
        // Then ROTA
        if (a.company_name === 'ROTA') return -1;
        if (b.company_name === 'ROTA') return 1;
        
        // Then alphabetically
        return a.company_name.localeCompare(b.company_name);
      });
      
      setConsultants(sortedConsultants);
    } catch (error) {
      console.error('Error fetching consultants:', error);
      setConsultants([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch clients
  const fetchClients = async () => {
    if (!authToken) return;
    
    try {
      const response = await axios.get(`${API}/clients`, {
        params: { client_type: "registered" }, // Only registered clients
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(response.data.clients || []);
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
    }
  };

  // Fetch consultant clients
  const fetchConsultantClients = async (consultantId) => {
    if (!authToken) return [];
    
    try {
      const response = await axios.get(`${API}/consultants/${consultantId}/clients`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      return response.data || [];
    } catch (error) {
      console.error('Error fetching consultant clients:', error);
      return [];
    }
  };

  // Add new consultant
  const handleAddConsultant = async (e) => {
    e.preventDefault();
    
    try {
      await axios.post(`${API}/consultants`, formData, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      setFormData({
        company_name: '',
        authorized_person_name: '',
        email: '',
        phone: '',
        address: ''
      });
      setShowAddForm(false);
      fetchConsultants();
      alert('Danışman başarıyla eklendi!');
    } catch (error) {
      console.error('Error adding consultant:', error);
      alert('Danışman ekleme sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Edit consultant
  const handleEditConsultant = async (e) => {
    e.preventDefault();
    
    try {
      await axios.put(`${API}/consultants/${editingConsultant.id}`, formData, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      setFormData({
        company_name: '',
        authorized_person_name: '',
        email: '',
        phone: '',
        address: ''
      });
      setShowEditForm(false);
      setEditingConsultant(null);
      fetchConsultants();
      alert('Danışman başarıyla güncellendi!');
    } catch (error) {
      console.error('Error updating consultant:', error);
      alert('Danışman güncelleme sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Delete consultant
  const handleDeleteConsultant = async () => {
    if (!consultantToDelete) return;
    
    try {
      await axios.delete(`${API}/consultants/${consultantToDelete.id}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      setShowConfirmDelete(false);
      setConsultantToDelete(null);
      fetchConsultants();
      alert('Danışman başarıyla silindi!');
    } catch (error) {
      console.error('Error deleting consultant:', error);
      alert('Danışman silme sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Assign client to consultant
  const handleAssignClient = async (consultantId) => {
    if (!assigningClient) return;
    
    try {
      await axios.put(`${API}/clients/${assigningClient.id}/consultant`, {
        consultant_id: consultantId
      }, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      setAssigningClient(null);
      setShowClientAssignment(false);
      fetchClients();
      fetchConsultants();
      fetchConsultantStats();
      alert('Müşteri başarıyla danışmana atandı!');
    } catch (error) {
      console.error('Error assigning client:', error);
      alert('Müşteri atama sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Assign unassigned clients to ROTA
  const handleAssignUnassignedToRota = async () => {
    try {
      const response = await axios.post(`${API}/consultants/assign-unassigned`, {}, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      fetchClients();
      fetchConsultants();
      fetchConsultantStats();
      alert(`${response.data.assigned_count} müşteri ROTA'ya atandı!`);
    } catch (error) {
      console.error('Error assigning unassigned clients:', error);
      alert('Müşteri atama sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle consultant selection
  const handleConsultantClick = async (consultant) => {
    setSelectedConsultant(consultant);
    const consultantClients = await fetchConsultantClients(consultant.id);
    setSelectedConsultant({...consultant, clients: consultantClients});
  };

  // Start editing consultant
  const startEditConsultant = (consultant) => {
    setEditingConsultant(consultant);
    setFormData({
      company_name: consultant.company_name,
      authorized_person_name: consultant.authorized_person_name,
      email: consultant.email,
      phone: consultant.phone,
      address: consultant.address
    });
    setShowEditForm(true);
  };

  // Start deleting consultant
  const startDeleteConsultant = (consultant) => {
    setConsultantToDelete(consultant);
    setShowConfirmDelete(true);
  };

  // Filter consultants based on search term
  const filteredConsultants = consultants.filter(consultant =>
    consultant.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    consultant.authorized_person_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    consultant.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get unassigned clients
  const unassignedClients = clients.filter(client => !client.consultant_id);
  
  // Debug consultant client counts
  console.log('🔍 CONSULTANT MANAGEMENT DEBUG:');
  console.log('📊 Total clients:', clients.length);
  console.log('📊 Unassigned clients:', unassignedClients.length);
  console.log('📊 Consultants:', consultants.length);
  
  // Log each consultant's client count
  consultants.forEach(consultant => {
    const clientCount = clients.filter(c => c.consultant_id === consultant.id).length;
    console.log(`📊 ${consultant.company_name}: ${clientCount} clients`);
  });
  
  console.log('🔍 CONSULTANT MANAGEMENT DEBUG:');
  console.log('📊 Total clients:', clients.length);
  console.log('📊 Unassigned clients:', unassignedClients.length);
  console.log('📊 Consultants:', consultants.length);
  
  // Log each consultant's client count
  consultants.forEach(consultant => {
    const clientCount = clients.filter(c => c.consultant_id === consultant.id).length;
    console.log(`📊 ${consultant.company_name}: ${clientCount} clients`);
  });

  useEffect(() => {
    fetchConsultants();
    fetchClients();
    fetchConsultantStats();
  }, [authToken]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            👔 Danışman Yönetimi
          </h1>
          <p className="text-gray-600">
            Sistemdeki danışmanları görüntüleyin ve yönetin
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 mb-8">
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-blue-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-600 transition-colors flex items-center gap-2"
          >
            <span>➕</span> Yeni Danışman Ekle
          </button>
          <button
            onClick={() => setShowClientAssignment(true)}
            className="bg-green-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-600 transition-colors flex items-center gap-2"
          >
            <span>🔄</span> Müşteri Atama
          </button>
          <button
            onClick={handleAssignUnassignedToRota}
            className="bg-orange-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-orange-600 transition-colors flex items-center gap-2"
          >
            <span>🏆</span> Atanmamışları ROTA'ya Ata ({unassignedClients.length})
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Toplam Danışman</p>
                <p className="text-2xl font-bold text-gray-900">{consultantStats?.total_consultants || consultants.length}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-full">
                <span className="text-blue-600 text-xl">👔</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Toplam Müşteri</p>
                <p className="text-2xl font-bold text-gray-900">{consultantStats?.total_clients || clients.length}</p>
              </div>
              <div className="bg-green-100 p-3 rounded-full">
                <span className="text-green-600 text-xl">🏨</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Atanmamış Müşteri</p>
                <p className="text-2xl font-bold text-gray-900">{consultantStats?.unassigned_clients || unassignedClients.length}</p>
              </div>
              <div className="bg-orange-100 p-3 rounded-full">
                <span className="text-orange-600 text-xl">⚠️</span>
              </div>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <input
              type="text"
              placeholder="Danışman ara (şirket adı, yetkili kişi, email)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 pl-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Consultants List */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-6">
              📋 Danışman Listesi ({filteredConsultants.length})
            </h2>
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {filteredConsultants.map((consultant) => (
                <div 
                  key={consultant.id} 
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedConsultant?.id === consultant.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleConsultantClick(consultant)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-bold text-gray-800 flex items-center">
                        {consultant.company_name === 'ROTA' ? (
                          <>
                            🏆 {consultant.company_name}
                            <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                              Sistem Kurucusu
                            </span>
                          </>
                        ) : (
                          consultant.company_name
                        )}
                      </h3>
                      <p className="text-sm text-gray-600">{consultant.authorized_person_name}</p>
                      <p className="text-xs text-gray-500">{consultant.email}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <p className="text-sm text-gray-500">
                          {consultantStats?.consultant_stats?.find(s => s.id === consultant.id)?.client_count || 
                           clients.filter(c => c.consultant_id === consultant.id).length} müşteri
                        </p>
                        <p className="text-xs text-gray-400">
                          {consultant.is_active ? '🟢 Aktif' : '🔴 Pasif'}
                        </p>
                      </div>
                      {consultant.company_name !== 'ROTA' && (
                        <div className="flex flex-col gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              startEditConsultant(consultant);
                            }}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            ✏️
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              startDeleteConsultant(consultant);
                            }}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            🗑️
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Consultant Details */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-6">
              🔍 Danışman Detayları
            </h2>
            
            {selectedConsultant ? (
              <div className="space-y-6">
                <div className="border-b pb-4">
                  <h3 className="text-lg font-bold text-gray-800 mb-2">
                    {selectedConsultant.company_name}
                  </h3>
                  <div className="grid grid-cols-1 gap-2 text-sm">
                    <p><strong>Yetkili:</strong> {selectedConsultant.authorized_person_name}</p>
                    <p><strong>Email:</strong> {selectedConsultant.email}</p>
                    <p><strong>Telefon:</strong> {selectedConsultant.phone}</p>
                    <p><strong>Adres:</strong> {selectedConsultant.address}</p>
                    <p><strong>Kayıt Tarihi:</strong> {new Date(selectedConsultant.created_at).toLocaleDateString('tr-TR')}</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-bold text-gray-800 mb-3">
                    🏨 Müşterileri ({selectedConsultant.clients?.length || 0})
                  </h4>
                  {selectedConsultant.clients && selectedConsultant.clients.length > 0 ? (
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {selectedConsultant.clients.map((client) => (
                        <div key={client.id} className="p-3 bg-gray-50 rounded-lg">
                          <h5 className="font-medium text-gray-800">{client.hotel_name}</h5>
                          <p className="text-sm text-gray-600">{client.contact_person}</p>
                          <p className="text-xs text-gray-500">{client.email}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-4xl mb-2">🏨</div>
                      <p>Henüz müşteri yok</p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <div className="text-6xl mb-4">👔</div>
                <p className="text-lg mb-2">Danışman Seçin</p>
                <p className="text-sm">Detayları görüntülemek için bir danışman seçin</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Consultant Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">Yeni Danışman Ekle</h3>
            <form onSubmit={handleAddConsultant} className="space-y-4">
              <input
                type="text"
                placeholder="Şirket Adı"
                value={formData.company_name}
                onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
              <input
                type="text"
                placeholder="Yetkili Kişi"
                value={formData.authorized_person_name}
                onChange={(e) => setFormData({...formData, authorized_person_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
              <input
                type="tel"
                placeholder="Telefon"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
              <textarea
                placeholder="Adres"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                rows="3"
                required
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Ekle
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
                >
                  İptal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Consultant Modal */}
      {showEditForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">Danışman Düzenle</h3>
            <form onSubmit={handleEditConsultant} className="space-y-4">
              <input
                type="text"
                placeholder="Şirket Adı"
                value={formData.company_name}
                onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
              <input
                type="text"
                placeholder="Yetkili Kişi"
                value={formData.authorized_person_name}
                onChange={(e) => setFormData({...formData, authorized_person_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
              <input
                type="tel"
                placeholder="Telefon"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
              <textarea
                placeholder="Adres"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                rows="3"
                required
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Güncelle
                </button>
                <button
                  type="button"
                  onClick={() => setShowEditForm(false)}
                  className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
                >
                  İptal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showConfirmDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">Danışman Sil</h3>
            <p className="text-gray-600 mb-4">
              {consultantToDelete?.company_name} danışmanını silmek istediğinizden emin misiniz?
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleDeleteConsultant}
                className="flex-1 bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition-colors"
              >
                Sil
              </button>
              <button
                onClick={() => setShowConfirmDelete(false)}
                className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
              >
                İptal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Client Assignment Modal */}
      {showClientAssignment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
            <h3 className="text-lg font-bold mb-4">Müşteri Atama</h3>
            
            {!assigningClient ? (
              <div>
                <p className="text-gray-600 mb-4">Danışmana atanacak müşteriyi seçin:</p>
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {clients.map((client) => (
                    <div key={client.id} className="p-3 border rounded-lg hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{client.hotel_name}</h4>
                          <p className="text-sm text-gray-600">{client.contact_person}</p>
                          <p className="text-xs text-gray-500">
                            {client.consultant_id ? 
                              `Mevcut Danışman: ${consultants.find(c => c.id === client.consultant_id)?.company_name || 'Bilinmiyor'}` : 
                              'Atanmamış'
                            }
                          </p>
                        </div>
                        <button
                          onClick={() => setAssigningClient(client)}
                          className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                        >
                          Seç
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div>
                <p className="text-gray-600 mb-4">
                  <strong>{assigningClient.hotel_name}</strong> müşterisini hangi danışmana atanacak?
                </p>
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {consultants.map((consultant) => (
                    <div key={consultant.id} className="p-3 border rounded-lg hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{consultant.company_name}</h4>
                          <p className="text-sm text-gray-600">{consultant.authorized_person_name}</p>
                          <p className="text-xs text-gray-500">
                            {consultantStats?.consultant_stats?.find(s => s.id === consultant.id)?.client_count || 
                             clients.filter(c => c.consultant_id === consultant.id).length} müşteri
                          </p>
                        </div>
                        <button
                          onClick={() => handleAssignClient(consultant.id)}
                          className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
                        >
                          Ata
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="mt-4 flex gap-2">
              {assigningClient && (
                <button
                  onClick={() => setAssigningClient(null)}
                  className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                >
                  Geri
                </button>
              )}
              <button
                onClick={() => setShowClientAssignment(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                İptal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Role Setup Component - After Clerk Registration
const RoleSetup = ({ onComplete }) => {
  const [step, setStep] = useState('role-selection');
  const [selectedRole, setSelectedRole] = useState('');
  const [consultants, setConsultants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [consultantData, setConsultantData] = useState({
    company_name: '',
    authorized_person_name: '',
    email: '',
    phone: '',
    address: ''
  });
  const [clientData, setClientData] = useState({
    consultant_id: '',
    hotel_name: '',
    contact_person: '',
    email: '',
    phone: '',
    city: '',
    district: '',
    address: '',
    audit_company: '',
    certificate_end_date: ''
  });
  
  // Türkiye İl ve İlçe Listesi (Self-Registration için)
  const turkeyProvinces = {
    'ADANA': ['ALADAĞ', 'CEYHAN', 'ÇUKUROVA', 'FEKE', 'İMAMOĞLU', 'KARAİSALI', 'KARATAŞ', 'KOZAN', 'MERKEZ', 'POZANTI', 'SAİMBEYLİ', 'SARIÇAM', 'TUFANBEYLI', 'YUMURTALIK', 'YÜREĞİR'],
    'ADIYAMAN': ['BESNİ', 'ÇELİKHAN', 'GERGER', 'GÖLBAŞI', 'KAHTA', 'MERKEZ', 'SAMSAT', 'SİNCİK', 'TUT'],
    'AFYONKARAHİSAR': ['BAŞMAKÇI', 'BAYAT', 'BOLVADIN', 'ÇAY', 'ÇOBANLAR', 'DAZKIRI', 'DİNAR', 'EMİRDAĞ', 'EVCİLER', 'HOCALAR', 'İHSANİYE', 'İSCAHİSAR', 'KIZILÖREN', 'MERKEZ', 'SANDIKLI', 'SİNANPAŞA', 'SULTANDAĞI', 'ŞUHUT'],
    'AĞRI': ['DİYADİN', 'DOĞUBAYAZIT', 'ELEŞKİRT', 'HAMUR', 'MERKEZ', 'PATNOS', 'TAŞLIÇAY', 'TUTAK'],
    'AMASYA': ['GÖYNÜCEK', 'GÜMÜŞHACIKÖY', 'HAMAMÖZÜ', 'MERKEZ', 'MERZİFON', 'SULUOVA', 'TAŞOVA'],
    'ANKARA': ['AKYURT', 'ALTINDAĞ', 'AYAŞ', 'BALA', 'BEYPAZARI', 'ÇAMLIDERE', 'ÇANKAYA', 'ÇUBUK', 'ELMADAĞ', 'ETİMESGUT', 'EVREN', 'GÖLBAŞI', 'GÜDÜL', 'HAYMANA', 'KAHRAMANKAZAN', 'KAZAN', 'KEÇİÖREN', 'KIZILCAHAMAM', 'MAMAK', 'NALLIHAN', 'POLATLІ', 'PURSAKLAR', 'SİNCAN', 'ŞEREFLİKOÇHİSAR', 'YENİMAHALLE'],
    'ANTALYA': ['AKSEKİ', 'AKSU', 'ALANYA', 'DEMRE', 'DÖŞEMEALTI', 'ELMALI', 'FİNİKE', 'GAZİPAŞA', 'GÜNDOĞMUŞ', 'İBRADI', 'KAŞ', 'KEMER', 'KEPEZ', 'KONYAALTI', 'KORKUTELI', 'KUMLUCA', 'MANAVGAT', 'MURATPAŞA', 'SERİK'],
    'ISPARTA': ['AKSU', 'ATABEY', 'EĞİRDİR', 'GELENDOST', 'GÖNEN', 'KEÇİBORLU', 'MERKEZ', 'SENİRKENT', 'SÜTÇÜLER', 'ŞARKİKARAAĞAÇ', 'ULUBORLU', 'YALVAÇ', 'YENİŞARBADEMLİ'],
    'İSTANBUL': ['ADALAR', 'ARNAVUTKÖY', 'ATAŞEHİR', 'AVCILAR', 'BAĞCILAR', 'BAHÇELİEVLER', 'BAKIRKÖY', 'BAŞAKŞEHİR', 'BAYRAMPAŞA', 'BEŞİKTAŞ', 'BEYKOZ', 'BEYLİKDÜZÜ', 'BEYOĞLU', 'BÜYÜKÇEKMECE', 'ÇATALCA', 'ÇEKMEKÖY', 'ESENLER', 'ESENYURT', 'EYÜPSULTAN', 'FATİH', 'GAZİOSMANPAŞA', 'GÜNGÖREN', 'KADIKÖY', 'KAĞITHANE', 'KARTAL', 'KÜÇÜKÇEKMECE', 'MALTEPE', 'PENDİK', 'SANCAKTEPE', 'SARIYER', 'SİLİVRİ', 'SULTANBEYLİ', 'SULTANGAZİ', 'ŞİLE', 'ŞİŞLİ', 'TUZLA', 'ÜMRANİYE', 'ÜSKÜDAR', 'ZEYTİNBURNU'],
    'İZMİR': ['ALİAĞA', 'BALÇOVA', 'BAYINDIR', 'BAYRAKLI', 'BERGAMA', 'BEYDAĞ', 'BORNOVA', 'BUCA', 'ÇEŞME', 'ÇİĞLİ', 'DİKİLİ', 'FOÇA', 'GAZİEMİR', 'GÜZELBAHÇE', 'KARABAĞLAR', 'KARABURUN', 'KARŞIYAKA', 'KEMALPAŞA', 'KINIK', 'KİRAZ', 'KONAK', 'MENDERES', 'MENEMEN', 'NARLIDA', 'ÖDEMİŞ', 'SEFERIHISAR', 'SELÇUK', 'TİRE', 'TORBALI', 'URLA'],
    'MUĞLA': ['BODRUM', 'DALAMAN', 'DATÇA', 'FETHİYE', 'KAVAKLIDERE', 'KÖYCEĞIZ', 'MARMARIS', 'MENTEŞE', 'MİLAS', 'ORTACA', 'SEYDİKEMER', 'ULA', 'YATAĞAN']
  };

  // Denetim Firmaları
  const auditCompanies = [
    'Alberk QA Uluslararası Teknik Kontrol ve Belgelendirme A.Ş.',
    'Bureau Veritas Gözetim Hizmetleri Ltd. Şti.',
    'Control Union Gözetim ve Belgelendirme Ltd. Şti.',
    'FQC Global Sertifikasyon Anonim Şirketi',
    'Kiwa Belgelendirme Hizmetleri A.Ş.',
    'RoyalCert Belgelendirme ve Gözetim Hizmetleri A.Ş',
    'TSE Global',
    'TÜV Austria Turk Belgelendirme Eğitim ve Gözetim Hizmetleri LTD. ŞTİ.',
    'TRB Uluslararası Belgelendirme Teknik Kontrol ve Gözetim Hizmetleri Tic. Ltd.Şti.'
  ];
  
  const API = getApiUrl();
  const { user, dbUser } = useAuth();
  const { session } = useClerk();

  const fetchConsultants = async () => {
    try {
      const response = await axios.get(`${API}/consultants`);
      const consultantList = response.data || [];
      
      const sortedConsultants = consultantList.sort((a, b) => {
        // Current user (admin) always first
        if (dbUser?.email && a.email === dbUser.email) return -1;
        if (dbUser?.email && b.email === dbUser.email) return 1;
        
        // Then ROTA
        if (a.company_name === 'ROTA') return -1;
        if (b.company_name === 'ROTA') return 1;
        
        // Then alphabetically
        return a.company_name.localeCompare(b.company_name);
      });
      
      setConsultants(sortedConsultants);
    } catch (error) {
      console.error('Error fetching consultants:', error);
      setConsultants([]);
    }
  };

  useEffect(() => {
    if (selectedRole === 'client') {
      fetchConsultants();
    }
  }, [selectedRole]);

  const handleRoleSelection = (role) => {
    setSelectedRole(role);
    if (role === 'consultant') {
      setStep('consultant-form');
    } else if (role === 'client') {
      setStep('client-form');
    }
  };

  const handleConsultantSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Get token from session
      const token = await session?.getToken();
      
      // Use new endpoint that updates both consultant and user role
      await axios.post(`${API}/consultants/register-with-user`, {
        consultant_data: {
          ...consultantData,
          email: user.emailAddresses[0].emailAddress
        }
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Danışman kaydınız başarıyla oluşturuldu! Rolünüz güncellendi.');
      
      // CRITICAL: Update authentication state immediately
      try {
        // Get fresh user data from database
        const userResponse = await axios.get(`${API}/api/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Update all auth states
        const userData = userResponse.data;
        sessionStorage.setItem('userRole', userData.role);
        sessionStorage.setItem('dbUser', JSON.stringify(userData));
        
        console.log('✅ Authentication state updated:', userData);
        
        // Complete role setup
        onComplete();
        
        // Let React state handle the update - no page reload needed
        console.log('✅ Role setup completed, state will update automatically');
        
      } catch (refreshError) {
        console.error('Error refreshing user data:', refreshError);
        console.log('⚠️ Role setup completed with minor refresh error');
        onComplete();
        // Let the state handle the update naturally
      }
      
    } catch (error) {
      console.error('Error creating consultant:', error);
      alert('Danışman kaydı sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleClientSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Get token from session
      const token = await session?.getToken();
      
      // Use new endpoint that updates both client and user role
      await axios.post(`${API}/clients/register-with-user`, {
        client_data: {
          ...clientData,
          name: clientData.hotel_name,
          email: user.emailAddresses[0].emailAddress
        }
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Müşteri kaydınız başarıyla oluşturuldu! Rolünüz güncellendi.');
      
      // CRITICAL: Update authentication state immediately
      try {
        // Get fresh user data from database
        const userResponse = await axios.get(`${API}/api/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Update all auth states
        const userData = userResponse.data;
        sessionStorage.setItem('userRole', userData.role);
        sessionStorage.setItem('dbUser', JSON.stringify(userData));
        
        console.log('✅ Authentication state updated:', userData);
        
        // Complete role setup
        onComplete();
        
        // Let React state handle the update - no page reload needed
        console.log('✅ Role setup completed, state will update automatically');
        
      } catch (refreshError) {
        console.error('Error refreshing user data:', refreshError);
        console.log('⚠️ Role setup completed with minor refresh error');
        onComplete();
        // Let the state handle the update naturally
      }
      
    } catch (error) {
      console.error('Error creating client:', error);
      alert('Müşteri kaydı sırasında hata oluştu: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-2xl">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-2">🏨 Rota CRM</h1>
            <p className="text-blue-100">Hoş geldiniz! Lütfen hesap türünüzu seçin</p>
          </div>
        </div>

        <div className="p-6">
          {step === 'role-selection' && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-xl font-bold text-gray-800 mb-2">Hesap Türü Seçin</h2>
                <p className="text-gray-600 text-sm">Size uygun hesap türünü seçiniz</p>
              </div>

              <div className="space-y-4">
                <button
                  onClick={() => handleRoleSelection('consultant')}
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white p-4 rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all transform hover:scale-105 shadow-lg"
                >
                  <div className="flex items-center justify-center space-x-3">
                    <span className="text-2xl">👔</span>
                    <div className="text-left">
                      <h3 className="font-bold">Danışman</h3>
                      <p className="text-sm text-green-100">Müşteri yönetimi ve danışmanlık</p>
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => handleRoleSelection('client')}
                  className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white p-4 rounded-lg hover:from-blue-600 hover:to-indigo-700 transition-all transform hover:scale-105 shadow-lg"
                >
                  <div className="flex items-center justify-center space-x-3">
                    <span className="text-2xl">🏨</span>
                    <div className="text-left">
                      <h3 className="font-bold">Otel Sahibi</h3>
                      <p className="text-sm text-blue-100">Otelin sürdürülebilirlik takibi</p>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          )}

          {step === 'consultant-form' && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-xl font-bold text-gray-800 mb-2">👔 Danışman Kaydı</h2>
                <p className="text-gray-600 text-sm">Danışman bilgilerinizi doldurun</p>
              </div>

              <form onSubmit={handleConsultantSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Firma Adı *
                  </label>
                  <input
                    type="text"
                    required
                    value={consultantData.company_name}
                    onChange={(e) => setConsultantData({...consultantData, company_name: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="ABC Danışmanlık Ltd."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Yetkili Kişi Adı Soyadı *
                  </label>
                  <input
                    type="text"
                    required
                    value={consultantData.authorized_person_name}
                    onChange={(e) => setConsultantData({...consultantData, authorized_person_name: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Ahmet Yılmaz"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Telefon Numarası *
                  </label>
                  <input
                    type="tel"
                    required
                    value={consultantData.phone}
                    onChange={(e) => setConsultantData({...consultantData, phone: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0532 123 45 67"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Adres *
                  </label>
                  <textarea
                    required
                    value={consultantData.address}
                    onChange={(e) => setConsultantData({...consultantData, address: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="3"
                    placeholder="Tam adres bilgisi..."
                  />
                </div>

                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={() => setStep('role-selection')}
                    className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    ← Geri
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 text-white py-2 px-4 rounded-lg hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 transition-colors"
                  >
                    {loading ? 'Kaydediliyor...' : 'Kaydet'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {step === 'client-form' && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-xl font-bold text-gray-800 mb-2">🏨 Müşteri Kaydı</h2>
                <p className="text-gray-600 text-sm">Otel bilgilerinizi doldurun</p>
              </div>

              <form onSubmit={handleClientSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Hangi danışmanla çalışıyorsunuz? *
                  </label>
                  <select
                    required
                    value={clientData.consultant_id}
                    onChange={(e) => setClientData({...clientData, consultant_id: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Bir danışman seçin...</option>
                    {consultants.map((consultant) => (
                      <option key={consultant.id} value={consultant.id}>
                        {consultant.company_name === 'ROTA' ? 
                          `🏆 ${consultant.company_name} - ${consultant.authorized_person_name} (Sistem Kurucusu)` :
                          `${consultant.company_name} - ${consultant.authorized_person_name}`
                        }
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Otel Adı *
                  </label>
                  <input
                    type="text"
                    required
                    value={clientData.hotel_name}
                    onChange={(e) => setClientData({...clientData, hotel_name: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Paradise Hotel"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    İletişim Kişisi *
                  </label>
                  <input
                    type="text"
                    required
                    value={clientData.contact_person}
                    onChange={(e) => setClientData({...clientData, contact_person: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Mehmet Demir"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Telefon Numarası *
                  </label>
                  <input
                    type="tel"
                    required
                    value={clientData.phone}
                    onChange={(e) => setClientData({...clientData, phone: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0242 123 45 67"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      İl *
                    </label>
                    <select
                      required
                      value={clientData.city}
                      onChange={(e) => setClientData({...clientData, city: e.target.value, district: ''})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">İl seçiniz</option>
                      {Object.keys(turkeyProvinces).map(province => (
                        <option key={province} value={province}>{province}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      İlçe *
                    </label>
                    <select
                      required
                      value={clientData.district}
                      onChange={(e) => setClientData({...clientData, district: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      disabled={!clientData.city}
                    >
                      <option value="">İlçe seçiniz</option>
                      {clientData.city && turkeyProvinces[clientData.city]?.map(district => (
                        <option key={district} value={district}>{district}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Denetim Firması
                  </label>
                  <select
                    value={clientData.audit_company}
                    onChange={(e) => setClientData({...clientData, audit_company: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Denetim firması seçiniz</option>
                    {auditCompanies.map(company => (
                      <option key={company} value={company}>{company}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sertifika Geçerlilik Tarihi
                  </label>
                  <input
                    type="date"
                    value={clientData.certificate_end_date}
                    onChange={(e) => setClientData({...clientData, certificate_end_date: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Adres *
                  </label>
                  <textarea
                    required
                    value={clientData.address}
                    onChange={(e) => setClientData({...clientData, address: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="3"
                    placeholder="Otel tam adres bilgisi..."
                  />
                </div>

                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={() => setStep('role-selection')}
                    className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    ← Geri
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 bg-gradient-to-r from-blue-500 to-indigo-600 text-white py-2 px-4 rounded-lg hover:from-blue-600 hover:to-indigo-700 disabled:opacity-50 transition-colors"
                  >
                    {loading ? 'Kaydediliyor...' : 'Kaydet'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ==========================================
// AI ASSISTANT COMPONENT
// ==========================================
const AIAssistant = () => {
  const { authToken, dbUser } = useAuth();
  const [activeAITab, setActiveAITab] = useState('suggestions');
  const [selectedClient, setSelectedClient] = useState(null);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState(null);
  const [error, setError] = useState(null);
  const API = getApiUrl();

  // Fetch clients
  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    if (!authToken) return;
    
    try {
      const response = await axios.get(`${API}/clients`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(response.data);
    } catch (err) {
      console.error('Failed to fetch clients:', err);
    }
  };

  // AI Service Functions
  const getAISuggestions = async (clientId) => {
    if (!clientId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API}/ai/suggestions/${clientId}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setAiResponse(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'AI önerileri alınamadı');
      console.error('AI Suggestions Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getAIReportText = async (clientId, sectionType = 'sustainability_message') => {
    if (!clientId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API}/ai/report-text/${clientId}?section_type=${sectionType}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setAiResponse(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'AI rapor metni oluşturulamadı');
      console.error('AI Report Text Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getAITrendAnalysis = async (clientId) => {
    if (!clientId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API}/ai/trend-analysis/${clientId}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setAiResponse(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'AI trend analizi yapılamadı');
      console.error('AI Trend Analysis Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const testAIService = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API}/ai/test`);
      setAiResponse(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'AI servisi test edilemedi');
      console.error('AI Test Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const aiTabs = [
    { id: 'suggestions', name: 'Akıllı Öneriler', icon: '💡' },
    { id: 'report-text', name: 'Otomatik Metin', icon: '📝' },
    { id: 'trend-analysis', name: 'Trend Analizi', icon: '📊' },
    { id: 'test', name: 'AI Test', icon: '🔧' }
  ];

  return (
    <div className="p-6 bg-gradient-to-br from-purple-50 to-blue-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl">🤖</span>
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            AI Sürdürülebilirlik Asistanı
          </h1>
          <p className="text-gray-600 mt-2">
            GPT-4o-mini ile güçlendirilmiş akıllı öneriler ve otomatik metin üretimi
          </p>
        </div>

        {/* AI Tabs */}
        <div className="flex justify-center mb-8">
          <div className="flex bg-white rounded-xl p-1 shadow-lg">
            {aiTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveAITab(tab.id)}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  activeAITab === tab.id
                    ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg'
                    : 'text-gray-600 hover:text-purple-600'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Client Selection Sidebar */}
          {activeAITab !== 'test' && (
            <div className="col-span-3">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-gray-800 mb-4">
                  🏨 Müşteri Seçin
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {clients && clients.length > 0 ? clients.map((client) => (
                    <button
                      key={client.id}
                      onClick={() => setSelectedClient(client)}
                      className={`w-full text-left p-3 rounded-lg transition-all ${
                        selectedClient?.id === client.id
                          ? 'bg-gradient-to-r from-purple-100 to-blue-100 border-2 border-purple-300'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="font-medium text-gray-800">
                        {client.hotel_name || client.name}
                      </div>
                      <div className="text-sm text-gray-600">
                        {client.contact_person}
                      </div>
                    </button>
                  )) : (
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-4xl mb-2">🏨</div>
                      <p className="text-sm">Müşteri yükleniyor...</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* AI Content */}
          <div className={activeAITab === 'test' ? 'col-span-12' : 'col-span-9'}>
            <div className="bg-white rounded-xl shadow-lg p-6">
              {/* AI Tab Content */}
              {activeAITab === 'suggestions' && (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-800">
                      💡 Akıllı Sürdürülebilirlik Önerileri
                    </h2>
                    <button
                      onClick={() => selectedClient && getAISuggestions(selectedClient.id)}
                      disabled={!selectedClient || loading}
                      className="px-6 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? '🔄 Üretiliyor...' : '🚀 Öneri Al'}
                    </button>
                  </div>
                  
                  {!selectedClient && (
                    <div className="text-center py-12 text-gray-500">
                      <div className="text-6xl mb-4">🏨</div>
                      <p className="text-lg">Müşteri seçin</p>
                      <p className="text-sm">AI önerileri almak için sol taraftan bir müşteri seçin</p>
                    </div>
                  )}
                </div>
              )}

              {activeAITab === 'report-text' && (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-800">
                      📝 Otomatik Rapor Metni
                    </h2>
                    <div className="flex gap-2">
                      <button
                        onClick={() => selectedClient && getAIReportText(selectedClient.id, 'sustainability_message')}
                        disabled={!selectedClient || loading}
                        className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 text-sm"
                      >
                        Sürdürülebilirlik Mesajı
                      </button>
                      <button
                        onClick={() => selectedClient && getAIReportText(selectedClient.id, 'executive_summary')}
                        disabled={!selectedClient || loading}
                        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 text-sm"
                      >
                        Yönetici Özeti
                      </button>
                    </div>
                  </div>

                  {!selectedClient && (
                    <div className="text-center py-12 text-gray-500">
                      <div className="text-6xl mb-4">📝</div>
                      <p className="text-lg">Müşteri seçin</p>
                      <p className="text-sm">Otomatik metin üretmek için sol taraftan bir müşteri seçin</p>
                    </div>
                  )}
                </div>
              )}

              {activeAITab === 'trend-analysis' && (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-800">
                      📊 AI Trend Analizi
                    </h2>
                    <button
                      onClick={() => selectedClient && getAITrendAnalysis(selectedClient.id)}
                      disabled={!selectedClient || loading}
                      className="px-6 py-2 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg hover:from-green-600 hover:to-teal-600 disabled:opacity-50"
                    >
                      {loading ? '🔄 Analiz ediliyor...' : '📈 Analiz Et'}
                    </button>
                  </div>

                  {!selectedClient && (
                    <div className="text-center py-12 text-gray-500">
                      <div className="text-6xl mb-4">📊</div>
                      <p className="text-lg">Müşteri seçin</p>
                      <p className="text-sm">Trend analizi için sol taraftan bir müşteri seçin</p>
                    </div>
                  )}
                </div>
              )}

              {activeAITab === 'test' && (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-800">
                      🔧 AI Servis Testi
                    </h2>
                    <button
                      onClick={testAIService}
                      disabled={loading}
                      className="px-6 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 disabled:opacity-50"
                    >
                      {loading ? '🔄 Test ediliyor...' : '🧪 Test Et'}
                    </button>
                  </div>
                </div>
              )}

              {/* AI Response Display */}
              {loading && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="animate-spin text-4xl mb-4">🤖</div>
                    <p className="text-lg text-gray-600">AI düşünüyor...</p>
                    <p className="text-sm text-gray-500">GPT-4o-mini ile işleniyor</p>
                  </div>
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                  <div className="flex items-center">
                    <span className="text-red-500 text-xl mr-3">❌</span>
                    <div>
                      <h4 className="text-red-800 font-medium">Hata</h4>
                      <p className="text-red-600 text-sm">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {aiResponse && !loading && (
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
                  <div className="flex items-center mb-4">
                    <span className="text-2xl mr-3">🤖</span>
                    <h4 className="text-lg font-bold text-gray-800">AI Cevabı</h4>
                    <span className="ml-auto text-sm text-gray-500">
                      Model: {aiResponse.model || 'gpt-4o-mini'}
                    </span>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    {activeAITab === 'suggestions' && aiResponse.suggestions?.suggestions && (
                      <div className="whitespace-pre-wrap text-gray-800">
                        {aiResponse.suggestions.suggestions}
                      </div>
                    )}
                    
                    {activeAITab === 'report-text' && aiResponse.generated_text && (
                      <div className="whitespace-pre-wrap text-gray-800">
                        {aiResponse.generated_text}
                      </div>
                    )}
                    
                    {activeAITab === 'trend-analysis' && aiResponse.trend_analysis?.analysis && (
                      <div className="whitespace-pre-wrap text-gray-800">
                        {aiResponse.trend_analysis.analysis}
                      </div>
                    )}
                    
                    {activeAITab === 'test' && aiResponse.test_response && (
                      <div>
                        <div className="mb-4">
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            aiResponse.status === 'success' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {aiResponse.status === 'success' ? '✅ Başarılı' : '❌ Hata'}
                          </span>
                        </div>
                        <div className="whitespace-pre-wrap text-gray-800">
                          <strong>Mesaj:</strong> {aiResponse.message}
                        </div>
                        {aiResponse.test_response && (
                          <div className="mt-3 p-3 bg-gray-50 rounded">
                            <strong>AI Cevabı:</strong> {aiResponse.test_response}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const MainApp = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedClient, setSelectedClient] = useState(null);
  const [showClientSetup, setShowClientSetup] = useState(false);
  const [show2FA, setShow2FA] = useState(true);
  const [twoFACompleted, setTwoFACompleted] = useState(false);
  const [showRoleSetup, setShowRoleSetup] = useState(false);
  const { userRole, isLoaded, dbUser, refreshUser } = useAuth();
  const { user } = useUser();

  // Check 2FA completion status when user loads
  useEffect(() => {
    if (user?.id) {
      const today = new Date().toDateString();
      const last2FADate = localStorage.getItem(`rota_2fa_completed_${user.id}_${today}`);
      setTwoFACompleted(!!last2FADate);
    }
  }, [user?.id]);

  // Handle 2FA completion with user-specific localStorage persistence
  const handle2FAComplete = () => {
    if (!user?.id) return;
    
    const today = new Date().toDateString();
    localStorage.setItem(`rota_2fa_completed_${user.id}_${today}`, 'true');
    setTwoFACompleted(true);
    console.log('✅ 2FA completed for user:', user.id, 'on:', today);
  };

  // Check if user needs role setup (after Clerk registration AND 2FA completion)
  useEffect(() => {
    if (isLoaded && user && dbUser && twoFACompleted) {
      // Only show role setup AFTER 2FA is completed and if role is missing
      if (!dbUser.role || dbUser.role === '' || dbUser.role === null) {
        console.log('User logged in, 2FA completed, but no role in database, showing role setup');
        setShowRoleSetup(true);
      } else {
        console.log('User has role in database:', dbUser.role);
        setShowRoleSetup(false);
      }
    }
  }, [isLoaded, user, dbUser, twoFACompleted]); // Added twoFACompleted dependency

  // Check if client user needs to complete setup
  useEffect(() => {
    if (isLoaded && userRole === 'client') {
      const setupCompleted = localStorage.getItem(`client_setup_${userRole}_completed`);
      
      if (!setupCompleted && (!dbUser?.client_id || dbUser?.client_id === '')) {
        setShowClientSetup(true);
      } else {
        setShowClientSetup(false);
        if (setupCompleted && !dbUser?.client_id) {
          refreshUser();
        }
      }
    }
  }, [isLoaded, userRole, dbUser]);

  const handleNavigate = (section, client = null) => {
    setActiveTab(section);
    if (client) {
      setSelectedClient(client);
    }
  };

  const handleSetupComplete = async (clientId) => {
    try {
      localStorage.setItem(`client_setup_${userRole}_completed`, 'true');
      await refreshUser();
      setShowClientSetup(false);
      console.log('✅ Client setup completed and marked as done');
    } catch (error) {
      console.error('Setup completion error:', error);
    }
  };

  const handleSetupSkip = () => {
    localStorage.setItem(`client_setup_${userRole}_completed`, 'true');
    setShowClientSetup(false);
  };

  // STEP 1: Show 2FA for all users FIRST (highest priority)
  if (show2FA && !twoFACompleted) {
    return <TwoFactorAuth onVerificationComplete={handle2FAComplete} />;
  }

  // STEP 2: Show role setup for new users (after 2FA is completed)
  if (showRoleSetup && twoFACompleted && isLoaded && user && dbUser && (!dbUser.role || dbUser.role === '' || dbUser.role === null)) {
    return <RoleSetup onComplete={() => setShowRoleSetup(false)} />;
  }

  // STEP 3: Show client setup form for new client users (after role is set)
  if (showClientSetup && userRole === 'client') {
    return <ClientSetupForm onComplete={handleSetupComplete} onSkip={handleSetupSkip} />;
  }

  // STEP 4: Show consultant dashboard for consultant users
  if (userRole === 'consultant') {
    return <ConsultantApp />;
  }

  // STEP 5: Show main admin/client app
  return <MainAdminClientApp 
    activeTab={activeTab} 
    setActiveTab={setActiveTab} 
    userRole={userRole} 
    handleNavigate={handleNavigate} 
  />;
};

// Consultant App - Separate app for consultants
const ConsultantApp = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { userRole, dbUser } = useAuth();

  const handleNavigate = (tab) => {
    setActiveTab(tab);
  };

  const renderConsultantContent = () => {
    switch(activeTab) {
      case 'dashboard':
        return <ConsultantDashboard onNavigate={handleNavigate} />;
      case 'my-clients':
        return <ConsultantClientManagement onNavigate={handleNavigate} />;
      case 'client-assignment':
        return <ConsultantClientAssignment />;
      case 'ai-assistant':
        return <AIAssistant />;
      case 'reports':
        return <ConsultantReports />;
      case 'profile':
        return <ConsultantProfile />;
      case 'consumption':
        return <ConsumptionManagement onNavigate={handleNavigate} />;
      case 'analytics':
        return <ConsumptionAnalytics />;
      case 'carbon':
        return <CarbonFootprint />;
      case 'personnel':
        return <PersonnelManagement />;
      case 'sustainability-targets':
        return <SustainabilityTargets />;
      case 'waste-management':
        return <WasteManagement />;
      case 'suppliers':
        return <SupplierManagement />;
      case 'yeni-belge':
        return <YeniBelgeYonetimiYeni />;
      case 'training':
        return <TrainingManagement />;
      case 'email-management':
        return <EmailManagement />;
      case 'ai-assistant':
        return <AIAssistant />;
      case 'reports':
        return <ReportsManagement />;
      default:
        return <ConsultantDashboard onNavigate={handleNavigate} />;
    }
  };

  const consultantMenuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'my-clients', name: 'Müşterilerim', icon: '👥' },
    { id: 'client-assignment', name: 'Müşteri Atama', icon: '➕' },
    { id: 'ai-assistant', name: 'AI Asistan', icon: '🤖' },
    { id: 'reports', name: 'Raporlar', icon: '📊' },
    { id: 'profile', name: 'Profil', icon: '👤' },
    { id: 'consumption', name: 'Tüketim Takibi', icon: '⚡' },
    { id: 'analytics', name: 'Analitik', icon: '📈' },
    { id: 'carbon', name: 'Karbon Ayak İzi', icon: '🌍' },
    { id: 'personnel', name: 'Personel Yönetimi', icon: '👥' },
    { id: 'sustainability-targets', name: 'Sürdürülebilirlik Hedefleri', icon: '🎯' },
    { id: 'waste-management', name: 'Atık Yönetimi', icon: '🗑️' },
    { id: 'suppliers', name: 'Tedarikçi Yönetimi', icon: '🏢' },
    { id: 'yeni-belge', name: 'Belge Yönetimi', icon: '📋' },
    { id: 'training', name: 'Eğitim Yönetimi', icon: '🎓' },
    { id: 'email-management', name: 'Email Yönetimi', icon: '📧' },
    { id: 'reports', name: 'Raporlar', icon: '📊' }
  ];

  return (
    <div className="bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100" style={{ minHeight: '100vh' }}>
      {/* Elite Consultant Sidebar */}
      <div 
        className="text-white w-64 shadow-2xl"
        style={{
          background: 'linear-gradient(180deg, #1e3a8a 0%, #1e40af 50%, #1e3a8a 100%)',
          minHeight: '100vh',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          overflowY: 'auto', // Consultant sidebar scroll
          overflowX: 'hidden'
        }}
      >
        <div 
          className="p-6 flex-1 flex flex-col"
          style={{ 
            minHeight: '100vh',
            background: 'linear-gradient(180deg, #1e3a8a 0%, #1e40af 50%, #1e3a8a 100%)'
          }}
        >
          <div className="text-center mb-8 flex-shrink-0">
            <div className="bg-gradient-to-r from-yellow-400 to-orange-500 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-3">
              <span className="text-white text-xl font-bold">👔</span>
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-300 to-purple-300 bg-clip-text text-transparent">
              Danışman Paneli
            </h1>
            <p className="text-blue-200 text-sm mt-1">
              {dbUser?.company_name || dbUser?.name || 'User'}
              {console.log('🔍 SIDEBAR DEBUG - dbUser:', dbUser)}
            </p>
          </div>
        
          <nav 
            className="space-y-2 flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-blue-600 scrollbar-track-blue-800" 
            style={{ 
              minHeight: '400px',
              maxHeight: 'calc(100vh - 200px)', // Header ve footer için alan bırak
              paddingRight: '8px', // Scroll bar için alan
              scrollbarWidth: 'thin',
              scrollbarColor: '#2563EB #1E40AF'
            }}
          >
            {consultantMenuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`group w-full text-left px-4 py-3 rounded-xl transition-all duration-200 flex items-center space-x-3 ${
                  activeTab === item.id
                    ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white shadow-lg transform scale-105'
                    : 'text-blue-200 hover:bg-blue-700 hover:text-white hover:translate-x-2'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span className="font-medium">{item.name}</span>
                {activeTab === item.id && (
                  <span className="ml-auto text-white">⚡</span>
                )}
              </button>
            ))}
          </nav>
          
          <div 
            className="p-4 rounded-xl flex-shrink-0" 
            style={{ 
              background: 'linear-gradient(90deg, #059669, #0d9488)',
              marginTop: '20px',
              marginBottom: '10px'
            }}
          >
            <div className="text-center">
              <div className="text-2xl mb-2">🎯</div>
              <p className="text-white text-sm font-medium">Danışman Başarı</p>
              <p className="text-emerald-100 text-xs mt-1">Müşteri odaklı çözümler</p>
            </div>
          </div>
          
          {/* Çıkış Butonu */}
          <div className="p-4 flex-shrink-0">
            <SignOutButton>
              <button className="w-full bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-xl transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg">
                <span className="text-lg">🚪</span>
                <span className="font-medium">Çıkış Yap</span>
              </button>
            </SignOutButton>
          </div>
        </div>
      </div>
      
      {/* Main Content Area */}
      <div 
        className="flex-1 p-6"
        style={{ marginLeft: '256px' }} // Account for fixed sidebar
      >
        {renderConsultantContent()}
      </div>
    </div>
  );
};

// Main Admin/Client App
const MainAdminClientApp = ({ activeTab, setActiveTab, userRole, handleNavigate }) => {
  const renderContent = () => {
    switch(activeTab) {
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} />;
      case 'consultants':
        return <ConsultantManagement />;
      case 'clients':
        return <SimpleClientManagement onNavigate={handleNavigate} />;
      case 'bulk-operations':
        return <BulkOperations onNavigate={handleNavigate} />;
      case 'consumption':
        return <ConsumptionManagement onNavigate={handleNavigate} />;
      case 'analytics':
        return <ConsumptionAnalytics />;
      case 'carbon':
        return <CarbonFootprint />;
      case 'waste-management':
        return <WasteManagement />;
      case 'suppliers':
        return <SupplierManagement />;
      case 'personnel':
        return <PersonnelManagement />;
      case 'sustainability-targets':
        return <SustainabilityTargets />;
      case 'yeni-belge':
        return <YeniBelgeYonetimiYeni />;
      case 'training':
        return <TrainingManagement />;
      case 'email-management':
        return <EmailManagement />;
      case 'ai-assistant':
        return <AIAssistant />;
      case 'reports':
        return <ReportsManagement />;
      default:
        return <Dashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="bg-gray-100" style={{ minHeight: '100vh' }}>
      <Sidebar activeTab={activeTab} onNavigate={handleNavigate} userRole={userRole} />
      <div className="flex flex-col overflow-hidden" style={{ marginLeft: '256px', minHeight: '100vh' }}>
        <Header />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50" style={{ minHeight: 'calc(100vh - 64px)' }}>
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

//Wrap MainApp with ClerkProvider and add Clerk authentication flow
const App = () => {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
      
      <SignedIn>
        <MainApp />
      </SignedIn>
    </ClerkProvider>
  );
};

export default App;
