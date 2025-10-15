import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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
  onMapClick?: (lat: number, lng: number) => void;
  className?: string;
}

const OneMapInteractive = ({ 
  center = [1.3521, 103.8198], // Singapore center
  zoom = 12,
  markers = [],
  polygons = [],
  onMapClick,
  className = ''
}: OneMapInteractiveProps) => {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const polygonsRef = useRef<L.Polygon[]>([]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize map
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

  // Update polygons
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

  return (
    <div 
      ref={mapContainerRef} 
      className={className}
      style={{ width: '100%', height: '100%' }}
    />
  );
};

export default OneMapInteractive;
