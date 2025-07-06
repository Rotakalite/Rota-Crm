import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Mock auth context for testing
const mockAuthContext = {
  authToken: 'test-token',
  userRole: 'admin'
};

// Get API URL helper
const getApiUrl = () => {
  return process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
};

// Email Management Test Component
const EmailManagementTest = () => {
  const [activeTab, setActiveTab] = useState('documents');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [trainings, setTrainings] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [emailData, setEmailData] = useState({
    recipients: '',
    subject: '',
    message: '',
    includeAttachments: true
  });
  const [clients, setClients] = useState([]);
  const [emailHistory, setEmailHistory] = useState([]);

  // Initialize with mock data
  useEffect(() => {
    console.log('EmailManagementTest useEffect running...');
    
    // Set mock data immediately
    setDocuments([
      {
        id: 1,
        title: 'Sürdürülebilirlik Rehberi',
        type: 'PDF',
        category: 'Training Material',
        upload_date: '2024-12-20T10:30:00.000Z',
        file_size: '2.5 MB'
      },
      {
        id: 2,
        title: 'Çevre Politikası',
        type: 'PDF',
        category: 'Policy Document',
        upload_date: '2024-12-19T14:15:00.000Z',
        file_size: '1.2 MB'
      },
      {
        id: 3,
        title: 'Atık Yönetimi Kılavuzu',
        type: 'PDF',
        category: 'Manual',
        upload_date: '2024-12-18T09:45:00.000Z',
        file_size: '3.1 MB'
      }
    ]);

    setTrainings([
      {
        id: 1,
        title: 'Sürdürülebilir Turizm Eğitimi',
        description: 'Temel sürdürülebilirlik prensipleri',
        duration: '2 saat',
        level: 'Başlangıç',
        category: 'Environment'
      },
      {
        id: 2,
        title: 'Enerji Tasarrufu Eğitimi',
        description: 'Enerji verimliliği teknikleri',
        duration: '1.5 saat',
        level: 'Orta',
        category: 'Energy'
      },
      {
        id: 3,
        title: 'Atık Azaltma Workshop',
        description: 'Zero waste prensipleri',
        duration: '3 saat',
        level: 'İleri',
        category: 'Waste Management'
      }
    ]);

    setClients([
      { id: 1, name: 'Hotel Paradise', email: 'info@hotelparadise.com' },
      { id: 2, name: 'Green Resort', email: 'contact@greenresort.com' },
      { id: 3, name: 'Eco Lodge', email: 'hello@ecolodge.com' }
    ]);

    setEmailHistory([
      {
        id: 1,
        to: 'client@example.com',
        subject: 'Sürdürülebilirlik Eğitimi',
        sent_at: '2024-12-20T11:00:00.000Z',
        status: 'delivered'
      }
    ]);

    console.log('Mock data loaded successfully');
  }, []);

  // Handle item selection
  const handleItemSelection = (itemId, itemType) => {
    const itemKey = `${itemType}_${itemId}`;
    setSelectedItems(prev => {
      if (prev.includes(itemKey)) {
        return prev.filter(id => id !== itemKey);
      } else {
        return [...prev, itemKey];
      }
    });
  };

  // Select all items
  const handleSelectAll = (itemType) => {
    const items = itemType === 'document' ? documents : trainings;
    const allItemKeys = items.map(item => `${itemType}_${item.id}`);
    
    const allSelected = allItemKeys.every(key => selectedItems.includes(key));
    
    if (allSelected) {
      setSelectedItems(prev => prev.filter(key => !key.startsWith(itemType)));
    } else {
      setSelectedItems(prev => {
        const filtered = prev.filter(key => !key.startsWith(itemType));
        return [...filtered, ...allItemKeys];
      });
    }
  };

  // Test send email function
  const sendEmailWithItems = async () => {
    if (!emailData.recipients || !emailData.subject || selectedItems.length === 0) {
      alert('Lütfen alıcı, konu ve en az bir doküman/eğitim seçin!');
      return;
    }

    console.log('Sending email with:', { emailData, selectedItems });
    alert('Email gönderildi! (Test Mode)');
    
    // Reset form
    setEmailData({ recipients: '', subject: '', message: '', includeAttachments: true });
    setSelectedItems([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-xl p-8 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 mb-2">📧 Email Management Test</h1>
              <p className="text-gray-600">Test version - bypassing authentication</p>
            </div>
            <div className="px-4 py-2 bg-green-100 text-green-800 rounded-full">
              ✅ Test Mode Active
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-xl mb-8">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-6 py-4 text-sm font-medium ${
                activeTab === 'documents'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              📄 Documents ({documents.length})
            </button>
            <button
              onClick={() => setActiveTab('trainings')}
              className={`px-6 py-4 text-sm font-medium ${
                activeTab === 'trainings'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              🎓 Trainings ({trainings.length})
            </button>
            <button
              onClick={() => setActiveTab('compose')}
              className={`px-6 py-4 text-sm font-medium ${
                activeTab === 'compose'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              ✉️ Compose
            </button>
          </div>

          <div className="p-6">
            {/* Documents Tab */}
            {activeTab === 'documents' && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">Available Documents</h3>
                  <button
                    onClick={() => handleSelectAll('document')}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                  >
                    Select All
                  </button>
                </div>
                <div className="grid gap-4">
                  {documents.map(doc => (
                    <div
                      key={doc.id}
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        selectedItems.includes(`document_${doc.id}`)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleItemSelection(doc.id, 'document')}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{doc.title}</h4>
                          <p className="text-sm text-gray-600">{doc.category} • {doc.file_size}</p>
                        </div>
                        <div className="text-right">
                          <span className="text-sm text-gray-500">{doc.type}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Trainings Tab */}
            {activeTab === 'trainings' && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">Available Trainings</h3>
                  <button
                    onClick={() => handleSelectAll('training')}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                  >
                    Select All
                  </button>
                </div>
                <div className="grid gap-4">
                  {trainings.map(training => (
                    <div
                      key={training.id}
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        selectedItems.includes(`training_${training.id}`)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleItemSelection(training.id, 'training')}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{training.title}</h4>
                          <p className="text-sm text-gray-600">{training.description}</p>
                        </div>
                        <div className="text-right">
                          <span className="text-sm text-gray-500">{training.duration}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Compose Tab */}
            {activeTab === 'compose' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Compose Email</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Recipients (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={emailData.recipients}
                      onChange={(e) => setEmailData({...emailData, recipients: e.target.value})}
                      placeholder="email1@example.com, email2@example.com"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Subject
                    </label>
                    <input
                      type="text"
                      value={emailData.subject}
                      onChange={(e) => setEmailData({...emailData, subject: e.target.value})}
                      placeholder="Email subject"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Message
                    </label>
                    <textarea
                      value={emailData.message}
                      onChange={(e) => setEmailData({...emailData, message: e.target.value})}
                      placeholder="Email message"
                      rows={6}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Selected Items ({selectedItems.length}):</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedItems.map(item => (
                        <span key={item} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button
                    onClick={sendEmailWithItems}
                    disabled={loading}
                    className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? 'Sending...' : 'Send Email'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailManagementTest;