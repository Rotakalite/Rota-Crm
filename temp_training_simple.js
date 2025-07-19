// SIMPLE TRAINING MANAGEMENT - NO JSX ISSUES

  return (
    <div className="space-y-6">
      {/* Client Selection */}
      {(userRole === 'admin' || userRole === 'consultant') && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Müşteri Seçimi</h3>
          <select
            value={selectedClient}
            onChange={(e) => setSelectedClient(e.target.value)}
            className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Bir müşteri seçin...</option>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>
                {client.hotel_name || client.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Training Management */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-800">📚 Eğitim Yönetimi</h2>
            <div className="flex items-center space-x-2">
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  📋 Liste
                </button>
                <button
                  onClick={() => setViewMode('calendar')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    viewMode === 'calendar' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  📅 Takvim
                </button>
              </div>
            </div>
          </div>

          {/* Calendar or List View */}
          {viewMode === 'calendar' ? (
            <TrainingCalendar trainings={trainings} clients={clients} />
          ) : (
            <div>Training List Here</div>
          )}
        </div>
      </div>
    </div>
  );
};