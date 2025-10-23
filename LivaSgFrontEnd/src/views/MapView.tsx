import { HiSearch, HiX, HiMap, HiCog, HiInformationCircle, HiChevronUp, HiChevronDown } from 'react-icons/hi';
import { useState, useRef, useEffect } from 'react';
import OneMapInteractive from '../components/OneMapInteractive';
import SpecificView from './SpecificView'; // Import the SpecificView

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

  // smooth pan/zoom animation state refs
  const animRef = useRef<number | null>(null);
  const animatingRef = useRef<boolean>(false);
  const lastUpdateRef = useRef<number>(0);
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
        window.cancelAnimationFrame(animRef.current as number);
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
    if (!coords || coords.length === 0) return 11;
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
    const clamped = Math.max(2, Math.min(18, rawZoom));
    return Number(clamped.toFixed(4));
  };

  const animateTo = (targetCenter: [number, number], targetZoom: number, duration = 800) => {
    const FRAME_MS = 1000 / 120;

    if (animRef.current) {
      window.cancelAnimationFrame(animRef.current as number);
      animRef.current = null;
    }

    animatingRef.current = true;
    lastUpdateRef.current = 0;

    return new Promise<void>((resolve) => {
      const fromCenter = mapCenter;
      const fromZoom = mapZoom;
      const start = performance.now();

      const step = (now: number) => {
        const elapsed = now - start;
        const tRaw = Math.min(1, Math.max(0, elapsed / duration));
        const eased = easeInOutQuad(tRaw);

        const lat = fromCenter[0] + (targetCenter[0] - fromCenter[0]) * eased;
        const lng = fromCenter[1] + (targetCenter[1] - fromCenter[1]) * eased;
        const z = fromZoom + (targetZoom - fromZoom) * eased;

        // Throttle updates to reduce re-render pressure on the map component
        if (tRaw >= 1 || (performance.now() - lastUpdateRef.current) >= FRAME_MS) {
          lastUpdateRef.current = performance.now();
          setMapCenter([Number(lat.toFixed(6)), Number(lng.toFixed(6))]);
          setMapZoom(Number(z.toFixed(4)));
        }

        if (tRaw < 1) {
          animRef.current = window.requestAnimationFrame(step);
        } else {
          animRef.current = null;
          animatingRef.current = false;
          // ensure final exact values
          setMapCenter([Number(targetCenter[0].toFixed(6)), Number(targetCenter[1].toFixed(6))]);
          setMapZoom(Number(targetZoom.toFixed(4)));
          resolve();
        }
      };

      animRef.current = window.requestAnimationFrame(step);
    });
  };

  const handleAreaClick = (areaName: string, coordinates: [number, number][]) => {
    setSelectedArea(areaName);
    setShowAreaInfo(false);
    
    const lats = coordinates.map(c => c[0]);
    const lngs = coordinates.map(c => c[1]);
    const c: [number, number] = [
      (Math.min(...lats) + Math.max(...lats)) / 2,
      (Math.min(...lngs) + Math.max(...lngs)) / 2
    ];

    let targetZoom = 14;
    try {
      // if computeZoomForBounds exists in this file, use it; otherwise fallback
      // @ts-ignore
      if (typeof computeZoomForBounds === 'function') {
        // @ts-ignore
        targetZoom = computeZoomForBounds(coordinates, 0.8);
      }
    } catch {}

    if (animRef.current) {
      window.cancelAnimationFrame(animRef.current as number);
      animRef.current = null;
    }

    animateTo(c, targetZoom, 900).then(() => {
      setSpecificViewCoords(coordinates);
      setSpecificViewArea(areaName);
      setSpecificViewOpen(true);
      console.log(`Opening SpecificView for area: ${areaName}`, coordinates);
    }).catch(() => {
      setSpecificViewCoords(coordinates);
      setSpecificViewArea(areaName);
      setSpecificViewOpen(true);
    });
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

  // Handler for opening SpecificView
  const handleViewDetails = () => {
    if (selectedArea && specificViewCoords) {
      setSpecificViewArea(selectedArea);
      setSpecificViewOpen(true);
    }
  };

  // Handler for closing SpecificView
  const handleBackFromSpecific = () => {
    if (animRef.current) {
      window.cancelAnimationFrame(animRef.current as number);
      animRef.current = null;
    }

    // keep SpecificView visible while animation runs; hide after animation completes
    animateTo(defaultCenterRef.current, defaultZoomRef.current, 800).then(() => {
      setSpecificViewOpen(false);
      setSpecificViewArea(null);
      setSpecificViewCoords(null);
      setSelectedArea(null);
      setShowAreaInfo(false);
    }).catch(() => {
      // fallback: hide if animation fails
      setSpecificViewOpen(false);
      setSpecificViewArea(null);
      setSpecificViewCoords(null);
      setSelectedArea(null);
      setShowAreaInfo(false);
    });
  };

  // Handlers for SpecificView buttons
  const handleSpecificRating = (areaName: string, coordinates: [number, number][]) => {
    console.log('Opening rating for:', areaName);
    // You can add your rating logic here
    // For example: setRatingOpen(true);
  };

  const handleSpecificDetails = (areaName: string, coordinates: [number, number][]) => {
    console.log('Opening details for:', areaName);
    // You can add your details logic here
    // For example: setDetailsOpen(true);
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