import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { ClerkProvider, SignedIn, SignedOut, RedirectToSignIn, useUser, useClerk } from '@clerk/clerk-react';

const CLERK_PUBLISHABLE_KEY = process.env.REACT_APP_CLERK_PUBLISHABLE_KEY;
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

if (!CLERK_PUBLISHABLE_KEY) {
  throw new Error("Missing Publishable Key")
}

// Authentication Hook
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
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">🌿 Sürdürülebilir Turizm CRM</h1>
          <p className="text-sm text-gray-600">
            {userRole === 'admin' ? 'Admin Paneli' : 'Müşteri Paneli'}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="font-semibold text-gray-800">{user?.fullName || user?.firstName}</p>
            <p className="text-sm text-gray-600">{user?.primaryEmailAddress?.emailAddress}</p>
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

// Components
const Dashboard = ({ onNavigate }) => {
  const [stats, setStats] = useState(null);
  const [clients, setClients] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const { authToken, userRole, dbUser } = useAuth();

  useEffect(() => {
    if (authToken) {
      fetchStats();
      fetchClients();
      if (userRole === 'client' && dbUser?.client_id) {
        fetchDocuments();
      }
    }
  }, [authToken, userRole, dbUser]);


  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setDocuments(response.data);
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  };

  const handleViewDocument = (document) => {
    setSelectedDocument(document);
    setShowDocumentModal(true);
  };

  const handleDownloadDocument = async (document) => {
    try {
      console.log('🔍 Download request for document:', document.id);
      console.log('🔍 Auth token exists:', !!authToken);
      
      const response = await axios.get(`${API}/documents/${document.id}/download`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      console.log('✅ Download response:', response.data);
      
      const downloadUrl = response.data.download_url;
      if (downloadUrl && downloadUrl !== '#') {
        console.log('🚀 Opening download URL:', downloadUrl);
        // Open download URL in new tab
        window.open(downloadUrl, '_blank');
      } else {
        console.error('❌ No download URL in response');
        alert('Dosya indirme bağlantısı bulunamadı.');
      }
    } catch (error) {
      console.error("❌ Error downloading document:", error);
      alert('Dosya indirilirken hata oluştu: ' + (error.response?.data?.detail || 'Bilinmeyen hata'));
    }
  };

  const getFileIcon = (filePath) => {
    const extension = filePath.split('.').pop().toLowerCase();
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

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setClients(response.data);
    } catch (error) {
      console.error("Error fetching clients:", error);
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
                {userRole === 'admin' ? 'Toplam Müşteri' : 'Hesap Durumu'}
              </h3>
              <p className="text-3xl font-bold text-blue-900">{stats.total_clients}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
              <h3 className="text-lg font-semibold text-green-700">I. Aşama</h3>
              <p className="text-3xl font-bold text-green-900">{stats.stage_distribution.stage_1}</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg border-l-4 border-yellow-500">
              <h3 className="text-lg font-semibold text-yellow-700">II. Aşama</h3>
              <p className="text-3xl font-bold text-yellow-900">{stats.stage_distribution.stage_2}</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
              <h3 className="text-lg font-semibold text-purple-700">III. Aşama</h3>
              <p className="text-3xl font-bold text-purple-900">{stats.stage_distribution.stage_3}</p>
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
              {clients.slice(0, 5).map((client) => (
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
      {userRole === 'client' && clients.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            🌱 Karbon Ayak İzi Raporlarım
          </h3>
          
          {clients.map((client) => (
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
                  <span className="text-3xl mr-3">{getFileIcon(selectedDocument.file_path)}</span>
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
    if (authToken) {
      fetchClients();
    }
  }, [authToken]);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setClients(response.data);
    } catch (error) {
      console.error("Error fetching clients:", error);
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
              {clients.map((client) => (
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

const DocumentManagement = () => {
  const [documents, setDocuments] = useState([]);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [uploadData, setUploadData] = useState({
    client_id: '',
    name: '',
    document_type: 'Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)',
    stage: 'I.Aşama',
    files: []
  });
  const { authToken, userRole, dbUser } = useAuth();

  useEffect(() => {
    if (authToken) {
      fetchDocuments();
      if (userRole === 'admin') {
        fetchClients();
      }
    }
  }, [authToken, userRole]);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setDocuments(response.data);
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      setClients(response.data);
    } catch (error) {
      console.error("Error fetching clients:", error);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    
    if (!uploadData.files || uploadData.files.length === 0) {
      alert('Lütfen en az bir dosya seçin!');
      return;
    }

    try {
      const clientId = userRole === 'admin' ? uploadData.client_id : dbUser.client_id;
      
      // Upload each file separately using the new Google Cloud Storage API
      for (let i = 0; i < uploadData.files.length; i++) {
        const file = uploadData.files[i];
        const fileName = file.name;
        
        // Create FormData for multipart file upload
        const formData = new FormData();
        formData.append('file', file);
        formData.append('client_id', clientId);
        formData.append('document_name', uploadData.files.length === 1 ? uploadData.name : `${uploadData.name} - ${fileName}`);
        formData.append('document_type', uploadData.document_type);
        formData.append('stage', uploadData.stage);

        // Debug: Log the auth token
        console.log('🔍 Auth Token:', authToken ? authToken.substring(0, 50) + '...' : 'No token');
        console.log('🔍 Client ID:', clientId);
        console.log('🔍 Document Type:', uploadData.document_type);
        console.log('🔍 Stage:', uploadData.stage);
        console.log('🔍 File:', file.name, file.size, 'bytes');
        console.log('🔍 Document Type:', uploadData.document_type);
        console.log('🔍 Stage:', uploadData.stage);
        console.log('🔍 File:', file.name, file.size, 'bytes');

        // Upload to Google Cloud Storage via our new API
        const response = await axios.post(`${API}/upload-document`, formData, {
          headers: { 
            'Authorization': `Bearer ${authToken}`
            // Note: Don't set 'Content-Type': 'multipart/form-data' manually
            // Let axios set it automatically with proper boundary
          }
        });
        
        console.log(`File ${i + 1} uploaded successfully:`, response.data);
      }

      fetchDocuments();
      setShowUploadForm(false);
      setUploadData({
        client_id: '',
        name: '',
        document_type: 'Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)',
        stage: 'I.Aşama',
        files: []
      });
      
      alert(`${uploadData.files.length} dosya Google Cloud Storage'a başarıyla yüklendi! 🎉`);
    } catch (error) {
      console.error("Error uploading documents:", error);
      alert('Dosya yüklenirken hata oluştu: ' + (error.response?.data?.detail || 'Bilinmeyen hata'));
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

  const getFileIcon = (filePath) => {
    const extension = filePath.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return '📄';
      case 'doc':
      case 'docx': return '📝';
      case 'xls':
      case 'xlsx': return '📊';
      case 'zip':
      case 'rar': return '📦';
      case 'jpg':
      case 'jpeg':
      case 'png': return '🖼️';
      default: return '📎';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filterDocuments = () => {
    if (userRole === 'admin' && selectedClient) {
      return documents.filter(doc => doc.client_id === selectedClient);
    }
    return documents;
  };

  const getClientName = (clientId) => {
    const client = clients.find(c => c.id === clientId);
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
            {userRole === 'admin' ? 'Belge Yönetimi' : 'Belgelerim'}
          </h2>
          <button
            onClick={() => setShowUploadForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            {userRole === 'admin' ? 'Yeni Belge Yükle' : 'Belge Yükle'}
          </button>
        </div>

        {/* Admin Client Filter */}
        {userRole === 'admin' && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Müşteriye Göre Filtrele:
            </label>
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              className="w-full md:w-64 p-2 border border-gray-300 rounded-md"
            >
              <option value="">Tüm Müşteriler</option>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.hotel_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Documents Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
              <tr>
                <th className="px-6 py-3">Belge Adı</th>
                <th className="px-6 py-3">Tür</th>
                <th className="px-6 py-3">Aşama</th>
                {userRole === 'admin' && <th className="px-6 py-3">Müşteri</th>}
                <th className="px-6 py-3">Yüklenme Tarihi</th>
                <th className="px-6 py-3">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {filterDocuments().map((document) => (
                <tr key={document.id} className="bg-white border-b hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <span className="text-lg mr-2">{getFileIcon(document.file_path)}</span>
                      <span className="font-medium text-gray-900">{document.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                      {document.document_type}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      document.stage === 'I.Aşama' ? 'bg-green-100 text-green-800' :
                      document.stage === 'II.Aşama' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-purple-100 text-purple-800'
                    }`}>
                      {document.stage}
                    </span>
                  </td>
                  {userRole === 'admin' && (
                    <td className="px-6 py-4">{getClientName(document.client_id)}</td>
                  )}
                  <td className="px-6 py-4">
                    {new Date(document.created_at).toLocaleDateString('tr-TR')}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleViewDocument(document)}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        📋 Detay
                      </button>
                      <button
                        onClick={() => handleDownloadDocument(document)}
                        className="text-green-600 hover:text-green-900 font-medium"
                      >
                        📥 İndir
                      </button>
                      {userRole === 'admin' && (
                        <button
                          onClick={() => handleDelete(document.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          🗑️ Sil
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {filterDocuments().length === 0 && (
                <tr>
                  <td colSpan={userRole === 'admin' ? 6 : 5} className="px-6 py-8 text-center text-gray-500">
                    Henüz belge yüklenmemiş.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

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
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.hotel_name}
                      </option>
                    ))}
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
                <p className="text-xs text-blue-600 mt-1">
                  💡 Birden fazla dosya seçebilirsiniz (Ctrl+Click)
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

      {/* Document Detail Modal */}
      {showDocumentModal && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-90vh overflow-y-auto">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 rounded-t-xl">
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <span className="text-3xl mr-3">{getFileIcon(selectedDocument.file_path)}</span>
                  <div>
                    <h3 className="text-xl font-bold">Belge Detayları</h3>
                    <p className="text-blue-100 text-sm">{selectedDocument.name}</p>
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
                <div className="bg-gray-50 p-4 rounded-lg border-l-4 border-blue-500">
                  <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                    Belge Türü
                  </label>
                  <p className="text-sm font-medium text-gray-900">{selectedDocument.document_type}</p>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg border-l-4 border-green-500">
                  <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
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
                <div className="bg-gray-50 p-4 rounded-lg border-l-4 border-orange-500">
                  <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                    Dosya Boyutu
                  </label>
                  <p className="text-lg font-bold text-gray-900">{formatFileSize(selectedDocument.file_size)}</p>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg border-l-4 border-purple-500">
                  <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                    Yüklenme Tarihi
                  </label>
                  <p className="text-sm font-medium text-gray-900">
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

              {userRole === 'admin' && (
                <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                  <label className="block text-xs font-semibold text-blue-700 uppercase tracking-wide mb-1">
                    İlgili Müşteri
                  </label>
                  <p className="text-sm font-medium text-blue-900">{getClientName(selectedDocument.client_id)}</p>
                </div>
              )}

              {/* File Path Info */}
              <div className="bg-gray-100 p-4 rounded-lg">
                <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                  Dosya Bilgileri
                </label>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Dosya Adı:</span>
                    <span className="text-sm font-medium text-gray-900 bg-white px-2 py-1 rounded">
                      {selectedDocument.file_path.split('/').pop()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Klasör:</span>
                    <span className="text-sm font-medium text-gray-900 bg-white px-2 py-1 rounded">
                      📁 {selectedDocument.stage}
                    </span>
                  </div>
                </div>
              </div>

              {/* Status Note */}
              <div className="bg-gradient-to-r from-green-50 to-blue-50 border-l-4 border-green-400 p-4 rounded-lg">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <span className="text-2xl">☁️</span>
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-semibold text-green-800 mb-1">
                      Belge Durumu
                    </h4>
                    <p className="text-sm text-green-700">
                      Belge başarıyla <strong>Google Cloud Storage</strong>'a yüklenmiştir. 
                      Aşağıdaki "İndir" butonuna tıklayarak dosyayı görüntüleyebilirsiniz.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex justify-between items-center">
              <div className="flex items-center text-sm text-gray-500">
                <span className="mr-2">📅</span>
                Son güncelleme: {new Date(selectedDocument.created_at).toLocaleDateString('tr-TR')}
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => handleDownloadDocument(selectedDocument)}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-all transform hover:scale-105 shadow-md"
                >
                  📥 İndir
                </button>
                {userRole === 'admin' && (
                  <button
                    onClick={() => {
                      if (window.confirm('Bu belgeyi kalıcı olarak silmek istediğinizden emin misiniz?')) {
                        handleDelete(selectedDocument.id);
                        setShowDocumentModal(false);
                      }
                    }}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-all transform hover:scale-105 shadow-md"
                  >
                    🗑️ Belgeyi Sil
                  </button>
                )}
                <button
                  onClick={() => setShowDocumentModal(false)}
                  className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-all transform hover:scale-105 shadow-md"
                >
                  ✕ Kapat
                </button>
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

  const handleViewDocument = (document) => {
    setSelectedDocument(document);
    setShowDocumentModal(true);
  };

  const getFileIcon = (filePath) => {
    const extension = filePath.split('.').pop().toLowerCase();
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

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
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
              {trainings.map((training) => (
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
            {documents.map((doc) => (
              <div key={doc.id} className="bg-white p-3 rounded border hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <span className="text-lg mr-2">{getFileIcon(doc.file_path)}</span>
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
    { id: 'documents', name: 'Belge Yönetimi', icon: '📋' },
    { id: 'reports', name: 'Raporlar', icon: '📈' }
  ];

  const clientMenuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'documents', name: 'Belgelerim', icon: '📋' },
    { id: 'trainings', name: 'Eğitimlerim', icon: '🎓' }
  ];

  const menuItems = userRole === 'admin' ? adminMenuItems : clientMenuItems;

  return (
    <div className="bg-gray-800 text-white w-64 min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold">🌿 Sürdürülebilir Turizm CRM</h1>
        <p className="text-sm text-gray-300">
          {userRole === 'admin' ? 'Admin Paneli' : 'Müşteri Paneli'}
        </p>
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
      case 'project':
        return <ProjectManagement client={selectedClient} onNavigate={handleNavigate} />;
      case 'documents':
        return <DocumentManagement />;
      case 'reports':
        return (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Raporlar</h2>
            <p className="text-gray-600">Yakında eklenecek...</p>
          </div>
        );
      case 'trainings':
        return (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Eğitimlerim</h2>
            <p className="text-gray-600">Yakında eklenecek...</p>
          </div>
        );
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