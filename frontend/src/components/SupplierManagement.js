import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './auth';
import { getApiUrl } from './utils';

// ====================================
// SUPPLIER MANAGEMENT COMPONENT
// ====================================

const SupplierManagement = () => {
  const [loading, setLoading] = useState(false);
  const [suppliers, setSuppliers] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const { authToken, userRole } = useAuth();
  const API = getApiUrl();

  // Fetch suppliers
  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/suppliers`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setSuppliers(response.data || []);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      setSuppliers([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Elite Header */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-800 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">🏢 Elite Tedarikçi Yönetimi</h1>
              <p className="text-blue-100 text-lg">Sürdürülebilir tedarik zinciri yönetimi</p>
            </div>
            <button
              onClick={() => setShowAddForm(true)}
              className="bg-white text-blue-700 px-6 py-3 rounded-xl hover:bg-blue-50 transition-all duration-300 shadow-lg font-semibold flex items-center gap-2"
            >
              <span className="text-xl">+</span> Yeni Tedarikçi
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-8">
        {/* Suppliers Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold">📊 Toplam Tedarikçi</h3>
              <div className="bg-white bg-opacity-20 rounded-full p-2">
                <span className="text-2xl">🏢</span>
              </div>
            </div>
            <p className="text-3xl font-bold mb-1">{suppliers.length}</p>
            <p className="text-blue-100 text-sm">Aktif tedarikçi</p>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold">🌱 Ortalama Sürdürülebilirlik</h3>
              <div className="bg-white bg-opacity-20 rounded-full p-2">
                <span className="text-2xl">📈</span>
              </div>
            </div>
            <p className="text-3xl font-bold mb-1">
              {suppliers.length > 0 ? (suppliers.reduce((sum, s) => sum + s.sustainability_score, 0) / suppliers.length).toFixed(1) : 0}
            </p>
            <p className="text-green-100 text-sm">Puan (0-100)</p>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold">🏠 Yerel Tedarikçi</h3>
              <div className="bg-white bg-opacity-20 rounded-full p-2">
                <span className="text-2xl">📍</span>
              </div>
            </div>
            <p className="text-3xl font-bold mb-1">
              {suppliers.filter(s => s.local_supplier).length}
            </p>
            <p className="text-purple-100 text-sm">
              %{suppliers.length > 0 ? ((suppliers.filter(s => s.local_supplier).length / suppliers.length) * 100).toFixed(0) : 0} yerel
            </p>
          </div>

          <div className="bg-gradient-to-br from-amber-500 to-amber-600 p-6 rounded-2xl text-white shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold">🏆 Sertifikalı</h3>
              <div className="bg-white bg-opacity-20 rounded-full p-2">
                <span className="text-2xl">🎖️</span>
              </div>
            </div>
            <p className="text-3xl font-bold mb-1">
              {suppliers.filter(s => s.certifications && s.certifications.length > 0).length}
            </p>
            <p className="text-amber-100 text-sm">Sertifikaya sahip</p>
          </div>
        </div>

        {/* Suppliers Table */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              📋 Tedarikçi Listesi
              <span className="text-sm font-normal text-gray-600">({suppliers.length} tedarikçi)</span>
            </h3>
          </div>
          
          {loading ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">⏳</div>
              <p className="text-gray-600">Yükleniyor...</p>
            </div>
          ) : suppliers.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gradient-to-r from-blue-50 to-blue-100">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                      🏢 Şirket
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                      👤 İletişim
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                      📂 Kategori
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                      🌱 Sürdürülebilirlik
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                      🏆 Sertifikalar
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                      📍 Konum
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                      ⚙️ İşlemler
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {suppliers.map((supplier) => (
                    <tr key={supplier.id} className="hover:bg-blue-50 transition-colors duration-200">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{supplier.company_name}</div>
                          <div className="text-sm text-gray-500">{supplier.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{supplier.contact_person}</div>
                          <div className="text-sm text-gray-500">{supplier.phone}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                          {supplier.category}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-1">
                            <div className={`text-sm font-bold ${
                              supplier.sustainability_score >= 80 ? 'text-green-600' :
                              supplier.sustainability_score >= 60 ? 'text-yellow-600' : 'text-red-600'
                            }`}>
                              {supplier.sustainability_score}/100
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  supplier.sustainability_score >= 80 ? 'bg-green-500' :
                                  supplier.sustainability_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                                }`}
                                style={{ width: `${supplier.sustainability_score}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {supplier.certifications?.slice(0, 2).map((cert, index) => (
                            <span key={index} className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                              {cert}
                            </span>
                          ))}
                          {supplier.certifications?.length > 2 && (
                            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                              +{supplier.certifications.length - 2}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          supplier.local_supplier ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {supplier.local_supplier ? '🏠 Yerel' : '🌍 Global'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button className="text-blue-600 hover:text-blue-900 transition-colors">
                          ✏️ Düzenle
                        </button>
                        <button className="text-red-600 hover:text-red-900 transition-colors">
                          🗑️ Sil
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🏢</div>
              <p className="text-xl text-gray-600 mb-2">Henüz tedarikçi bulunmuyor</p>
              <p className="text-gray-500">İlk tedarikçinizi eklemek için "Yeni Tedarikçi" butonunu kullanın</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SupplierManagement;