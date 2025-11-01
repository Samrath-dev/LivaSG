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

// Interface for polygon styling
interface PolygonStyle {
  fillColor: string;
  fillOpacity: number;
  color: string;
  weight: number;
  opacity: number;
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
  // New locking props
  locked?: boolean;
  dragging?: boolean;
  touchZoom?: boolean;
  scrollWheelZoom?: boolean;
  doubleClickZoom?: boolean;
  boxZoom?: boolean;
  keyboard?: boolean;
  zoomControl?: boolean;
  // New polygon styling prop
  getPolygonStyle?: (areaName: string) => PolygonStyle;
}

const OneMapInteractive = ({ 
  center = [1.3521, 103.8198], // Singapore center
  zoom = 13, // Increased default zoom to prevent starting too far out
  markers = [],
  polygons = [],
  showPlanningAreas = true,
  planningAreasYear = 2019,
  weightsProfileId = 'default',
  onMapClick,
  onAreaClick,
  className = '',
  // New locking props with defaults
  locked = false,
  dragging = true,
  touchZoom = true,
  scrollWheelZoom = true,
  doubleClickZoom = true,
  boxZoom = true,
  keyboard = true,
  zoomControl = true,
  // New polygon styling prop
  getPolygonStyle
}: OneMapInteractiveProps) => {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const polygonsRef = useRef<L.Polygon[]>([]);
  const planningAreasRef = useRef<L.Polygon[]>([]);
  const zoomControlRef = useRef<L.Control.Zoom | null>(null);
  const [planningAreas, setPlanningAreas] = useState<PlanningAreaFeature[]>([]);
  const [choroplethData, setChoroplethData] = useState<ChoroplethData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingChoropleth, setIsLoadingChoropleth] = useState(false);
  const [dataRange, setDataRange] = useState<{ min: number; max: number; range: number }>({ 
    min: 0, 
    max: 1, 
    range: 1 
  });

  // Singapore bounds to prevent grey areas - using LatLng objects
  const singaporeBounds = L.latLngBounds(
    L.latLng(1.15, 103.6), // Southwest corner
    L.latLng(1.48, 104.1)  // Northeast corner
  );

  // Stricter zoom limits - prevent excessive zoom out
  const MIN_ZOOM = 12; 
  const MAX_ZOOM = 18;

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

  // Fetch choropleth data and calculate dynamic range
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
        
        // Calculate dynamic range from actual data
        if (data.length > 0) {
          const ratings = data.map(d => d.total).filter(total => total != null);
          if (ratings.length > 0) {
            const minRating = Math.min(...ratings);
            const maxRating = Math.max(...ratings);
            const range = maxRating - minRating;
            
            setDataRange({
              min: minRating,
              max: maxRating,
              range: range
            });
          }
        }
      } catch (error) {
        console.error('Error fetching choropleth data:', error);
        setChoroplethData([]);
      } finally {
        setIsLoadingChoropleth(false);
      }
    };

    fetchChoroplethData();
  }, [showPlanningAreas, weightsProfileId]);

  // Apply map locking settings
  useEffect(() => {
    if (!mapRef.current) return;

    const map = mapRef.current;

    // Apply all the interactive settings based on locked state and individual props
    const shouldDisable = locked || !dragging;
    if (map.dragging) {
      shouldDisable ? map.dragging.disable() : map.dragging.enable();
    }

    if (map.touchZoom) {
      const shouldDisableTouch = locked || !touchZoom;
      shouldDisableTouch ? map.touchZoom.disable() : map.touchZoom.enable();
    }

    if (map.scrollWheelZoom) {
      const shouldDisableScroll = locked || !scrollWheelZoom;
      shouldDisableScroll ? map.scrollWheelZoom.disable() : map.scrollWheelZoom.enable();
    }

    if (map.doubleClickZoom) {
      const shouldDisableDoubleClick = locked || !doubleClickZoom;
      shouldDisableDoubleClick ? map.doubleClickZoom.disable() : map.doubleClickZoom.enable();
    }

    if (map.boxZoom) {
      const shouldDisableBox = locked || !boxZoom;
      shouldDisableBox ? map.boxZoom.disable() : map.boxZoom.enable();
    }

    if (map.keyboard) {
      const shouldDisableKeyboard = locked || !keyboard;
      shouldDisableKeyboard ? map.keyboard.disable() : map.keyboard.enable();
    }

    // Handle zoom control
    const shouldShowZoomControl = !locked && zoomControl;
    
    // Remove existing zoom control if it exists
    if (zoomControlRef.current) {
      map.removeControl(zoomControlRef.current);
      zoomControlRef.current = null;
    }
    
    // Add zoom control if needed
    if (shouldShowZoomControl) {
      zoomControlRef.current = L.control.zoom({
        position: 'topright'
      });
      zoomControlRef.current.addTo(map);
    }

    // Add/remove CSS class for visual feedback when locked
    const container = map.getContainer();
    if (locked) {
      container.classList.add('map-locked');
      container.style.cursor = 'not-allowed';
    } else {
      container.classList.remove('map-locked');
      container.style.cursor = 'grab';
    }

  }, [locked, dragging, touchZoom, scrollWheelZoom, doubleClickZoom, boxZoom, keyboard, zoomControl]);

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

  // Normalize rating to 0-1 scale based on actual data range
  const normalizeRating = (rating: number | null): number | null => {
    if (rating === null) return null;
    
    // If range is 0 (all values are the same), return middle value
    if (dataRange.range === 0) return 0.5;
    
    // Normalize to 0-1 based on actual data range
    return (rating - dataRange.min) / dataRange.range;
  };

  // Generate color based on normalized rating
  const getRatingColor = (rating: number | null): string => {
    if (rating === null) {
      return '#cccccc'; // Gray for areas without data
    }
    
    const normalizedRating = normalizeRating(rating);
    if (normalizedRating === null) return '#cccccc';
    
    // Different color for every 0.1 interval in the normalized range
    if (normalizedRating <= 0.1) return '#ff0000'; // Red
    if (normalizedRating <= 0.2) return '#ff3300';
    if (normalizedRating <= 0.3) return '#ff6600';
    if (normalizedRating <= 0.4) return '#ff9900'; // Orange
    if (normalizedRating <= 0.5) return '#ffcc00';
    if (normalizedRating <= 0.6) return '#ffff00'; // Yellow
    if (normalizedRating <= 0.7) return '#ccff00';
    if (normalizedRating <= 0.8) return '#99ff00';
    if (normalizedRating <= 0.9) return '#66ff00';
    return '#00ff00'; // Green
  };

  // Get color intensity for fill opacity based on normalized rating
  const getFillOpacity = (rating: number | null): number => {
    if (rating === null) return 0.1;
    
    const normalizedRating = normalizeRating(rating);
    if (normalizedRating === null) return 0.1;
    
    return 0.4 + (normalizedRating * 0.5); // 0.4 to 0.9 opacity based on normalized rating
  };

  // Get border weight based on normalized rating
  const getBorderWeight = (rating: number | null): number => {
    if (rating === null) return 1;
    
    const normalizedRating = normalizeRating(rating);
    if (normalizedRating === null) return 1;
    
    return 1.5 + (normalizedRating * 2.5); // 1.5 to 4 weight based on normalized rating
  };

  // Default polygon styling when no custom styling is provided
  const getDefaultPolygonStyle = (areaName: string): PolygonStyle => {
    const areaRating = getAreaRating(areaName);
    const areaColor = getRatingColor(areaRating);
    const fillOpacity = getFillOpacity(areaRating);
    const borderWeight = getBorderWeight(areaRating);
    
    return {
      fillColor: areaColor,
      fillOpacity: fillOpacity,
      color: '#000000', // Black borders for separation
      weight: borderWeight,
      opacity: 0.8
    };
  };

  // Get the final polygon style - uses custom styling if provided, otherwise default
  const getFinalPolygonStyle = (areaName: string): PolygonStyle => {
    if (getPolygonStyle) {
      return getPolygonStyle(areaName);
    }
    return getDefaultPolygonStyle(areaName);
  };

  // Initialize map with STRONG bounds and zoom restrictions
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapRef.current) {
      mapRef.current = L.map(mapContainerRef.current, {
        center: center,
        zoom: Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom)), // Enforce zoom limits immediately
        zoomControl: false, // We'll control this manually
        // Add bounds restriction to prevent grey areas
        maxBounds: singaporeBounds,
        maxBoundsViscosity: 1.0, // Prevents dragging outside bounds
        // STRONG zoom restrictions
        minZoom: MIN_ZOOM,
        maxZoom: MAX_ZOOM,
        // Disable some zoom methods that might allow bypassing limits
        boxZoom: false, // Disable shift-drag to zoom
      });

      // Set min and max zoom explicitly (redundant but ensures it's set)
      mapRef.current.setMinZoom(MIN_ZOOM);
      mapRef.current.setMaxZoom(MAX_ZOOM);

      // SET BLUE BACKGROUND COLOR - Key change here
      if (mapContainerRef.current) {
        mapContainerRef.current.style.backgroundColor = '#6da7e3';
      }

      // Add OneMap tiles with matching zoom restrictions
      const oneMapLayer = L.tileLayer('https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png', {
        detectRetina: true,
        maxZoom: MAX_ZOOM,
        minZoom: MIN_ZOOM,
        bounds: singaporeBounds, // Restrict tiles to Singapore bounds
        attribution: '<img src="https://www.onemap.gov.sg/web-assets/images/logo/om_logo.png" style="height:20px;width:20px;"/> OneMap | Map data © contributors, <a href="http://SLA.gov.sg">Singapore Land Authority</a>'
      });

      oneMapLayer.addTo(mapRef.current);

      // Add event to keep map within bounds
      mapRef.current.on('drag', () => {
        mapRef.current!.panInsideBounds(singaporeBounds, { animate: false });
      });

      // STRONG zoom enforcement - catch any zoom events and enforce limits
      mapRef.current.on('zoom', () => {
        const currentZoom = mapRef.current!.getZoom();
        if (currentZoom < MIN_ZOOM) {
          mapRef.current!.setZoom(MIN_ZOOM, { animate: false });
        } else if (currentZoom > MAX_ZOOM) {
          mapRef.current!.setZoom(MAX_ZOOM, { animate: false });
        }
      });

      // Additional protection on zoom end
      mapRef.current.on('zoomend', () => {
        const currentZoom = mapRef.current!.getZoom();
        if (currentZoom < MIN_ZOOM) {
          mapRef.current!.setZoom(MIN_ZOOM);
        } else if (currentZoom > MAX_ZOOM) {
          mapRef.current!.setZoom(MAX_ZOOM);
        }
      });

      // Add click handler (only if not locked)
      if (onMapClick) {
        mapRef.current.on('click', (e: L.LeafletMouseEvent) => {
          if (!locked) {
            onMapClick(e.latlng.lat, e.latlng.lng);
          }
        });
      }
    }

    return () => {
      if (mapRef.current) {
        // Clean up zoom control
        if (zoomControlRef.current) {
          mapRef.current.removeControl(zoomControlRef.current);
          zoomControlRef.current = null;
        }
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Update center and zoom (only if not locked)
  useEffect(() => {
    if (mapRef.current && !locked) {
      // Ensure center is within Singapore bounds
      const centerLatLng = L.latLng(center[0], center[1]);
      const validCenter: [number, number] = singaporeBounds.contains(centerLatLng) 
        ? [center[0], center[1]] 
        : [1.3521, 103.8198];
      
      // STRONG zoom enforcement
      const validZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom));
      
      mapRef.current.setView(validCenter, validZoom);
    }
  }, [center, zoom, locked]);

  // Update markers
  useEffect(() => {
    if (!mapRef.current) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add new markers
    markers.forEach(markerData => {
      if (mapRef.current) {
        // Support colorized markers by using the leaflet-color-markers icon set when a color is provided.
        let marker: L.Marker;
        if (markerData.color) {
          // sanitize color name for URL (lowercase, remove non-alphanum and hyphen)
          const colorName = markerData.color.toString().toLowerCase().replace(/[^a-z0-9-]/g, '');
          const iconUrl = `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${colorName}.png`;
          const iconRetina = `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${colorName}.png`;
          const markerIcon = L.icon({
            iconUrl,
            iconRetinaUrl: iconRetina,
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
          });

          marker = L.marker(markerData.position, { icon: markerIcon });
        } else {
          marker = L.marker(markerData.position);
        }

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

  // Update planning areas polygons with custom or default styling
  useEffect(() => {
    if (!mapRef.current || !showPlanningAreas) return;

    // Clear existing planning areas
    planningAreasRef.current.forEach(polygon => polygon.remove());
    planningAreasRef.current = [];

    // Add planning area polygons with styling
    planningAreas.forEach(area => {
      if (mapRef.current) {
        const coordinates = convertCoordinates(area.geometry.coordinates);
        const areaRating = getAreaRating(area.properties.pln_area_n);
        const style = getFinalPolygonStyle(area.properties.pln_area_n);
        
        coordinates.forEach(polygonCoords => {
          const polygon = L.polygon(polygonCoords, {
            color: style.color,
            fillColor: style.fillColor,
            fillOpacity: style.fillOpacity,
            weight: style.weight,
            opacity: style.opacity
          });

          // Add click handler for area selection (only if not locked)
          polygon.on('click', (e: L.LeafletMouseEvent) => {
            L.DomEvent.stopPropagation(e);
            if (onAreaClick && !locked) {
              onAreaClick(area.properties.pln_area_n, polygonCoords, areaRating || undefined);
            }
          });

          // Add hover effects (only if not locked)
          if (!locked) {
            polygon.on('mouseover', function (this: L.Polygon, e: L.LeafletMouseEvent) {
              this.setStyle({
                fillOpacity: Math.min(0.9, style.fillOpacity + 0.2),
                weight: style.weight + 1
              });
            });

            polygon.on('mouseout', function (this: L.Polygon, e: L.LeafletMouseEvent) {
              this.setStyle({
                fillOpacity: style.fillOpacity,
                weight: style.weight
              });
            });
          }

          polygon.addTo(mapRef.current!);
          planningAreasRef.current.push(polygon);
        });
      }
    });
  }, [planningAreas, choroplethData, showPlanningAreas, onAreaClick, locked, getPolygonStyle, dataRange]);

  return (
    <div className="relative w-full h-full">
      <div 
        ref={mapContainerRef} 
        className={className}
        style={{ 
          width: '100%', 
          height: '100%',
          backgroundColor: '#6da7e3' // Added blue background here
        }}
      />
      
      {/* Lock indicator */}
      {locked && (
        <div className="absolute top-4 right-4 bg-yellow-500 text-white rounded-lg shadow-lg px-3 py-2 z-[1000]">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
            </svg>
            <span className="text-sm font-medium">Map Locked</span>
          </div>
        </div>
      )}
      
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