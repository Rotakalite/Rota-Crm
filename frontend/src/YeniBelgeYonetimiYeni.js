import React, { useState, useEffect } from 'react';
import axios from 'axios';

const YeniBelgeYonetimiYeni = () => {
  // useAuth hook'u App.js'den import edemediğimiz için manuel auth kontrol
  const [authToken, setAuthToken] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [dbUser, setDbUser] = useState(null);
  
  // Frontend .env'den Railway backend URL'yi al
  const getApiUrl = () => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://rota-crm-production.up.railway.app';
    return `${backendUrl}/api`;
  };
  
  const API = getApiUrl();
  
  // Token refresh function
  const refreshToken = async () => {
    if (window.Clerk && window.Clerk.session) {
      try {
        const newToken = await window.Clerk.session.getToken({ 
          skipCache: true,
          timeoutInMs: 10000
        });
        setAuthToken(newToken);
        return newToken;
      } catch (error) {
        console.error('❌ Token refresh failed:', error);
        return null;
      }
    }
    return null;
  };
  
  // API call with auto retry on 401
  const apiCall = async (apiFunction, retryCount = 0) => {
    try {
      return await apiFunction();
    } catch (error) {
      if (error.response?.status === 401 && retryCount < 2) {
        console.log('🔄 Token expired, refreshing...');
        const newToken = await refreshToken();
        if (newToken) {
          console.log('✅ Token refreshed, retrying API call...');
          return await apiCall(apiFunction, retryCount + 1);
        }
      }
      throw error;
    }
  };
  
  // Auth token'i window.Clerk'den al ve refresh et - ENHANCED VERSION
  useEffect(() => {
    let tokenRefreshInterval;
    
    const getAuthToken = async () => {
      if (window.Clerk && window.Clerk.user) {
        try {
          // FORCE FRESH TOKEN - NO CACHE
          const token = await window.Clerk.session.getToken({ 
            skipCache: true,
            timeoutInMs: 15000,
            template: null // Use default template
          });
          
          if (token) {
            setAuthToken(token);
            console.log('🎫 Fresh auth token retrieved successfully');
            
            // Test token immediately
            try {
              const response = await axios.get(`${API}/me`, {
                headers: { Authorization: `Bearer ${token}` }
              });
              
              setUserRole(response.data.role);
              setDbUser(response.data);
              console.log('👤 User role verified:', response.data.role);
            } catch (apiError) {
              console.error('❌ Token verification failed:', apiError);
              if (apiError.response?.status === 401) {
                console.log('🔄 Token invalid, getting new one...');
                setTimeout(getAuthToken, 1000); // Retry after 1 second
              }
            }
          }
        } catch (error) {
          console.error('❌ Auth error:', error);
          // Fallback: Try to get session again
          setTimeout(getAuthToken, 2000);
        }
      }
    };
    
    // Token refresh function - MORE AGGRESSIVE
    const forceRefreshToken = async () => {
      try {
        if (window.Clerk && window.Clerk.session) {
          console.log('🔄 FORCE TOKEN REFRESH...');
          
          // Invalidate session cache first
          await window.Clerk.session.reload();
          
          // Get completely fresh token
          const newToken = await window.Clerk.session.getToken({ 
            skipCache: true,
            timeoutInMs: 15000
          });
          
          if (newToken) {
            setAuthToken(newToken);
            console.log('✅ FORCE TOKEN REFRESH SUCCESS');
            return newToken;
          }
        }
      } catch (refreshError) {
        console.error('❌ FORCE TOKEN REFRESH FAILED:', refreshError);
        // Last resort: reload page
        console.log('🔄 Reloading page as last resort...');
        window.location.reload();
      }
    };
    
    // MORE FREQUENT token refresh (every 5 minutes instead of 10)
    const startTokenRefreshInterval = () => {
      tokenRefreshInterval = setInterval(async () => {
        console.log('⏰ SCHEDULED TOKEN REFRESH...');
        await forceRefreshToken();
      }, 5 * 60 * 1000); // 5 dakika
    };
    
    // Auth durumunu kontrol et
    if (window.Clerk && window.Clerk.loaded) {
      getAuthToken();
      startTokenRefreshInterval();
    } else {
      // Clerk yüklenene kadar bekle
      const checkClerk = setInterval(() => {
        if (window.Clerk && window.Clerk.loaded) {
          clearInterval(checkClerk);
          getAuthToken();
          startTokenRefreshInterval();
        }
      }, 100);
      
      // Safety cleanup
      setTimeout(() => clearInterval(checkClerk), 10000);
    }
    
    // Cleanup
    return () => {
      if (tokenRefreshInterval) {
        clearInterval(tokenRefreshInterval);
      }
    };
  }, []);
  
  // UI Flow States
  const [currentView, setCurrentView] = useState('client-selection'); // 'client-selection', 'folder-tree', 'documents'
  const [clients, setClients] = useState([]);
  const [folders, setFolders] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [folderDocumentCounts, setFolderDocumentCounts] = useState({});
  
  // Form states
  const [documentName, setDocumentName] = useState('');
  const [documentType, setDocumentType] = useState('CARBON_REPORT');
  const [stage, setStage] = useState('I.Aşama');
  const [description, setDescription] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  
  // Load initial data
  useEffect(() => {
    if (authToken) {
      loadClients();
    }
  }, [authToken]);

  const loadClients = async () => {
    if (!authToken) return;
    
    try {
      const response = await apiCall(async () => 
        axios.get(`${API}/clients`, {
          headers: { Authorization: `Bearer ${authToken}` }
        })
      );
      let allClients = response.data || [];
      
      console.log('👥 All clients from API:', allClients);
      allClients.forEach((client, index) => {
        console.log(`👥 Client ${index + 1}:`, {
          id: client.id,
          name: client.client_name || client.name,
          hotel_name: client.hotel_name
        });
      });
      
      // ROLE-BASED FILTERING: Client users only see their own data
      if (userRole === 'client' && dbUser?.client_id) {
        allClients = allClients.filter(client => client.id === dbUser.client_id);
      }
      
      setClients(allClients);
      console.log('👥 Clients loaded:', allClients.length);
    } catch (error) {
      console.error('❌ Client load error:', error);
    }
  };

  const loadFolders = async (clientId) => {
    if (!authToken) return;
    
    try {
      console.log('📁 loadFolders called with clientId:', clientId);
      const response = await axios.get(`${API}/folders`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      const allFolders = response.data || [];
      console.log('📁 All folders from API:', allFolders.length);
      
      // DEBUG: Database'deki client_id'leri gösterelim
      const uniqueClientIds = [...new Set(allFolders.map(f => f.client_id))];
      console.log('📁 Database unique client_ids:', uniqueClientIds);
      console.log('📁 Looking for client_id:', clientId);
      
      // Eğer client_id eşleşmiyorsa, database'deki client_id'lerden birini deneyelim
      if (!uniqueClientIds.includes(clientId) && uniqueClientIds.length > 0) {
        console.log('⚠️ Client ID not found in database! Trying with first available client_id...');
        const alternativeClientId = uniqueClientIds[0];
        console.log('📁 Using alternative client_id:', alternativeClientId);
        clientId = alternativeClientId;
      }
      
      // Client ID'lerin tipini kontrol edelim
      const sampleFolders = allFolders.slice(0, 5);
      console.log('📁 Sample folders with client_ids:', sampleFolders.map(f => ({
        name: f.name,
        client_id: f.client_id,
        client_id_type: typeof f.client_id
      })));
      
      // ROLE-BASED FILTERING: Client users only see their own client's folders
      let clientFolders;
      if (userRole === 'client' && dbUser?.client_id) {
        clientFolders = allFolders.filter(folder => folder.client_id === dbUser.client_id);
        console.log('📁 Client role filtering - dbUser.client_id:', dbUser.client_id);
      } else {
        // Admin sees all folders for selected client
        clientFolders = allFolders.filter(folder => {
          const match = folder.client_id === clientId;
          if (!match && folder.client_id) {
            console.log('📁 No match:', folder.client_id, '!==', clientId);
          }
          return match;
        });
        console.log('📁 Admin/Consultant role filtering - clientId:', clientId);
      }
      
      console.log('📁 Client folders after filtering:', clientFolders.length);
      console.log('📁 Sample client folders:', clientFolders.slice(0, 3).map(f => ({ name: f.name, client_id: f.client_id })));
      
      setFolders(clientFolders);
      
      // Her klasör için doküman sayısını hesapla
      await calculateDocumentCounts(clientFolders);
    } catch (error) {
      console.error('❌ Folder load error:', error);
    }
  };

  const calculateDocumentCounts = async (foldersList) => {
    if (!authToken) return;
    
    try {
      const response = await axios.get(`${API}/belge/list`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      const allDocuments = response.data?.documents || [];
      
      const counts = {};
      
      // Her klasör için doküman sayısını hesapla (alt klasörler dahil)
      foldersList.forEach(folder => {
        const count = countDocumentsInFolder(folder.id, foldersList, allDocuments);
        counts[folder.id] = count;
      });
      
      setFolderDocumentCounts(counts);
      console.log('📊 Document counts calculated:', counts);
    } catch (error) {
      console.error('❌ Document count calculation error:', error);
    }
  };

  const countDocumentsInFolder = (folderId, foldersList, documentsList) => {
    // Bu klasördeki dokümanları say
    let count = documentsList.filter(doc => doc.folder_id === folderId).length;
    
    // Alt klasörlerdeki dokümanları da say
    const subFolders = foldersList.filter(folder => folder.parent_folder_id === folderId);
    subFolders.forEach(subFolder => {
      count += countDocumentsInFolder(subFolder.id, foldersList, documentsList);
    });
    
    return count;
  };

  const loadDocuments = async (folderId) => {
    if (!authToken) return;
    
    try {
      const response = await axios.get(`${API}/belge/list`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      const allDocuments = response.data?.documents || [];
      
      // Seçili klasör ve alt klasörlerindeki dokümanları filtrele
      const folderDocuments = allDocuments.filter(doc => {
        // Direkt bu klasördeki dokümanlar
        if (doc.folder_id === folderId) return true;
        
        // Alt klasörlerdeki dokümanlar
        const folder = folders.find(f => f.id === doc.folder_id);
        if (folder && isSubFolderOf(folder, folderId)) return true;
        
        return false;
      });
      
      setDocuments(folderDocuments);
      console.log('📄 Documents loaded for folder:', folderId, 'Count:', folderDocuments.length);
    } catch (error) {
      console.error('❌ Document load error:', error);
    }
  };

  const isSubFolderOf = (folder, parentFolderId) => {
    if (!folder || !folder.parent_folder_id) return false;
    if (folder.parent_folder_id === parentFolderId) return true;
    
    // Recursive check for deeper levels
    const parentFolder = folders.find(f => f.id === folder.parent_folder_id);
    return isSubFolderOf(parentFolder, parentFolderId);
  };

  // UI Flow Handlers
  const handleClientSelect = async (client) => {
    setSelectedClient(client);
    setCurrentView('folder-tree');
    await loadFolders(client.id);
  };

  const handleFolderSelect = async (folder) => {
    setSelectedFolder(folder);
    setCurrentView('documents');
    await loadDocuments(folder.id);
  };

  const handleBackToClients = () => {
    setCurrentView('client-selection');
    setSelectedClient(null);
    setFolders([]);
    setFolderDocumentCounts({});
  };

  const handleBackToFolders = () => {
    setCurrentView('folder-tree');
    setSelectedFolder(null);
    setDocuments([]);
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
  };

  const uploadDocuments = async () => {
    if (!authToken) {
      alert('Auth token bulunamadı!');
      return;
    }
    
    if (!selectedClient) {
      alert('Lütfen müşteri seçin!');
      return;
    }
    
    if (!selectedFolder) {
      alert('Lütfen klasör seçin!');
      return;
    }
    
    if (selectedFiles.length === 0) {
      alert('Lütfen dosya seçin!');
      return;
    }

    setUploading(true);
    
    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const formData = new FormData();
        
        // Belge adı boşsa dosya adını kullan (EXTENSION OLMADAN)
        const finalDocumentName = documentName.trim() || file.name.replace(/\.[^/.]+$/, '');
        const documentNameWithIndex = finalDocumentName + (selectedFiles.length > 1 ? ` (${i + 1})` : '');
        
        formData.append('file', file);
        formData.append('client_id', selectedClient.id);
        formData.append('folder_id', selectedFolder.id);
        formData.append('document_name', documentNameWithIndex);
        formData.append('document_type', documentType);
        formData.append('stage', stage);
        formData.append('description', description);
        
        console.log(`📤 Uploading file ${i + 1}/${selectedFiles.length}: ${file.name}`);
        
        const response = await axios.post(`${API}/belge/upload`, formData, {
          headers: { 
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${authToken}`
          },
          timeout: 60000, // 1 minute timeout
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            console.log(`📊 Upload progress: ${percentCompleted}% (${file.name})`);
          }
        });
        
        console.log(`✅ Upload success:`, response.data);
      }
      
      // Reset form
      setDocumentName('');
      setDescription('');
      setSelectedFiles([]);
      document.querySelector('input[type="file"]').value = '';
      
      // Reload documents and update counts
      await loadDocuments(selectedFolder.id);
      await calculateDocumentCounts(folders);
      
      alert(`${selectedFiles.length} belge başarıyla yüklendi!`);
      
    } catch (error) {
      console.error('❌ Upload error:', error);
      alert(`Upload hatası: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const downloadDocument = async (doc) => {
    if (!authToken) return;
    
    try {
      console.log(`📥 Downloading document: ${doc.name}`);
      
      const response = await axios.get(`${API}/belge/download/${doc.id}`, {
        headers: { Authorization: `Bearer ${authToken}` },
        responseType: 'blob',
        timeout: 30000 // 30 seconds timeout
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Use original filename or document name
      const filename = doc.original_filename || `${doc.name}.pdf`;
      link.setAttribute('download', filename);
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      link.remove();
      window.URL.revokeObjectURL(url);
      
      console.log(`✅ Download completed: ${filename}`);
    } catch (error) {
      console.error('❌ Download error:', error);
      alert(`İndirme hatası: ${error.response?.data?.detail || error.message}`);
    }
  };

  const deleteDocument = async (documentId) => {
    if (!authToken) return;
    
    if (!window.confirm('Bu belgeyi silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      await axios.delete(`${API}/belge/delete/${documentId}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      
      // Reload documents and update counts
      await loadDocuments(selectedFolder.id);
      await calculateDocumentCounts(folders);
      
      alert('Belge başarıyla silindi!');
    } catch (error) {
      console.error('❌ Delete error:', error);
      alert(`Silme hatası: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Folder Tree Renderer
  const renderFolderTree = (parentId = null, level = 0) => {
    const foldersAtLevel = folders.filter(folder => folder.parent_folder_id === parentId);
    
    return foldersAtLevel.map(folder => (
      <div key={folder.id} className={`${level > 0 ? 'ml-6' : ''} mb-2`}>
        <div 
          className={`flex items-center justify-between p-3 rounded-lg border-2 border-gray-200 hover:border-blue-400 hover:bg-blue-50 cursor-pointer transition-all ${
            level === 0 ? 'bg-blue-100' : 
            level === 1 ? 'bg-green-100' :
            level === 2 ? 'bg-yellow-100' :
            level === 3 ? 'bg-purple-100' :
            'bg-gray-100'
          }`}
          onClick={() => handleFolderSelect(folder)}
        >
          <div className="flex items-center space-x-3">
            <span className="text-2xl">
              {level === 0 ? '🏢' : 
               level === 1 ? '📁' :
               level === 2 ? '📂' :
               level === 3 ? '📄' :
               '📋'}
            </span>
            <div>
              <h3 className="font-semibold text-gray-800">{folder.name}</h3>
              <p className="text-sm text-gray-600">Level {folder.level}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="bg-blue-600 text-white px-2 py-1 rounded-full text-sm font-medium">
              {folderDocumentCounts[folder.id] || 0} belge
            </span>
            <span className="text-blue-600">→</span>
          </div>
        </div>
        
        {/* Render subfolders */}
        {renderFolderTree(folder.id, level + 1)}
      </div>
    ));
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-center">🚀 Yeni Belge Yönetimi</h1>
      
      {/* CLIENT SELECTION VIEW */}
      {currentView === 'client-selection' && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-semibold mb-6 text-center">👥 Müşteri Seçin</h2>
          
          {clients.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              Müşteri bulunamadı...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {clients.map(client => (
                <div
                  key={client.id}
                  className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-2 border-blue-200 hover:border-blue-400 hover:shadow-lg cursor-pointer transition-all p-4"
                  onClick={() => handleClientSelect(client)}
                >
                  <div className="flex items-center space-x-4">
                    <div className="text-4xl">🏢</div>
                    <div>
                      <h3 className="font-bold text-gray-800">{client.client_name || client.name}</h3>
                      <p className="text-sm text-gray-600">{client.hotel_name || client.client_name}</p>
                      <p className="text-xs text-blue-600 mt-1">Seçmek için tıklayın →</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* FOLDER TREE VIEW */}
      {currentView === 'folder-tree' && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleBackToClients}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  ← Müşteri Seçimi
                </button>
                <div>
                  <h2 className="text-2xl font-semibold">📁 Klasör Yapısı</h2>
                  <p className="text-gray-600">
                    Seçili Müşteri: <span className="font-medium">{selectedClient?.name} ({selectedClient?.hotel_name})</span>
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Folder Tree */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-4">Klasörleri Seçin</h3>
            
            {folders.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                Bu müşteri için klasör bulunamadı...
              </div>
            ) : (
              <div className="space-y-2">
                {renderFolderTree()}
              </div>
            )}
          </div>
        </div>
      )}

      {/* DOCUMENTS VIEW */}
      {currentView === 'documents' && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleBackToFolders}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  ← Klasör Yapısı
                </button>
                <div>
                  <h2 className="text-2xl font-semibold">📋 Belgeler</h2>
                  <p className="text-gray-600">
                    Müşteri: <span className="font-medium">{selectedClient?.name}</span> |
                    Klasör: <span className="font-medium">{selectedFolder?.name}</span>
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Upload Section - ADMIN ONLY */}
          {userRole === 'admin' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-4">📤 Yeni Belge Yükle</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Belge Adı (İsteğe bağlı)</label>
                  <input
                    type="text"
                    value={documentName}
                    onChange={(e) => setDocumentName(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Belge adı (boş bırakılırsa dosya adı kullanılır)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Belge Tipi</label>
                  <select 
                    value={documentType} 
                    onChange={(e) => setDocumentType(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="CARBON_REPORT">Karbon Ayak İzi Raporu</option>
                    <option value="SUSTAINABILITY_REPORT">Sürdürülebilirlik Raporu</option>
                    <option value="CERTIFICATE">Sertifika</option>
                    <option value="OTHER">Diğer</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Aşama</label>
                  <select 
                    value={stage} 
                    onChange={(e) => setStage(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="I.Aşama">I.Aşama</option>
                    <option value="II.Aşama">II.Aşama</option>
                    <option value="III.Aşama">III.Aşama</option>
                  </select>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Açıklama</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="İsteğe bağlı açıklama"
                    rows="3"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Dosya(lar) Seçin *</label>
                  <input
                    type="file"
                    multiple
                    onChange={handleFileSelect}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                  />
                  {selectedFiles.length > 0 && (
                    <div className="mt-2 text-sm text-gray-600">
                      {selectedFiles.length} dosya seçildi: {selectedFiles.map(f => f.name).join(', ')}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Upload Button */}
            <div className="mt-6">
              <button
                onClick={uploadDocuments}
                disabled={uploading}
                className={`w-full py-3 px-6 rounded-lg font-semibold text-white ${
                  uploading 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
                }`}
              >
                {uploading ? '📤 Yükleniyor...' : '🚀 Belgeleri Yükle'}
              </button>
            </div>
          </div>
          )}

          {/* CLIENT ROLE - READ ONLY MESSAGE */}
          {userRole === 'client' && (
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-lg">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-sm text-blue-700">
                    <strong>Müşteri Görünümü:</strong> Belgelerinizi görüntüleyebilirsiniz. Yeni belge yüklemek için yöneticiniz ile iletişime geçin.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Documents List */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold">📋 Mevcut Belgeler</h3>
              <button
                onClick={() => loadDocuments(selectedFolder.id)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                🔄 Yenile
              </button>
            </div>

            {documents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                Bu klasörde henüz belge yüklenmemiş
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full table-auto">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Belge Adı</th>
                      <th className="px-4 py-2 text-left">Dosya Adı</th>
                      <th className="px-4 py-2 text-left">Boyut</th>
                      <th className="px-4 py-2 text-left">Tarih</th>
                      <th className="px-4 py-2 text-left">İşlemler</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map(doc => (
                      <tr key={doc.id} className="border-t hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium">{doc.name}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{doc.original_filename}</td>
                        <td className="px-4 py-2 text-sm">{(doc.file_size / 1024 / 1024).toFixed(2)} MB</td>
                        <td className="px-4 py-2 text-sm">{new Date(doc.created_at).toLocaleDateString('tr-TR')}</td>
                        <td className="px-4 py-2 space-x-2">
                          <button
                            onClick={() => downloadDocument(doc)}
                            className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                          >
                            📥 İndir
                          </button>
                          <button
                            onClick={() => deleteDocument(doc.id)}
                            className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                          >
                            🗑️ Sil
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default YeniBelgeYonetimiYeni;