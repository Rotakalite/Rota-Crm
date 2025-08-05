import React from 'react';

// Mobile-optimized table component that converts table data to cards
const MobileDataTable = ({ data, columns, title, onRowClick, actions = [] }) => {
  if (!data || data.length === 0) {
    return (
      <div className="mobile-card">
        <div className="text-center py-8">
          <p className="text-gray-500">Veri bulunamadı</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mobile-data-table">
      {title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      
      <div className="space-y-3">
        {data.map((row, index) => (
          <div
            key={index}
            className={`mobile-card cursor-pointer hover:shadow-md transition-shadow ${
              onRowClick ? 'hover:bg-gray-50' : ''
            }`}
            onClick={() => onRowClick && onRowClick(row)}
          >
            <div className="space-y-3">
              {columns.map((column) => (
                <div key={column.key} className="flex justify-between items-start">
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-600">
                      {column.label}:
                    </span>
                  </div>
                  <div className="flex-2 text-right ml-4">
                    <span className="text-sm text-gray-900">
                      {typeof column.render === 'function'
                        ? column.render(row[column.key], row)
                        : row[column.key] || '-'
                      }
                    </span>
                  </div>
                </div>
              ))}
              
              {/* Action buttons */}
              {actions.length > 0 && (
                <div className="pt-3 border-t border-gray-100">
                  <div className="flex flex-wrap gap-2">
                    {actions.map((action, actionIndex) => (
                      <button
                        key={actionIndex}
                        onClick={(e) => {
                          e.stopPropagation();
                          action.onClick(row);
                        }}
                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                          action.variant === 'danger'
                            ? 'bg-red-100 text-red-700 hover:bg-red-200'
                            : action.variant === 'warning'
                            ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                            : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                        }`}
                      >
                        {action.icon && <span className="mr-1">{action.icon}</span>}
                        {action.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Mobile-optimized form component
const MobileForm = ({ children, title, onSubmit, submitLabel = "Kaydet" }) => {
  return (
    <div className="mobile-card">
      {title && (
        <div className="mobile-card-header">
          <h3 className="font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      
      <form onSubmit={onSubmit} className="space-y-4">
        {children}
        
        <div className="pt-4">
          <button
            type="submit"
            className="w-full bg-green-600 hover:bg-green-700 text-white py-3 px-4 rounded-lg font-medium transition-colors"
          >
            {submitLabel}
          </button>
        </div>
      </form>
    </div>
  );
};

// Mobile form field component
const MobileFormField = ({ label, type = "text", value, onChange, placeholder, required = false, options = [] }) => {
  const inputClasses = "w-full p-3 border-2 border-gray-200 rounded-lg focus:border-green-500 focus:outline-none transition-colors text-base";

  if (type === 'select') {
    return (
      <div className="mobile-form-group">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <select
          value={value}
          onChange={onChange}
          required={required}
          className={inputClasses}
        >
          <option value="">{placeholder || `${label} seçin`}</option>
          {options.map((option, index) => (
            <option key={index} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (type === 'textarea') {
    return (
      <div className="mobile-form-group">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <textarea
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          rows={4}
          className={inputClasses}
        />
      </div>
    );
  }

  return (
    <div className="mobile-form-group">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        className={inputClasses}
      />
    </div>
  );
};

// Mobile stats component
const MobileStatsCard = ({ title, value, change, icon, color = "green" }) => {
  const colorClasses = {
    green: "text-green-600 bg-green-100",
    blue: "text-blue-600 bg-blue-100",
    yellow: "text-yellow-600 bg-yellow-100",
    red: "text-red-600 bg-red-100",
    purple: "text-purple-600 bg-purple-100"
  };

  return (
    <div className="mobile-card text-center">
      <div className={`w-12 h-12 ${colorClasses[color]} rounded-full flex items-center justify-center mx-auto mb-3`}>
        <span className="text-xl">{icon}</span>
      </div>
      <div className="space-y-1">
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-600">{title}</p>
        {change !== undefined && (
          <p className={`text-xs ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? '↗' : '↘'} {Math.abs(change)}%
          </p>
        )}
      </div>
    </div>
  );
};

// Mobile action sheet (bottom modal)
const MobileActionSheet = ({ isOpen, onClose, title, actions = [] }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl max-h-96 overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">{title}</h3>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full"
            >
              ✕
            </button>
          </div>
        </div>
        <div className="p-4 space-y-2">
          {actions.map((action, index) => (
            <button
              key={index}
              onClick={() => {
                action.onClick();
                onClose();
              }}
              className={`w-full flex items-center space-x-3 p-4 rounded-lg transition-colors ${
                action.variant === 'danger'
                  ? 'text-red-600 hover:bg-red-50'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {action.icon && <span className="text-xl">{action.icon}</span>}
              <span className="font-medium">{action.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export {
  MobileDataTable,
  MobileForm,
  MobileFormField,
  MobileStatsCard,
  MobileActionSheet
};