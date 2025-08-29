import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useIsMobile } from './MobileComponents';

const YeniBelgeYonetimiYeni = ({ selectedClient: propSelectedClient }) => {
  const isMobile = useIsMobile();
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
  const [documentType, setDocumentType] = useState('PROCEDURE');
  const [stage, setStage] = useState('I.Aşama');
  const [description, setDescription] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [showBulkFolderUpload, setShowBulkFolderUpload] = useState(false);
  
  // Bulk folder upload states
  const [selectedBulkFolder, setSelectedBulkFolder] = useState(null);
  const [folderAnalysis, setFolderAnalysis] = useState(null);
  const [folderMapping, setFolderMapping] = useState({});
  const [bulkUploading, setBulkUploading] = useState(false);
  const [systemFolders, setSystemFolders] = useState([]);
  
  // Load initial data
  useEffect(() => {
    if (authToken) {
      loadClients();
    }
  }, [authToken]);

  // Auto-select client for CLIENT role users
  useEffect(() => {
    if (userRole === 'client' && dbUser?.client_id && !selectedClient) {
      // Find the client in clients array
      const clientObj = clients.find(c => c.id === dbUser.client_id);
      if (clientObj) {
        setSelectedClient(clientObj);
        console.log('🔄 Auto-selected client for CLIENT user:', clientObj);
      }
    }
  }, [userRole, dbUser, clients]);

  const loadClients = async () => {
    if (!authToken) return;
    
    try {
      const response = await apiCall(async () => 
        axios.get(`${API}/clients`, {
          params: { client_type: "registered" }, // Only registered clients
          headers: { Authorization: `Bearer ${authToken}` }
        })
      );
      let allClients = response.data.clients || [];
      
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
    
    // Admin/consultant için client seçimi zorunlu
    if ((userRole === 'admin' || userRole === 'consultant') && !selectedClient) {
      alert('Lütfen müşteri seçin!');
      return;
    }
    
    // Client kullanıcılar için folder zorunlu
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
        
        // Client ID - Admin/consultant için selectedClient, client için otomatik
        if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
          formData.append('client_id', selectedClient.id);
        } else if (userRole === 'client' && dbUser?.client_id) {
          formData.append('client_id', dbUser.client_id);
        } else if (userRole === 'client' && selectedClient) {
          formData.append('client_id', selectedClient.id);
        }
        
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

  const bulkDownloadDocuments = async () => {
    if (!authToken) return;
    
    try {
      console.log('📦 Starting bulk download...');
      
      // Show loading state
      const loadingMsg = document.createElement('div');
      loadingMsg.innerHTML = '📦 ZIP dosyası hazırlanıyor, lütfen bekleyin...';
      loadingMsg.style.cssText = 'position:fixed;top:20px;right:20px;background:#059669;color:white;padding:15px;border-radius:8px;z-index:9999;';
      document.body.appendChild(loadingMsg);
      
      // Build URL with parameters
      let url = `${API}/documents/bulk-download`;
      const params = new URLSearchParams();
      
      // Add client_id for admin/consultant users
      if (userRole === 'admin' || userRole === 'consultant' || userRole === 'ADMIN' || userRole === 'CONSULTANT') {
        console.log('🔍 ZIP DOWNLOAD DEBUG - userRole:', userRole, 'selectedClient:', selectedClient?.id);
        if (selectedClient) {
          params.append('client_id', selectedClient.id);
          console.log('✅ client_id added to params:', selectedClient.id);
        } else {
          console.log('❌ No selectedClient found');
          alert('Lütfen bir müşteri seçin');
          document.body.removeChild(loadingMsg);
          return;
        }
      } else {
        console.log('🔍 ZIP DOWNLOAD DEBUG - CLIENT role, userRole:', userRole);
      }
      
      // Note: folder_id parametresi kaldırıldı - tüm klasörler indirilecek
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${authToken}` },
        responseType: 'blob',
        timeout: 120000 // 2 minutes timeout for ZIP creation
      });
      
      // Remove loading message
      document.body.removeChild(loadingMsg);
      
      // Create download link
      const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      // Generate filename
      const clientName = selectedClient?.hotel_name || selectedClient?.name || 'Belgeler';
      const safeName = clientName.replace(/[<>:"/\\|?*]/g, '_');
      const timestamp = new Date().toISOString().slice(0, 16).replace(/[-:]/g, '');
      const filename = `${safeName}_belgeler_${timestamp}.zip`;
      
      link.setAttribute('download', filename);
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
      console.log('✅ Bulk download completed');
      
      // Show success message
      const successMsg = document.createElement('div');
      successMsg.innerHTML = '✅ ZIP dosyası başarıyla indirildi!';
      successMsg.style.cssText = 'position:fixed;top:20px;right:20px;background:#10b981;color:white;padding:15px;border-radius:8px;z-index:9999;';
      document.body.appendChild(successMsg);
      setTimeout(() => {
        if (document.body.contains(successMsg)) {
          document.body.removeChild(successMsg);
        }
      }, 3000);
      
    } catch (error) {
      console.error('❌ Bulk download error:', error);
      
      // Remove loading message if still present
      const loadingMsg = document.querySelector('div[style*="ZIP dosyası hazırlanıyor"]');
      if (loadingMsg) {
        document.body.removeChild(loadingMsg);
      }
      
      let errorMsg = 'Toplu indirme hatası';
      if (error.response?.status === 404) {
        errorMsg = 'İndirilecek belge bulunamadı';
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      }
      
      alert(errorMsg);
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

  // Analyze folder structure for bulk upload
  const analyzeFolderStructure = (files) => {
    const folderMap = {};
    const supportedExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.png', '.jpg', '.jpeg'];
    
    // Filter files by supported extensions
    const validFiles = files.filter(file => {
      const extension = '.' + file.name.split('.').pop().toLowerCase();
      return supportedExtensions.includes(extension);
    });
    
    // Group files by folder path
    validFiles.forEach(file => {
      const path = file.webkitRelativePath || file.name;
      const pathParts = path.split('/');
      
      if (pathParts.length > 1) {
        // Get folder path (everything except the file name)
        const folderPath = pathParts.slice(0, -1).join('/');
        
        if (!folderMap[folderPath]) {
          folderMap[folderPath] = {
            path: folderPath,
            files: [],
            fileCount: 0
          };
        }
        
        folderMap[folderPath].files.push(file);
        folderMap[folderPath].fileCount++;
      }
    });
    
    const folders = Object.values(folderMap);
    
    // 🤖 OTOMATIK EŞLEŞTİRME - Klasör isimlerini analiz et
    const autoMapping = generateAutoMapping(folders);
    
    return {
      totalFiles: validFiles.length,
      folders: folders,
      validFiles: validFiles,
      autoMapping: autoMapping
    };
  };

  // 🤖 Otomatik klasör eşleştirme algoritması
  const generateAutoMapping = (folders) => {
    const mapping = {};
    
    // Eşleştirme pattern'leri ve keyword'leri - LEVEL 1-4 COMPLETE
    const patterns = {
      // LEVEL 1 - Ana Sütunlar
      'A_SUTUNU': [
        'a', 'a_', 'a-', 'a sütunu', 'a sutunu', 'a_sutunu', 'a_belge', 'a_belgeler', 'a_dosya', 'a_dosyalar',
        'politika', 'politikalar', 'policy', 'policies', 'strateji', 'strategy', 'yönetmelik', 'regulation',
        'kurallar', 'rules', 'standart', 'standard', 'kalite', 'quality', 'iso', 'belge_a', 'document_a'
      ],
      'B_SUTUNU': [
        'b', 'b_', 'b-', 'b sütunu', 'b sutunu', 'b_sutunu', 'b_belge', 'b_belgeler', 'b_dosya', 'b_dosyalar', 
        'talimat', 'talimatlar', 'instruction', 'instructions', 'prosedür', 'prosedur', 'procedure', 'procedures',
        'is_talimati', 'iş_talimatı', 'work_instruction', 'operasyon', 'operation', 'belge_b', 'document_b'
      ],
      'C_SUTUNU': [
        'c', 'c_', 'c-', 'c sütunu', 'c sutunu', 'c_sutunu', 'c_belge', 'c_belgeler', 'c_dosya', 'c_dosyalar',
        'form', 'formlar', 'forms', 'liste', 'listeler', 'list', 'lists', 'kontrol', 'control', 'check',
        'kayit', 'kayıt', 'kayitlar', 'kayıtlar', 'record', 'records', 'belge_c', 'document_c'
      ],
      'D_SUTUNU': [
        'd', 'd_', 'd-', 'd sütunu', 'd sutunu', 'd_sutunu', 'd_belge', 'd_belgeler', 'd_dosya', 'd_dosyalar',
        'sertifika', 'sertifikalar', 'certificate', 'certificates', 'onay', 'onaylar', 'approval', 'approvals',
        'lisans', 'lisanslar', 'license', 'licenses', 'yetki', 'authority', 'belge_d', 'document_d'
      ],
      
      // LEVEL 2 - A Sütunu Alt Klasörleri
      'A1': [
        'a1', 'a_1', 'a-1', 'a 1', 'politika_1', 'politika1', 'genel_politika', 'genel', 'ana_politika'
      ],
      'A2': [
        'a2', 'a_2', 'a-2', 'a 2', 'politika_2', 'politika2', 'kalite_politika', 'kalite', 'quality_policy'
      ],
      'A3': [
        'a3', 'a_3', 'a-3', 'a 3', 'politika_3', 'politika3', 'cevre_politika', 'çevre', 'environment'
      ],
      'A4': [
        'a4', 'a_4', 'a-4', 'a 4', 'politika_4', 'politika4', 'is_sagligi', 'iş_sağlığı', 'occupational'
      ],
      'A5': [
        'a5', 'a_5', 'a-5', 'a 5', 'politika_5', 'politika5', 'guvenlik_politika', 'güvenlik', 'safety'
      ],
      'A7.1': [
        'a7_1', 'a7.1', 'a-7-1', 'a 7 1', 'a71', 'yasal_gereklilik', 'yasal', 'legal', 'requirement'
      ],
      'A7.2': [
        'a7_2', 'a7.2', 'a-7-2', 'a 7 2', 'a72', 'mevzuat', 'kanun', 'law', 'regulation'
      ],
      'A7.3': [
        'a7_3', 'a7.3', 'a-7-3', 'a 7 3', 'a73', 'standart_gereklilik', 'standard_requirement'
      ],
      'A7.4': [
        'a7_4', 'a7.4', 'a-7-4', 'a 7 4', 'a74', 'diger_gereklilik', 'diğer', 'other_requirement'
      ],
      'A8': [
        'a8', 'a_8', 'a-8', 'a 8', 'politika_8', 'politika8', 'sosyal_politika', 'sosyal', 'social'
      ],
      'A9': [
        'a9', 'a_9', 'a-9', 'a 9', 'politika_9', 'politika9', 'etik', 'ethics', 'etik_kod'
      ],
      'A10': [
        'a10', 'a_10', 'a-10', 'a 10', 'politika_10', 'politika10', 'surdurulebilirlik', 'sustainability'
      ],
      
      // LEVEL 2 - B Sütunu Alt Klasörleri  
      'B1': [
        'b1', 'b_1', 'b-1', 'b 1', 'prosedur_1', 'prosedur1', 'genel_prosedur', 'main_procedure'
      ],
      'B2': [
        'b2', 'b_2', 'b-2', 'b 2', 'prosedur_2', 'prosedur2', 'kalite_prosedur', 'quality_procedure'
      ],
      'B3': [
        'b3', 'b_3', 'b-3', 'b 3', 'prosedur_3', 'prosedur3', 'cevre_prosedur', 'environment_procedure'
      ],
      'B4': [
        'b4', 'b_4', 'b-4', 'b 4', 'prosedur_4', 'prosedur4', 'is_sagligi_prosedur', 'ohs_procedure'
      ],
      'B5': [
        'b5', 'b_5', 'b-5', 'b 5', 'prosedur_5', 'prosedur5', 'guvenlik_prosedur', 'safety_procedure'
      ],
      'B6': [
        'b6', 'b_6', 'b-6', 'b 6', 'prosedur_6', 'prosedur6', 'bilgi_guvenlik', 'information_security'
      ],
      'B7': [
        'b7', 'b_7', 'b-7', 'b 7', 'prosedur_7', 'prosedur7', 'insan_kaynak', 'human_resources'
      ],
      'B8': [
        'b8', 'b_8', 'b-8', 'b 8', 'prosedur_8', 'prosedur8', 'mali_isler', 'financial'
      ],
      'B9': [
        'b9', 'b_9', 'b-9', 'b 9', 'prosedur_9', 'prosedur9', 'operasyonel', 'operational'
      ],
      
      // LEVEL 2 - C Sütunu Alt Klasörleri
      'C1': [
        'c1', 'c_1', 'c-1', 'c 1', 'form_1', 'form1', 'genel_form', 'general_form'
      ],
      'C2': [
        'c2', 'c_2', 'c-2', 'c 2', 'form_2', 'form2', 'kalite_form', 'quality_form'
      ],
      'C3': [
        'c3', 'c_3', 'c-3', 'c 3', 'form_3', 'form3', 'cevre_form', 'environment_form'
      ],
      'C4': [
        'c4', 'c_4', 'c-4', 'c 4', 'form_4', 'form4', 'is_sagligi_form', 'ohs_form'
      ],
      
      // LEVEL 2 - D Sütunu Ana Klasörleri
      'D1': [
        'd1', 'd_1', 'd-1', 'd 1', 'sertifika_1', 'sertifika1', 'kalite_sertifika', 'quality_certificate'
      ],
      'D2': [
        'd2', 'd_2', 'd-2', 'd 2', 'sertifika_2', 'sertifika2', 'cevre_sertifika', 'environment_certificate'
      ],
      'D3': [
        'd3', 'd_3', 'd-3', 'd 3', 'sertifika_3', 'sertifika3', 'is_sagligi_sertifika', 'ohs_certificate'
      ],
      
      // LEVEL 3 - D1 Alt Klasörleri
      'D1.1': [
        'd1_1', 'd1.1', 'd-1-1', 'd 1 1', 'd11', 'iso_9001', 'iso9001', 'kalite_yonetim'
      ],
      'D1.2': [
        'd1_2', 'd1.2', 'd-1-2', 'd 1 2', 'd12', 'ts_en_iso', 'kalite_standart'
      ],
      'D1.3': [
        'd1_3', 'd1.3', 'd-1-3', 'd 1 3', 'd13', 'kalite_belge', 'quality_document'
      ],
      'D1.4': [
        'd1_4', 'd1.4', 'd-1-4', 'd 1 4', 'd14', 'kalite_onay', 'quality_approval'
      ],
      
      // LEVEL 3 - D2 Alt Klasörleri
      'D2.1': [
        'd2_1', 'd2.1', 'd-2-1', 'd 2 1', 'd21', 'iso_14001', 'iso14001', 'cevre_yonetim'
      ],
      'D2.2': [
        'd2_2', 'd2.2', 'd-2-2', 'd 2 2', 'd22', 'cevre_izin', 'environment_permit'
      ],
      'D2.3': [
        'd2_3', 'd2.3', 'd-2-3', 'd 2 3', 'd23', 'atik_lisans', 'waste_license'
      ],
      'D2.4': [
        'd2_4', 'd2.4', 'd-2-4', 'd 2 4', 'd24', 'emisyon_rapor', 'emission_report'
      ],
      'D2.5': [
        'd2_5', 'd2.5', 'd-2-5', 'd 2 5', 'd25', 'cevre_etki', 'environmental_impact'
      ],
      'D2.6': [
        'd2_6', 'd2.6', 'd-2-6', 'd 2 6', 'd26', 'cevre_denetim', 'environmental_audit'
      ],
      
      // LEVEL 3 - D3 Alt Klasörleri
      'D3.1': [
        'd3_1', 'd3.1', 'd-3-1', 'd 3 1', 'd31', 'iso_45001', 'iso45001', 'is_sagligi_yonetim'
      ],
      'D3.2': [
        'd3_2', 'd3.2', 'd-3-2', 'd 3 2', 'd32', 'is_sagligi_rapor', 'ohs_report'
      ],
      'D3.3': [
        'd3_3', 'd3.3', 'd-3-3', 'd 3 3', 'd33', 'risk_degerlendirme', 'risk_assessment'
      ],
      'D3.4': [
        'd3_4', 'd3.4', 'd-3-4', 'd 3 4', 'd34', 'acil_durum', 'emergency'
      ],
      'D3.5': [
        'd3_5', 'd3.5', 'd-3-5', 'd 3 5', 'd35', 'egitim_kayit', 'training_record'
      ],
      'D3.6': [
        'd3_6', 'd3.6', 'd-3-6', 'd 3 6', 'd36', 'saglik_rapor', 'health_report'
      ],
      
      // LEVEL 4 - TÜRKÇE BELGE TÜRLERİ - GERÇEK SİSTEM KLASÖR İSİMLERİ
      'POLİTİKALAR': [
        'politikalar', 'politika', 'policies', 'policy', 'politic', 'politics'
      ],
      'PROSEDÜRLER': [
        'prosedurler', 'prosedür', 'prosedur', 'procedures', 'procedure', 'proc'
      ],
      'KAYITLAR': [
        'kayitlar', 'kayıtlar', 'kayit', 'kayıt', 'records', 'record', 'kayıtları'
      ],
      'FORMLAR': [
        'formlar', 'form', 'forms', 'format', 'formları'
      ],
      'LİSTELER': [
        'listeler', 'liste', 'lists', 'list', 'listing', 'listeleri'
      ],
      'TALİMATLAR': [
        'talimatlar', 'talimat', 'instructions', 'instruction', 'talimatları'
      ],
      'BELGELERİ': [
        'belgeleri', 'belge', 'belgeler', 'documents', 'document', 'doc'
      ],
      'ŞEMALARı': [
        'şemaları', 'şema', 'şemalar', 'schemas', 'schema', 'diagram'
      ],
      'RESİMLER': [
        'resimler', 'resim', 'images', 'image', 'img', 'picture', 'photo'
      ],
      'RAPORLAR': [
        'raporlar', 'rapor', 'reports', 'report', 'rpt'
      ]
    };
    
    folders.forEach(folder => {
      const folderName = folder.path.toLowerCase()
        .replace(/[çÇ]/g, 'c')
        .replace(/[ğĞ]/g, 'g') 
        .replace(/[ıİ]/g, 'i')
        .replace(/[öÖ]/g, 'o')
        .replace(/[şŞ]/g, 's')
        .replace(/[üÜ]/g, 'u')
        .replace(/[^a-z0-9]/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_|_$/g, '');
      
      let bestMatch = null;
      let bestScore = 0;
      
      // Her sistem klasörü için benzerlik skoru hesapla
      Object.keys(patterns).forEach(systemFolder => {
        const keywords = patterns[systemFolder];
        let score = 0;
        
        keywords.forEach(keyword => {
          // Tam eşleşme - yüksek skor
          if (folderName === keyword) {
            score += 100;
          }
          // İçerik eşleşmesi - orta skor  
          else if (folderName.includes(keyword) || keyword.includes(folderName)) {
            score += 50;
          }
          // Başlangıç eşleşmesi - düşük skor
          else if (folderName.startsWith(keyword) || keyword.startsWith(folderName)) {
            score += 25;
          }
        });
        
        if (score > bestScore) {
          bestScore = score;
          bestMatch = systemFolder;
        }
      });
      
      // Minimum güven skoru kontrolü
      if (bestScore >= 25) {
        mapping[folder.path] = bestMatch;
      }
    });
    
    return mapping;
  };

  // Document viewer function - SIMPLE: Open in new tab
  const viewDocument = async (document) => {
    try {
      const viewUrl = `${API}/documents/view/${document.id}`;
      
      // ÇÖZÜM: PDF'ler için özel URL parametresi ekle
      const isPDF = document.document_name && document.document_name.toLowerCase().endsWith('.pdf');
      
      if (isPDF) {
        // PDF'ler için #toolbar=0 parametresi ekleyerek browser'ın built-in viewer'ını kullan
        const pdfViewUrl = `${viewUrl}#toolbar=0&navpanes=0&scrollbar=0`;
        window.open(pdfViewUrl, '_blank', 'toolbar=no,scrollbars=yes,resizable=yes,width=800,height=600');
      } else {
        // Diğer dosyalar için normal açım (indirecek)
        window.open(viewUrl, '_blank');
      }
      
      console.log('📄 Viewing document:', document.document_name, 'Type:', isPDF ? 'PDF (embedded)' : 'Other');
    } catch (error) {
      console.error('Error opening document:', error);
      alert('Belge açılırken hata oluştu: ' + error.message);
    }
  };

  // Bulk folder upload function - WITH CHUNKING TO PREVENT TIMEOUT
  const processBulkFolderUpload = async () => {
    if (!folderAnalysis || !selectedBulkFolder) {
      alert('Klasör analizi bulunamadı!');
      return;
    }
    
    // Check if all folders are mapped
    const unmappedFolders = folderAnalysis.folders.filter(folder => !folderMapping[folder.path]);
    if (unmappedFolders.length > 0) {
      alert(`Lütfen tüm klasörleri eşleştirin!\nEşleştirilmemiş: ${unmappedFolders.map(f => f.path).join(', ')}`);
      return;
    }
    
    setBulkUploading(true);
    
    try {
      const CHUNK_SIZE = 10; // Process 10 files at a time to prevent timeout
      const totalFiles = selectedBulkFolder.length;
      let uploadedCount = 0;
      let successCount = 0;
      let errorCount = 0;
      const allErrors = [];
      
      // Get fresh token once
      let currentToken = authToken;
      if (window.Clerk && window.Clerk.session) {
        try {
          const freshToken = await window.Clerk.session.getToken({ skipCache: true });
          if (freshToken) {
            currentToken = freshToken;
          }
        } catch (tokenError) {
          console.error('Failed to get fresh token:', tokenError);
        }
      }
      
      // Process files in chunks
      for (let i = 0; i < totalFiles; i += CHUNK_SIZE) {
        const chunk = selectedBulkFolder.slice(i, i + CHUNK_SIZE);
        
        try {
          // Prepare FormData for this chunk
          const formData = new FormData();
          
          // Add folder mapping as JSON string
          formData.append('folder_mapping', JSON.stringify(folderMapping));
          
          // Add client_id for admin/consultant users
          if ((userRole === 'admin' || userRole === 'consultant') && selectedClient) {
            formData.append('client_id', selectedClient.id);
          }
          
          // Add files from this chunk
          chunk.forEach((file) => {
            const relativePath = file.webkitRelativePath || file.name;
            const pathParts = relativePath.split('/');
            
            if (pathParts.length > 1) {
              const folderPath = pathParts.slice(0, -1).join('/');
              const key = `file_${folderPath}/${file.name}`;
              formData.append(key, file);
            }
          });
          
          // Send chunk to backend with extended timeout
          const response = await axios.post(`${API}/documents/bulk`, formData, {
            headers: { 
              'Authorization': `Bearer ${currentToken}`,
              'Content-Type': 'multipart/form-data'
            },
            timeout: 300000, // 5 minutes timeout per chunk
            onUploadProgress: (progressEvent) => {
              const chunkProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              console.log(`Chunk ${Math.floor(i/CHUNK_SIZE) + 1} progress: ${chunkProgress}%`);
            }
          });
          
          const result = response.data;
          successCount += result.success_count || 0;
          errorCount += result.failed_count || 0;
          
          if (result.errors && result.errors.length > 0) {
            allErrors.push(...result.errors);
          }
          
          uploadedCount += chunk.length;
          
          // Update progress
          const overallProgress = Math.round((uploadedCount / totalFiles) * 100);
          console.log(`📁 Overall progress: ${overallProgress}% (${uploadedCount}/${totalFiles} files)`);
          
          // Short delay between chunks to prevent overwhelming server
          if (i + CHUNK_SIZE < totalFiles) {
            await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
          }
          
        } catch (chunkError) {
          console.error(`❌ Chunk ${Math.floor(i/CHUNK_SIZE) + 1} error:`, chunkError);
          errorCount += chunk.length;
          allErrors.push(`Chunk ${Math.floor(i/CHUNK_SIZE) + 1}: ${chunkError.message || chunkError}`);
        }
      }
      
      // Show comprehensive results
      const successRate = totalFiles > 0 ? Math.round((successCount / totalFiles) * 100) : 0;
      let resultMessage = `✅ Toplu belge yükleme tamamlandı!\n\n`;
      resultMessage += `📊 Özet:\n`;
      resultMessage += `• Toplam dosya: ${totalFiles}\n`;
      resultMessage += `• Başarılı: ${successCount}\n`;
      resultMessage += `• Başarısız: ${errorCount}\n`;
      resultMessage += `• Başarı oranı: ${successRate}%\n`;
      
      if (allErrors.length > 0) {
        resultMessage += `\n❌ Hatalar (ilk 5):\n`;
        resultMessage += allErrors.slice(0, 5).join('\n');
      }
      
      alert(resultMessage);
      
      // Reset states and close modal
      setShowBulkFolderUpload(false);
      setSelectedBulkFolder(null);
      setFolderAnalysis(null);
      setFolderMapping({});
      
      // Reload documents and folders
      await loadFolders();
      if (selectedFolder) {
        await loadDocuments(selectedFolder.id);
      }
      
    } catch (error) {
      console.error('❌ Bulk folder upload error:', error);
      alert('Toplu klasör yükleme hatası: ' + (error.response?.data?.detail || error.message));
    } finally {
      setBulkUploading(false);
    }
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
            <div className={`grid gap-4 ${isMobile ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'}`}>
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
              
              {/* ZIP Download Button - Klasör Yapısı Sayfasında */}
              <div className="flex items-center space-x-3">
                <button
                  onClick={bulkDownloadDocuments}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                  title="Tüm belgeleri klasör yapısıyla ZIP olarak indir"
                >
                  <span>📦</span>
                  <span>ZIP İndir</span>
                </button>
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

          {/* Upload Section - ADMIN AND CONSULTANT */}
          {(userRole === 'admin' || userRole === 'consultant') && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-4">📤 Yeni Belge Yükle</h3>
            
            <div className={`grid gap-6 ${isMobile ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2'}`}>
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
                    <option value="TR1_CRITERIA">Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)</option>
                    <option value="STAGE_1_DOC">I. Aşama Belgesi</option>
                    <option value="STAGE_2_DOC">II. Aşama Belgesi</option>
                    <option value="STAGE_3_DOC">III. Aşama Belgesi</option>
                    <option value="CARBON_REPORT">Karbon Ayak İzi Raporu</option>
                    <option value="SUSTAINABILITY_REPORT">Sürdürülebilirlik Raporu</option>
                    <option value="PROCEDURE">Prosedür</option>
                    <option value="FORM">Form</option>
                    <option value="LIST">Liste</option>
                    <option value="INSTRUCTION">Talimat</option>
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
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,image/*"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    📱 Galeri, kamera veya dosya seçebilirsiniz • PDF, Word, Excel, Resim desteklenir
                  </p>
                  {selectedFiles.length > 0 && (
                    <div className="mt-2 text-sm text-gray-600">
                      {selectedFiles.length} dosya seçildi: {selectedFiles.map(f => f.name).join(', ')}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Upload Buttons */}
            <div className="mt-6 grid grid-cols-1 gap-4">
              <button
                onClick={uploadDocuments}
                disabled={uploading}
                className={`py-3 px-6 rounded-lg font-semibold text-white ${
                  uploading 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
                }`}
              >
                {uploading ? '📤 Yükleniyor...' : '🚀 Belgeleri Yükle'}
              </button>
              
              {/* Toplu Klasör Yükle butonu şimdilik gizli */}
              {false && (
                <button
                  onClick={() => setShowBulkFolderUpload(true)}
                  className="py-3 px-6 rounded-lg font-semibold text-white bg-purple-600 hover:bg-purple-700 active:bg-purple-800"
                >
                  📁 Toplu Klasör Yükle
                </button>
              )}
            </div>
          </div>
          )}

          {/* CLIENT ROLE - UPLOAD ENABLED */}
          {userRole === 'client' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-4">📤 Yeni Belge Yükle</h3>
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-lg mb-6">
                <p className="text-sm text-blue-700">
                  <strong>Client Kullanıcısı:</strong> Kendi belgelerinizi yükleyebilir ve yönetebilirsiniz.
                </p>
              </div>
            
            <div className={`grid gap-6 ${isMobile ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2'}`}>
              {/* Left Column */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Belge Adı</label>
                  <input
                    type="text"
                    value={documentName}
                    onChange={(e) => setDocumentName(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Belge adını girin"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Belge Türü</label>
                  <select
                    value={documentType}
                    onChange={(e) => setDocumentType(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="PROCEDURE">Prosedür</option>
                    <option value="POLICY">Politika</option>
                    <option value="FORM">Form</option>
                    <option value="LIST">Liste</option>
                    <option value="RECORD">Kayıt</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Aşama</label>
                  <select
                    value={stage}
                    onChange={(e) => setStage(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                  <label className="block text-sm font-medium text-gray-700 mb-2">Açıklama</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Belge açıklaması (opsiyonel)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Dosya Seç</label>
                  <input
                    type="file"
                    multiple
                    onChange={handleFileSelect}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,image/*"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    📷 Kamera, galeri veya dosya sistemi seçenekleri
                  </p>
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
              <>
                {/* Mobile View */}
                {isMobile ? (
                  <div className="space-y-4">
                    {documents.map(doc => (
                      <div key={doc.id} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-medium text-gray-900 flex-1 mr-2">{doc.name}</h4>
                          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                            {(doc.file_size / 1024 / 1024).toFixed(2)} MB
                          </span>
                        </div>
                        
                        <div className="space-y-1 mb-3">
                          <p className="text-sm text-gray-600">
                            📄 {doc.original_filename}
                          </p>
                          <p className="text-xs text-gray-500">
                            📅 {new Date(doc.created_at).toLocaleDateString('tr-TR')}
                          </p>
                        </div>
                        
                        <div className="flex space-x-2">
                          {/* Görüntüle butonu geçici olarak gizlendi */}
                          {/* <button
                            onClick={() => viewDocument(doc)}
                            className="flex-1 px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm font-medium"
                          >
                            👁️ Görüntüle
                          </button> */}
                          <button
                            onClick={() => downloadDocument(doc)}
                            className="flex-1 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
                          >
                            📥 İndir
                          </button>
                          <button
                            onClick={() => deleteDocument(doc.id)}
                            className="flex-1 px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm font-medium"
                          >
                            🗑️ Sil
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  /* Desktop Table View */
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
                              {/* Görüntüle butonu geçici olarak gizlendi */}
                              {/* <button
                                onClick={() => viewDocument(doc)}
                                className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700"
                                title={`${doc.original_filename} dosyasını görüntüle`}
                              >
                                👁️ Görüntüle
                              </button> */}
                              <button
                                onClick={() => downloadDocument(doc)}
                                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                                title={`${doc.original_filename} dosyasını indir`}
                              >
                                📥 İndir
                              </button>
                              <button
                                onClick={() => deleteDocument(doc.id)}
                                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                                title={`${doc.original_filename} dosyasını sil`}
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
              </>
            )}
          </div>
        </div>
      )}
      
      {/* Bulk Folder Upload Modal */}
      {showBulkFolderUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 m-4 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">📁 Toplu Klasör Yükleme</h2>
              <button
                onClick={() => setShowBulkFolderUpload(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            
            {!folderAnalysis ? (
              // Step 1: Folder Selection
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-800 mb-2">📋 Nasıl Çalışır?</h3>
                  <div className="text-sm text-blue-700">
                    <p className="mb-2">1. Bilgisayarınızdan belgelerin bulunduğu ana klasörü seçin</p>
                    <p className="mb-2">2. Sistem klasör yapısını analiz edecek</p>
                    <p className="mb-2">3. Klasörler sistemdeki uygun yerlerle eşleştirilecek</p>
                    <p>4. Tüm dosyalar otomatik olarak doğru klasörlere yüklenecek</p>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ana Klasör Seçin (Alt klasörler dahil tüm yapı analiz edilecek)
                  </label>
                  <input
                    type="file"
                    webkitdirectory="true"
                    directory="true"
                    multiple
                    onChange={(e) => {
                      const files = Array.from(e.target.files);
                      setSelectedBulkFolder(files);
                      
                      // Analyze folder structure
                      const analysis = analyzeFolderStructure(files);
                      setFolderAnalysis(analysis);
                      
                      // 🤖 OTOMATIK EŞLEŞTİRME - Auto-apply mapping
                      setFolderMapping(analysis.autoMapping);
                      
                      console.log('🤖 Otomatik eşleştirme:', analysis.autoMapping);
                    }}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    💡 Tüm klasör yapısı seçilecek. Desteklenen formatlar: PDF, Word, Excel, PowerPoint, PNG, JPG, JPEG
                  </p>
                </div>
                
                {selectedBulkFolder && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-green-800 font-medium">
                      ✅ {selectedBulkFolder.length} dosya seçildi, analiz ediliyor...
                    </p>
                  </div>
                )}
              </div>
            ) : (
              // Step 2: Folder Mapping & Upload
              <div className="space-y-6">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-800 mb-2">📊 Klasör Yapısı Analizi</h3>
                  <div className="text-sm text-yellow-700">
                    <p>Toplam {folderAnalysis.totalFiles} dosya, {folderAnalysis.folders.length} klasör bulundu</p>
                    <p className="mt-1">🤖 Otomatik eşleştirme: {Object.keys(folderAnalysis.autoMapping).length}/{folderAnalysis.folders.length} klasör eşleştirildi</p>
                  </div>
                </div>
                
                {/* Otomatik Eşleştirme Özeti */}
                {Object.keys(folderAnalysis.autoMapping).length > 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h3 className="font-medium text-green-800 mb-2">✅ Otomatik Eşleştirmeler</h3>
                    <div className="space-y-2">
                      {Object.entries(folderAnalysis.autoMapping).map(([folderPath, systemFolder]) => (
                        <div key={folderPath} className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">{folderPath}</span>
                          <span className="text-green-700 font-medium">→ {systemFolder}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Manuel Eşleştirme Gereken Klasörler */}
                {folderAnalysis.folders.filter(folder => !folderAnalysis.autoMapping[folder.path]).length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-orange-700">⚠️ Manuel Eşleştirme Gerekli</h3>
                    <div className="space-y-3">
                      {folderAnalysis.folders
                        .filter(folder => !folderAnalysis.autoMapping[folder.path])
                        .map((folder, index) => (
                          <div key={index} className="flex items-center justify-between p-3 border border-orange-200 rounded-lg bg-orange-50">
                            <div className="flex-1">
                              <p className="font-medium text-orange-800">{folder.path}</p>
                              <p className="text-sm text-orange-600">{folder.fileCount} dosya - Otomatik eşleştirme yapılamadı</p>
                            </div>
                            <div className="flex-1 ml-4">
                              <select
                                value={folderMapping[folder.path] || ''}
                                onChange={(e) => setFolderMapping({...folderMapping, [folder.path]: e.target.value})}
                                className="w-full p-2 border border-orange-300 rounded focus:ring-2 focus:ring-blue-500"
                              >
                                <option value="">Hedef klasör seçin...</option>
                                <optgroup label="🅰️ A SÜTUNU">
                                  <option value="A_SUTUNU">A SÜTUNU</option>
                                  <option value="A1">A1</option>
                                  <option value="A2">A2</option>
                                  <option value="A3">A3</option>
                                  <option value="A4">A4</option>
                                  <option value="A5">A5</option>
                                  <option value="A7.1">A7.1</option>
                                  <option value="A7.2">A7.2</option>
                                  <option value="A7.3">A7.3</option>
                                  <option value="A7.4">A7.4</option>
                                  <option value="A8">A8</option>
                                  <option value="A9">A9</option>
                                  <option value="A10">A10</option>
                                </optgroup>
                                <optgroup label="🅱️ B SÜTUNU">
                                  <option value="B_SUTUNU">B SÜTUNU</option>
                                  <option value="B1">B1</option>
                                  <option value="B2">B2</option>
                                  <option value="B3">B3</option>
                                  <option value="B4">B4</option>
                                  <option value="B5">B5</option>
                                  <option value="B6">B6</option>
                                  <option value="B7">B7</option>
                                  <option value="B8">B8</option>
                                  <option value="B9">B9</option>
                                </optgroup>
                                <optgroup label="🅲 C SÜTUNU">
                                  <option value="C_SUTUNU">C SÜTUNU</option>
                                  <option value="C1">C1</option>
                                  <option value="C2">C2</option>
                                  <option value="C3">C3</option>
                                  <option value="C4">C4</option>
                                </optgroup>
                                <optgroup label="🅳 D SÜTUNU">
                                  <option value="D_SUTUNU">D SÜTUNU</option>
                                  <option value="D1">D1</option>
                                  <option value="D1.1">D1.1</option>
                                  <option value="D1.2">D1.2</option>
                                  <option value="D1.3">D1.3</option>
                                  <option value="D1.4">D1.4</option>
                                  <option value="D2">D2</option>
                                  <option value="D2.1">D2.1</option>
                                  <option value="D2.2">D2.2</option>
                                  <option value="D2.3">D2.3</option>
                                  <option value="D2.4">D2.4</option>
                                  <option value="D2.5">D2.5</option>
                                  <option value="D2.6">D2.6</option>
                                  <option value="D3">D3</option>
                                  <option value="D3.1">D3.1</option>
                                  <option value="D3.2">D3.2</option>
                                  <option value="D3.3">D3.3</option>
                                  <option value="D3.4">D3.4</option>
                                  <option value="D3.5">D3.5</option>
                                  <option value="D3.6">D3.6</option>
                                </optgroup>
                                <optgroup label="📁 LEVEL 4 - BELGE TÜRLERİ">
                                  <option value="POLİTİKALAR">POLİTİKALAR</option>
                                  <option value="PROSEDÜRLER">PROSEDÜRLER</option>
                                  <option value="KAYITLAR">KAYITLAR</option>
                                  <option value="FORMLAR">FORMLAR</option>
                                  <option value="LİSTELER">LİSTELER</option>
                                  <option value="TALİMATLAR">TALİMATLAR</option>
                                  <option value="BELGELERİ">BELGELERİ</option>
                                  <option value="ŞEMALARı">ŞEMALARı</option>
                                  <option value="RESİMLER">RESİMLER</option>
                                  <option value="RAPORLAR">RAPORLAR</option>
                                </optgroup>
                              </select>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
                
                {/* Tüm Klasör Eşleştirmelerini Gözden Geçir */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">🔍 Tüm Eşleştirmeleri Gözden Geçir</h3>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {folderAnalysis.folders.map((folder, index) => {
                      const isAutoMapped = folderAnalysis.autoMapping[folder.path];
                      const currentMapping = folderMapping[folder.path] || '';
                      
                      return (
                        <div key={index} className={`flex items-center justify-between p-2 rounded border ${
                          isAutoMapped ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                        }`}>
                          <div className="flex-1">
                            <p className="font-medium text-sm">{folder.path}</p>
                            <p className="text-xs text-gray-500">
                              {folder.fileCount} dosya {isAutoMapped && '• Otomatik eşleştirildi'}
                            </p>
                          </div>
                          <div className="flex-1 ml-4">
                            <select
                              value={currentMapping}
                              onChange={(e) => setFolderMapping({...folderMapping, [folder.path]: e.target.value})}
                              className="w-full p-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="">Hedef klasör seçin...</option>
                              <optgroup label="🅰️ A SÜTUNU">
                                <option value="A_SUTUNU">A SÜTUNU</option>
                                <option value="A1">A1</option>
                                <option value="A2">A2</option>
                                <option value="A3">A3</option>
                                <option value="A4">A4</option>
                                <option value="A5">A5</option>
                                <option value="A7.1">A7.1</option>
                                <option value="A7.2">A7.2</option>
                                <option value="A7.3">A7.3</option>
                                <option value="A7.4">A7.4</option>
                                <option value="A8">A8</option>
                                <option value="A9">A9</option>
                                <option value="A10">A10</option>
                              </optgroup>
                              <optgroup label="🅱️ B SÜTUNU">
                                <option value="B_SUTUNU">B SÜTUNU</option>
                                <option value="B1">B1</option>
                                <option value="B2">B2</option>
                                <option value="B3">B3</option>
                                <option value="B4">B4</option>
                                <option value="B5">B5</option>
                                <option value="B6">B6</option>
                                <option value="B7">B7</option>
                                <option value="B8">B8</option>
                                <option value="B9">B9</option>
                              </optgroup>
                              <optgroup label="🅲 C SÜTUNU">
                                <option value="C_SUTUNU">C SÜTUNU</option>
                                <option value="C1">C1</option>
                                <option value="C2">C2</option>
                                <option value="C3">C3</option>
                                <option value="C4">C4</option>
                              </optgroup>
                              <optgroup label="🅳 D SÜTUNU">
                                <option value="D_SUTUNU">D SÜTUNU</option>
                                <option value="D1">D1</option>
                                <option value="D1.1">D1.1</option>
                                <option value="D1.2">D1.2</option>
                                <option value="D1.3">D1.3</option>
                                <option value="D1.4">D1.4</option>
                                <option value="D2">D2</option>
                                <option value="D2.1">D2.1</option>
                                <option value="D2.2">D2.2</option>
                                <option value="D2.3">D2.3</option>
                                <option value="D2.4">D2.4</option>
                                <option value="D2.5">D2.5</option>
                                <option value="D2.6">D2.6</option>
                                <option value="D3">D3</option>
                                <option value="D3.1">D3.1</option>
                                <option value="D3.2">D3.2</option>
                                <option value="D3.3">D3.3</option>
                                <option value="D3.4">D3.4</option>
                                <option value="D3.5">D3.5</option>
                                <option value="D3.6">D3.6</option>
                              </optgroup>
                              <optgroup label="📁 LEVEL 4 - BELGE TÜRLERİ">
                                <option value="POLİTİKALAR">POLİTİKALAR</option>
                                <option value="PROSEDÜRLER">PROSEDÜRLER</option>
                                <option value="KAYITLAR">KAYITLAR</option>
                                <option value="FORMLAR">FORMLAR</option>
                                <option value="LİSTELER">LİSTELER</option>
                                <option value="TALİMATLAR">TALİMATLAR</option>
                                <option value="BELGELERİ">BELGELERİ</option>
                                <option value="ŞEMALARı">ŞEMALARı</option>
                                <option value="RESİMLER">RESİMLER</option>
                                <option value="RAPORLAR">RAPORLAR</option>
                              </optgroup>
                            </select>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
                
                <div className="flex justify-end space-x-4">
                  <button
                    onClick={() => {
                      setFolderAnalysis(null);
                      setSelectedBulkFolder(null);
                      setFolderMapping({});
                    }}
                    className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    ⬅️ Geri
                  </button>
                  <button
                    onClick={processBulkFolderUpload}
                    disabled={bulkUploading}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                  >
                    {bulkUploading ? '📤 Yükleniyor...' : '🚀 Toplu Yüklemeyi Başlat'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default YeniBelgeYonetimiYeni;