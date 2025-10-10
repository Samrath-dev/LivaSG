import { useState } from 'react';
import { HiSearch, HiX } from "react-icons/hi";
import mapDummy from '../assets/mapDummy.png'; 

const MapView = () => {
  const [searchQuery, setSearchQuery] = useState('');

  const clearSearch = () => {
    setSearchQuery('');
  };

  return (
    <div className="h-full flex flex-col">
      {/* Search Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-4 py-3">
          <div className="relative">
            <HiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Location Search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <HiX className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Map Content - fills remaining space */}
      <div className="flex-1 bg-gray-100">
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-center">
            <p className="text-gray-500">Map will be displayed here</p>
            <p className="text-sm text-gray-400 mt-2">Search: {searchQuery || 'No search query'}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;