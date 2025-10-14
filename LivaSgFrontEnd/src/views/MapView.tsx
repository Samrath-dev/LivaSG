import { useState } from 'react';
import { HiSearch, HiX, HiMap, HiCog } from 'react-icons/hi';
import mapDummy from '../assets/mapDummy.png'; 

interface MapViewProps {
  onSearchClick: () => void;
  searchQuery: string;
  onSearchQueryChange: (query: string) => void;
}

const MapView = ({ onSearchClick, searchQuery, onSearchQueryChange }: MapViewProps) => {
  const clearSearch = () => {
    onSearchQueryChange('');
  };

  const handleInputFocus = () => {
    // When user focuses on search input, show SearchView
    onSearchClick();
  };

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header with Search Bar */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        {/* Title and Spacers */}
        <div className="flex items-center justify-between w-full mb-3">
          {/* Spacer for balance */}
          <div className="w-6"></div>
          
          <div className="flex items-center text-purple-700">
            <HiMap className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Explore</h1>
          </div>
          
          {/* Spacer for balance */}
          <div className="w-6"></div>
        </div>

        {/* Search Bar and Settings */}
        <div className="flex items-center gap-3">
          {/* Search Bar */}
          <div className="flex-1">
            <div className="relative">
              <HiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-purple-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchQueryChange(e.target.value)}
                onFocus={handleInputFocus}
                placeholder="Search for locations..."
                className="w-full pl-10 pr-10 py-3 border border-purple-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white text-purple-900 placeholder-purple-400"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-purple-400 hover:text-purple-600 transition-colors"
                >
                  <HiX className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>

          {/* Settings Gear Icon */}
          <button
            className="p-3 rounded-xl text-purple-600 hover:text-purple-800 hover:bg-purple-100 transition-all duration-200 border border-purple-200"
            onClick={() => {
              console.log('Settings clicked');
            }}
          >
            <HiCog className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Map Content */}
      <div className="flex-1 bg-purple-50 relative">
        <div className="w-full h-full">
          <img 
            src={mapDummy} 
            alt="Singapore map"
            className="w-full h-full object-cover"
          />
          
          {/* Search Indicator */}
          {searchQuery && (
            <div className="absolute top-4 left-4 bg-purple-600 text-white px-4 py-2 rounded-xl shadow-lg">
              <p className="text-sm font-medium">Searching: <span className="font-semibold">"{searchQuery}"</span></p>
            </div>
          )}

          {/* Map Controls */}
          <div className="absolute bottom-4 right-4 flex flex-col gap-2">
            <button className="bg-white p-3 rounded-xl shadow-lg border border-purple-200 hover:bg-purple-50 transition-colors text-purple-700">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </button>
            <button className="bg-white p-3 rounded-xl shadow-lg border border-purple-200 hover:bg-purple-50 transition-colors text-purple-700">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
          </div>

          {/* Location Pins Info */}
          <div className="absolute top-4 right-4 bg-white rounded-xl p-4 shadow-lg border border-purple-200 max-w-xs">
            <h3 className="font-bold text-purple-900 text-sm mb-2">Map Legend</h3>
            <div className="space-y-2 text-xs text-purple-700">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>Affordable Areas</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span>Good Amenities</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <span>High Growth</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;