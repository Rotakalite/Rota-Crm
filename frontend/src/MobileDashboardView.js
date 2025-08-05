import React, { useState, useEffect } from 'react';
import { 
  MobileDashboard, 
  MobileStatsGrid, 
  MobileCard, 
  TouchButton,
  MobileNavigation,
  useIsMobile 
} from './MobileComponents';

const MobileDashboardView = ({ 
  user, 
  clients, 
  documents, 
  trainings, 
  onNavigate 
}) => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const isMobile = useIsMobile();

  // Dashboard stats
  const dashboardStats = [
    {
      label: 'Toplam Müşteri',
      value: clients?.length || 0,
      change: 5.2
    },
    {
      label: 'Belgeler',
      value: documents?.length || 0,
      change: 12.5
    },
    {
      label: 'Eğitimler', 
      value: trainings?.length || 0,
      change: -2.1
    },
    {
      label: 'Bu Ay',
      value: new Date().toLocaleDateString('tr-TR', { month: 'long' }),
      change: null
    }
  ];

  // Recent activities (mock data)
  const recentActivities = [
    {
      id: 1,
      title: 'Yeni doküman yüklendi',
      description: 'Çevre Raporu - ABC Hotel',
      time: '2 saat önce',
      icon: '📄',
      type: 'document'
    },
    {
      id: 2,
      title: 'Eğitim tamamlandı',
      description: 'Sürdürülebilirlik Eğitimi - XYZ Resort',
      time: '5 saat önce',
      icon: '🎓',
      type: 'training'
    },
    {
      id: 3,
      title: 'AI raporu hazır',
      description: 'Aylık analiz raporu oluşturuldu',
      time: '1 gün önce',
      icon: '🤖',
      type: 'ai'
    },
    {
      id: 4,
      title: 'Yeni müşteri eklendi',
      description: 'Green Paradise Hotel',
      time: '2 gün önce', 
      icon: '🏨',
      type: 'client'
    }
  ];

  // Quick actions
  const quickActions = [
    {
      title: 'Doküman Yükle',
      icon: '📤',
      color: 'bg-blue-500',
      action: () => onNavigate('documents')
    },
    {
      title: 'AI Raporu',
      icon: '🤖',
      color: 'bg-green-500',
      action: () => onNavigate('ai-report')
    },
    {
      title: 'Müşteri Ekle',
      icon: '➕',
      color: 'bg-purple-500',
      action: () => onNavigate('add-client')
    },
    {
      title: 'Analitik',
      icon: '📊',
      color: 'bg-orange-500',
      action: () => onNavigate('analytics')
    }
  ];

  const handlePageChange = (page) => {
    setCurrentPage(page);
    if (onNavigate) {
      onNavigate(page);
    }
  };

  if (!isMobile) {
    return null; // Desktop'ta normal dashboard gösterilecek
  }

  return (
    <>
      <MobileDashboard
        title="GreenWave CRM"
        subtitle={`Hoş geldiniz, ${user?.firstName || 'Kullanıcı'}`}
      >
        {/* Stats Grid */}
        <MobileStatsGrid stats={dashboardStats} />

        {/* Quick Actions */}
        <MobileCard title="Hızlı İşlemler">
          <div className="grid grid-cols-2 gap-3">
            {quickActions.map((action, index) => (
              <TouchButton
                key={index}
                onClick={action.action}
                className={`${action.color} text-white flex-col h-20`}
              >
                <span className="text-2xl mb-1">{action.icon}</span>
                <span className="text-xs font-medium">{action.title}</span>
              </TouchButton>
            ))}
          </div>
        </MobileCard>

        {/* Recent Activities */}
        <MobileCard title="Son Aktiviteler">
          <div className="space-y-3">
            {recentActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex-shrink-0 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-sm">
                  {activity.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {activity.title}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {activity.description}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {activity.time}
                  </p>
                </div>
              </div>
            ))}
          </div>
          
          <TouchButton
            onClick={() => onNavigate('activities')}
            variant="outline"
            className="w-full mt-4"
          >
            Tüm Aktiviteleri Gör
          </TouchButton>
        </MobileCard>

        {/* Performance Summary */}
        <MobileCard title="Bu Ay Özet">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Karbon Emisyonu</span>
              <span className="text-sm font-semibold text-green-600">-15%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: '85%' }}></div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Enerji Tasarrufu</span>
              <span className="text-sm font-semibold text-blue-600">+8%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: '65%' }}></div>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Su Tasarrufu</span>
              <span className="text-sm font-semibold text-teal-600">+12%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-teal-500 h-2 rounded-full" style={{ width: '78%' }}></div>
            </div>
          </div>
        </MobileCard>

        {/* Weekly Goals */}
        <MobileCard title="Haftalık Hedefler">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs">✓</span>
                </div>
                <span className="text-sm text-gray-700">5 doküman yükle</span>
              </div>
              <span className="text-xs text-green-600 font-medium">Tamamlandı</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs">3</span>
                </div>
                <span className="text-sm text-gray-700">AI raporu oluştur</span>
              </div>
              <span className="text-xs text-yellow-600 font-medium">3/5</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs">2</span>
                </div>
                <span className="text-sm text-gray-700">Müşteri ziyareti</span>
              </div>
              <span className="text-xs text-blue-600 font-medium">2/3</span>
            </div>
          </div>
        </MobileCard>
      </MobileDashboard>

      {/* Mobile Navigation */}
      <MobileNavigation 
        currentPage={currentPage}
        onPageChange={handlePageChange}
      />
    </>
  );
};

export default MobileDashboardView;