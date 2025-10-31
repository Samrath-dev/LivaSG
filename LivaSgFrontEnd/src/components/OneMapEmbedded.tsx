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
    color?: string; // optional color name for colored marker icons
  }>;
  className?: string;
  interactive?: boolean;
  zoomOnly?: boolean;  // New prop: allow zooming but not dragging
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
}: OneMapEmbeddedProps) => {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);

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

      // Add markers (support optional colored icons)
      const colorIconBase = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon';
      const colorRetinaBase = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x';
      const shadowUrl = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png';

      markers.forEach(markerData => {
        if (!mapRef.current) return;

        let marker: L.Marker;

        if (markerData.color) {
          // sanitize color (only allow alphanumeric and hyphen)
          const colorKey = String(markerData.color).toLowerCase().replace(/[^a-z0-9-]/g, '');
          const iconUrl = `${colorIconBase}-${colorKey}.png`;
          const iconRetinaUrl = `${colorRetinaBase}-${colorKey}.png`;

          const coloredIcon = L.icon({
            iconUrl,
            iconRetinaUrl,
            shadowUrl,
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
          });

          marker = L.marker(markerData.position, { icon: coloredIcon });
        } else {
          marker = L.marker(markerData.position);
        }

        if (markerData.popup) {
          marker.bindPopup(markerData.popup);
        }

        marker.addTo(mapRef.current);
        markersRef.current.push(marker);
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
