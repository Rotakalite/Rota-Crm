import React, { useState, useEffect } from 'react';

const MobileNavigation = ({ currentPage, onPageChange, userRole }) => {
  // Role-based navigation items
  const getNavItems = () => {
    if (userRole === 'admin') {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠' },
        { id: 'clients', label: 'Müşteriler', icon: '🏨' },
        { id: 'consultants', label: 'Danışman', icon: '👥' },
        { id: 'ai-assistant', label: 'AI Asistan', icon: '🤖' },
        { id: 'settings', label: 'Ayarlar', icon: '⚙️' }
      ];
    } else if (userRole === 'client') {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠' },
        { id: 'yeni-belge', label: 'Belgeler', icon: '📄' },
        { id: 'consumption', label: 'Tüketim', icon: '⚡' },
        { id: 'ai-assistant', label: 'AI Asistan', icon: '🤖' },
        { id: 'analytics', label: 'Analitik', icon: '📊' }
      ];
    } else if (userRole === 'consultant') {
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠' },
        { id: 'my-clients', label: 'Müşteriler', icon: '👥' },
        { id: 'reports', label: 'Raporlar', icon: '📊' },
        { id: 'ai-assistant', label: 'AI Asistan', icon: '🤖' },
        { id: 'profile', label: 'Profil', icon: '👤' }
      ];
    } else {
      // Default items
      return [
        { id: 'dashboard', label: 'Ana Sayfa', icon: '🏠' },
        { id: 'yeni-belge', label: 'Belgeler', icon: '📄' },
        { id: 'analytics', label: 'Analitik', icon: '📊' },
        { id: 'ai-assistant', label: 'AI Asistan', icon: '🤖' },
        { id: 'profile', label: 'Profil', icon: '👤' }
      ];
    }
  };

  const navItems = getNavItems();

  return (
    <nav className="mobile-nav md:hidden">
      <div className="flex justify-around items-center">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onPageChange(item.id)}
            className={`mobile-nav-item ${
              currentPage === item.id ? 'active' : ''
            }`}
          >
            <span className="text-lg mb-1">{item.icon}</span>
            <span className="text-xs font-medium">{item.label}</span>
          </button>
        ))}
      </div>
    </nav>
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