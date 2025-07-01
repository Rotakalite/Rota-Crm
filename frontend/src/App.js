import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { ClerkProvider, SignedIn, SignedOut, RedirectToSignIn, useUser, useClerk } from '@clerk/clerk-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

// Global utility function for file icons
const getFileIcon = (filePath) => {
  const extension = filePath?.split('.').pop()?.toLowerCase();
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
                Sistemde beklenmeyen bir hata oluştu. Lütfen sayfayı yenileyin.
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
  Title,
  Tooltip,
  Legend
);

const CLERK_PUBLISHABLE_KEY = process.env.REACT_APP_CLERK_PUBLISHABLE_KEY;

// Dynamic API URL detection
const getApiUrl = () => {
  // Production domain - Use Railway backend
  if (window.location.hostname === 'portal.rotakalitedanismanlik.com') {
    return 'https://rota-crm-production.up.railway.app/api';
  }
  
  // Development/Preview domains - ALSO use Railway!
  if (window.location.hostname.includes('.preview.emergentagent.com')) {
    return 'https://rota-crm-production.up.railway.app/api';
  }
  
  // Localhost - local development
  if (window.location.hostname === 'localhost') {
    return 'http://localhost:8001/api';
  }
  
  // Fallback to Railway
  return 'https://rota-crm-production.up.railway.app/api';
};

// Backend URL Discovery Function
const discoverBackendURL = async () => {
  const possibleUrls = [
    // Current session's backend URL (stored in localStorage)
    localStorage.getItem('ROTA_BACKEND_URL'),
    // Latest known working URL pattern
    'https://45c51488-b08d-4ec3-832c-628720c8dcae.preview.emergentagent.com',
    // Development
    'http://localhost:8001'
  ].filter(Boolean);
  
  for (const url of possibleUrls) {
    try {
      console.log('🔍 Testing backend URL:', url);
      const response = await fetch(`${url}/api/health`, { 
        method: 'GET',
        timeout: 5000 
      });
      
      if (response.ok) {
        console.log('✅ Found working backend URL:', url);
        localStorage.setItem('ROTA_BACKEND_URL', url); // Store for future use
        return url;
      }
    } catch (error) {
      console.log('❌ Backend URL not reachable:', url);
    }
  }
  
  // If all fails, return the Railway backend (stable)
  console.warn('⚠️ Using fallback Railway backend URL');
  return 'https://rota-crm-production.up.railway.app/api';
};

const API = getApiUrl();

// Configure axios to automatically refresh tokens
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        console.log('🔄 Token expired, refreshing...');
        // Force page refresh to re-authenticate with Clerk
        setTimeout(() => {
          window.location.reload();
        }, 1000);
        
      } catch (refreshError) {
        console.error('❌ Token refresh failed:', refreshError);
        window.location.reload();
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

// Authentication Hook - Working version from GitHub
const useAuth = () => {
  const { user, isLoaded } = useUser();
  const { session } = useClerk();
  const [authToken, setAuthToken] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [dbUser, setDbUser] = useState(null);

  const refreshUser = async () => {
    if (authToken) {
      try {
        const response = await axios.get(`${API}/auth/me`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        setDbUser(response.data);
        console.log('✅ User data refreshed:', response.data);
      } catch (error) {
        console.error('Error refreshing user:', error);
      }
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      if (isLoaded && user && session) {
        try {
          // DIRECT role from Clerk metadata - highest priority
          const directRole = user.publicMetadata?.role || 'client';
          setUserRole(directRole);
          console.log('🔍 Clerk Role:', directRole);
          console.log('✅ Set role to:', directRole);

          // Get token from session
          try {
            const token = await session.getToken();
            setAuthToken(token);
            console.log('🎯 Token received successfully');
            
            // Register/update user in our database
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
            console.log('✅ User registered in database');
            
          } catch (tokenError) {
            console.error('Token error:', tokenError);
            console.log('🎯 Setting role without token');
            setUserRole(directRole);
          }
          
        } catch (error) {
          console.error('Auth initialization error:', error);
          // Fallback role setting
          const directRole = user.publicMetadata?.role || 'client';
          setUserRole(directRole);
        }
      } else if (isLoaded && user) {
        // If no session but user exists, still set role
        const directRole = user.publicMetadata?.role || 'client';
        setUserRole(directRole);
        console.log('🎯 No session, setting role without token:', directRole);
      }
    };

    initAuth();
  }, [user, isLoaded, session]);

  return { user, authToken, userRole, dbUser, isLoaded, refreshUser };
};

// Header Component
const Header = () => {
  const { user } = useUser();
  const { signOut } = useClerk();
  const { userRole } = useAuth();

  const handleSignOut = () => {
    // Clear any localStorage data on logout
    localStorage.removeItem(`client_setup_${userRole}_completed`);
    signOut();
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
                : 'bg-blue-100 text-blue-800'
            }`}>
              {userRole === 'admin' ? 'Admin' : 'Müşteri'}
            </span>
          </div>
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

// Consumption Analytics Components
const ConsumptionAnalytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [selectedYear, setSelectedYear] = useState(2025);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState('charts');

  const { authToken, userRole, dbUser } = useAuth();

  useEffect(() => {
    if (!authToken) return;
    if (userRole === 'admin') fetchClients();
  }, [authToken, userRole]);

  useEffect(() => {
    if (!authToken) return;
    if (selectedClient || userRole === 'client') fetchAnalyticsData();
  }, [authToken, selectedYear, selectedClient]);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setClients(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error("Error fetching clients:", error);
    }
  };

  const fetchAnalyticsData = async () => {
    setLoading(true);
    try {
      const clientId = userRole === 'admin' ? selectedClient : dbUser?.client_id;
      if (!clientId) {
        setLoading(false);
        return;
      }
      const response = await axios.get(`${API}/consumptions/analytics?year=${selectedYear}&client_id=${clientId}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setAnalyticsData(response.data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
    }
    setLoading(false);
  };

  const getMonthlyChart = () => {
    if (!analyticsData?.monthly_comparison) return null;
    
    const months = analyticsData.monthly_comparison.map(m => m.month_name);
    const electricity = analyticsData.monthly_comparison.map(m => m.current_year?.electricity || 0);
    const water = analyticsData.monthly_comparison.map(m => m.current_year?.water || 0);
    const gas = analyticsData.monthly_comparison.map(m => m.current_year?.natural_gas || 0);
    const coal = analyticsData.monthly_comparison.map(m => m.current_year?.coal || 0);

    return {
      labels: months,
      datasets: [
        {
          label: 'Elektrik (kWh)',
          data: electricity,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4
        },
        {
          label: 'Su (m³)',
          data: water,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          tension: 0.4
        },
        {
          label: 'Doğalgaz (m³)',
          data: gas,
          borderColor: 'rgb(249, 115, 22)',
          backgroundColor: 'rgba(249, 115, 22, 0.1)',
          tension: 0.4
        },
        {
          label: 'Kömür (kg)',
          data: coal,
          borderColor: 'rgb(107, 114, 128)',
          backgroundColor: 'rgba(107, 114, 128, 0.1)',
          tension: 0.4
        }
      ]
    };
  };

  const getYearlyChart = () => {
    if (!analyticsData?.yearly_totals) return null;
    
    const current = analyticsData.yearly_totals.current_year;
    const previous = analyticsData.yearly_totals.previous_year;

    return {
      labels: ['Elektrik', 'Su', 'Doğalgaz', 'Kömür'],
      datasets: [
        {
          label: `${selectedYear}`,
          data: [current?.electricity || 0, current?.water || 0, current?.natural_gas || 0, current?.coal || 0],
          backgroundColor: ['#3B82F6', '#22C55E', '#F97316', '#6B7280'],
          borderWidth: 2
        },
        {
          label: `${selectedYear - 1}`,
          data: [previous?.electricity || 0, previous?.water || 0, previous?.natural_gas || 0, previous?.coal || 0],
          backgroundColor: ['#93C5FD', '#86EFAC', '#FDBA74', '#D1D5DB'],
          borderWidth: 2
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Tüketim Analizi' }
    },
    scales: {
      y: { beginAtZero: true }
    }
  };

  if (loading) {
    return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-green-600 text-white p-6 rounded-lg shadow-xl">
        <h1 className="text-3xl font-bold mb-4">📊 Elite Tüketim Analizi</h1>
        
        <div className="flex flex-wrap gap-4">
          {userRole === 'admin' && (
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              className="px-4 py-2 rounded-lg text-gray-800 font-medium"
            >
              <option value="">Müşteri Seçin</option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>{client.hotel_name}</option>
              ))}
            </select>
          )}
          
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="px-4 py-2 rounded-lg text-gray-800 font-medium"
          >
            <option value={2025}>2025</option>
            <option value={2024}>2024</option>
            <option value={2023}>2023</option>
          </select>

          <div className="flex gap-2">
            <button
              onClick={() => setActiveView('charts')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeView === 'charts' ? 'bg-white text-purple-600' : 'bg-purple-500 hover:bg-purple-400'
              }`}
            >
              📈 Grafikler
            </button>
            <button
              onClick={() => setActiveView('comparison')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeView === 'comparison' ? 'bg-white text-purple-600' : 'bg-purple-500 hover:bg-purple-400'
              }`}
            >
              🔄 Karşılaştırma
            </button>
          </div>
        </div>
      </div>

      {!analyticsData ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <h3 className="text-xl font-semibold text-gray-800 mb-2">📊 Analiz İçin Müşteri Seçin</h3>
          <p className="text-gray-600">
            {userRole === 'admin' && !selectedClient 
              ? 'Lütfen bir müşteri seçin ve elite analizi başlatın'
              : 'Seçilen dönem için tüketim verisi bulunmuyor.'
            }
          </p>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">⚡ Elektrik</h3>
              <p className="text-3xl font-bold">{analyticsData.yearly_totals?.current_year?.electricity?.toLocaleString() || 0}</p>
              <p className="text-blue-100">kWh</p>
              {analyticsData.yearly_totals?.previous_year?.electricity && (
                <p className="text-sm mt-2">
                  {(() => {
                    const current = analyticsData.yearly_totals.current_year.electricity || 0;
                    const previous = analyticsData.yearly_totals.previous_year.electricity || 0;
                    const change = previous > 0 ? ((current - previous) / previous * 100) : 0;
                    return (
                      <span className={`font-bold ${change > 0 ? 'text-red-200' : 'text-green-200'}`}>
                        {change > 0 ? '↗' : '↘'} {Math.abs(change).toFixed(1)}%
                      </span>
                    );
                  })()}
                </p>
              )}
            </div>
            <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">💧 Su</h3>
              <p className="text-3xl font-bold">{analyticsData.yearly_totals?.current_year?.water?.toLocaleString() || 0}</p>
              <p className="text-green-100">m³</p>
              {analyticsData.yearly_totals?.previous_year?.water && (
                <p className="text-sm mt-2">
                  {(() => {
                    const current = analyticsData.yearly_totals.current_year.water || 0;
                    const previous = analyticsData.yearly_totals.previous_year.water || 0;
                    const change = previous > 0 ? ((current - previous) / previous * 100) : 0;
                    return (
                      <span className={`font-bold ${change > 0 ? 'text-red-200' : 'text-green-200'}`}>
                        {change > 0 ? '↗' : '↘'} {Math.abs(change).toFixed(1)}%
                      </span>
                    );
                  })()}
                </p>
              )}
            </div>
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">🔥 Doğalgaz</h3>
              <p className="text-3xl font-bold">{analyticsData.yearly_totals?.current_year?.natural_gas?.toLocaleString() || 0}</p>
              <p className="text-orange-100">m³</p>
              {analyticsData.yearly_totals?.previous_year?.natural_gas && (
                <p className="text-sm mt-2">
                  {(() => {
                    const current = analyticsData.yearly_totals.current_year.natural_gas || 0;
                    const previous = analyticsData.yearly_totals.previous_year.natural_gas || 0;
                    const change = previous > 0 ? ((current - previous) / previous * 100) : 0;
                    return (
                      <span className={`font-bold ${change > 0 ? 'text-red-200' : 'text-green-200'}`}>
                        {change > 0 ? '↗' : '↘'} {Math.abs(change).toFixed(1)}%
                      </span>
                    );
                  })()}
                </p>
              )}
            </div>
            <div className="bg-gradient-to-br from-gray-500 to-gray-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">🏔️ Kömür</h3>
              <p className="text-3xl font-bold">{analyticsData.yearly_totals?.current_year?.coal?.toLocaleString() || 0}</p>
              <p className="text-gray-100">kg</p>
              {analyticsData.yearly_totals?.previous_year?.coal && (
                <p className="text-sm mt-2">
                  {(() => {
                    const current = analyticsData.yearly_totals.current_year.coal || 0;
                    const previous = analyticsData.yearly_totals.previous_year.coal || 0;
                    const change = previous > 0 ? ((current - previous) / previous * 100) : 0;
                    return (
                      <span className={`font-bold ${change > 0 ? 'text-red-200' : 'text-green-200'}`}>
                        {change > 0 ? '↗' : '↘'} {Math.abs(change).toFixed(1)}%
                      </span>
                    );
                  })()}
                </p>
              )}
            </div>
          </div>

          {/* Kişi Başı Aylık Tüketim */}
          <div className="bg-gradient-to-br from-purple-100 to-pink-100 border-l-4 border-purple-500 p-6 rounded-lg">
            <h4 className="text-lg font-bold text-purple-800 mb-4">👥 Kişi Başı Aylık Tüketim ({selectedYear})</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {analyticsData.monthly_comparison && analyticsData.monthly_comparison.length > 0 && (
                analyticsData.monthly_comparison.map((month, index) => (
                  <div key={index} className="text-center bg-white p-3 rounded-lg shadow-sm">
                    <div className="text-sm font-bold text-purple-700 mb-2">{month.month_name}</div>
                    <div className="space-y-1">
                      <div className="text-xs text-blue-600 font-medium">
                        ⚡ {month.current_year_per_person?.electricity?.toFixed(1) || '0.0'}
                      </div>
                      <div className="text-xs text-green-600 font-medium">
                        💧 {month.current_year_per_person?.water?.toFixed(1) || '0.0'}
                      </div>
                      <div className="text-xs text-orange-600 font-medium">
                        🔥 {month.current_year_per_person?.natural_gas?.toFixed(1) || '0.0'}
                      </div>
                      <div className="text-xs text-gray-600 font-medium">
                        🏔️ {month.current_year_per_person?.coal?.toFixed(1) || '0.0'}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {activeView === 'charts' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <h3 className="text-xl font-bold mb-4">📈 Aylık Trend Analizi</h3>
                {getMonthlyChart() && <Line data={getMonthlyChart()} options={chartOptions} />}
              </div>
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <h3 className="text-xl font-bold mb-4">📊 Yıllık Karşılaştırma</h3>
                {getYearlyChart() && <Bar data={getYearlyChart()} options={chartOptions} />}
              </div>
            </div>
          )}

          {activeView === 'comparison' && analyticsData.monthly_comparison && (
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <h3 className="text-xl font-bold mb-4">🔄 Detaylı Aylık Karşılaştırma</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse">
                  <thead>
                    <tr className="bg-gradient-to-r from-purple-100 to-blue-100">
                      <th className="px-4 py-3 border text-left font-bold">Ay</th>
                      <th className="px-4 py-3 border text-left font-bold text-blue-700">⚡ Elektrik (kWh)</th>
                      <th className="px-4 py-3 border text-left font-bold text-green-700">💧 Su (m³)</th>
                      <th className="px-4 py-3 border text-left font-bold text-orange-700">🔥 Doğalgaz (m³)</th>
                      <th className="px-4 py-3 border text-left font-bold text-gray-700">🏔️ Kömür (kg)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analyticsData.monthly_comparison.map((month, index) => (
                      <tr key={index} className={`hover:bg-gray-50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-25'}`}>
                        <td className="px-4 py-3 border font-bold text-purple-800">{month.month_name}</td>
                        <td className="px-4 py-3 border text-blue-700 font-semibold">{(month.current_year?.electricity || 0).toLocaleString()}</td>
                        <td className="px-4 py-3 border text-green-700 font-semibold">{(month.current_year?.water || 0).toLocaleString()}</td>
                        <td className="px-4 py-3 border text-orange-700 font-semibold">{(month.current_year?.natural_gas || 0).toLocaleString()}</td>
                        <td className="px-4 py-3 border text-gray-700 font-semibold">{(month.current_year?.coal || 0).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};


const Dashboard = ({ onNavigate }) => {
  const [stats, setStats] = useState(null);
  const [clients, setClients] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [folders, setFolders] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const { authToken, userRole, dbUser } = useAuth();

  const handleViewDocument = (document) => {
    setSelectedDocument(document);
    setShowDocumentModal(true);
  };

  const handleDownloadDocument = async (docData) => {
    try {
      console.log('📥 Starting download for:', docData.name);
      
      const downloadUrl = `${API}/documents/${docData.id}/download`;
      
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

  const handleDeleteDocument = async (document) => {
    if (!window.confirm(`"${document.name}" belgesini silmek istediğinizden emin misiniz?`)) {
      return;
    }

    try {
      console.log('🗑️ Deleting document:', document.name);
      
      const response = await axios.delete(`${API}/documents/${document.id}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      console.log('✅ Document deleted successfully');
      alert('Belge başarıyla silindi!');
      
      // Refresh documents list
      fetchDocuments();
    } catch (error) {
      console.error('❌ Delete error:', error);
      alert('Belge silinemedi!');
    }
  };

  useEffect(() => {
    // Token hazır olmadan API call yapma
    if (!authToken) {
      console.log('🔄 Waiting for auth token for initial data fetch...');
      return;
    }
    
    console.log('🎯 Auth token ready, fetching initial data...');
    fetchStats();
    fetchClients();
    if (userRole === 'client' && dbUser?.client_id) {
      fetchDocuments();
      fetchFolders(); // Client kullanıcıları için klasörleri de getir
    }
  }, [authToken, userRole, dbUser]);


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

  const fetchStats = async () => {
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const response = await axios.get(`${API}/stats`, { headers });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
      // Set default stats
      setStats({
        total_clients: 0,
        stage_distribution: { stage_1: 0, stage_2: 0, stage_3: 0 }
      });
    }
  };

  const fetchClients = async () => {
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      console.log('🔍 Fetching clients with role:', userRole);
      const response = await axios.get(`${API}/clients`, { headers });
      
      // Check if response is actually JSON array
      if (Array.isArray(response.data)) {
        setClients(response.data);
        console.log('✅ Clients fetched:', response.data.length, 'for role:', userRole);
        console.log('📋 Client data:', response.data);
      } else {
        console.error('❌ Invalid response type:', typeof response.data, response.data);
        setClients([]);
      }
    } catch (error) {
      console.error("❌ Error fetching clients:", error.response?.status, error.response?.data);
      setClients([]);
    }
  };

  const fetchFolders = async () => {
    if (!authToken) return;
    
    try {
      const headers = { 'Authorization': `Bearer ${authToken}` };
      console.log('📁 Dashboard: Fetching folders...');
      
      const response = await axios.get(`${API}/folders`, { headers });
      console.log('📁 Dashboard: Folders response:', response.data);
      
      setFolders(Array.isArray(response.data) ? response.data : []);
      console.log('✅ Dashboard: Folders set in state:', Array.isArray(response.data) ? response.data.length : 0, 'folders');
      
      // Folders yüklendikten sonra documents da yükle ki doküman sayısı hesaplanabilsin
      if (userRole === 'admin') {
        fetchDocuments();
      }
    } catch (error) {
      console.error("❌ Dashboard: Error fetching folders:", error);
      setFolders([]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          {userRole === 'admin' ? 'Admin Dashboard' : 'Müşteri Dashboard'}
        </h2>
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
              <h3 className="text-lg font-semibold text-blue-700">
                {userRole === 'admin' ? 'Toplam Müşteri' : 'Toplam Belge'}
              </h3>
              <p className="text-3xl font-bold text-blue-900">
                {userRole === 'admin' ? stats.total_clients : stats.total_documents}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
              <h3 className="text-lg font-semibold text-green-700">
                {userRole === 'admin' ? 'I. Aşama' : 'Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)'}
              </h3>
              <p className="text-3xl font-bold text-green-900">
                {userRole === 'admin' 
                  ? (stats.stage_distribution?.stage_1 || 0)
                  : (stats.document_type_distribution?.TR1_CRITERIA || 0)
                }
              </p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg border-l-4 border-yellow-500">
              <h3 className="text-lg font-semibold text-yellow-700">
                {userRole === 'admin' ? 'II. Aşama' : 'I. Aşama Belgeleri'}
              </h3>
              <p className="text-3xl font-bold text-yellow-900">
                {userRole === 'admin' 
                  ? (stats.stage_distribution?.stage_2 || 0)
                  : (stats.document_type_distribution?.STAGE_1_DOC || 0)
                }
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
              <h3 className="text-lg font-semibold text-purple-700">
                {userRole === 'admin' ? 'III. Aşama' : 'II. Aşama Belgeleri'}
              </h3>
              <p className="text-3xl font-bold text-purple-900">
                {userRole === 'admin' 
                  ? (stats.stage_distribution?.stage_3 || 0)
                  : (stats.document_type_distribution?.STAGE_2_DOC || 0)
                }
              </p>
            </div>
          </div>
        )}
        
        {/* Additional document type cards for client */}
        {stats && userRole === 'client' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-red-50 p-4 rounded-lg border-l-4 border-red-500">
              <h3 className="text-lg font-semibold text-red-700">III. Aşama Belgeleri</h3>
              <p className="text-3xl font-bold text-red-900">
                {stats.document_type_distribution?.STAGE_3_DOC || 0}
              </p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg border-l-4 border-orange-500">
              <h3 className="text-lg font-semibold text-orange-700">Karbon Ayak İzi</h3>
              <p className="text-3xl font-bold text-orange-900">
                {stats.document_type_distribution?.CARBON_REPORT || 0}
              </p>
            </div>
            <div className="bg-indigo-50 p-4 rounded-lg border-l-4 border-indigo-500">
              <h3 className="text-lg font-semibold text-indigo-700">Sürdürülebilirlik</h3>
              <p className="text-3xl font-bold text-indigo-900">
                {stats.document_type_distribution?.SUSTAINABILITY_REPORT || 0}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-gray-800">
            {userRole === 'admin' ? 'Son Müşteriler' : 'Hesap Bilgileri'}
          </h3>
          {userRole === 'admin' && (
            <button
              onClick={() => onNavigate('clients')}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Tüm Müşterileri Gör
            </button>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
              <tr>
                <th className="px-6 py-3">Otel Adı</th>
                <th className="px-6 py-3">İletişim Kişisi</th>
                <th className="px-6 py-3">Aşama</th>
                <th className="px-6 py-3">Tarih</th>
                {userRole === 'admin' && <th className="px-6 py-3">İşlemler</th>}
              </tr>
            </thead>
            <tbody>
              {(Array.isArray(clients) ? clients : []).slice(0, 5).map((client) => (
                <tr key={client.id} className="bg-white border-b hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{client.hotel_name}</td>
                  <td className="px-6 py-4">{client.contact_person}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      client.current_stage === 'I.Aşama' ? 'bg-green-100 text-green-800' :
                      client.current_stage === 'II.Aşama' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-purple-100 text-purple-800'
                    }`}>
                      {client.current_stage}
                    </span>
                  </td>
                  <td className="px-6 py-4">{new Date(client.created_at).toLocaleDateString('tr-TR')}</td>
                  {userRole === 'admin' && (
                    <td className="px-6 py-4">
                      <button
                        onClick={() => onNavigate('project', client)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Detay
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Carbon Reports Section for Client Users */}
      {userRole === 'client' && Array.isArray(clients) && clients.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            🌱 Karbon Ayak İzi Raporlarım
          </h3>
          
          {(Array.isArray(clients) ? clients : []).map((client) => (
            <div key={client.id} className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-lg border border-green-200 mb-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h4 className="font-semibold text-green-800 mb-2">
                    🏨 {client.hotel_name}
                  </h4>
                  
                  {client.carbon_footprint ? (
                    <div className="space-y-2">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">📊</span>
                        <div>
                          <p className="font-bold text-2xl text-green-700">
                            {client.carbon_footprint.toFixed(2)} kg CO2/yıl
                          </p>
                          <p className="text-sm text-green-600">
                            Yıllık Karbon Ayak İzi
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center text-sm text-gray-600">
                        <span className="mr-2">✅</span>
                        <span>Karbon ayak izi analizi tamamlandı</span>
                      </div>
                      
                      <div className="flex items-center text-sm text-gray-600">
                        <span className="mr-2">📄</span>
                        <span>Detaylı rapor hazır</span>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center">
                      <span className="text-2xl mr-3">⏳</span>
                      <div>
                        <p className="font-semibold text-gray-700">
                          Karbon Ayak İzi Analizi
                        </p>
                        <p className="text-sm text-gray-500">
                          Analiziniz devam ediyor, tamamlandığında size bildirilecektir
                        </p>
                      </div>
                    </div>
                  )}
                </div>
                
                {client.carbon_footprint && (
                  <button
                    onClick={() => {
                      // Find carbon report for this client
                      const carbonReport = documents.find(d => 
                        d.client_id === client.id && 
                        d.document_type === "Karbon Ayak İzi Raporu"
                      );
                      if (carbonReport) {
                        handleViewDocument(carbonReport);
                      } else {
                        alert('Karbon ayak izi raporu henüz yüklenmemiş.');
                      }
                    }}
                    className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-all transform hover:scale-105 shadow-md flex items-center"
                  >
                    <span className="mr-2">📋</span>
                    Raporu Görüntüle
                  </button>
                )}
              </div>


              {client.carbon_footprint && (
                <div className="mt-4 pt-4 border-t border-green-200">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div className="bg-white p-3 rounded-lg shadow-sm">
                      <div className="text-lg font-bold text-green-600">
                        {(client.carbon_footprint / 365).toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-500">kg CO2/gün</div>
                    </div>
                    <div className="bg-white p-3 rounded-lg shadow-sm">
                      <div className="text-lg font-bold text-blue-600">
                        {(client.carbon_footprint / 12).toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-500">kg CO2/ay</div>
                    </div>
                    <div className="bg-white p-3 rounded-lg shadow-sm">
                      <div className="text-lg font-bold text-purple-600">
                        {client.current_stage}
                      </div>
                      <div className="text-xs text-gray-500">Mevcut Aşama</div>
                    </div>
                    <div className="bg-white p-3 rounded-lg shadow-sm">
                      <div className="text-lg font-bold text-orange-600">
                        {documents.filter(d => d.client_id === client.id).length}
                      </div>
                      <div className="text-xs text-gray-500">Toplam Belge</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Document Detail Modal for Dashboard */}
      {showDocumentModal && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-90vh overflow-y-auto">
            {/* Header */}
            <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-6 rounded-t-xl">
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <span className="text-3xl mr-3">{getFileIcon(selectedDocument?.original_filename || selectedDocument?.file_path || '')}</span>
                  <div>
                    <h3 className="text-xl font-bold">Karbon Ayak İzi Raporu</h3>
                    <p className="text-green-100 text-sm">{selectedDocument.name}</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowDocumentModal(false)}
                  className="text-white hover:text-red-300 text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-white hover:bg-opacity-20 transition-all"
                >
                  ×
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="p-6 space-y-6">
              
              {/* File Info Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
                  <label className="block text-xs font-semibold text-green-700 uppercase tracking-wide mb-1">
                    Belge Türü
                  </label>
                  <p className="text-sm font-medium text-green-900">{selectedDocument.document_type}</p>
                </div>
                
                <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                  <label className="block text-xs font-semibold text-blue-700 uppercase tracking-wide mb-1">
                    Proje Aşaması
                  </label>
                  <span className={`inline-block px-3 py-1 text-sm font-semibold rounded-full ${
                    selectedDocument.stage === 'I.Aşama' ? 'bg-green-100 text-green-800' :
                    selectedDocument.stage === 'II.Aşama' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-purple-100 text-purple-800'
                  }`}>
                    {selectedDocument.stage}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-orange-50 p-4 rounded-lg border-l-4 border-orange-500">
                  <label className="block text-xs font-semibold text-orange-700 uppercase tracking-wide mb-1">
                    Dosya Boyutu
                  </label>
                  <p className="text-lg font-bold text-orange-900">{formatFileSize(selectedDocument.file_size)}</p>
                </div>
                
                <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                  <label className="block text-xs font-semibold text-purple-700 uppercase tracking-wide mb-1">
                    Yüklenme Tarihi
                  </label>
                  <p className="text-sm font-medium text-purple-900">
                    {new Date(selectedDocument.created_at).toLocaleDateString('tr-TR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              </div>

              {/* Status Note */}
              <div className="bg-gradient-to-r from-green-50 to-blue-50 border-l-4 border-green-400 p-4 rounded-lg">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <span className="text-2xl">🌱</span>
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-semibold text-green-800 mb-1">
                      Karbon Ayak İzi Raporu
                    </h4>
                    <p className="text-sm text-green-700">
                      Bu rapor, otelimizin yıllık karbon emisyonlarının detaylı analizini içermektedir. 
                      Sürdürülebilirlik hedeflerinize ulaşmanızda rehber olacaktır.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex justify-between items-center">
              <div className="flex items-center text-sm text-gray-500">
                <span className="mr-2">📅</span>
                Rapor tarihi: {new Date(selectedDocument.created_at).toLocaleDateString('tr-TR')}
              </div>
              
              <button
                onClick={() => setShowDocumentModal(false)}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-all transform hover:scale-105 shadow-md"
              >
                ✓ Tamam
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ClientManagement = ({ onNavigate }) => {
  const [clients, setClients] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    hotel_name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: ''
  });
  const { authToken, userRole } = useAuth();

  useEffect(() => {
    fetchClients();
  }, [authToken]);

  const fetchClients = async () => {
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const response = await axios.get(`${API}/clients`, { headers });
      setClients(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error("Error fetching clients:", error);
      setClients([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedClient) {
        await axios.put(`${API}/clients/${selectedClient.id}`, formData, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
      } else {
        await axios.post(`${API}/clients`, formData, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
      }
      fetchClients();
      setShowForm(false);
      setSelectedClient(null);
      setFormData({
        name: '',
        hotel_name: '',
        contact_person: '',
        email: '',
        phone: '',
        address: ''
      });
    } catch (error) {
      console.error("Error saving client:", error);
      alert('Hata: ' + (error.response?.data?.detail || 'Bilinmeyen hata'));
    }
  };

  const handleEdit = (client) => {
    setSelectedClient(client);
    setFormData({
      name: client.name,
      hotel_name: client.hotel_name,
      contact_person: client.contact_person,
      email: client.email,
      phone: client.phone,
      address: client.address
    });
    setShowForm(true);
  };

  const handleDelete = async (clientId) => {
    if (window.confirm('Bu müşteriyi silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`${API}/clients/${clientId}`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        fetchClients();
      } catch (error) {
        console.error("Error deleting client:", error);
        alert('Silme işleminde hata oluştu!');
      }
    }
  };

  const updateStage = async (clientId, newStage) => {
    try {
      await axios.put(`${API}/clients/${clientId}`, { current_stage: newStage }, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      fetchClients();
    } catch (error) {
      console.error("Error updating stage:", error);
    }
  };

  // Only admin can access client management
  if (userRole !== 'admin') {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Bu sayfaya erişim yetkiniz yok.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-800">Müşteri Yönetimi</h2>
          <button
            onClick={() => setShowForm(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
          >
            Yeni Müşteri Ekle
          </button>
        </div>

        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">
                {selectedClient ? 'Müşteri Düzenle' : 'Yeni Müşteri Ekle'}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <input
                  type="text"
                  placeholder="Firma Adı"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-md"
                  required
                />
                <input
                  type="text"
                  placeholder="Otel Adı"
                  value={formData.hotel_name}
                  onChange={(e) => setFormData({...formData, hotel_name: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-md"
                  required
                />
                <input
                  type="text"
                  placeholder="İletişim Kişisi"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-md"
                  required
                />
                <input
                  type="email"
                  placeholder="E-posta"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-md"
                  required
                />
                <input
                  type="tel"
                  placeholder="Telefon"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-md"
                  required
                />
                <textarea
                  placeholder="Adres"
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-md"
                  rows="3"
                  required
                />
                <div className="flex space-x-3">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition-colors"
                  >
                    {selectedClient ? 'Güncelle' : 'Kaydet'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false);
                      setSelectedClient(null);
                      setFormData({
                        name: '',
                        hotel_name: '',
                        contact_person: '',
                        email: '',
                        phone: '',
                        address: ''
                      });
                    }}
                    className="flex-1 bg-gray-500 text-white py-2 rounded-md hover:bg-gray-600 transition-colors"
                  >
                    İptal
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
              <tr>
                <th className="px-6 py-3">Otel Adı</th>
                <th className="px-6 py-3">İletişim Kişisi</th>
                <th className="px-6 py-3">E-posta</th>
                <th className="px-6 py-3">Aşama</th>
                <th className="px-6 py-3">Tarih</th>
                <th className="px-6 py-3">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {(Array.isArray(clients) ? clients : []).map((client) => (
                <tr key={client.id} className="bg-white border-b hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{client.hotel_name}</td>
                  <td className="px-6 py-4">{client.contact_person}</td>
                  <td className="px-6 py-4">{client.email}</td>
                  <td className="px-6 py-4">
                    <select
                      value={client.current_stage}
                      onChange={(e) => updateStage(client.id, e.target.value)}
                      className="px-2 py-1 text-xs border rounded"
                    >
                      <option value="I.Aşama">I.Aşama</option>
                      <option value="II.Aşama">II.Aşama</option>
                      <option value="III.Aşama">III.Aşama</option>
                    </select>
                  </td>
                  <td className="px-6 py-4">{new Date(client.created_at).toLocaleDateString('tr-TR')}</td>
                  <td className="px-6 py-4">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEdit(client)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Düzenle
                      </button>
                      <button
                        onClick={() => onNavigate('project', client)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Proje
                      </button>
                      <button
                        onClick={() => handleDelete(client.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Sil
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Document Modal Component
const DocumentModal = ({ document, onClose, onDownload }) => {

  if (!document) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Belge Detayları</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center">
            <span className="text-3xl mr-3">
              {getFileIcon(document.original_filename || document.file_path || '')}
            </span>
            <div>
              <h4 className="font-semibold text-gray-800">{document.name}</h4>
              <p className="text-sm text-gray-500">{document.original_filename}</p>
            </div>
          </div>
          
          <div className="border-t pt-3 space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">Doküman Türü:</span>
              <span>{document.document_type}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Aşama:</span>
              <span>{document.stage}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Yüklenme Tarihi:</span>
              <span>{new Date(document.created_at).toLocaleDateString('tr-TR')}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Dosya Boyutu:</span>
              <span>{(document.file_size / 1024 / 1024).toFixed(2)} MB</span>
            </div>
          </div>
        </div>

        <div className="flex space-x-2 mt-6">
          <button
            onClick={() => onDownload(document)}
            className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors"
          >
            📥 İndir
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600 transition-colors"
          >
            Kapat
          </button>
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
  const { authToken, userRole, dbUser } = useAuth();


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
      
      const downloadUrl = `${API}/documents/${docData.id}/download`;
      
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
  const { authToken, userRole, dbUser } = useAuth();

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
    if (userRole === 'admin') {
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
      const response = await axios.get(`${API}/clients`, { headers });
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

  const uploadLargeFile = async (file, metadata) => {
    // Her dosya için direkt upload kullan - chunk karmaşıklığı kaldırıldı
    console.log(`📤 Uploading file: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
    return await uploadSingleFile(file, metadata);
  };

  const uploadSingleFile = async (file, metadata) => {
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

    const response = await axios.post(`${API}/upload-document`, formData, {
      headers: { 
        'Authorization': `Bearer ${authToken}`
      },
      timeout: timeoutMs,
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        console.log(`📊 Upload progress: ${percentCompleted}% (${file.name})`);
      }
    });
    
    return response;
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
      const downloadUrl = `${API}/documents/${docData.id}/download`;
      
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
          <h2 className="text-2xl font-bold text-gray-800">📋 Belge Yönetimi (Admin)</h2>
          {selectedClient && (
            <button
              onClick={() => setShowUploadForm(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Yeni Belge Yükle
            </button>
          )}
        </div>

        {/* Client Selection */}
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
                fetchDocuments(client.id);
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
                .filter(folder => folder.client_id === selectedClient.id)
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
                .filter(folder => folder.client_id === selectedClient.id)
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
    accommodation_count: ''
  });
  const { authToken, userRole } = useAuth();

  useEffect(() => {
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
    
    // Admin için müşteri seçimi zorunlu
    if (userRole === 'admin' && !selectedClient) {
      console.log('⚠️ Admin must select client for consumptions');
      setConsumptions([]);
      return;
    }
    
    try {
      let url = `${API}/consumptions?year=${selectedYear}`;
      if (userRole === 'admin' && selectedClient) {
        url += `&client_id=${selectedClient}`;
      }
      
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
    
    try {
      let url = `${API}/consumptions/analytics?year=${selectedYear}`;
      if (userRole === 'admin' && selectedClient) {
        url += `&client_id=${selectedClient}`;
      }
      
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
    if (!authToken || userRole !== 'admin') {
      return; // Only admin needs clients list
    }
    try {
      const response = await axios.get(`${API}/clients`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (Array.isArray(response.data)) {
        setClients(response.data);
        console.log('✅ Clients fetched for consumption:', response.data.length);
      } else {
        setClients([]);
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
        accommodation_count: parseInt(consumptionData.accommodation_count) || 0,
        ...(userRole === 'admin' && consumptionData.client_id && { client_id: consumptionData.client_id })
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
        
        {userRole === 'admin' && (
          <button
            onClick={() => {
              setEditingConsumption(null);
              setConsumptionData({
                year: selectedYear,
                month: new Date().getMonth() + 1,
                electricity: '',
                water: '',
                natural_gas: '',
                coal: '',
                accommodation_count: ''
              });
              setShowConsumptionForm(true);
            }}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
          >
            <span className="mr-2">+</span>
            Yeni Tüketim Verisi
          </button>
        )}
        
        {userRole === 'client' && (
          <div className="text-gray-600 text-sm">
            📊 Tüketim verilerinizi görüntüleyebilirsiniz
          </div>
        )}
      </div>

      {/* Consumption Form Modal */}
      {showConsumptionForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-90vh overflow-y-auto">
            <div className="bg-gradient-to-r from-blue-600 to-green-600 text-white p-6 rounded-t-xl">
              <h3 className="text-xl font-bold">
                {editingConsumption ? 'Tüketim Verisini Düzenle' : 'Yeni Tüketim Verisi'}
              </h3>
            </div>
            
            <form onSubmit={handleConsumptionSubmit} className="p-6 space-y-4">
              {userRole === 'admin' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Müşteri Seçin</label>
                  <select
                    value={consumptionData.client_id || ''}
                    onChange={(e) => setConsumptionData({...consumptionData, client_id: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Müşteri seçin...</option>
                    {(Array.isArray(clients) ? clients : []).map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.hotel_name}
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

              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
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
            </form>
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
                      {userRole === 'admin' && (
                        <>
                          <button
                            onClick={() => handleEdit(consumption)}
                            className="text-blue-600 hover:text-blue-900 font-medium"
                          >
                            ✏️ Düzenle
                          </button>
                          <button
                            onClick={() => handleDelete(consumption.id)}
                            className="text-red-600 hover:text-red-900 font-medium"
                          >
                            🗑️ Sil
                          </button>
                        </>
                      )}
                      {userRole === 'client' && (
                        <span className="text-gray-500 text-sm">Sadece görüntüleme</span>
                      )}
                      {userRole === 'client' && (
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

      {/* Analytics Section */}
      {userRole === 'admin' && !consumptionData.client_id && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
          <h3 className="text-lg font-medium text-yellow-800 mb-2">📊 Analiz için Müşteri Seçin</h3>
          <p className="text-yellow-600 mb-3">Tüketim analizlerini görüntülemek için yukarıdan bir müşteri seçin.</p>
          <select
            value={consumptionData.client_id || ''}
            onChange={(e) => {
              setConsumptionData({...consumptionData, client_id: e.target.value});
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
            className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Müşteri seçin...</option>
            {(Array.isArray(clients) ? clients : []).map((client) => (
              <option key={client.id} value={client.id}>
                {client.hotel_name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Admin için müşteri seçim uyarısı */}
      {userRole === 'admin' && !selectedClient && (
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
              {(analytics?.monthly_comparison || []).slice(0, 6).map((month) => (
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
  const { authToken, userRole } = useAuth();

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
                      <h4 className="font-semibold text-sm">{training.title}</h4>
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
  const { authToken, userRole, dbUser } = useAuth();

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

const TrainingManagement = () => {
  const [trainings, setTrainings] = useState([]);
  const [clients, setClients] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    client_id: '',
    name: '',
    subject: '',
    participant_count: '',
    trainer: '',
    training_date: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const { authToken, userRole } = useAuth();

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

  useEffect(() => {
    if (authToken && userRole === 'admin') {
      fetchTrainings();
      fetchClients();
    }
  }, [authToken, userRole]);

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
    
    try {
      console.log("👥 Admin fetching clients...");
      const response = await axios.get(`${API}/clients`, {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      console.log("👥 Admin clients response:", response.data);
      setClients(response.data);
    } catch (error) {
      console.error("❌ Error fetching clients:", error);
      setClients([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const trainingData = {
        ...formData,
        participant_count: parseInt(formData.participant_count) || 0,
        training_date: formData.training_date ? new Date(formData.training_date + "T00:00:00Z").toISOString() : null,
        training_date: formData.training_date ? new Date(formData.training_date + 'T00:00:00Z').toISOString() : null
      };
      
      console.log('📚 Creating training:', trainingData);
      
      const response = await axios.post(`${API}/trainings`, trainingData, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      console.log('✅ Training created:', response.data);
      setFormData({
        client_id: '',
        name: '',
        subject: '',
        participant_count: '',
        trainer: '',
        training_date: '',
        description: ''
      });
      setShowAddForm(false);
      fetchTrainings();
      
    } catch (error) {
      console.error('❌ Error creating training:', error);
      alert('Eğitim oluşturma hatası: ' + (error.response?.data?.detail || error.message));
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
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Eğitim Yönetimi</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
        >
          <span className="mr-2">+</span>
          Yeni Eğitim Ekle
        </button>
      </div>

      {/* Add Training Form */}
      {showAddForm && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">Yeni Eğitim Ekle</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Müşteri Seçin *
                </label>
                <select
                  value={formData.client_id}
                  onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Bir müşteri seçin...</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.hotel_name || client.name}
                    </option>
                  ))}
                </select>
              </div>
              
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Müşteri Seçin *
                </label>
                <select
                  value={formData.client_id}
                  onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Bir müşteri seçin...</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.hotel_name || client.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Eğitimin Adı *
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
                  Konusu *
                </label>
                <input
                  type="text"
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
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
                  min="0"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Eğitimi Kimin Vereceği *
                </label>
                <input
                  type="text"
                  value={formData.trainer}
                  onChange={(e) => setFormData({ ...formData, trainer: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tarih *
                </label>
                <input
                  type="date"
                  value={formData.training_date}
                  onChange={(e) => setFormData({ ...formData, training_date: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>
            
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
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Ekleniyor...' : 'Eğitimi Ekle'}
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
                İptal
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Trainings List */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Eğitimler</h3>
          
          {trainings.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <span className="text-6xl mb-4 block">📚</span>
              <h4 className="text-xl font-semibold mb-2">Henüz eğitim yok</h4>
              <p>İlk eğitimi eklemek için yukarıdaki butonu kullanın.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {trainings.map((training) => (
                <div key={training.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="text-2xl mr-3">📚</span>
                        <div>
                          <h4 className="font-semibold text-lg">{training.name}</h4>
                          <p className="text-sm text-gray-600">{training.subject}</p>
                          <p className="text-xs text-blue-600 font-medium">🏨 {getClientName(training.client_id)}</p>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
                        <div>
                          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Eğitmen</span>
                          <p className="text-sm font-medium">{training.trainer}</p>
                        </div>
                        <div>
                          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Tarih</span>
                          <p className="text-sm font-medium">{formatDate(training.training_date)}</p>
                        </div>
                        <div>
                          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Katılımcı Sayısı</span>
                          <p className="text-sm font-medium">{training.participant_count || 0}</p>
                        </div>
                      </div>
                      
                      {training.description && (
                        <div className="mt-3">
                          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Açıklama</span>
                          <p className="text-sm text-gray-700 mt-1">{training.description}</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center ml-4 space-x-2">
                      <button
                        onClick={() => deleteTraining(training.id)}
                        className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 transition-colors"
                        title="Eğitimi sil"
                      >
                        🗑️ Sil
                      </button>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        isUpcoming(training.training_date) 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {isUpcoming(training.training_date) ? 'Yaklaşan' : 'Geçmiş'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ClientSetupForm = ({ onComplete, onSkip }) => {
  const [formData, setFormData] = useState({
    name: '',
    hotel_name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: ''
  });
  const [loading, setLoading] = useState(false);
  const { user, authToken, refreshUser } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Create client record
      const clientResponse = await axios.post(`${API}/clients`, {
        ...formData,
        email: user.primaryEmailAddress?.emailAddress || formData.email
      }, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });

      // Update user record with client_id
      await axios.put(`${API}/auth/me`, {
        client_id: clientResponse.data.id
      }, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });

      // Refresh user data
      await refreshUser();

      alert('Otel bilgileriniz başarıyla kaydedildi! Sistemi kullanmaya başlayabilirsiniz.');
      onComplete();
    } catch (error) {
      console.error('Client setup error:', error);
      alert('Hata oluştu: ' + (error.response?.data?.detail || 'Bilinmeyen hata'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800">🏨 Otel Bilgilerinizi Tamamlayın</h1>
          <p className="text-gray-600 mt-2">
            Sürdürülebilir turizm yolculuğunuza başlamak için otel bilgilerinizi girin.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Firma Adı <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="Örn: Antalya Turizm A.Ş."
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Otel/Tesis Adı <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="Örn: Grand Resort & Spa"
              value={formData.hotel_name}
              onChange={(e) => setFormData({...formData, hotel_name: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              İletişim Kişisi <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="Örn: Ahmet Yılmaz"
              value={formData.contact_person}
              onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              E-posta <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              placeholder="Örn: info@grandresort.com"
              value={formData.email || user?.primaryEmailAddress?.emailAddress || ''}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Telefon <span className="text-red-500">*</span>
            </label>
            <input
              type="tel"
              placeholder="Örn: +90 242 123 4567"
              value={formData.phone}
              onChange={(e) => setFormData({...formData, phone: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Adres <span className="text-red-500">*</span>
            </label>
            <textarea
              placeholder="Tam adresinizi girin..."
              value={formData.address}
              onChange={(e) => setFormData({...formData, address: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows="3"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                Kaydediliyor...
              </div>
            ) : (
              'Otel Bilgilerini Kaydet'
            )}
          </button>

          <button
            type="button"
            onClick={onSkip}
            className="w-full bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600 transition-colors mt-2"
          >
            Şimdilik Atla (Sonra Tamamlayabilirim)
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Bu bilgiler sürdürülebilirlik danışmanlığı sürecinde kullanılacaktır.
          </p>
        </div>
      </div>
    </div>
  );
};

const Sidebar = ({ activeTab, onNavigate, userRole }) => {
  const adminMenuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'clients', name: 'Müşteri Yönetimi', icon: '🏨' },
    { id: 'consumption', name: 'Tüketim Yönetimi', icon: '⚡' },
    { id: 'analytics', name: 'Tüketim Analizi', icon: '📈' },
    { id: 'documents', name: 'Belge Yönetimi', icon: '📋' },
    { id: 'trainings', name: 'Eğitim Yönetimi', icon: '🎓' },
    { id: 'email', name: 'Email Yönetimi', icon: '📧' },
    { id: 'reports', name: 'Raporlar', icon: '📊' },
  ];

  const clientMenuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'consumption', name: 'Tüketim Takibi', icon: '⚡' },
    { id: 'analytics', name: 'Tüketim Analizi', icon: '📈' },
    { id: 'documents', name: 'Belgelerim', icon: '📋' },
    { id: 'trainings', name: 'Eğitimlerim', icon: '🎓' }
  ];

  const menuItems = userRole === 'admin' ? adminMenuItems : clientMenuItems;

  return (
    <div className="bg-gray-800 text-white w-64 min-h-screen p-4">
      <div className="mb-8">
        {/* Header kaldırıldı */}
      </div>
      
      <nav className="space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
              activeTab === item.id 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <span className="mr-3">{item.icon}</span>
            {item.name}
          </button>
        ))}
      </nav>
    </div>
  );
};

// Main App Component
const MainApp = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedClient, setSelectedClient] = useState(null);
  const [showClientSetup, setShowClientSetup] = useState(false);
  const { userRole, isLoaded, dbUser, refreshUser } = useAuth();

  // Check if client user needs to complete setup
  useEffect(() => {
    if (isLoaded && userRole === 'client') {
      // Check localStorage first
      const setupCompleted = localStorage.getItem(`client_setup_${userRole}_completed`);
      
      if (!setupCompleted && (!dbUser?.client_id || dbUser?.client_id === '')) {
        setShowClientSetup(true);
      } else {
        setShowClientSetup(false);
        // If localStorage says completed but no dbUser.client_id, refresh user data
        if (setupCompleted && !dbUser?.client_id) {
          refreshUser();
        }
      }
    }
  }, [isLoaded, userRole, dbUser, refreshUser]);

  const handleNavigate = (tab, client = null) => {
    setActiveTab(tab);
    setSelectedClient(client);
  };

  const handleSetupComplete = async () => {
    try {
      // Mark setup as completed in localStorage
      localStorage.setItem(`client_setup_${userRole}_completed`, 'true');
      
      // Refresh user data to get latest client_id
      await refreshUser();
      
      // Hide setup form
      setShowClientSetup(false);
      
      console.log('✅ Client setup completed and marked as done');
    } catch (error) {
      console.error('Setup completion error:', error);
    }
  };

  const handleSetupSkip = () => {
    // Mark as completed even if skipped
    localStorage.setItem(`client_setup_${userRole}_completed`, 'true');
    setShowClientSetup(false);
  };

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  // Show client setup form for new client users
  if (showClientSetup && userRole === 'client') {
    return <ClientSetupForm onComplete={handleSetupComplete} onSkip={handleSetupSkip} />;
  }

  const renderContent = () => {
    switch(activeTab) {
      case 'dashboard':
        return <Dashboard onNavigate={handleNavigate} />;
      case 'clients':
        return <ClientManagement onNavigate={handleNavigate} />;
      case 'consumption':
        return <ConsumptionManagement onNavigate={handleNavigate} />;
      case 'analytics':
        return <ConsumptionAnalytics />;
      case 'project':
        return <ProjectManagement client={selectedClient} onNavigate={handleNavigate} />;
      case 'documents':
        return userRole === 'admin' ? <DocumentManagement /> : <ClientDocuments />;
      case 'client-documents':
        return <ClientDocuments />;
      case 'reports':
        return (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Raporlar</h2>
            <p className="text-gray-600">Yakında eklenecek...</p>
          </div>
        );
      case 'email':
        return <EmailManagement />;
      case 'trainings':
        return userRole === 'admin' ? <TrainingManagement /> : <ClientTrainings />;
      default:
        return <Dashboard onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar activeTab={activeTab} onNavigate={handleNavigate} userRole={userRole} />
        <div className="flex-1 p-6">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

// Email Management Component
const EmailManagement = () => {
  const [testEmailStatus, setTestEmailStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [trainings, setTrainings] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const { authToken } = useAuth();

  // Get client name helper function
  const getClientName = (clientId) => {
    const client = clients.find(c => c.id === clientId);
    return client ? client.name : 'Bilinmiyen Müşteri';
  };

  // Get client email helper function  
  const getClientEmail = (clientId) => {
    const client = clients.find(c => c.id === clientId);
    return client ? client.email : 'Email bulunamadı';
  };

  const fetchClients = async () => {
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const response = await axios.get(`${API}/clients`, { headers });
      setClients(response.data || []);
    } catch (error) {
      console.error("❌ Error fetching clients:", error);
      setClients([]);
    }
  };



  const fetchDocuments = async () => {
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const response = await axios.get(`${API}/documents`, { headers });
      setDocuments(response.data || []);
    } catch (error) {
      console.error("❌ Error fetching documents:", error);
      setDocuments([]);
    }
  };

  const fetchTrainings = async () => {
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const response = await axios.get(`${API}/trainings`, { headers });
      setTrainings(response.data || []);
    } catch (error) {
      console.error("❌ Error fetching trainings:", error);
      setTrainings([]);
    }
  };

  useEffect(() => {
    if (authToken) {
      fetchClients();
      fetchDocuments();
      fetchTrainings();
    }
  }, [authToken]);

  const sendTestEmail = async () => {
    setLoading(true);
    setTestEmailStatus('');
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const response = await axios.post(`${API}/email/test`, {}, { headers });
      setTestEmailStatus(`✅ ${response.data.message} (${response.data.email})`);
    } catch (error) {
      setTestEmailStatus(`❌ Hata: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const sendDocumentNotification = async (documentId) => {
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const formData = new FormData();
      formData.append('document_id', documentId);
      
      const response = await axios.post(`${API}/email/document-notification`, formData, { headers });
      alert(`✅ ${response.data.message}`);
    } catch (error) {
      alert(`❌ Hata: ${error.response?.data?.detail || error.message}`);
    }
  };

  const sendTrainingNotification = async (trainingId) => {
    try {
      const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
      const formData = new FormData();
      formData.append('training_id', trainingId);
      
      const response = await axios.post(`${API}/email/training-notification`, formData, { headers });
      alert(`✅ ${response.data.message}`);
    } catch (error) {
      alert(`❌ Hata: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Checkbox handling functions
  const handleDocumentSelect = (docId, isSelected) => {
    if (isSelected) {
      setSelectedDocuments(prev => [...prev, docId]);
    } else {
      setSelectedDocuments(prev => prev.filter(id => id !== docId));
    }
  };

  const handleSelectAll = (isSelected) => {
    if (isSelected) {
      setSelectedDocuments(documents.map(doc => doc.id));
    } else {
      setSelectedDocuments([]);
    }
  };

  // Send bulk notification
  const sendBulkNotification = async () => {
    if (selectedDocuments.length === 0) {
      alert('❌ Lütfen en az bir doküman seçin!');
      return;
    }

    // Group documents by client
    const selectedDocs = documents.filter(doc => selectedDocuments.includes(doc.id));
    const groupedByClient = selectedDocs.reduce((groups, doc) => {
      const clientId = doc.client_id;
      if (!groups[clientId]) {
        groups[clientId] = [];
      }
      groups[clientId].push(doc);
      return groups;
    }, {});

    try {
      // Send emails for each client group
      for (const [clientId, clientDocs] of Object.entries(groupedByClient)) {
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        const formData = new FormData();
        formData.append('document_ids', clientDocs.map(doc => doc.id).join(','));
        
        const response = await axios.post(`${API}/email/bulk-document-notification`, formData, { headers });
        console.log(`✅ ${response.data.message}`);
      }
      
      const clientCount = Object.keys(groupedByClient).length;
      const docCount = selectedDocuments.length;
      alert(`✅ ${docCount} doküman için ${clientCount} müşteriye toplu bildirim gönderildi!`);
      setSelectedDocuments([]);
      
    } catch (error) {
      alert(`❌ Toplu bildirim hatası: ${error.response?.data?.detail || error.message}`);
    }
  };


  return (
    <div className="email-management">
      <h2>📧 Email Yönetimi</h2>
      
      {/* Test Email Section */}
      <div className="email-section">
        <h3>🧪 Test Email</h3>
        <p>Sistem email ayarlarını test etmek için kendinize test emaili gönderebilirsiniz.</p>
        <button 
          onClick={sendTestEmail}
          disabled={loading}
          className="btn-primary"
        >
          {loading ? 'Gönderiliyor...' : 'Test Email Gönder'}
        </button>
        {testEmailStatus && (
          <div className={`status-message ${testEmailStatus.includes('✅') ? 'success' : 'error'}`}>
            {testEmailStatus}
          </div>
        )}
      </div>

      {/* Document Notifications */}
      <div className="email-section">
        <h3>📄 Doküman Bildirimleri</h3>
        <p>Yüklenen dokümanlar için müşterilere email bildirimi gönderebilirsiniz.</p>
        
        {documents.length > 0 && (
          <div className="bulk-controls">
            <label className="select-all">
              <input
                type="checkbox"
                checked={selectedDocuments.length === documents.length}
                onChange={(e) => handleSelectAll(e.target.checked)}
              />
              Tümünü Seç ({documents.length} doküman)
            </label>
            <button
              onClick={sendBulkNotification}
              disabled={selectedDocuments.length === 0}
              className="btn-bulk"
            >
              📧 Seçilenleri Gönder ({selectedDocuments.length})
            </button>
          </div>
        )}
        
        <div className="documents-list">
          {documents.length === 0 ? (
            <p>Henüz doküman bulunmuyor.</p>
          ) : (
            documents.map(doc => (
              <div key={doc.id} className="document-item">
                <input
                  type="checkbox"
                  checked={selectedDocuments.includes(doc.id)}
                  onChange={(e) => handleDocumentSelect(doc.id, e.target.checked)}
                  className="document-checkbox"
                />
                <div className="document-info">
                  <span className="document-name">📄 {doc.document_name}</span>
                  <span className="document-client">🏨 {getClientName(doc.client_id)}</span>
                  <span className="document-email">📧 {getClientEmail(doc.client_id)}</span>
                  <span className="document-date">📅 {doc.created_at ? new Date(doc.created_at).toLocaleDateString('tr-TR') : 'Bilinmiyor'}</span>
                </div>
                <button 
                  onClick={() => sendDocumentNotification(doc.id)}
                  className="btn-secondary"
                >
                  📧 Tek Gönder
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Training Notifications */}
      <div className="email-section">
        <h3>🎓 Eğitim Bildirimleri</h3>
        <p>Tanımlanan eğitimler için müşterilere email bildirimi gönderebilirsiniz.</p>
        <div className="trainings-list">
          {trainings.length === 0 ? (
            <p>Henüz eğitim bulunmuyor.</p>
          ) : (
            trainings.map(training => (
              <div key={training.id} className="training-item">
                <span className="training-name">🎓 {training.name}</span>
                <span className="training-date">📅 {training.training_date}</span>
                <button 
                  onClick={() => sendTrainingNotification(training.id)}
                  className="btn-secondary"
                >
                  📧 Tek Gönder
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <style jsx>{`
        .email-management {
          padding: 20px;
        }
        .email-section {
          margin-bottom: 30px;
          padding: 20px;
          background: #f8f9fa;
          border-radius: 8px;
          border: 1px solid #dee2e6;
        }
        .email-section h3 {
          margin-top: 0;
          color: #495057;
        }
        .btn-primary, .btn-secondary {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          margin: 5px;
        }
        .btn-primary {
          background-color: #007bff;
          color: white;
        }
        .btn-primary:disabled {
          background-color: #6c757d;
          cursor: not-allowed;
        }
        .btn-secondary {
          background-color: #28a745;
          color: white;
        }
        .status-message {
          margin-top: 10px;
          padding: 10px;
          border-radius: 4px;
        }
        .status-message.success {
          background-color: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }
        .status-message.error {
          background-color: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }
        .documents-list, .trainings-list {
          margin-top: 15px;
        }
        .document-item, .training-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 15px;
          margin: 8px 0;
          background: white;
          border-radius: 8px;
          border: 1px solid #dee2e6;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .document-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
          flex: 1;
        }
        .document-name, .training-name {
          font-weight: 600;
          color: #333;
          font-size: 14px;
        }
        .document-client, .document-email, .document-date {
          font-size: 12px;
          color: #666;
        }
        .bulk-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin: 15px 0;
          padding: 12px;
          background: #e3f2fd;
          border-radius: 6px;
          border: 1px solid #2196F3;
        }
        .select-all {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
          color: #1976d2;
        }
        .btn-bulk {
          background-color: #4CAF50;
          color: white;
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
        }
        .btn-bulk:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }
        .document-checkbox {
          margin-right: 10px;
        }
        .document-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
          flex: 1;
        }
        .document-name, .training-name {
          font-weight: 600;
          color: #333;
          font-size: 14px;
        }
        .document-client, .document-email, .document-date {
          font-size: 12px;
          color: #666;
        }
        .document-name, .training-name {
          font-weight: 500;
          flex: 1;
        }
        .document-client, .training-date {
          color: #6c757d;
          font-size: 12px;
          margin: 0 10px;
        }
      `}</style>
    </div>
  );
};

// Müşteri telefon satırı bileşeni
const ClientPhoneRow = ({ client, onUpdatePhone }) => {
  const [editing, setEditing] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState(client.phone_number || '');

  const handleSave = () => {
    onUpdatePhone(client.id, phoneNumber);
    setEditing(false);
  };

  return (
    <tr>
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="text-sm font-medium text-gray-900">{client.hotel_name}</div>
          <div className="text-sm text-gray-500">ID: {client.id.substring(0, 8)}...</div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        {editing ? (
          <input
            type="text"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            placeholder="05xxxxxxxxx"
            className="px-3 py-1 border border-gray-300 rounded text-sm w-full"
          />
        ) : (
          <span className="text-sm text-gray-900">
            {client.phone_number || 'Telefon numarası yok'}
          </span>
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
        {editing ? (
          <div className="space-x-2">
            <button
              onClick={handleSave}
              className="text-green-600 hover:text-green-900"
            >
              Kaydet
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setPhoneNumber(client.phone_number || '');
              }}
              className="text-gray-600 hover:text-gray-900"
            >
              İptal
            </button>
          </div>
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="text-blue-600 hover:text-blue-900"
          >
            Düzenle
          </button>
        )}
      </td>
    </tr>
  );
};

// Root App Component with Clerk Provider
function App() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <SignedIn>
        <MainApp />
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </ClerkProvider>
  );
}

export default App;