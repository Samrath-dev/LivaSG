import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Types for planning areas
interface PlanningAreaFeature {
  type: "Feature";
  properties: {
    pln_area_n: string;
    [key: string]: any;
  };
  geometry: {
    type: "MultiPolygon" | "Polygon";
    coordinates: number[][][][] | number[][][];
  };
}

interface PlanningAreaData {
  type: "FeatureCollection";
  features: PlanningAreaFeature[];
}

interface ChoroplethData {
  areaId: string;
  total: number;
  weightsProfileId: string;
  computedAt: string;
}

interface OneMapInteractiveProps {
  center?: [number, number];
  zoom?: number;
  markers?: Array<{
    position: [number, number];
    popup?: string;
    color?: string;
  }>;
  polygons?: Array<{
    positions: [number, number][];
    color?: string;
    fillColor?: string;
    fillOpacity?: number;
    popup?: string;
  }>;
  showPlanningAreas?: boolean;
  planningAreasYear?: number;
  weightsProfileId?: string;
  onMapClick?: (lat: number, lng: number) => void;
  onAreaClick?: (areaName: string, coordinates: [number, number][], rating?: number) => void;
  className?: string;
}

const OneMapInteractive = ({ 
  center = [1.3521, 103.8198], // Singapore center
  zoom = 12,
  markers = [],
  polygons = [],
  showPlanningAreas = true,
  planningAreasYear = 2019,
  weightsProfileId = 'default',
  onMapClick,
  onAreaClick,
  className = ''
}: OneMapInteractiveProps) => {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const polygonsRef = useRef<L.Polygon[]>([]);
  const planningAreasRef = useRef<L.Polygon[]>([]);
  const [planningAreas, setPlanningAreas] = useState<PlanningAreaFeature[]>([]);
  const [choroplethData, setChoroplethData] = useState<ChoroplethData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingChoropleth, setIsLoadingChoropleth] = useState(false);

  // Fetch planning areas from API
  useEffect(() => {
    if (!showPlanningAreas) return;

    const fetchPlanningAreas = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `http://localhost:8000/onemap/planning-areas?year=${planningAreasYear}`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch planning areas');
        }
        
        const data: PlanningAreaData = await response.json();
        setPlanningAreas(data.features || []);
      } catch (error) {
        console.error('Error fetching planning areas:', error);
        setPlanningAreas([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPlanningAreas();
  }, [showPlanningAreas, planningAreasYear]);

  // Fetch choropleth data
  useEffect(() => {
    if (!showPlanningAreas) return;

    const fetchChoroplethData = async () => {
      setIsLoadingChoropleth(true);
      try {
        const response = await fetch(
          `http://localhost:8000/map/choropleth?weightsId=${weightsProfileId}`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch choropleth data');
        }
        
        const data: ChoroplethData[] = await response.json();
        setChoroplethData(data);
      } catch (error) {
        console.error('Error fetching choropleth data:', error);
        setChoroplethData([]);
      } finally {
        setIsLoadingChoropleth(false);
      }
    };

    fetchChoroplethData();
  }, [showPlanningAreas, weightsProfileId]);

  // Convert GeoJSON coordinates to Leaflet positions
  const convertCoordinates = (coords: number[][][][] | number[][][]): [number, number][][] => {
    if (coords.length === 0) return [];
    
    // Handle MultiPolygon coordinates (4 levels deep)
    if (Array.isArray(coords[0][0][0])) {
      return (coords as number[][][][]).map(polygon => 
        polygon[0].map(coord => [coord[1], coord[0]] as [number, number])
      );
    }
    
    // Handle Polygon coordinates (3 levels deep)
    return [(coords as number[][][])[0].map(coord => [coord[1], coord[0]] as [number, number])];
  };

  // Get rating for a specific area
  const getAreaRating = (areaName: string): number | null => {
    const areaData = choroplethData.find(data => 
      data.areaId.toLowerCase() === areaName.toLowerCase()
    );
    return areaData ? areaData.total : null;
  };

  // Generate color based on rating (green = high, red = low)
  const getRatingColor = (rating: number | null): string => {
    if (rating === null) {
      return '#cccccc'; // Gray for areas without data
    }
    
    // Normalize rating to 0-1 scale (assuming ratings are between 0 and 1)
    const normalizedRating = Math.max(0, Math.min(1, rating));
    
    // Create gradient from red (0) to green (1)
    if (normalizedRating < 0.5) {
      // Red to Yellow
      const ratio = normalizedRating * 2;
      const red = 255;
      const green = Math.floor(255 * ratio);
      return `rgb(${red}, ${green}, 0)`;
    } else {
      // Yellow to Green
      const ratio = (normalizedRating - 0.5) * 2;
      const red = Math.floor(255 * (1 - ratio));
      const green = 255;
      return `rgb(${red}, ${green}, 0)`;
    }
  };

  // Get color intensity for fill opacity
  const getFillOpacity = (rating: number | null): number => {
    if (rating === null) return 0.1;
    return 0.3 + (rating * 0.4); // 0.3 to 0.7 opacity based on rating
  };

  // Get border weight based on rating
  const getBorderWeight = (rating: number | null): number => {
    if (rating === null) return 1;
    return 1 + (rating * 2); // 1 to 3 weight based on rating
  };

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapRef.current) {
      mapRef.current = L.map(mapContainerRef.current, {
        center: center,
        zoom: zoom,
        zoomControl: true,
      });

      // Add OneMap tiles
      L.tileLayer('https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png', {
        detectRetina: true,
        maxZoom: 19,
        minZoom: 11,
        attribution: '<img src="https://www.onemap.gov.sg/web-assets/images/logo/om_logo.png" style="height:20px;width:20px;"/> OneMap | Map data © contributors, <a href="http://SLA.gov.sg">Singapore Land Authority</a>'
      }).addTo(mapRef.current);

      // Add click handler
      if (onMapClick) {
        mapRef.current.on('click', (e: L.LeafletMouseEvent) => {
          onMapClick(e.latlng.lat, e.latlng.lng);
        });
      }
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Update center and zoom
  useEffect(() => {
    if (mapRef.current) {
      mapRef.current.setView(center, zoom);
    }
  }, [center, zoom]);

  // Update markers
  useEffect(() => {
    if (!mapRef.current) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add new markers
    markers.forEach(markerData => {
      if (mapRef.current) {
        const marker = L.marker(markerData.position);
        
        if (markerData.popup) {
          marker.bindPopup(markerData.popup);
        }
        
        marker.addTo(mapRef.current);
        markersRef.current.push(marker);
      }
    });
  }, [markers]);

  // Update custom polygons
  useEffect(() => {
    if (!mapRef.current) return;

    // Clear existing polygons
    polygonsRef.current.forEach(polygon => polygon.remove());
    polygonsRef.current = [];

    // Add new polygons
    polygons.forEach(polygonData => {
      if (mapRef.current) {
        const polygon = L.polygon(polygonData.positions, {
          color: polygonData.color || '#3388ff',
          fillColor: polygonData.fillColor || '#3388ff',
          fillOpacity: polygonData.fillOpacity || 0.2,
        });
        
        if (polygonData.popup) {
          polygon.bindPopup(polygonData.popup);
        }
        
        polygon.addTo(mapRef.current);
        polygonsRef.current.push(polygon);
      }
    });
  }, [polygons]);

  // Update planning areas polygons with choropleth coloring
  useEffect(() => {
    if (!mapRef.current || !showPlanningAreas) return;

    // Clear existing planning areas
    planningAreasRef.current.forEach(polygon => polygon.remove());
    planningAreasRef.current = [];

    // Add planning area polygons with choropleth coloring
    planningAreas.forEach(area => {
      if (mapRef.current) {
        const coordinates = convertCoordinates(area.geometry.coordinates);
        const areaRating = getAreaRating(area.properties.pln_area_n);
        const areaColor = getRatingColor(areaRating);
        const fillOpacity = getFillOpacity(areaRating);
        const borderWeight = getBorderWeight(areaRating);
        
        coordinates.forEach(polygonCoords => {
          const polygon = L.polygon(polygonCoords, {
            color: '#000000', // Black borders for separation
            fillColor: areaColor,
            fillOpacity: fillOpacity,
            weight: borderWeight,
            opacity: 0.8
          });

          // Add click handler for area selection
          polygon.on('click', (e: L.LeafletMouseEvent) => {
            L.DomEvent.stopPropagation(e);
            if (onAreaClick) {
              onAreaClick(area.properties.pln_area_n, polygonCoords, areaRating || undefined);
            }
          });

          // Add hover effects
          polygon.on('mouseover', function (this: L.Polygon, e: L.LeafletMouseEvent) {
            this.setStyle({
              fillOpacity: Math.min(0.8, fillOpacity + 0.2),
              weight: borderWeight + 1
            });
          });

          polygon.on('mouseout', function (this: L.Polygon, e: L.LeafletMouseEvent) {
            this.setStyle({
              fillOpacity: fillOpacity,
              weight: borderWeight
            });
          });

          polygon.addTo(mapRef.current!);
          planningAreasRef.current.push(polygon);
        });
      }
    });
  }, [planningAreas, choroplethData, showPlanningAreas, onAreaClick]);

  return (
    <div className="relative w-full h-full">
      <div 
        ref={mapContainerRef} 
        className={className}
        style={{ width: '100%', height: '100%' }}
      />
      
      {/* Loading overlay */}
      {(isLoading || isLoadingChoropleth) && showPlanningAreas && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg px-4 py-2 z-[1000]">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-500 border-t-transparent"></div>
            <span className="text-sm text-purple-700">
              {isLoading ? 'Loading planning areas...' : 'Loading ratings...'}
            </span>
          </div>
        </div>
      )}
      
      {/* Error message */}
      {!isLoading && !isLoadingChoropleth && showPlanningAreas && planningAreas.length === 0 && (
        <div className="absolute top-4 left-4 bg-red-50 border border-red-200 rounded-lg shadow-lg px-4 py-2 z-[1000]">
          <span className="text-sm text-red-700">Failed to load planning areas</span>
        </div>
      )}
    </div>
  );
};

export default OneMapInteractive;