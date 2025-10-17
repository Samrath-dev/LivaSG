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
  onMapClick?: (lat: number, lng: number) => void;
  onAreaClick?: (areaName: string, coordinates: [number, number][]) => void;
  className?: string;
}

const OneMapInteractive = ({ 
  center = [1.3521, 103.8198], // Singapore center
  zoom = 12,
  markers = [],
  polygons = [],
  showPlanningAreas = true,
  planningAreasYear = 2019,
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
  const [isLoading, setIsLoading] = useState(false);

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

  // Generate color based on area name for consistency
  const getAreaColor = (areaName: string): string => {
    const colors = [
      '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
      '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43',
      '#a29bfe', '#fd79a8', '#81ecec', '#55efc4', '#74b9ff',
      '#dfe6e9', '#00b894', '#e17055', '#0984e3', '#6c5ce7'
    ];
    const index = areaName.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length;
    return colors[index];
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

  // Update planning areas polygons
  useEffect(() => {
    if (!mapRef.current || !showPlanningAreas) return;

    // Clear existing planning areas
    planningAreasRef.current.forEach(polygon => polygon.remove());
    planningAreasRef.current = [];

    // Add planning area polygons
    planningAreas.forEach(area => {
      if (mapRef.current) {
        const coordinates = convertCoordinates(area.geometry.coordinates);
        
        coordinates.forEach(polygonCoords => {
          const polygon = L.polygon(polygonCoords, {
            color: getAreaColor(area.properties.pln_area_n),
            fillColor: getAreaColor(area.properties.pln_area_n),
            fillOpacity: 0.3,
            weight: 2,
            opacity: 0.8
          });

          // Add popup with area name
          polygon.bindPopup(`
            <div class="p-2">
              <h3 class="font-bold text-lg">${area.properties.pln_area_n}</h3>
              <p class="text-sm text-gray-600">Planning Area</p>
            </div>
          `);

          // Add click handler for area selection
          polygon.on('click', (e: L.LeafletMouseEvent) => {
            L.DomEvent.stopPropagation(e);
            if (onAreaClick) {
              onAreaClick(area.properties.pln_area_n, polygonCoords);
            }
          });

          // Add hover effects with proper 'this' typing
          polygon.on('mouseover', function (this: L.Polygon, e: L.LeafletMouseEvent) {
            this.setStyle({
              fillOpacity: 0.5,
              weight: 3
            });
          });

          polygon.on('mouseout', function (this: L.Polygon, e: L.LeafletMouseEvent) {
            this.setStyle({
              fillOpacity: 0.3,
              weight: 2
            });
          });

          polygon.addTo(mapRef.current!);
          planningAreasRef.current.push(polygon);
        });
      }
    });
  }, [planningAreas, showPlanningAreas, onAreaClick]);

  return (
    <div className="relative w-full h-full">
      <div 
        ref={mapContainerRef} 
        className={className}
        style={{ width: '100%', height: '100%' }}
      />
      
      {/* Loading overlay for planning areas */}
      {isLoading && showPlanningAreas && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg px-4 py-2 z-[1000]">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-500 border-t-transparent"></div>
            <span className="text-sm text-purple-700">Loading planning areas...</span>
          </div>
        </div>
      )}
      
      {/* Error message */}
      {!isLoading && showPlanningAreas && planningAreas.length === 0 && (
        <div className="absolute top-4 left-4 bg-red-50 border border-red-200 rounded-lg shadow-lg px-4 py-2 z-[1000]">
          <span className="text-sm text-red-700">Failed to load planning areas</span>
        </div>
      )}
    </div>
  );
};

export default OneMapInteractive;