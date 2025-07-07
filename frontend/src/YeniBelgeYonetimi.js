import React, { useState, useEffect } from 'react';
import axios from 'axios';

const YeniBelgeYonetimi = () => {
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
  
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Load initial data
  useEffect(() => {
    loadClients();
    loadFolders();
    loadDocuments();
  }, []);

  const loadClients = async () => {
    try {
      const response = await axios.get(`${API}/api/clients`);
      setClients(response.data || []);
    } catch (error) {
      console.error('❌ Client load error:', error);
    }
  };

  const loadFolders = async (clientId = null) => {
    try {
      let url = `${API}/api/folders`;
      if (clientId) {
        url = `${API}/api/folders/by-client/${clientId}`;
      }
      const response = await axios.get(url);
      setFolders(response.data || []);
    } catch (error) {
      console.error('❌ Folder load error:', error);
    }
  };

  // Client seçildiğinde klasörleri filtrele
  const handleClientChange = (event) => {
    const newClientId = event.target.value;
    setSelectedClient(newClientId);
    
    // Client seçildiğinde o client'a ait klasörleri yükle
    if (newClientId) {
      loadFolders(newClientId);
    } else {
      loadFolders(); // Tüm klasörleri yükle
    }
    
    // Folder seçimini sıfırla
    setSelectedFolder('');
  };

  const loadDocuments = async () => {
    try {
      const response = await axios.get(`${API}/api/belge/list`);
      setDocuments(response.data?.documents || []);
    } catch (error) {
      console.error('❌ Document load error:', error);
    }
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
  };

  const uploadDocuments = async () => {
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
    
    if (!documentName.trim()) {
      alert('Lütfen belge adı girin!');
      return;
    }

    setUploading(true);
    
    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const formData = new FormData();
        
        formData.append('file', file);
        formData.append('client_id', selectedClient);
        formData.append('folder_id', selectedFolder);
        formData.append('document_name', documentName + (selectedFiles.length > 1 ? ` (${i + 1})` : ''));
        formData.append('document_type', documentType);
        formData.append('stage', stage);
        formData.append('description', description);
        
        console.log(`📤 Uploading file ${i + 1}/${selectedFiles.length}: ${file.name}`);
        
        const response = await axios.post(`${API}/api/belge/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
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
      
      // Reload documents
      await loadDocuments();
      
      alert(`${selectedFiles.length} belge başarıyla yüklendi!`);
      
    } catch (error) {
      console.error('❌ Upload error:', error);
      alert(`Upload hatası: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const downloadDocument = async (doc) => {
    try {
      console.log(`📥 Downloading: ${doc.name}`);
      
      const response = await axios.get(`${API}/api/belge/download/${doc.id}`, {
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = doc.original_filename || doc.name || 'document';
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      window.URL.revokeObjectURL(url);
      
      console.log(`✅ Download completed: ${doc.original_filename}`);
      
    } catch (error) {
      console.error('❌ Download error:', error);
      alert(`Download hatası: ${error.response?.data?.detail || error.message}`);
    }
  };

  const deleteDocument = async (doc) => {
    if (!window.confirm(`"${doc.name}" belgesini silmek istediğinizden emin misiniz?`)) {
      return;
    }
    
    try {
      await axios.delete(`${API}/api/belge/delete/${doc.id}`);
      console.log(`🗑️ Document deleted: ${doc.name}`);
      loadDocuments(); // Refresh list
      alert('Belge silindi!');
    } catch (error) {
      console.error('❌ Delete error:', error);
      alert(`Silme hatası: ${error.response?.data?.detail || error.message}`);
    }
  };

  const getClientName = (clientId) => {
    const client = clients.find(c => c.id === clientId);
    return client ? client.name : 'Bilinmeyen Müşteri';
  };

  const getFolderName = (folderId) => {
    const folder = folders.find(f => f.id === folderId);
    return folder ? folder.name : 'Bilinmeyen Klasör';
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-center">🚀 Yeni Belge Yönetimi</h1>
      
      {/* UPLOAD SECTION */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <h2 className="text-2xl font-semibold mb-6">📤 Belge Yükleme</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Müşteri Seçin *</label>
              <select 
                value={selectedClient} 
                onChange={handleClientChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">-- Müşteri Seçin --</option>
                {clients.map(client => (
                  <option key={client.id} value={client.id}>
                    {client.name} ({client.hotel_name})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Klasör Seçin *</label>
              <select 
                value={selectedFolder} 
                onChange={(e) => setSelectedFolder(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">-- Klasör Seçin --</option>
                {folders.map(folder => (
                  <option key={folder.id} value={folder.id}>
                    {folder.name} ({folder.folder_path})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Belge Adı *</label>
              <input
                type="text"
                value={documentName}
                onChange={(e) => setDocumentName(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Belge adını girin"
                required
              />
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-4">
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
          </div>
        </div>

        {/* File Selection */}
        <div className="mt-6">
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

      {/* DOCUMENTS LIST */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold">📋 Yüklenen Belgeler</h2>
          <button
            onClick={loadDocuments}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            🔄 Yenile
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            Henüz belge yüklenmemiş
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">Belge Adı</th>
                  <th className="px-4 py-2 text-left">Dosya Adı</th>
                  <th className="px-4 py-2 text-left">Müşteri</th>
                  <th className="px-4 py-2 text-left">Klasör</th>
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
                    <td className="px-4 py-2 text-sm">{getClientName(doc.client_id)}</td>
                    <td className="px-4 py-2 text-sm">{getFolderName(doc.folder_id)}</td>
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
  );
};

export default YeniBelgeYonetimi;