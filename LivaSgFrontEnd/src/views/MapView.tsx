import { HiSearch, HiX, HiMap, HiCog, HiInformationCircle, HiChevronUp, HiChevronDown } from 'react-icons/hi';
import { useState, useRef, useEffect } from 'react';
import OneMapInteractive from '../components/OneMapInteractive';
import SpecificView from './SpecificView';

interface MapViewProps {
  onSearchClick: () => void;
  searchQuery: string;
  onSearchQueryChange: (query: string) => void;
  onSettingsClick: () => void; 
}

const MapView = ({ onSearchClick, searchQuery, onSearchQueryChange, onSettingsClick }: MapViewProps) => {
  const [selectedArea, setSelectedArea] = useState<string | null>(null);
  const [showAreaInfo, setShowAreaInfo] = useState(false);
  const [isLegendOpen, setIsLegendOpen] = useState(false);
  // New state for SpecificView
  const [specificViewOpen, setSpecificViewOpen] = useState(false);
  const [specificViewArea, setSpecificViewArea] = useState<string | null>(null);
  const [specificViewCoords, setSpecificViewCoords] = useState<[number, number][] | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([1.3521, 103.8198]);
  const [mapZoom, setMapZoom] = useState<number>(12);

  // Animation refs (keeping for back navigation)
  const animRef = useRef<number | null>(null);
  const defaultInitializedRef = useRef<boolean>(false);
  const defaultCenterRef = useRef<[number, number]>(mapCenter);
  const defaultZoomRef = useRef<number>(mapZoom);

  useEffect(() => {
    return () => {
      if (animRef.current) {
        window.cancelAnimationFrame(animRef.current);
        animRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!defaultInitializedRef.current) {
      defaultCenterRef.current = mapCenter;
      defaultZoomRef.current = mapZoom;
      defaultInitializedRef.current = true;
    }
  }, []);

  const easeInOutQuad = (t: number) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t);

  const animateTo = (targetCenter: [number, number], targetZoom: number, duration = 1200): Promise<void> => {
    return new Promise((resolve) => {
      if (animRef.current) {
        window.cancelAnimationFrame(animRef.current);
        animRef.current = null;
      }

      const animStartTime = performance.now();
      const animFromCenter = [...mapCenter];
      const animFromZoom = mapZoom;

      const animate = (currentTime: number) => {
        const elapsed = currentTime - animStartTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = easeInOutQuad(progress);

        const newLat = animFromCenter[0] + (targetCenter[0] - animFromCenter[0]) * eased;
        const newLng = animFromCenter[1] + (targetCenter[1] - animFromCenter[1]) * eased;
        const newZoom = animFromZoom + (targetZoom - animFromZoom) * eased;

        setMapCenter([Number(newLat.toFixed(6)), Number(newLng.toFixed(6))]);
        setMapZoom(Number(newZoom.toFixed(4)));

        if (progress < 1) {
          animRef.current = window.requestAnimationFrame(animate);
        } else {
          // Animation complete
          animRef.current = null;
          resolve();
        }
      };

      animRef.current = window.requestAnimationFrame(animate);
    });
  };

  const handleAreaClick = async (areaName: string, coordinates: [number, number][]) => {
    setSelectedArea(areaName);
    setShowAreaInfo(false);
    
    // Directly open SpecificView without zooming animation
    setSpecificViewCoords(coordinates);
    setSpecificViewArea(areaName);
    setSpecificViewOpen(true);
  };

  const clearSearch = () => {
    onSearchQueryChange('');
  };

  const handleInputFocus = () => {
    onSearchClick();
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

  const toggleLegend = () => {
    setIsLegendOpen(!isLegendOpen);
  };

  // Handler for closing SpecificView
  const handleBackFromSpecific = async () => {
    if (animRef.current) {
      window.cancelAnimationFrame(animRef.current);
      animRef.current = null;
    }

    // Zoom back to default view with animation
    await animateTo(defaultCenterRef.current, defaultZoomRef.current, 800);
    
    // Close SpecificView
    setSpecificViewOpen(false);
    setSpecificViewArea(null);
    setSpecificViewCoords(null);
    setSelectedArea(null);
    setShowAreaInfo(false);
  };

  // Handlers for SpecificView buttons
  const handleSpecificRating = (areaName: string, coordinates: [number, number][]) => {
    console.log('Opening rating for:', areaName);
  };

  const handleSpecificDetails = (areaName: string, coordinates: [number, number][]) => {
    console.log('Opening details for:', areaName);
  };

  // If SpecificView is open, render it instead of the main map
  if (specificViewOpen && specificViewArea && specificViewCoords) {
    return (
      <SpecificView
        areaName={specificViewArea}
        coordinates={specificViewCoords}
        onBack={handleBackFromSpecific}
        onRatingClick={handleSpecificRating}
        onDetailsClick={handleSpecificDetails}
      />
    );
  }

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header with Search Bar */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        {/* Title and Spacers */}
        <div className="flex items-center justify-between w-full mb-3">
          <div className="w-6"></div>
          
          <div className="flex items-center text-purple-700">
            <HiMap className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Explore</h1>
          </div>
          
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
      <div className="flex-1 bg-[#6da7e3] relative">
        <div className="w-full h-full" style={{ backgroundColor: '#6da7e3' }}>
          <OneMapInteractive 
            center={mapCenter}
            zoom={mapZoom}
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

          {/* Legend Toggle Button */}
          <div className="absolute bottom-4 right-4 flex flex-col items-end gap-2 z-[1000]">
            {/* Map Legend - Only shown when isLegendOpen is true */}
            {isLegendOpen && (
              <div className="bg-white rounded-xl p-4 shadow-lg border border-purple-200 max-w-xs mb-2">
                <h3 className="font-bold text-purple-900 text-sm mb-2">Neighbourhood Rating</h3>
                
                {/* Color Gradient Legend */}
                <div className="mb-3">
                  <div className="flex justify-between text-xs text-purple-600 mb-1">
                    <span>Higher Rating</span>
                    <span>Lower Rating</span>
                  </div>
                  <div className="h-4 rounded-lg bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 w-full"></div>
                  <div className="flex justify-between text-xs text-purple-600 mt-1">
                    <span>Better</span>
                    <span>Worse</span>
                  </div>
                </div>

                {/* Relative Rating Explanation */}
                <div className="mt-3 pt-3 border-t border-purple-100">
                  <div className="flex items-start gap-2">
                    <HiInformationCircle className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-purple-600 font-medium mb-1">Relative Rating Scale</p>
                      <p className="text-xs text-purple-500">
                        Colors show relative performance compared to other areas. Green areas perform better, red areas perform worse relative to neighboring regions.
                      </p>
                    </div>
                  </div>
                </div>

                {/* No Data Indicator */}
                <div className="mt-3 pt-3 border-t border-purple-100">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded border border-gray-300 bg-gray-300"></div>
                    <span className="text-xs text-purple-600">Gray areas = No data available</span>
                  </div>
                </div>

                {/* Instructions */}
                <div className="mt-3 pt-3 border-t border-purple-100">
                  <p className="text-xs text-purple-600">
                    Click on any colored region to see detailed information about that area.
                  </p>
                </div>
              </div>
            )}

            {/* Toggle Button */}
            <button
              onClick={toggleLegend}
              className="flex items-center gap-2 bg-purple-600 text-white px-4 py-3 rounded-xl shadow-lg hover:bg-purple-700 transition-colors border border-purple-500"
            >
              <HiInformationCircle className="w-5 h-5" />
              <span className="font-medium">{isLegendOpen ? 'Hide Legend' : 'Show Legend'}</span>
              {isLegendOpen ? (
                <HiChevronDown className="w-4 h-4" />
              ) : (
                <HiChevronUp className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;