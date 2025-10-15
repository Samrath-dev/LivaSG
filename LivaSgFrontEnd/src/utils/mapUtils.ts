/**
 * Utility functions for working with OneMap and geographic data
 */

/**
 * Singapore's approximate center coordinates
 */
export const SINGAPORE_CENTER: [number, number] = [1.3521, 103.8198];

/**
 * Default zoom levels for different use cases
 */
export const ZOOM_LEVELS = {
  COUNTRY: 11,      // View entire Singapore
  CITY: 12,         // View city area
  DISTRICT: 14,     // View district/neighborhood
  STREET: 16,       // View street level
  BUILDING: 18,     // View building details
} as const;

/**
 * Calculate the center point of a polygon
 */
export const calculatePolygonCenter = (coordinates: [number, number][]): [number, number] => {
  if (coordinates.length === 0) return SINGAPORE_CENTER;
  
  const lats = coordinates.map(coord => coord[0]);
  const lngs = coordinates.map(coord => coord[1]);
  
  const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
  const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
  
  return [centerLat, centerLng];
};

/**
 * Calculate the bounding box of coordinates
 */
export const calculateBounds = (coordinates: [number, number][]): {
  minLat: number;
  maxLat: number;
  minLng: number;
  maxLng: number;
} => {
  if (coordinates.length === 0) {
    return { minLat: 0, maxLat: 0, minLng: 0, maxLng: 0 };
  }
  
  const lats = coordinates.map(coord => coord[0]);
  const lngs = coordinates.map(coord => coord[1]);
  
  return {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLng: Math.min(...lngs),
    maxLng: Math.max(...lngs),
  };
};

/**
 * Calculate distance between two points (Haversine formula)
 * Returns distance in kilometers
 */
export const calculateDistance = (
  point1: [number, number],
  point2: [number, number]
): number => {
  const [lat1, lon1] = point1;
  const [lat2, lon2] = point2;
  
  const R = 6371; // Earth's radius in km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  
  return distance;
};

/**
 * Convert degrees to radians
 */
const toRad = (degrees: number): number => {
  return degrees * (Math.PI / 180);
};

/**
 * Format coordinates for display
 */
export const formatCoordinates = (lat: number, lng: number): string => {
  return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
};

/**
 * Check if a point is within Singapore bounds (approximate)
 */
export const isWithinSingaporeBounds = (lat: number, lng: number): boolean => {
  // Approximate bounds of Singapore
  const bounds = {
    minLat: 1.15,
    maxLat: 1.47,
    minLng: 103.6,
    maxLng: 104.1,
  };
  
  return (
    lat >= bounds.minLat &&
    lat <= bounds.maxLat &&
    lng >= bounds.minLng &&
    lng <= bounds.maxLng
  );
};

/**
 * Generate a static map URL for OneMap
 */
export const generateStaticMapUrl = (
  center: [number, number],
  zoom: number = 16,
  width: number = 400,
  height: number = 300,
  markers?: Array<{ position: [number, number]; color?: string; label?: string }>
): string => {
  const [lat, lng] = center;
  let url = `https://www.onemap.gov.sg/api/staticmap/getStaticImage?layerchosen=default&lat=${lat}&lng=${lng}&zoom=${zoom}&height=${height}&width=${width}`;
  
  if (markers && markers.length > 0) {
    const markerStrings = markers.map(m => {
      const [mLat, mLng] = m.position;
      const color = m.color || 'red';
      const label = m.label || '';
      return `${mLat},${mLng},${color},${label}`;
    });
    url += `&points=${markerStrings.join('|')}`;
  }
  
  return url;
};

/**
 * Common marker colors for categorization
 */
export const MARKER_COLORS = {
  RED: 'red',
  BLUE: 'blue',
  GREEN: 'green',
  YELLOW: 'yellow',
  PURPLE: 'purple',
  ORANGE: 'orange',
} as const;

/**
 * Common polygon colors with theme
 */
export const POLYGON_COLORS = {
  PRIMARY: '#8b5cf6',      // Purple
  SUCCESS: '#10b981',      // Green
  INFO: '#3b82f6',         // Blue
  WARNING: '#f59e0b',      // Orange
  DANGER: '#ef4444',       // Red
} as const;

/**
 * Generate HTML popup content for markers
 */
export const createPopupContent = (title: string, details: Record<string, string>): string => {
  let html = `<div style="min-width: 200px;">`;
  html += `<h3 style="font-weight: bold; margin-bottom: 8px; font-size: 16px;">${title}</h3>`;
  
  Object.entries(details).forEach(([key, value]) => {
    html += `<div style="margin-bottom: 4px;">`;
    html += `<span style="color: #666;">${key}:</span> `;
    html += `<span style="font-weight: 600;">${value}</span>`;
    html += `</div>`;
  });
  
  html += `</div>`;
  return html;
};
