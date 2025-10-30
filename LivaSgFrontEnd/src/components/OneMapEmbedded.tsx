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

interface OneMapEmbeddedProps {
  center: [number, number];
  zoom?: number;
  markers?: Array<{
    position: [number, number];
    popup?: string;
  }>;
  className?: string;
  interactive?: boolean;
  zoomOnly?: boolean;  // New prop: allow zooming but not dragging
  // Planning areas (lightweight support similar to OneMapInteractive)
  showPlanningAreas?: boolean;
  planningAreasYear?: number;
  getPolygonStyle?: (areaName: string) => {
    fillColor: string;
    fillOpacity: number;
    color: string;
    weight: number;
    opacity: number;
  };
}

/**
 * A simplified embedded map component for displaying location
 * Better alternative to static images with more reliability
 */
const OneMapEmbedded = ({ 
  center,
  zoom = 16,
  markers = [],
  className = '',
  interactive = false,
  zoomOnly = false
  , showPlanningAreas = false, planningAreasYear = 2019, getPolygonStyle
}: OneMapEmbeddedProps) => {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const planningAreasRef = useRef<L.Polygon[]>([]);
  const [planningAreas, setPlanningAreas] = useState<any[]>([]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize map
    if (!mapRef.current) {
      // Determine interaction settings
      const allowZoom = interactive || zoomOnly;
      const allowDrag = interactive && !zoomOnly;
      
      mapRef.current = L.map(mapContainerRef.current, {
        center: center,
        zoom: zoom,
        zoomControl: allowZoom,
        dragging: allowDrag,
        scrollWheelZoom: allowZoom,
        doubleClickZoom: allowZoom,
        touchZoom: allowZoom,
        boxZoom: allowDrag,
        keyboard: allowDrag,
      });

      // Add OneMap tiles
      L.tileLayer('https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png', {
        detectRetina: true,
        maxZoom: 19,
        minZoom: 11,
        attribution: '<img src="https://www.onemap.gov.sg/web-assets/images/logo/om_logo.png" style="height:20px;width:20px;"/> OneMap | Map data © contributors, <a href="http://SLA.gov.sg">Singapore Land Authority</a>'
      }).addTo(mapRef.current);

      // Add markers
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
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        markersRef.current = [];
      }
    };
  }, [center, zoom, markers, interactive]);

  // Simple helper to convert GeoJSON polygon coordinates to Leaflet latlng arrays
  const convertCoordinates = (coords: number[][][][] | number[][][]): [number, number][][] => {
    if (!coords || coords.length === 0) return [];

    // MultiPolygon (4 levels)
    if (Array.isArray(coords[0][0][0])) {
      return (coords as number[][][][]).map(polygon =>
        polygon[0].map(coord => [coord[1], coord[0]] as [number, number])
      );
    }

    // Polygon (3 levels)
    return [(coords as number[][][])[0].map(coord => [coord[1], coord[0]] as [number, number])];
  };

  // Fetch planning areas (lightweight)
  useEffect(() => {
    if (!showPlanningAreas) return;

    const fetchPlanningAreas = async () => {
      try {
        const res = await fetch(`http://localhost:8000/onemap/planning-areas?year=${planningAreasYear}`);
        if (!res.ok) throw new Error('Failed to fetch planning areas');
        const data = await res.json();
        setPlanningAreas(data.features || []);
      } catch (err) {
        console.error('Failed to load planning areas', err);
        setPlanningAreas([]);
      }
    };

    fetchPlanningAreas();
  }, [showPlanningAreas, planningAreasYear]);

  // Render planning areas onto the map
  useEffect(() => {
    if (!mapRef.current) return;
    if (!showPlanningAreas) return;

    // Clear existing
    planningAreasRef.current.forEach(p => p.remove());
    planningAreasRef.current = [];

    planningAreas.forEach(area => {
      const coords = convertCoordinates(area.geometry.coordinates);
      const style = getPolygonStyle ? getPolygonStyle(area.properties.pln_area_n) : {
        fillColor: '#3388ff',
        fillOpacity: 0.12,
        color: '#000000',
        weight: 1,
        opacity: 0.8
      };

      coords.forEach(polygonCoords => {
        const polygon = L.polygon(polygonCoords, {
          color: style.color,
          fillColor: style.fillColor,
          fillOpacity: style.fillOpacity,
          weight: style.weight,
          opacity: style.opacity
        });

        // Add hover effects
        polygon.on('mouseover', function (this: L.Polygon) {
          this.setStyle({ fillOpacity: Math.min(0.9, style.fillOpacity + 0.2), weight: style.weight + 1 });
        });

        polygon.on('mouseout', function (this: L.Polygon) {
          this.setStyle({ fillOpacity: style.fillOpacity, weight: style.weight });
        });

        polygon.addTo(mapRef.current!);
        planningAreasRef.current.push(polygon);
      });
    });

    return () => {
      planningAreasRef.current.forEach(p => p.remove());
      planningAreasRef.current = [];
    };
  }, [planningAreas, showPlanningAreas, getPolygonStyle]);

  return (
    <div 
      ref={mapContainerRef} 
      className={className}
      style={{ width: '100%', height: '100%', minHeight: '300px' }}
    />
  );
};

export default OneMapEmbedded;
