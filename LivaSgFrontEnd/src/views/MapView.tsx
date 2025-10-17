import { HiSearch, HiX, HiMap, HiCog, HiInformationCircle } from 'react-icons/hi';
import { useState } from 'react';
import OneMapInteractive from '../components/OneMapInteractive';

interface MapViewProps {
  onSearchClick: () => void;
  searchQuery: string;
  onSearchQueryChange: (query: string) => void;
  onSettingsClick: () => void; 
}

const MapView = ({ onSearchClick, searchQuery, onSearchQueryChange, onSettingsClick }: MapViewProps) => {
  const [selectedArea, setSelectedArea] = useState<string | null>(null);
  const [showAreaInfo, setShowAreaInfo] = useState(false);

  const clearSearch = () => {
    onSearchQueryChange('');
  };

  const handleInputFocus = () => {
    onSearchClick();
  };

  const handleAreaClick = (areaName: string, coordinates: [number, number][]) => {
    setSelectedArea(areaName);
    setShowAreaInfo(true);
    console.log(`Selected area: ${areaName}`, coordinates);
  };

  const clearSelectedArea = () => {
    setSelectedArea(null);
    setShowAreaInfo(false);
  };

  const handleMapClick = (lat: number, lng: number) => {
    // Clear selected area when clicking on empty map space
    if (selectedArea) {
      setSelectedArea(null);
      setShowAreaInfo(false);
    }
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

        <p className="text-purple-600 text-sm text-center">
          Search a location or click on a region on map to find out more!
        </p>

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
            onClick={onSettingsClick} 
          >
            <HiCog className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Map Content */}
      <div className="flex-1 bg-purple-50 relative">
        <div className="w-full h-full">
          <OneMapInteractive 
            center={[1.3521, 103.8198]}
            zoom={11}
            showPlanningAreas={true}
            planningAreasYear={2019}
            onAreaClick={handleAreaClick}
            onMapClick={handleMapClick}
            className="w-full h-full"
          />
          
          {/* Search Indicator */}
          {searchQuery && (
            <div className="absolute top-4 left-4 bg-purple-600 text-white px-4 py-2 rounded-xl shadow-lg z-[1000]">
              <p className="text-sm font-medium">Searching: <span className="font-semibold">"{searchQuery}"</span></p>
            </div>
          )}

          {/* Selected Area Indicator */}
          {selectedArea && (
            <div className="absolute top-4 left-4 bg-white border border-purple-200 rounded-xl shadow-lg z-[1000] max-w-sm">
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-purple-900 text-lg">{selectedArea}</h3>
                  <button
                    onClick={clearSelectedArea}
                    className="text-purple-400 hover:text-purple-600 transition-colors"
                  >
                    <HiX className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-sm text-purple-600 mb-3">Planning Area</p>
                
                {/* Area Statistics - Removed Properties and Growth, kept only Amenities and Avg Price */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-green-50 p-2 rounded-lg">
                    <div className="text-green-500">Avg Price</div>
                    <div className="font-semibold text-green-900">$850k</div>
                  </div>
                  <div className="bg-blue-50 p-2 rounded-lg">
                    <div className="text-blue-500">Amenities</div>
                    <div className="font-semibold text-blue-900">45</div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 mt-3">
                  <button className="flex-1 bg-purple-600 text-white py-2 px-3 rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors">
                    View Properties
                  </button>
                  <button className="flex-1 border border-purple-200 text-purple-700 py-2 px-3 rounded-lg text-sm font-medium hover:bg-purple-50 transition-colors">
                    Compare
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Map Legend */}
          <div className="absolute top-4 right-4 bg-white rounded-xl p-4 shadow-lg border border-purple-200 max-w-xs z-[1000]">
            <h3 className="font-bold text-purple-900 text-sm mb-2">Map Legend</h3>
            <div className="space-y-2 text-xs text-purple-700">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <span>Planning Areas</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>Affordable Areas</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span>Good Amenities</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                <span>High Growth</span>
              </div>
            </div>
            
            {/* Instructions */}
            <div className="mt-3 pt-3 border-t border-purple-100">
              <div className="flex items-start gap-2">
                <HiInformationCircle className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-purple-600">
                  Click on any colored region to see detailed information about that area.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;