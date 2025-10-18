import { useState, useEffect } from 'react';
import { HiChevronLeft, HiStar, HiInformationCircle, HiBookmark } from 'react-icons/hi';
import OneMapInteractive from '../components/OneMapInteractive';

interface SpecificViewProps {
  areaName: string;
  coordinates: [number, number][];
  onBack: () => void;
  onRatingClick: (areaName: string, coordinates: [number, number][]) => void;
  onDetailsClick: (areaName: string, coordinates: [number, number][]) => void;
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

  useEffect(() => {
    if (coordinates && coordinates.length > 0) {
      // Calculate centroid for the polygon
      const centroid = centroidOf(coordinates);
      setMapCenter(centroid);
      
      // Calculate appropriate zoom level to fit the polygon
      const targetZoom = computeZoomForBounds(coordinates, 0.9);
      setMapZoom(targetZoom);
    }
  }, [coordinates]);

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

    // longitude-based zoom
    const zoomLon = Math.log2((360 * (viewportW * fraction)) / (TILE_SIZE * lonDelta));

    // latitude-based zoom with Mercator projection
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
    const zoom = Math.max(12, Math.min(18, Math.round(rawZoom))); // Higher minimum zoom for closer view
    return zoom;
  };

  const handleRatingClick = () => {
    onRatingClick(areaName, coordinates);
  };

  const handleDetailsClick = () => {
    onDetailsClick(areaName, coordinates);
  };

  const handleSaveClick = () => {
    setIsSaved(!isSaved);
    // You can add your save logic here
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
      <div className="flex-1 bg-purple-50 relative">
        <OneMapInteractive 
          center={mapCenter}
          zoom={mapZoom}
          showPlanningAreas={true}
          planningAreasYear={2019}
          className="w-full h-full"
        />
      </div>
    </div>
  );
};

export default SpecificView;