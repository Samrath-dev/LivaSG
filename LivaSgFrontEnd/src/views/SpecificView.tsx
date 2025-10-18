import { useState, useEffect, useRef } from 'react';
import { HiChevronLeft, HiStar, HiInformationCircle, HiBookmark } from 'react-icons/hi';
import OneMapInteractive from '../components/OneMapInteractive';
import CompareLocations from './CompareLocations';
import DetailsView from './DetailsView';

interface SpecificViewProps {
  areaName: string;
  coordinates: [number, number][];
  onBack: () => void;
  onRatingClick: (areaName: string, coordinates: [number, number][]) => void;
  onDetailsClick: (areaName: string, coordinates: [number, number][]) => void;
}

interface LocationResult {
  id: number;
  street: string;
  area: string;
  district: string;
  priceRange: [number, number];
  avgPrice: number;
  facilities: string[];
  description: string;
  growth: number;
  amenities: string[];
  transitScore: number;
  schoolScore: number;
  amenitiesScore: number; // Added this missing property
}

const SpecificView = ({ 
  areaName, 
  coordinates, 
  onBack, 
  onRatingClick, 
  onDetailsClick 
}: SpecificViewProps) => {
  const [mapCenter, setMapCenter] = useState<[number, number]>([1.3521, 103.8198]);
  const [mapZoom, setMapZoom] = useState<number>(14);
  const [isSaved, setIsSaved] = useState(false);
  const [selectedAreaLocation, setSelectedAreaLocation] = useState<LocationResult | null>(null);
  const [loadingAreaData, setLoadingAreaData] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsDragY, setDetailsDragY] = useState(0);
  const [detailsIsDragging, setDetailsIsDragging] = useState(false);
  const [detailsVisible, setDetailsVisible] = useState(false);
  const detailsStartYRef = useRef(0);
  const detailsModalRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (coordinates && coordinates.length > 0) {
      const centroid = centroidOf(coordinates);
      setMapCenter(centroid);
      const targetZoom = computeZoomForBounds(coordinates, 0.9);
      setMapZoom(targetZoom);
    }

    // Create mock location data for the area
    const mockLocationData: LocationResult = {
      id: Date.now(),
      street: `${areaName} Central`,
      area: areaName,
      district: "District",
      priceRange: [800000, 2000000],
      avgPrice: 1200,
      facilities: ['Near MRT', 'Good Schools', 'Shopping Malls', 'Parks'],
      description: `${areaName} is a well-established planning area with excellent amenities and connectivity.`,
      growth: 10.5,
      amenities: ["Shopping Mall", "MRT Station", "Schools", "Parks"],
      transitScore: 85,
      schoolScore: 80,
      amenitiesScore: 90 // Added the missing property
    };
    setSelectedAreaLocation(mockLocationData);
  }, [coordinates, areaName]);

  useEffect(() => {
    if (detailsOpen) {
      requestAnimationFrame(() => setDetailsVisible(true));
    } else {
      setDetailsVisible(false);
      setDetailsDragY(0);
      setDetailsIsDragging(false);
    }
  }, [detailsOpen]);

  const handleDetailsPointerDown = (e: React.PointerEvent) => {
    (e.currentTarget as Element & { setPointerCapture?: (id: number) => void })
      .setPointerCapture?.(e.pointerId);
    setDetailsIsDragging(true);
    detailsStartYRef.current = e.clientY;
  };

  const handleDetailsPointerMove = (e: React.PointerEvent) => {
    if (!detailsIsDragging) return;
    const delta = Math.max(0, e.clientY - detailsStartYRef.current);
    setDetailsDragY(delta);
  };

  const handleDetailsPointerUp = (e?: React.PointerEvent) => {
    if (e) {
      try {
        (e.currentTarget as Element & { releasePointerCapture?: (id: number) => void })
          .releasePointerCapture?.(e.pointerId);
      } catch {}
    }
    setDetailsIsDragging(false);
    const threshold = 120;
    if (detailsDragY > threshold) {
      setDetailsDragY(window.innerHeight);
      setTimeout(() => setDetailsOpen(false), 180);
      return;
    }
    setDetailsDragY(0);
  };

  // Overlay opacity tied to drag
  const detailsModalMaxHeight = (typeof window !== 'undefined') ? window.innerHeight * 0.9 : 800;
  const detailsBaseOverlayOpacity = 0.45;
  const detailsDragFactor = Math.max(0, 1 - detailsDragY / detailsModalMaxHeight);
  const detailsOverlayOpacity = detailsVisible ? detailsBaseOverlayOpacity * detailsDragFactor : 0;
  const detailsOverlayTransition = detailsIsDragging ? 'none' : 'opacity 320ms cubic-bezier(0.2,0.9,0.2,1)';

  const detailsModalTransform = detailsIsDragging
    ? `translateY(${detailsDragY}px)`
    : !detailsVisible
    ? 'translateY(100%)'
    : undefined;
  
  const detailsTransitionStyle = detailsIsDragging ? 'none' : 'transform 220ms cubic-bezier(.2,.9,.2,1)';
  const detailsSheetTranslate = detailsVisible ? `translateY(${detailsDragY}px)` : 'translateY(100%)';

  const centroidOf = (coords: [number, number][]) => {
    const lats = coords.map(c => c[0]);
    const lngs = coords.map(c => c[1]);
    const lat = (Math.min(...lats) + Math.max(...lats)) / 2;
    const lng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
    return [lat, lng] as [number, number];
  };

  const computeZoomForBounds = (coords: [number, number][], fraction = 0.8) => {
    if (!coords || coords.length === 0) return 14;
    const lats = coords.map(c => c[0]);
    const lngs = coords.map(c => c[1]);
    const latMin = Math.min(...lats);
    const latMax = Math.max(...lats);
    const lonMin = Math.min(...lngs);
    const lonMax = Math.max(...lngs);

    const lonDelta = Math.max(0.00001, lonMax - lonMin);
    const latDelta = Math.max(0.00001, latMax - latMin);

    const padding = 32;
    const viewportW = Math.max(320, (window.innerWidth || 1024) - padding * 2);
    const viewportH = Math.max(320, (window.innerHeight || 768) - padding * 2);

    const TILE_SIZE = 256;

    const zoomLon = Math.log2((360 * (viewportW * fraction)) / (TILE_SIZE * lonDelta));

    const latToMerc = (lat: number) => {
      const rad = (lat * Math.PI) / 180;
      return Math.log(Math.tan(Math.PI / 4 + rad / 2));
    };
    const mercMin = latToMerc(latMin);
    const mercMax = latToMerc(latMax);
    const mercDelta = Math.max(1e-8, Math.abs(mercMax - mercMin));

    const worldMercatorHeight = 2 * Math.PI;
    const zoomLat = Math.log2((worldMercatorHeight * (viewportH * fraction)) / (TILE_SIZE * mercDelta));

    const rawZoom = Math.min(zoomLon, zoomLat);
    const zoom = Math.max(12, Math.min(18, Math.round(rawZoom)));
    return zoom;
  };

  const handleRatingClick = () => {
    setCompareOpen(true);
  };

  const handleDetailsClick = () => {
    setDetailsOpen(true);
  };

  const handleSaveClick = () => {
    setIsSaved(!isSaved);
    console.log(`${areaName} ${isSaved ? 'unsaved' : 'saved'}`);
  };

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        <div className="flex items-center justify-between w-full mb-3">
          {/* Back Button - Top Left */}
          <button
            onClick={onBack}
            className="text-purple-700 hover:text-purple-900 transition-colors"
          >
            <HiChevronLeft className="w-6 h-6" />
          </button>

          {/* Title - Centered */}
          <div className="flex items-center text-purple-700">
            <h1 className="text-lg font-bold">{areaName}</h1>
          </div>

          {/* Save Button - Top Right */}
          <button
            onClick={handleSaveClick}
            className={`transition-colors ${
              isSaved 
                ? 'text-yellow-500 hover:text-yellow-600' 
                : 'text-purple-400 hover:text-purple-600'
            }`}
          >
            <HiBookmark className="w-6 h-6" />
          </button>
        </div>

        <p className="text-purple-600 text-sm text-center">
          Zoomed view of {areaName} planning area
        </p>

        {/* Action Buttons */}
        <div className="flex gap-3 mt-4">
          <button
            onClick={handleRatingClick}
            className="flex-1 flex items-center justify-center gap-2 bg-yellow-500 text-white py-3 px-4 rounded-xl font-medium hover:bg-yellow-600 transition-colors shadow-sm"
          >
            <HiStar className="w-5 h-5" />
            Rating
          </button>
          
          <button
            onClick={handleDetailsClick}
            className="flex-1 flex items-center justify-center gap-2 bg-purple-600 text-white py-3 px-4 rounded-xl font-medium hover:bg-purple-700 transition-colors shadow-sm"
          >
            <HiInformationCircle className="w-5 h-5" />
            Details
          </button>
        </div>
      </div>

      {/* Zoomed Map */}
      <div className={`flex-1 bg-purple-50 relative ${(compareOpen || detailsOpen) ? 'pointer-events-none filter blur-sm brightness-90' : ''}`}>
        <OneMapInteractive 
          center={mapCenter}
          zoom={mapZoom}
          showPlanningAreas={true}
          planningAreasYear={2019}
          className="w-full h-full"
        />
      </div>

      {/* Compare / Details overlays */}
      {compareOpen && selectedAreaLocation && (
        <CompareLocations
          locations={[selectedAreaLocation]}
          onClose={() => setCompareOpen(false)}
        />
      )}

      {detailsOpen && selectedAreaLocation && (
        <div
          className="fixed inset-0 z-[2000] flex items-end justify-center"
          onClick={() => setDetailsOpen(false)}
          aria-hidden
        >
          <div
            className="absolute inset-0 bg-black z-40"
            style={{ opacity: detailsOverlayOpacity, transition: detailsOverlayTransition }}
          />

          <style>{`
            @keyframes slideUp {
              0% { transform: translateY(100%); }
              100% { transform: translateY(0%); }
            }
            .sheet { animation-fill-mode: forwards; }
            .sheet.enter { animation: slideUp 420ms cubic-bezier(0.2,0.9,0.2,1); }
            .drag-handle { width: 48px; height: 6px; border-radius: 9999px; background: rgba(107,21,168,0.18); margin-top: 8px; margin-bottom: 8px; }
          `}</style>

          <div
            ref={detailsModalRef}
            className={`sheet bg-white rounded-t-2xl z-50 ${detailsVisible ? 'enter' : ''}`}
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '90vw',
              maxWidth: '90vw',
              height: '90vh',
              maxHeight: '90vh',
              transform: detailsSheetTranslate,
              transition: detailsVisible ? detailsTransitionStyle : undefined,
              borderTopLeftRadius: 16,
              borderTopRightRadius: 16,
              overflow: 'hidden',
              touchAction: 'none',
            }}
          >
            <div
              className="w-full flex items-center justify-center cursor-grab select-none"
              onPointerDown={handleDetailsPointerDown}
              onPointerMove={handleDetailsPointerMove}
              onPointerUp={handleDetailsPointerUp}
              onPointerCancel={handleDetailsPointerUp}
            >
              <div className="drag-handle" />
            </div>

            <div className="p-4 h-[calc(100%-40px)] overflow-auto">
              <DetailsView
                location={selectedAreaLocation}
                onBack={() => setDetailsOpen(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SpecificView;