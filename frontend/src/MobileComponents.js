import React, { useState, useEffect } from 'react';
import { useClerk } from '@clerk/clerk-react';

const MobileNavigation = ({ currentPage, onPageChange, userRole }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { signOut } = useClerk();

  // Handle proper logout
  const handleLogout = async () => {
    try {
      await signOut();
      // Clerk will automatically redirect to sign-in page after successful logout
    } catch (error) {
      console.error('Logout error:', error);
      // Fallback: redirect manually if Clerk fails
      window.location.href = '/sign-in';
    }
  };

  // Main bottom navigation (4 items + menu)
  const getMainNavItems = () => {
    if (userRole === 'admin') {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠' },
        { id: 'clients', label: 'Müşteri', icon: '🏨' },
        { id: 'ai-assistant', label: 'AI', icon: '🤖' },
        { id: 'settings', label: 'Ayarlar', icon: '⚙️' }
      ];
    } else if (userRole === 'client') {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠' },
        { id: 'yeni-belge', label: 'Belgeler', icon: '📄' },
        { id: 'consumption', label: 'Tüketim', icon: '⚡' },
        { id: 'ai-assistant', label: 'AI', icon: '🤖' }
      ];
    } else if (userRole === 'consultant') {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠' },
        { id: 'my-clients', label: 'Müşteri', icon: '👥' },
        { id: 'reports', label: 'Rapor', icon: '📊' },
        { id: 'ai-assistant', label: 'AI', icon: '🤖' }
      ];
    } else {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠' },
        { id: 'yeni-belge', label: 'Belgeler', icon: '📄' },
        { id: 'consumption', label: 'Tüketim', icon: '⚡' },
        { id: 'ai-assistant', label: 'AI', icon: '🤖' }
      ];
    }
  };

  // All menu items for drawer
  const getAllMenuItems = () => {
    if (userRole === 'admin') {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠', group: 'main' },
        { id: 'clients', label: 'Müşteri Yönetimi', icon: '🏨', group: 'main' },
        { id: 'consultants', label: 'Danışman Yönetimi', icon: '👥', group: 'main' },
        { id: 'yeni-belge', label: 'Belge Yönetimi', icon: '📄', group: 'documents' },
        { id: 'training', label: 'Eğitim Yönetimi', icon: '🎓', group: 'documents' },
        { id: 'email-management', label: 'Email Yönetimi', icon: '📧', group: 'documents' },
        { id: 'consumption', label: 'Tüketim Takibi', icon: '⚡', group: 'analytics' },
        { id: 'waste-management', label: 'Atık Yönetimi', icon: '♻️', group: 'analytics' },
        { id: 'suppliers', label: 'Tedarikçi Yönetimi', icon: '🚚', group: 'analytics' },
        { id: 'personnel', label: 'Personel Yönetimi', icon: '👤', group: 'analytics' },
        { id: 'ai-assistant', label: 'AI Asistan', icon: '🤖', group: 'ai' },
        { id: 'reports', label: 'Raporlar', icon: '📊', group: 'ai' },
        { id: 'settings', label: 'Sistem Ayarları', icon: '⚙️', group: 'settings' },
        { id: 'sustainability-targets', label: 'Sürdürülebilirlik Hedefleri', icon: '🎯', group: 'settings' }
      ];
    } else if (userRole === 'client') {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠', group: 'main' },
        { id: 'yeni-belge', label: 'Belge Yükle', icon: '📄', group: 'documents' },
        { id: 'training', label: 'Eğitimlerim', icon: '🎓', group: 'documents' },
        { id: 'consumption', label: 'Tüketim Takibi', icon: '⚡', group: 'analytics' },
        { id: 'waste-management', label: 'Atık Yönetimi', icon: '♻️', group: 'analytics' },
        { id: 'suppliers', label: 'Tedarikçiler', icon: '🚚', group: 'analytics' },
        { id: 'personnel', label: 'Personel', icon: '👤', group: 'analytics' },
        { id: 'ai-assistant', label: 'AI Asistan', icon: '🤖', group: 'ai' },
        { id: 'reports', label: 'Raporlarım', icon: '📊', group: 'ai' },
        { id: 'sustainability-targets', label: 'Hedeflerim', icon: '🎯', group: 'settings' }
      ];
    } else if (userRole === 'consultant') {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠', group: 'main' },
        { id: 'my-clients', label: 'Müşterilerim', icon: '👥', group: 'main' },
        { id: 'reports', label: 'Raporlar', icon: '📊', group: 'main' },
        { id: 'ai-assistant', label: 'AI Asistan', icon: '🤖', group: 'ai' },
        { id: 'training', label: 'Eğitim Yönetimi', icon: '🎓', group: 'documents' },
        { id: 'email-management', label: 'Email Yönetimi', icon: '📧', group: 'documents' }
      ];
    } else {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠', group: 'main' },
        { id: 'yeni-belge', label: 'Belgeler', icon: '📄', group: 'documents' },
        { id: 'consumption', label: 'Tüketim', icon: '⚡', group: 'analytics' },
        { id: 'ai-assistant', label: 'AI Asistan', icon: '🤖', group: 'ai' }
      ];
    }
  };

  const mainNavItems = getMainNavItems();
  const allMenuItems = getAllMenuItems();

  const handleItemClick = (item) => {
    if (item.isLogout) {
      handleLogout();
    } else {
      onPageChange(item.id);
      setIsMenuOpen(false); // Close menu after selection
    }
  };

  const groupedMenuItems = {
    main: allMenuItems.filter(item => item.group === 'main'),
    documents: allMenuItems.filter(item => item.group === 'documents'),
    analytics: allMenuItems.filter(item => item.group === 'analytics'),
    ai: allMenuItems.filter(item => item.group === 'ai'),
    settings: allMenuItems.filter(item => item.group === 'settings')
  };

  return (
    <>
      {/* Main Bottom Navigation */}
      <nav className="mobile-nav md:hidden">
        <div className="flex justify-around items-center">
          {/* Main 4 navigation items */}
          {mainNavItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleItemClick(item)}
              className={`mobile-nav-item ${
                currentPage === item.id ? 'active' : ''
              }`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
          
          {/* Menu Button */}
          <button
            onClick={() => setIsMenuOpen(true)}
            className="mobile-nav-item"
          >
            <span className="nav-icon">☰</span>
            <span className="nav-label">Menü</span>
          </button>
        </div>
      </nav>

      {/* Drawer Menu Modal */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
            onClick={() => setIsMenuOpen(false)}
          />
          
          {/* Drawer */}
          <div className="fixed inset-y-0 right-0 w-80 max-w-[85vw] bg-white shadow-xl transform transition-transform">
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="mobile-dashboard-header rounded-t-none">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="mobile-dashboard-title text-lg">Menü</h2>
                    <p className="mobile-dashboard-subtitle text-sm">
                      {userRole === 'admin' ? 'Admin Menüsü' : 
                       userRole === 'client' ? 'Müşteri Menüsü' : 
                       userRole === 'consultant' ? 'Danışman Menüsü' : 'Ana Menü'}
                    </p>
                  </div>
                  <button
                    onClick={() => setIsMenuOpen(false)}
                    className="text-white hover:text-gray-200 p-2"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* Menu Content */}
              <div className="flex-1 overflow-y-auto p-4">
                {/* Main Section */}
                {groupedMenuItems.main.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                      Ana Menü
                    </h3>
                    {groupedMenuItems.main.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleItemClick(item)}
                        className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                          currentPage === item.id
                            ? 'bg-green-100 text-green-800'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-lg">{item.icon}</span>
                        <span className="font-medium">{item.label}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Documents Section */}
                {groupedMenuItems.documents.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                      Belgeler & Eğitim
                    </h3>
                    {groupedMenuItems.documents.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleItemClick(item)}
                        className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                          currentPage === item.id
                            ? 'bg-green-100 text-green-800'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-lg">{item.icon}</span>
                        <span className="font-medium">{item.label}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Analytics Section */}
                {groupedMenuItems.analytics.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                      Takip & Analiz
                    </h3>
                    {groupedMenuItems.analytics.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleItemClick(item)}
                        className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                          currentPage === item.id
                            ? 'bg-green-100 text-green-800'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-lg">{item.icon}</span>
                        <span className="font-medium">{item.label}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* AI Section */}
                {groupedMenuItems.ai.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                      AI & Raporlar
                    </h3>
                    {groupedMenuItems.ai.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleItemClick(item)}
                        className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                          currentPage === item.id
                            ? 'bg-green-100 text-green-800'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-lg">{item.icon}</span>
                        <span className="font-medium">{item.label}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Settings Section */}
                {groupedMenuItems.settings.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                      Ayarlar
                    </h3>
                    {groupedMenuItems.settings.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleItemClick(item)}
                        className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                          currentPage === item.id
                            ? 'bg-green-100 text-green-800'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        <span className="text-lg">{item.icon}</span>
                        <span className="font-medium">{item.label}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer with Logout */}
              <div className="p-4 border-t border-gray-200">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center justify-center space-x-2 bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-lg transition-colors"
                >
                  <span className="text-lg">🚪</span>
                  <span className="font-medium">Çıkış Yap</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

const MobileCard = ({ title, children, className = '' }) => {
  return (
    <div className={`mobile-card ${className}`}>
      {title && (
        <div className="mobile-card-header">
          <h3 className="font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      <div className="mobile-card-content">
        {children}
      </div>
    </div>
  );
};

const MobileStatsGrid = ({ stats }) => {
  return (
    <div className="mobile-stats-grid">
      {stats.map((stat, index) => (
        <div key={index} className="mobile-stat-card">
          <div className="mobile-stat-value">{stat.value}</div>
          <div className="mobile-stat-label">{stat.label}</div>
          {stat.change && (
            <div className={`text-xs mt-1 ${
              stat.change > 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {stat.change > 0 ? '↗' : '↘'} {Math.abs(stat.change)}%
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const MobileModal = ({ isOpen, onClose, title, children }) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="mobile-modal" onClick={onClose}>
      <div 
        className="mobile-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

const MobileTable = ({ data, columns }) => {
  return (
    <div className="mobile-table md:hidden">
      {data.map((row, index) => (
        <div key={index} className="mobile-table-row">
          {columns.map((column) => (
            <div key={column.key} className="mobile-table-cell">
              <span className="mobile-table-label">{column.label}:</span>
              <span className="mobile-table-value">
                {typeof column.render === 'function' 
                  ? column.render(row[column.key], row)
                  : row[column.key]
                }
              </span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

const MobileDashboard = ({ title, subtitle, children }) => {
  return (
    <div className="mobile-dashboard md:hidden">
      <div className="mobile-dashboard-header">
        <h1 className="mobile-dashboard-title">{title}</h1>
        {subtitle && (
          <p className="mobile-dashboard-subtitle">{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  );
};

const TouchButton = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'medium',
  disabled = false,
  className = ''
}) => {
  const baseClasses = 'touch-button flex items-center justify-center font-medium transition-all duration-200';
  
  const variants = {
    primary: 'bg-green-600 hover:bg-green-700 text-white shadow-lg',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    outline: 'border-2 border-green-600 text-green-600 hover:bg-green-50',
    danger: 'bg-red-600 hover:bg-red-700 text-white'
  };

  const sizes = {
    small: 'px-3 py-2 text-sm min-h-[36px]',
    medium: 'px-4 py-3 text-base min-h-[44px]',
    large: 'px-6 py-4 text-lg min-h-[52px]'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        ${baseClasses}
        ${variants[variant]}
        ${sizes[size]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${className}
      `}
    >
      {children}
    </button>
  );
};

const SwipeableCard = ({ children, onSwipeLeft, onSwipeRight, className = '' }) => {
  const [startX, setStartX] = useState(null);
  const [currentX, setCurrentX] = useState(null);
  const [cardOffset, setCardOffset] = useState(0);

  const handleTouchStart = (e) => {
    setStartX(e.touches[0].clientX);
  };

  const handleTouchMove = (e) => {
    if (!startX) return;
    
    const currentX = e.touches[0].clientX;
    setCurrentX(currentX);
    setCardOffset(currentX - startX);
  };

  const handleTouchEnd = () => {
    if (!startX || !currentX) return;

    const diffX = currentX - startX;
    const threshold = 100;

    if (Math.abs(diffX) > threshold) {
      if (diffX > 0 && onSwipeRight) {
        onSwipeRight();
      } else if (diffX < 0 && onSwipeLeft) {
        onSwipeLeft();
      }
    }

    setStartX(null);
    setCurrentX(null);
    setCardOffset(0);
  };

  return (
    <div
      className={`swipeable ${className}`}
      style={{ transform: `translateX(${cardOffset}px)` }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {children}
    </div>
  );
};

// Hook for mobile detection
export const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);

    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

  return isMobile;
};

export {
  MobileNavigation,
  MobileCard,
  MobileStatsGrid,
  MobileModal,
  MobileTable,
  MobileDashboard,
  TouchButton,
  SwipeableCard
};