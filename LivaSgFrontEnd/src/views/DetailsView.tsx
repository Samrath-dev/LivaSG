import { useState, useEffect } from 'react';
import { FaDumbbell, FaTree, FaShoppingBag, FaSchool, FaHospital, FaParking, FaUtensils, FaBus } from 'react-icons/fa';
import React, { isValidElement, cloneElement } from 'react';
import type { ReactNode } from 'react';
import OneMapEmbedded from '../components/OneMapEmbedded';
import api from '../api/https';

interface DetailsViewProps {
  location: {
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
    latitude?: number;
    longitude?: number;
    lat?: number;
    lng?: number;
  };
  onBack: () => void;
}

type FilterItemProps = {
  icon: ReactNode;
  label: string;
  checked: boolean;
  onChange: () => void;
  count?: number;
  iconStyle?: React.CSSProperties;
  iconClassName?: string;
};

const DetailsView = ({ location, onBack }: DetailsViewProps) => {
  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  // Get coordinates from location, with fallback to Singapore center
  const getLocationCoordinates = (): [number, number] => {
    if (location.latitude !== undefined && location.longitude !== undefined) {
      return [location.latitude, location.longitude];
    }
    if (location.lat !== undefined && location.lng !== undefined) {
      return [location.lat, location.lng];
    }
    return [1.3521, 103.8198];
  };

  const [mapCenter, setMapCenter] = useState<[number, number]>(getLocationCoordinates());
  const [mapZoom, setMapZoom] = useState<number>(13);

  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [facilityMarkers, setFacilityMarkers] = useState<Array<{
    position: [number, number];
    popup: string;
  }>>([]);
  const [loadingFacilities, setLoadingFacilities] = useState(false);
  const [facilityCounts, setFacilityCounts] = useState<{
    gym: number;
    park: number;
    mall: number;
    school: number;
    hospital: number;
    parking: number;
    dining: number;
    transport: number;
  }>({
    gym: 0,
    park: 0,
    mall: 0,
    school: 0,
    hospital: 0,
    parking: 0,
    dining: 0,
    transport: 0
  });
  const [selectedOptions, setSelectedOptions] = useState<{ 
    gym: boolean; 
    park: boolean;
    mall: boolean;
    school: boolean;
    hospital: boolean;
    parking: boolean;
    dining: boolean;
    transport: boolean;
  }>({
    // default: show all facilities when the map opens
    gym: true,
    park: true,
    mall: true,
    school: true,
    hospital: true,
    parking: true,
    dining: true,
    transport: true
  });

  const toggleOption = (key: keyof typeof selectedOptions) => {
    setSelectedOptions(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const fetchFacilities = async () => {
    if (!location.street) return;
    
    setLoadingFacilities(true);
    try {
      // Map UI filter keys to backend types
      const filterMap: Record<string, string> = {
        gym: 'sports',
        park: 'parks',
        mall: 'sports',
        school: 'schools',
        hospital: 'healthcare',
        parking: 'carparks',
        dining: 'hawkers',
        transport: 'transit' // Add transport mapping
      };

      // Get selected types
      const selectedTypes = Object.entries(selectedOptions)
        .filter(([_, checked]) => checked)
        .map(([key, _]) => filterMap[key])
        .filter((v, i, a) => a.indexOf(v) === i) // remove duplicates
        .join(',');

      if (!selectedTypes) {
        setFacilityMarkers([]);
        return;
      }

      const response = await api.get(
        `/details/street/${encodeURIComponent(location.street)}/facilities-locations`,
        { params: { types: selectedTypes } }
      );

      const data = response.data as {
        facilities: Record<string, Array<{ name: string; latitude: number; longitude: number; distance: number }>>;
      };
      const markers: Array<{ position: [number, number]; popup: string }> = [];

      // Convert facilities to markers
      const categoryIcons: Record<string, string> = {
        schools: '🏫',
        sports: '⚽',
        hawkers: '🍽️',
        healthcare: '🏥',
        parks: '🌳',
        carparks: '🅿️',
        transport: '🚌' // Add transport icon
      };

      Object.entries(data.facilities).forEach(([category, items]: [string, any]) => {
        if (Array.isArray(items)) {
          items.forEach((facility: any) => {
            markers.push({
              position: [facility.latitude, facility.longitude],
              popup: `${categoryIcons[category] || '📍'} <strong>${facility.name}</strong><br/>${category}<br/>${facility.distance}km away`
            });
          });
        }
      });

      setFacilityMarkers(markers);
    } catch (error) {
      console.error('Failed to fetch facilities:', error);
      setFacilityMarkers([]);
    } finally {
      setLoadingFacilities(false);
    }
  };

  // Fetch facility counts on mount
  useEffect(() => {
    const fetchFacilityCounts = async () => {
      if (!location.street) return;
      
      try {
        // Fetch all facilities to get counts
        const response = await api.get(
          `/details/street/${encodeURIComponent(location.street)}/facilities-locations`,
          { params: { types: 'schools,sports,hawkers,healthcare,parks,carparks,transit' } } // Add transport
        );

        const data = response.data as {
          facilities: Record<string, Array<any>>;
        };

        // Map backend categories to UI keys
        const counts = {
          gym: data.facilities.sports?.length || 0,
          park: data.facilities.parks?.length || 0,
          mall: data.facilities.sports?.length || 0, // mall uses sports
          school: data.facilities.schools?.length || 0,
          hospital: data.facilities.healthcare?.length || 0,
          parking: data.facilities.carparks?.length || 0,
          dining: data.facilities.hawkers?.length || 0,
          transport: data.facilities.transit?.length || 0 // Add transport count
        };

        setFacilityCounts(counts);
      } catch (error) {
        console.error('Failed to fetch facility counts:', error);
      }
    };

    fetchFacilityCounts();
  }, [location.street]);

    // Helpers to compute centroid and zoom for polygon bounds
    const centroidOf = (coords: [number, number][]) => {
      const lats = coords.map(c => c[0]);
      const lngs = coords.map(c => c[1]);
      const lat = (Math.min(...lats) + Math.max(...lats)) / 2;
      const lng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
      return [lat, lng] as [number, number];
    };

    const computeZoomForBounds = (coords: [number, number][], fraction = 0.8) => {
      if (!coords || coords.length === 0) return 13;
      const lats = coords.map(c => c[0]);
      const lngs = coords.map(c => c[1]);
      const latMin = Math.min(...lats);
      const latMax = Math.max(...lats);
      const lonMin = Math.min(...lngs);
      const lonMax = Math.max(...lngs);

      const lonDelta = Math.max(0.00001, lonMax - lonMin);

      const TILE_SIZE = 256;
      const viewportW = Math.max(320, window.innerWidth || 1024);
      const viewportH = Math.max(200, (window.innerHeight || 768) - 160); // leave room for header

      const padding = 32;
      const frac = Math.max(0.5, Math.min(0.95, fraction));
      const availableW = Math.max(240, viewportW - padding * 2);
      const availableH = Math.max(200, viewportH - padding * 2);

      const zoomLon = Math.log2((360 * (availableW * frac)) / (TILE_SIZE * lonDelta));

      const latToMerc = (lat: number) => {
        const rad = (lat * Math.PI) / 180;
        return Math.log(Math.tan(Math.PI / 4 + rad / 2));
      };
      const mercMin = latToMerc(latMin);
      const mercMax = latToMerc(latMax);
      const mercDelta = Math.max(1e-8, Math.abs(mercMax - mercMin));

      const worldMercatorHeight = 2 * Math.PI;
      const zoomLat = Math.log2((worldMercatorHeight * (availableH * frac)) / (TILE_SIZE * mercDelta));

      const rawZoom = Math.min(zoomLon, zoomLat);
      const zoom = Math.max(2, Math.min(18, Math.round(rawZoom)));
      return zoom;
    };

    // Fetch planning-area geometry and fit map to polygon if available
    useEffect(() => {
      const fitToPlanningArea = async () => {
        if (!location.area) return;
        try {
          const resp = await fetch('http://localhost:8000/onemap/planning-areas?year=2019');
          if (!resp.ok) return;
          const data = await resp.json();
          const features = data.features || [];
          const match = features.find((f: any) => (f.properties?.pln_area_n || '').toString().trim().toUpperCase() === (location.area || '').toString().trim().toUpperCase());
          if (!match) return;
          // Use first polygon exterior ring
          const multi = match.geometry?.coordinates;
          if (!multi || !Array.isArray(multi) || multi.length === 0) return;
          const exterior = multi[0] && multi[0][0] ? multi[0][0] : null;
          if (!exterior || exterior.length === 0) return;
          const coords: [number, number][] = exterior.map((c: number[]) => [c[1], c[0]]);
          const center = centroidOf(coords);
          const zoom = computeZoomForBounds(coords, 0.85);
          setMapZoom(zoom);
          // Slight delay to let map mount if needed
          setMapCenter(center);
        } catch (err) {
          // ignore
        }
      };

      fitToPlanningArea();
    }, [location.area]);

  // On mount / when location.street changes, load all facilities (default = all on)
  useEffect(() => {
    // Call fetchFacilities to populate markers according to the current selectedOptions (now default all true)
    fetchFacilities();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.street]);

  // Keep center updated if the raw location coords change
  useEffect(() => {
    setMapCenter(getLocationCoordinates());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.latitude, location.longitude, location.lat, location.lng, location.street]);

  const handleApplyFilters = async () => {
    await fetchFacilities();
    setShowFilterMenu(false);
  };

  const handleResetFilters = () => {
    // Reset back to default: all facilities shown
    setSelectedOptions({
      gym: true,
      park: true,
      mall: true,
      school: true,
      hospital: true,
      parking: true,
      dining: true,
      transport: true
    });
    setFacilityMarkers([]);
  };

  const FilterItem = ({ icon, label, checked, onChange, count, iconStyle, iconClassName }: FilterItemProps) => (
    <label className="flex items-center justify-between w-full p-4 rounded-xl hover:bg-purple-50 transition-colors cursor-pointer border border-purple-200 bg-white">
      <div className="flex items-center gap-4">
        <span
          className={`flex-shrink-0 p-3 rounded-xl border-2 ${
            checked ? 'border-purple-500 text-purple-600 bg-purple-50' : 'border-purple-300 text-purple-400 bg-white'
          } ${iconClassName ?? ''}`}
          style={{
            width: '52px',
            height: '52px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            ...(iconStyle || {})
          }}>
          {isValidElement(icon)
            ? cloneElement(icon as React.ReactElement<any>, {
                className: `${(icon as any)?.props?.className ?? ''} w-6 h-6`
              })
            : icon}
        </span>
        <div>
          <span className="text-lg font-semibold text-gray-900">{label}</span>
          {count !== undefined && (
            <span className="block text-sm text-purple-600 mt-1">{count} locations nearby</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          checked={checked}
          onChange={onChange}
          className="hidden"
        />
        <div 
          className={`relative w-7 h-7 rounded-xl border-2 transition-all cursor-pointer ${
            checked 
              ? 'bg-purple-500 border-purple-500' 
              : 'bg-white border-purple-300'
          }`}
          onClick={onChange}
        >
          {checked && (
            <svg className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </div>
      </div>
    </label>
  );

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header - Simplified back button */}
  <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4 relative z-40">
        <div className="relative w-full mb-4">
          {/* Title (Location Address) - absolutely centered so it's visually centered regardless of button widths */}
          <div className="absolute left-1/2 -top-1/2 transform -translate-x-1/2 text-center">
            <h1 className="text-2xl font-bold text-purple-900">{location.street}</h1>
            <p className="text-purple-600 mt-2 flex items-center gap-2 justify-center">
              <span className="bg-purple-100 text-purple-800 text-sm font-semibold px-3 py-1 rounded-full border border-purple-200">
                {location.area}
              </span>
              <span className="text-purple-400">•</span>
              <span className="font-medium text-purple-700">{location.district}</span>
            </p>
          </div>

          {/* Right control — keeps functionality (Filter Facilities) */}
          <div className="flex items-center justify-end">
            <button
              onClick={() => setShowFilterMenu(true)}
              className="inline-flex items-center px-4 py-2 bg-white text-purple-700 rounded-xl text-sm font-semibold border-2 border-purple-300 hover:border-purple-500 hover:bg-purple-50 transition-all"
            >
              Filter Facilities
            </button>
          </div>
        </div>
      </div>

      {/* Content: full-bleed map in purple background */}
      <div className="flex-1 relative z-0">
        <div className="w-full h-full">
          <OneMapEmbedded
            center={mapCenter}
            zoom={mapZoom}
            markers={facilityMarkers}
            interactive={true}
            zoomOnly={false}
            className="w-full h-full"
          />
        </div>
      </div>

      {/* Filter Modal */}
      {showFilterMenu && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-auto"
          role="dialog"
          aria-modal="true"
        >
          {/* backdrop (below modal) */}
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-50 z-[9998]"
            onClick={() => setShowFilterMenu(false)}
          />

          <div
            className="relative bg-white rounded-2xl w-full max-w-md mx-auto shadow-2xl border border-purple-300 max-h-[90vh] overflow-auto z-[9999]"
            onClick={(e) => e.stopPropagation()}
          >

            {/* Header - Pale purple */}
            <div className="flex items-center justify-between p-6 border-b border-purple-200 bg-purple-100 text-purple-900 rounded-t-2xl">
              <div>
                <h3 className="text-xl font-bold">Filter Facilities</h3>
                <p className="text-purple-700 text-sm mt-1">Select amenities to show on map</p>
              </div>
              <button
                onClick={() => setShowFilterMenu(false)}
                className="p-2 hover:bg-purple-200 rounded-xl transition-colors text-purple-700 hover:text-purple-900"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
              {[
                { key: 'gym' as const, label: 'Fitness Centers', icon: <FaDumbbell />, count: facilityCounts.gym },
                { key: 'park' as const, label: 'Parks & Recreation', icon: <FaTree />, count: facilityCounts.park },
                { key: 'mall' as const, label: 'Shopping Malls', icon: <FaShoppingBag />, count: facilityCounts.mall },
                { key: 'school' as const, label: 'Schools', icon: <FaSchool />, count: facilityCounts.school },
                { key: 'hospital' as const, label: 'Healthcare', icon: <FaHospital />, count: facilityCounts.hospital },
                { key: 'parking' as const, label: 'Parking Lots', icon: <FaParking />, count: facilityCounts.parking },
                { key: 'dining' as const, label: 'Dining Options', icon: <FaUtensils />, count: facilityCounts.dining },
                { key: 'transport' as const, label: 'Transport', icon: <FaBus />, count: facilityCounts.transport } // Added transport filter
              ].map(f => (
                <FilterItem
                  key={f.key}
                  icon={f.icon}
                  label={f.label}
                  checked={selectedOptions[f.key]}
                  onChange={() => toggleOption(f.key)}
                  count={f.count}
                />
              ))}
            </div>

            <div className="flex gap-3 p-6 border-t border-purple-200 bg-purple-50 rounded-b-2xl">
              <button
                onClick={handleResetFilters}
                className="flex-1 px-4 py-3 text-purple-700 bg-white border border-purple-300 rounded-xl font-semibold hover:bg-purple-100 transition-colors"
              >
                Reset All
              </button>
              <button
                onClick={handleApplyFilters}
                disabled={loadingFacilities}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl font-semibold hover:from-purple-600 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loadingFacilities ? 'Loading...' : 'Apply Filters'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DetailsView;