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

interface OneMapEmbeddedProps {
  center: [number, number];
  zoom?: number;
  markers?: Array<{
    position: [number, number];
    popup?: string;
  }>;
  className?: string;
  interactive?: boolean;
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
  interactive = false
}: OneMapEmbeddedProps) => {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize map
    if (!mapRef.current) {
      mapRef.current = L.map(mapContainerRef.current, {
        center: center,
        zoom: zoom,
        zoomControl: interactive,
        dragging: interactive,
        scrollWheelZoom: interactive,
        doubleClickZoom: interactive,
        touchZoom: interactive,
        boxZoom: interactive,
        keyboard: interactive,
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

  return (
    <div 
      ref={mapContainerRef} 
      className={className}
      style={{ width: '100%', height: '100%', minHeight: '300px' }}
    />
  );
};

export default OneMapEmbedded;
