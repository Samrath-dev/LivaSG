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
  const [isAnimating, setIsAnimating] = useState(false);

  // Animation refs
  const animRef = useRef<number | null>(null);
  const animatingRef = useRef<boolean>(false);
  const animStartRef = useRef<number | null>(null);
  const animFromCenter = useRef<[number, number] | null>(null);
  const animToCenter = useRef<[number, number] | null>(null);
  const animFromZoom = useRef<number | null>(null);
  const animToZoom = useRef<number | null>(null);
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

  const computeZoomForBounds = (coords: [number, number][], fraction = 0.8) => {
    if (!coords || coords.length === 0) return 14;
    const lats = coords.map(c => c[0]);
    const lngs = coords.map(c => c[1]);
    const latMin = Math.min(...lats), latMax = Math.max(...lats);
    const lonMin = Math.min(...lngs), lonMax = Math.max(...lngs);
    const lonDelta = Math.max(0.00001, lonMax - lonMin);
    
    const latToMerc = (lat: number) => {
      const rad = (lat * Math.PI) / 180;
      return Math.log(Math.tan(Math.PI / 4 + rad / 2));
    };
    const mercMin = latToMerc(latMin), mercMax = latToMerc(latMax);
    const mercDelta = Math.max(1e-8, Math.abs(mercMax - mercMin));
    
    const TILE_SIZE = 256;
    const viewportW = Math.max(320, (window.innerWidth || 1024) * fraction);
    const viewportH = Math.max(320, (window.innerHeight || 768) * fraction);
    
    const zoomLon = Math.log2((360 * viewportW) / (TILE_SIZE * lonDelta));
    const worldMercatorHeight = 2 * Math.PI;
    const zoomLat = Math.log2((worldMercatorHeight * viewportH) / (TILE_SIZE * mercDelta));
    
    const rawZoom = Math.min(zoomLon, zoomLat);
    const clamped = Math.max(11, Math.min(16, rawZoom)); // Adjusted zoom range for better polygon visibility
    return Number(clamped.toFixed(4));
  };

  const animateTo = (targetCenter: [number, number], targetZoom: number, duration = 1200): Promise<void> => {
    return new Promise((resolve) => {
      if (animRef.current) {
        window.cancelAnimationFrame(animRef.current);
        animRef.current = null;
      }

      setIsAnimating(true);
      animatingRef.current = true;
      animStartRef.current = performance.now();
      animFromCenter.current = [...mapCenter];
      animToCenter.current = targetCenter;
      animFromZoom.current = mapZoom;
      animToZoom.current = targetZoom;

      const animate = (currentTime: number) => {
        if (!animStartRef.current) {
          animStartRef.current = currentTime;
        }

        const elapsed = currentTime - animStartRef.current;
        const progress = Math.min(elapsed / duration, 1);
        const eased = easeInOutQuad(progress);

        if (animFromCenter.current && animToCenter.current && animFromZoom.current !== null && animToZoom.current !== null) {
          const newLat = animFromCenter.current[0] + (animToCenter.current[0] - animFromCenter.current[0]) * eased;
          const newLng = animFromCenter.current[1] + (animToCenter.current[1] - animFromCenter.current[1]) * eased;
          const newZoom = animFromZoom.current + (animToZoom.current - animFromZoom.current) * eased;

          setMapCenter([Number(newLat.toFixed(6)), Number(newLng.toFixed(6))]);
          setMapZoom(Number(newZoom.toFixed(4)));

          if (progress < 1) {
            animRef.current = window.requestAnimationFrame(animate);
          } else {
            // Animation complete
            setIsAnimating(false);
            animatingRef.current = false;
            animRef.current = null;
            resolve();
          }
        }
      };

      animRef.current = window.requestAnimationFrame(animate);
    });
  };

  const handleAreaClick = async (areaName: string, coordinates: [number, number][]) => {
    setSelectedArea(areaName);
    setShowAreaInfo(false);
    
    // Calculate centroid of the polygon
    const lats = coordinates.map(c => c[0]);
    const lngs = coordinates.map(c => c[1]);
    const centroid: [number, number] = [
      (Math.min(...lats) + Math.max(...lats)) / 2,
      (Math.min(...lngs) + Math.max(...lngs)) / 2
    ];

    // Calculate optimal zoom level to fit the polygon
    const targetZoom = computeZoomForBounds(coordinates, 0.7); // Slightly tighter fit

    console.log(`Zooming to area: ${areaName}`, { centroid, targetZoom });

    try {
      // First zoom into the polygon with a smooth animation
      await animateTo(centroid, targetZoom, 1000);
      
      // Small delay to let user see the zoomed polygon
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Then open SpecificView
      setSpecificViewCoords(coordinates);
      setSpecificViewArea(areaName);
      setSpecificViewOpen(true);
      
    } catch (error) {
      console.error('Animation error:', error);
      // Fallback: open SpecificView immediately
      setSpecificViewCoords(coordinates);
      setSpecificViewArea(areaName);
      setSpecificViewOpen(true);
    }
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

    try {
      // Zoom back to default view
      await animateTo(defaultCenterRef.current, defaultZoomRef.current, 800);
    } catch (error) {
      console.error('Return animation error:', error);
    } finally {
      // Always close SpecificView
      setSpecificViewOpen(false);
      setSpecificViewArea(null);
      setSpecificViewCoords(null);
      setSelectedArea(null);
      setShowAreaInfo(false);
    }
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
          
          {/* Animation Overlay */}
          {isAnimating && (
            <div className="absolute inset-0 bg-black bg-opacity-10 z-[999] pointer-events-none flex items-center justify-center">
              <div className="bg-white rounded-lg px-4 py-2 shadow-lg flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-500 border-t-transparent"></div>
                <span className="text-sm text-purple-700 font-medium">Zooming to area...</span>
              </div>
            </div>
          )}

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
                    <span>Highest Rating</span>
                    <span>Lowest Rating</span>
                  </div>
                  <div className="h-4 rounded-lg bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 w-full"></div>
                  <div className="flex justify-between text-xs text-purple-600 mt-1">
                    <span>Green</span>
                    <span>Red</span>
                  </div>
                </div>

                {/* Rating Explanation */}
                <div className="mt-3 pt-3 border-t border-purple-100">
                  <div className="flex items-start gap-2">
                    <HiInformationCircle className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-purple-600 font-medium mb-1">About Neighbourhood Rating</p>
                      <p className="text-xs text-purple-500">
                        A weighted score determined by Affordability, Accessibility, Amenities, Environment and Community after weighing user preferences.
                      </p>
                    </div>
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