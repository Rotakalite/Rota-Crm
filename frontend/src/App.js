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
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';

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

// Dashboard Component
const Dashboard = ({ onNavigate }) => {
  const { user } = useUser();
  const { authToken, userRole, dbUser } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const API = getApiUrl();

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/stats`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authToken) {
      fetchDashboardData();
    }
  }, [authToken]);

  if (loading) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Dashboard yükleniyor...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Hoş Geldiniz, {user?.firstName || 'Kullanıcı'}! 👋
          </h1>
          <p className="text-gray-600">
            {userRole === 'admin' ? 'Admin Panel - Sistemin tüm özelliklerine erişebilirsiniz.' 
            : 'Müşteri Paneli - Kendi verilerinizi görüntüleyebilir ve yönetebilirsiniz.'}
          </p>
        </div>

        {/* Admin Dashboard */}
        {userRole === 'admin' && dashboardData && (
          <>
            {/* Admin Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">🏨 Toplam Müşteri</h3>
                    <p className="text-3xl font-bold">{dashboardData.total_clients || 0}</p>
                  </div>
                  <div className="text-4xl opacity-80">🏨</div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">📄 Toplam Doküman</h3>
                    <p className="text-3xl font-bold">{dashboardData.total_documents || 0}</p>
                  </div>
                  <div className="text-4xl opacity-80">📄</div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">🎓 Toplam Eğitim</h3>
                    <p className="text-3xl font-bold">{dashboardData.total_trainings || 0}</p>
                  </div>
                  <div className="text-4xl opacity-80">🎓</div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">📊 Aktif Proje</h3>
                    <p className="text-3xl font-bold">{dashboardData.stage_distribution ? Object.values(dashboardData.stage_distribution).reduce((a, b) => a + b, 0) : 0}</p>
                  </div>
                  <div className="text-4xl opacity-80">📊</div>
                </div>
              </div>
            </div>

            {/* Quick Action Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('clients')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">🏨 Müşteri Yönetimi</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-indigo-100">
                  Müşteri bilgilerini yönetin ve analiz edin
                </p>
              </div>

              <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('carbon')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">🌍 Karbon Ayak İzi</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-green-100">
                  DEFRA standardında karbon emisyon analizi
                </p>
              </div>

              <div className="bg-gradient-to-br from-amber-500 to-amber-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('waste-management')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">🗑️ Atık Yönetimi</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-amber-100">
                  Atık takibi ve geri dönüşüm analizi
                </p>
              </div>

              <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('guest-engagement')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">🎯 Guest Engagement</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-blue-100">
                  Misafir sürdürülebilirlik skorları
                </p>
              </div>

              <div className="bg-gradient-to-br from-red-500 to-red-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('documents')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">📄 Doküman Yönetimi</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-red-100">
                  Dokümanları klasörler halinde organize edin
                </p>
              </div>

              <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('trainings')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">🎓 Eğitim Yönetimi</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-cyan-100">
                  Eğitim programlarını planlayın
                </p>
              </div>
            </div>
          </>
        )}

        {/* Client Dashboard */}
        {userRole === 'client' && dashboardData && (
          <>
            {/* Client Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">📄 Dokümanlarım</h3>
                    <p className="text-3xl font-bold">{dashboardData.total_documents || 0}</p>
                  </div>
                  <div className="text-4xl opacity-80">📄</div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">🎓 Eğitimlerim</h3>
                    <p className="text-3xl font-bold">{dashboardData.total_trainings || 0}</p>
                  </div>
                  <div className="text-4xl opacity-80">🎓</div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">📊 TR1 Kriterleri</h3>
                    <p className="text-3xl font-bold">{dashboardData.document_type_distribution?.TR1_CRITERIA || 0}</p>
                  </div>
                  <div className="text-4xl opacity-80">📊</div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">🌍 Karbon Raporu</h3>
                    <p className="text-3xl font-bold">{dashboardData.document_type_distribution?.CARBON_REPORT || 0}</p>
                  </div>
                  <div className="text-4xl opacity-80">🌍</div>
                </div>
              </div>
            </div>

            {/* Client Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('documents')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">📄 Belgelerim</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-blue-100">
                  Dokümanlarınızı görüntüleyin ve indirin
                </p>
              </div>

              <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('consumption')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">⚡ Tüketim Takibi</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-purple-100">
                  Enerji ve su tüketim verileriniz
                </p>
              </div>

              <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('carbon')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">🌍 Karbon Ayak İzi</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-green-100">
                  Karbon emisyon analizi ve raporları
                </p>
              </div>

              <div className="bg-gradient-to-br from-amber-500 to-amber-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('waste-management')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">🗑️ Atık Yönetimi</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-amber-100">
                  Atık takibi ve geri dönüşüm verileri
                </p>
              </div>

              <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('guest-engagement')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">🎯 Guest Engagement</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-cyan-100">
                  Misafir sürdürülebilirlik programı
                </p>
              </div>

              <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 p-6 rounded-xl text-white shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
                   onClick={() => onNavigate('trainings')}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">🎓 Eğitimlerim</h3>
                  <span className="text-2xl">→</span>
                </div>
                <p className="text-indigo-100">
                  Eğitim programları ve sertifikalar
                </p>
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
  ArcElement,
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
    'https://616edfad-2f75-4e2d-b9f7-ddbd6ff57760.preview.emergentagent.com',
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

// Carbon Footprint Component
const CarbonFootprint = () => {
  const [carbonData, setCarbonData] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [selectedYear, setSelectedYear] = useState(2025);
  const [loading, setLoading] = useState(false);

  const { authToken, userRole, dbUser } = useAuth();

  // Fetch clients for admin users
  const fetchClients = async () => {
    try {
      console.log('🏨 [DEBUG] Fetching clients for admin...');
      console.log('🏨 [DEBUG] AuthToken:', authToken ? 'EXISTS' : 'MISSING');
      console.log('🏨 [DEBUG] UserRole:', userRole);
      
      const response = await axios.get(`${API}/clients`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      console.log('🏨 [DEBUG] Clients API response:', response.data);
      console.log('🏨 [DEBUG] Response type:', Array.isArray(response.data) ? 'Array' : typeof response.data);
      
      setClients(Array.isArray(response.data) ? response.data : []);
      console.log('🏨 [DEBUG] Clients set in state');
    } catch (error) {
      console.error("❌ [ERROR] Error fetching clients:", error);
      console.error("❌ [ERROR] Error response:", error.response?.data);
      setClients([]);
    }
  };

  // Fetch carbon footprint data
  const fetchCarbonData = async () => {
    setLoading(true);
    try {
      const clientId = userRole === 'admin' ? selectedClient : dbUser?.client_id;
      if (!clientId) {
        setLoading(false);
        return;
      }
      
      console.log('🌍 Fetching carbon data for client:', clientId, 'year:', selectedYear);
      
      const response = await axios.get(`${API}/analytics/carbon-footprint?year=${selectedYear}&client_id=${clientId}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
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
    if (authToken && userRole === 'admin') {
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
          {/* Admin Client Selection */}
          {userRole === 'admin' && (
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              className="px-4 py-2 rounded-lg bg-white text-gray-800 font-medium min-w-[200px]"
            >
              <option value="">Müşteri Seçin</option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.name}
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
            disabled={loading || (!selectedClient && userRole === 'admin')}
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
                  ))}
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

  const { authToken, userRole, dbUser } = useAuth();

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
      setClients(response.data);
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
const WasteManagement = () => {
  const [wasteRecords, setWasteRecords] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [selectedYear, setSelectedYear] = useState(2025);
  const [showAddRecord, setShowAddRecord] = useState(false);
  const [loading, setLoading] = useState(false);
  const [newRecord, setNewRecord] = useState({
    year: 2025,
    month: new Date().getMonth() + 1,
    organic_waste: 0,
    plastic_waste: 0,
    glass_waste: 0,
    paper_waste: 0,
    metal_waste: 0,
    electronic_waste: 0,
    oil_waste: 0,
    mixed_waste: 0
  });

  const { authToken, userRole, dbUser } = useAuth();
  const API = getApiUrl();

  // Fetch clients for admin users
  const fetchClients = async () => {
    if (userRole !== 'admin') return;
    
    try {
      const response = await axios.get(`${API}/clients`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(response.data || []);
      if (response.data?.length > 0) {
        setSelectedClient(response.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  // Fetch waste records from analytics (since analytics endpoint works)
  const fetchWasteRecords = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedYear) params.append('year', selectedYear);
      if (userRole === 'admin' && selectedClient) params.append('client_id', selectedClient);

      // Use analytics endpoint since it works and has all the data we need
      const response = await axios.get(`${API}/consumptions/waste/analytics?${params}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      // Convert analytics data to records format for display
      const analyticsData = response.data;
      
      // Create monthly cards from analytics data
      const monthlyCards = analyticsData.monthly_data || [];
      setWasteRecords(monthlyCards);
      
      // Set waste breakdown for pie chart
      setWasteBreakdown(analyticsData.waste_breakdown || {});
      
      // Set totals for summary cards
      setYearlyTotals(analyticsData.yearly_totals || {});
      
    } catch (error) {
      console.error('Error fetching waste records:', error);
      setWasteRecords([]);
      setWasteBreakdown({});
      setYearlyTotals({});
    } finally {
      setLoading(false);
    }
  };

  // Fetch analytics
  const fetchAnalytics = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedYear) params.append('year', selectedYear);
      if (userRole === 'admin' && selectedClient) params.append('client_id', selectedClient);

      const response = await axios.get(`${API}/consumptions/waste/analytics?${params}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setAnalytics(null);
    }
  };

  // Submit new waste record
  const handleSubmitRecord = async () => {
    try {
      setLoading(true);
      const recordData = { ...newRecord };
      if (userRole === 'admin' && selectedClient) {
        recordData.client_id = selectedClient;
      }

      await axios.post(`${API}/consumptions/waste`, recordData, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      alert('Atık kaydı başarıyla eklendi!');
      setShowAddRecord(false);
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
        mixed_waste: 0
      });
      fetchWasteRecords();
      fetchAnalytics();
    } catch (error) {
      console.error('Error creating waste record:', error);
      alert('Hata: ' + (error.response?.data?.detail || error.message));
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
    if (authToken && (userRole === 'client' || (userRole === 'admin' && selectedClient))) {
      fetchWasteRecords();
      fetchAnalytics();
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🗑️ Atık Yönetimi</h1>
          <p className="text-gray-600">
            Atık takibi, geri dönüşüm analizi ve maliyet hesaplama sistemi
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex gap-4 items-center">
              {/* Client Selection for Admin */}
              {userRole === 'admin' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Müşteri Seçin
                  </label>
                  <select
                    value={selectedClient}
                    onChange={(e) => setSelectedClient(e.target.value)}
                    className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Müşteri Seçin</option>
                    {clients.map(client => (
                      <option key={client.id} value={client.id}>
                        {client.hotel_name}
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

            <button
              onClick={() => setShowAddRecord(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              ➕ Yeni Atık Kaydı
            </button>
          </div>
        </div>

        {/* Analytics Cards */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">♻️ Geri Dönüşüm Oranı</h3>
              <p className="text-3xl font-bold">{analytics.recycling_performance?.current_rate?.toFixed(1) || 0}%</p>
              <p className="text-green-100">
                Hedef: {analytics.recycling_performance?.target_rate || 60}%
              </p>
            </div>

            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">📊 Toplam Atık</h3>
              <p className="text-3xl font-bold">{analytics.yearly_totals?.total_waste?.toFixed(1) || 0}</p>
              <p className="text-blue-100">kg/yıl</p>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">💰 Net Maliyet</h3>
              <p className="text-3xl font-bold">{analytics.yearly_totals?.total_cost?.toFixed(0) || 0}</p>
              <p className="text-purple-100">TL/yıl</p>
            </div>

            <div className="bg-gradient-to-br from-amber-500 to-amber-600 p-6 rounded-xl text-white shadow-lg">
              <h3 className="text-lg font-bold mb-2">🛢️ Yağ Atığı</h3>
              <p className="text-3xl font-bold">{analytics.yearly_totals?.oil_waste?.toFixed(1) || 0}</p>
              <p className="text-amber-100">litre/yıl</p>
            </div>
          </div>
        )}

        {/* Waste Records Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Atık Kayıtları</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center text-gray-500">Yükleniyor...</div>
          ) : wasteRecords.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Henüz atık kaydı bulunmuyor. İlk kaydınızı ekleyin.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tarih
                    </th>
                    {userRole === 'admin' && (
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Müşteri
                      </th>
                    )}
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Organik (kg)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Plastik (kg)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cam (kg)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Yağ (L)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Geri Dönüşüm %
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Net Maliyet
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {wasteRecords.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.month}/{record.year}
                      </td>
                      {userRole === 'admin' && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {getClientName(record.client_id)}
                        </td>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.organic_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.plastic_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.glass_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {record.oil_waste || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`font-medium ${
                          record.recycling_rate >= 60 ? 'text-green-600' : 
                          record.recycling_rate >= 40 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {record.recycling_rate?.toFixed(1) || 0}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        ₺{record.net_cost?.toFixed(0) || 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Add Record Modal */}
      {showAddRecord && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Yeni Atık Kaydı Ekle</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Yıl</label>
                  <input
                    type="number"
                    value={newRecord.year}
                    onChange={(e) => setNewRecord({...newRecord, year: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ay</label>
                  <select
                    value={newRecord.month}
                    onChange={(e) => setNewRecord({...newRecord, month: parseInt(e.target.value)})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    {Array.from({length: 12}, (_, i) => (
                      <option key={i+1} value={i+1}>{i+1}. Ay</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🥬 Organik Atık (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.organic_waste}
                    onChange={(e) => setNewRecord({...newRecord, organic_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">♻️ Plastik (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.plastic_waste}
                    onChange={(e) => setNewRecord({...newRecord, plastic_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🍾 Cam (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.glass_waste}
                    onChange={(e) => setNewRecord({...newRecord, glass_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">📄 Kağıt/Karton (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newRecord.paper_waste}
                    onChange={(e) => setNewRecord({...newRecord, paper_waste: parseFloat(e.target.value) || 0})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">🔩 Metal (kg)</label>
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
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? 'Kaydediliyor...' : 'Kaydet'}
                </button>
                <button
                  onClick={() => setShowAddRecord(false)}
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

// Client Management Component
const ClientManagement = ({ onNavigate }) => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddClient, setShowAddClient] = useState(false);
  const [newClient, setNewClient] = useState({
    name: '',
    hotel_name: '',
    email: '',
    phone: '',
    address: ''
  });

  const { authToken, userRole } = useAuth();
  const API = getApiUrl();

  // Fetch clients
  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/clients`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(response.data || []);
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  // Add new client
  const handleAddClient = async () => {
    try {
      await axios.post(`${API}/clients`, newClient, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      alert('Müşteri başarıyla eklendi!');
      setShowAddClient(false);
      setNewClient({
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

  useEffect(() => {
    if (authToken && userRole === 'admin') {
      fetchClients();
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
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Müşteri Listesi</h2>
              <p className="text-sm text-gray-600">Toplam {clients.length} müşteri</p>
            </div>
            <button
              onClick={() => setShowAddClient(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              ➕ Yeni Müşteri
            </button>
          </div>
        </div>

        {/* Clients Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Müşteriler yükleniyor...</p>
          </div>
        ) : clients.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-500">Henüz müşteri bulunmuyor. İlk müşterinizi ekleyin.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {clients.map((client) => (
              <div key={client.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {client.hotel_name}
                    </h3>
                    <p className="text-sm text-gray-600">{client.name}</p>
                  </div>
                  <div className="flex-shrink-0">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Aktif
                    </span>
                  </div>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="mr-2">📧</span>
                    {client.email || 'Email belirtilmemiş'}
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="mr-2">📞</span>
                    {client.phone || 'Telefon belirtilmemiş'}
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <span className="mr-2">📍</span>
                    {client.address || 'Adres belirtilmemiş'}
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => onNavigate('documents')}
                    className="flex-1 bg-blue-50 text-blue-600 px-3 py-2 rounded text-sm hover:bg-blue-100 transition-colors"
                  >
                    📄 Belgeleri
                  </button>
                  <button
                    onClick={() => onNavigate('consumption')}
                    className="flex-1 bg-green-50 text-green-600 px-3 py-2 rounded text-sm hover:bg-green-100 transition-colors"
                  >
                    ⚡ Tüketim
                  </button>
                </div>
              </div>
            ))}
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
                    value={newClient.name}
                    onChange={(e) => setNewClient({...newClient, name: e.target.value})}
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
                    value={newClient.hotel_name}
                    onChange={(e) => setNewClient({...newClient, hotel_name: e.target.value})}
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
                    value={newClient.email}
                    onChange={(e) => setNewClient({...newClient, email: e.target.value})}
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
                    value={newClient.phone}
                    onChange={(e) => setNewClient({...newClient, phone: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="Telefon numarası"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Adres
                  </label>
                  <textarea
                    value={newClient.address}
                    onChange={(e) => setNewClient({...newClient, address: e.target.value})}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    placeholder="Adres bilgisi"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={handleAddClient}
                  disabled={!newClient.name || !newClient.hotel_name}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Kaydet
                </button>
                <button
                  onClick={() => setShowAddClient(false)}
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

  const { authToken, userRole, dbUser } = useAuth();
  const API = getApiUrl();

  // Fetch clients for admin users
  const fetchClients = async () => {
    if (userRole !== 'admin') return;
    
    try {
      const response = await axios.get(`${API}/clients`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setClients(response.data || []);
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
      if (userRole === 'admin' && selectedClient) params.append('client_id', selectedClient);

      const response = await axios.get(`${API}/consumptions/analytics?${params}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setAnalyticsData(response.data);
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
    if (authToken && (userRole !== 'admin' || selectedClient)) {
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
            {/* Client Selection for Admin */}
            {userRole === 'admin' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Müşteri Seçin
                </label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Müşteri Seçin</option>
                  {clients.map(client => (
                    <option key={client.id} value={client.id}>
                      {client.hotel_name}
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
        // DEFRA F-Gases
        r134a_gas: parseFloat(consumptionData.r134a_gas) || 0,
        r600a_gas: parseFloat(consumptionData.r600a_gas) || 0,
        r410a_gas: parseFloat(consumptionData.r410a_gas) || 0,
        r32_gas: parseFloat(consumptionData.r32_gas) || 0,
        co2_fire: parseFloat(consumptionData.co2_fire) || 0,
        fm200_fire: parseFloat(consumptionData.fm200_fire) || 0,
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
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
            <div className="bg-gradient-to-r from-blue-600 to-green-600 text-white p-6 rounded-t-xl">
              <h3 className="text-xl font-bold">
                {editingConsumption ? 'Tüketim Verisini Düzenle' : 'Yeni Tüketim Verisi'}
              </h3>
            </div>
            
            <form className="p-6 overflow-y-auto flex-1 space-y-4">
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
    { id: 'carbon', name: 'Karbon Ayak İzi', icon: '🌍' },
    { id: 'waste-management', name: 'Atık Yönetimi', icon: '🗑️' },
    { id: 'guest-engagement', name: 'Guest Engagement', icon: '🎯' },
    { id: 'documents', name: 'Belge Yönetimi', icon: '📋' },
    { id: 'trainings', name: 'Eğitim Yönetimi', icon: '🎓' },
    { id: 'email', name: 'Email Yönetimi', icon: '📧' },
    { id: 'reports', name: 'Raporlar', icon: '📊' },
  ];

  const clientMenuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'consumption', name: 'Tüketim Takibi', icon: '⚡' },
    { id: 'analytics', name: 'Tüketim Analizi', icon: '📈' },
    { id: 'carbon', name: 'Karbon Ayak İzi', icon: '🌍' },
    { id: 'waste-management', name: 'Atık Yönetimi', icon: '🗑️' },
    { id: 'guest-engagement', name: 'Guest Engagement', icon: '🎯' },
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
            <span className="text-yellow-600 text-sm">🛡️</span>
            <p className="text-yellow-800 text-xs">
              <strong>Güvenlik:</strong> Bu kodu kimseyle paylaşmayın. Kod 5 dakika boyunca geçerlidir.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const MainApp = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedClient, setSelectedClient] = useState(null);
  const [showClientSetup, setShowClientSetup] = useState(false);
  const [show2FA, setShow2FA] = useState(true); // 2FA state - başlangıçta aktif
  const [twoFACompleted, setTwoFACompleted] = useState(false);
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

  // Show 2FA verification (ÖNCE 2FA, SONRA CLIENT SETUP)
  if (show2FA && !twoFACompleted) {
    return (
      <TwoFactorAuth 
        onVerificationComplete={() => {
          setTwoFACompleted(true);
          setShow2FA(false);
        }} 
      />
    );
  }

  // Show client setup form for new client users (2FA'DAN SONRA)
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
      case 'carbon':
        return <CarbonFootprint />;
      case 'guest-engagement':
        return <GuestEngagement />;
      case 'waste-management':
        return <WasteManagement />;
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