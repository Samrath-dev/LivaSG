import { HiChevronLeft, HiTrendingUp, HiStar, HiMap, HiHome } from 'react-icons/hi';
import { useState } from 'react';
import { FaDumbbell, FaTree, FaShoppingBag, FaSchool, FaHospital, FaParking, FaUtensils } from 'react-icons/fa';
import React, { isValidElement, cloneElement } from 'react';
import type { ReactNode } from 'react';
import OneMapEmbedded from '../components/OneMapEmbedded';
import priceGraphDummy from '../assets/priceGraphDummy.png';

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
    // Check for latitude/longitude properties
    if (location.latitude !== undefined && location.longitude !== undefined) {
      console.log("Using latitude/longitude" + location.latitude + ", " + location.longitude);
      return [location.latitude, location.longitude];
    }
    // Check for lat/lng properties
    if (location.lat !== undefined && location.lng !== undefined) {
      return [location.lat, location.lng];
    }
    // Fallback to Singapore center
    return [1.3521, 103.8198];
  };

  const mapCenter = getLocationCoordinates();

  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [selectedOptions, setSelectedOptions] = useState<{ 
    gym: boolean; 
    park: boolean;
    mall: boolean;
    school: boolean;
    hospital: boolean;
    parking: boolean;
    dining: boolean;
  }>({
    gym: false,
    park: false,
    mall: false,
    school: false,
    hospital: false,
    parking: false,
    dining: false
  });

  const toggleOption = (key: keyof typeof selectedOptions) => {
    setSelectedOptions(prev => ({ ...prev, [key]: !prev[key] }));
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

  const getAmenityIcon = (amenity: string) => {
    const lowerAmenity = amenity.toLowerCase();
    if (lowerAmenity.includes('mall') || lowerAmenity.includes('shopping')) return <FaShoppingBag className="w-5 h-5" />;
    if (lowerAmenity.includes('school') || lowerAmenity.includes('education')) return <FaSchool className="w-5 h-5" />;
    if (lowerAmenity.includes('hospital') || lowerAmenity.includes('medical')) return <FaHospital className="w-5 h-5" />;
    if (lowerAmenity.includes('park') || lowerAmenity.includes('garden')) return <FaTree className="w-5 h-5" />;
    if (lowerAmenity.includes('gym') || lowerAmenity.includes('fitness')) return <FaDumbbell className="w-5 h-5" />;
    if (lowerAmenity.includes('parking')) return <FaParking className="w-5 h-5" />;
    if (lowerAmenity.includes('food') || lowerAmenity.includes('dining')) return <FaUtensils className="w-5 h-5" />;
    return <HiStar className="w-5 h-5" />;
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white px-6 py-4 shadow-sm">
        <div className="relative">
          <button
            onClick={onBack}
            className="absolute left-0 top-1/2 transform -translate-y-1/2 flex items-center text-purple-700 hover:text-purple-900 transition-colors group md:static md:transform-none md:mr-4"
          >
            <HiChevronLeft className="w-6 h-6 mr-2 group-hover:-translate-x-1 transition-transform" />
            <span className="font-semibold">Back to Search</span>
          </button>
          <div className="hidden sm:block text-center">
            <h1 className="text-2xl font-bold text-gray-900">{location.street}</h1>
            <p className="text-gray-600 mt-2 flex items-center gap-2 justify-center">
            <span className="bg-gradient-to-r from-purple-500 to-purple-600 text-white text-sm font-semibold px-3 py-1 rounded-full">
              {location.area}
            </span>
            <span className="text-gray-400">•</span>
            <span className="font-medium text-gray-700">{location.district}</span>
          </p>
          </div>
        </div>

        <div className="mt-4 sm:hidden w-full">
          <h1 className="text-2xl font-bold text-gray-900 justify-center text-center">{location.street}</h1>
          <p className="text-gray-600 mt-2 flex items-center gap-2 justify-center">
            <span className="bg-gradient-to-r from-purple-500 to-purple-600 text-white text-sm font-semibold px-3 py-1 rounded-full">
              {location.area}
            </span>
            <span className="text-gray-400">•</span>
            <span className="font-medium text-gray-700">{location.district}</span>
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="w-full max-w-full mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          {/* Price History and Facilities Map shown first */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
            {/* Price History */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200 flex flex-col max-h-[50vh] md:max-h-[420px] overflow-auto">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-lg text-gray-900 flex items-center gap-2">
                  <HiTrendingUp className="w-5 h-5 text-green-500" />
                  Price History
                </h2>
                <div className="text-sm text-gray-600 font-medium bg-gray-100 px-3 py-1 rounded-full">
                  Last 5 years
                </div>
              </div>
              <img
                src={priceGraphDummy}
                alt={`Price history for ${location.street}`}
                className="w-full rounded-xl object-contain border border-gray-100 max-h-full"
                loading="lazy"
              />
            </div>

            {/* Facilities Map */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200 flex flex-col max-h-[50vh] md:max-h-[420px] overflow-auto">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-lg text-gray-900 flex items-center gap-2">
                  <HiMap className="w-5 h-5 text-blue-500" />
                  Facilities Map
                </h2>
                <button
                  onClick={() => setShowFilterMenu(true)}
                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl text-sm font-semibold hover:from-purple-600 hover:to-purple-700 transition-all shadow-lg"
                >
                  Filter Facilities
                </button>
              </div>
              <div className="w-full rounded-xl border border-gray-100 overflow-hidden z-50" style={{ height: '400px' }}>
                <OneMapEmbedded
                  center={mapCenter}
                  zoom={16}
                  markers={[
                    { 
                      position: mapCenter, 
                      popup: `<strong>${location.street}</strong><br/>${location.area}<br/>${location.district}` 
                    }
                  ]}
                  interactive={false}
                  className="w-full h-full"
                />
              </div>
            </div>
          </div>

          {/* Price Information */}
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl p-6 text-white shadow-lg">
            <h2 className="font-bold text-lg mb-6 flex items-center gap-2">
              <HiHome className="w-5 h-5" />
              Price Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-blue-200 text-sm mb-2">Price Range</div>
                <div className="font-bold text-2xl">
                  {formatPrice(location.priceRange[0])} - {formatPrice(location.priceRange[1])}
                </div>
              </div>
              <div className="text-center">
                <div className="text-blue-200 text-sm mb-2">Average PSF</div>
                <div className="font-bold text-2xl">
                  ${location.avgPrice.toLocaleString()} psf
                </div>
              </div>
              <div className="text-center">
                <div className="text-blue-200 text-sm mb-2">Annual Growth</div>
                <div className="flex items-center justify-center font-bold text-2xl text-green-300">
                  <HiTrendingUp className="w-5 h-5 mr-2" />
                  +{location.growth}%
                </div>
              </div>
            </div>
          </div>

          {/* Description & Features Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Description */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
              <h2 className="font-bold text-lg mb-4 text-gray-900 flex items-center gap-2">
                <HiStar className="w-5 h-5 text-yellow-500" />
                About this Location
              </h2>
              <p className="text-gray-700 leading-relaxed">{location.description}</p>
            </div>

            {/* Key Features */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
              <h2 className="font-bold text-lg mb-4 text-gray-900">Key Features</h2>
              <div className="flex flex-wrap gap-3">
                {location.facilities.map(facility => (
                  <span
                    key={facility}
                    className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 text-sm font-semibold rounded-xl border border-green-200 hover:bg-green-200 transition-colors"
                  >
                    {facility}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Nearby Amenities */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
            <h2 className="font-bold text-lg mb-4 text-gray-900">Nearby Amenities</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {location.amenities.map((amenity, index) => (
                <div key={index} className="flex items-center gap-4 p-4 rounded-xl hover:bg-gray-50 transition-colors border border-gray-100">
                  <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl flex items-center justify-center text-white shadow-sm">
                    {getAmenityIcon(amenity)}
                  </div>
                  <span className="text-gray-800 font-medium">{amenity}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Market Insights */}
          <div className="bg-gradient-to-r from-amber-500 to-amber-600 rounded-2xl p-6 text-white shadow-lg">
            <h2 className="font-bold text-lg mb-3 flex items-center gap-2">
              <HiTrendingUp className="w-5 h-5" />
              Market Insights
            </h2>
            <p className="text-amber-50 leading-relaxed">
              Properties in {location.street} have shown consistent growth of {location.growth}% annually, 
              making it a promising investment opportunity in the {location.area} area. This location 
              combines excellent amenities with strong potential for long-term value appreciation.
            </p>
          </div>
        </div>
      </div>

      {/* Filter Modal - Grey Background with Pale Purple Header */}
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
            className="relative bg-white rounded-2xl w-full max-w-md mx-auto shadow-2xl border border-gray-300 max-h-[90vh] overflow-auto z-[9999]"
            onClick={(e) => e.stopPropagation()}
          >

            {/* Pale Purple Header */}
            <div className="flex items-center justify-between p-6 border-b border-purple-200 bg-gradient-to-r from-purple-100 to-purple-200 text-purple-900 rounded-t-2xl">
              <div>
                <h3 className="text-xl font-bold">Filter Facilities</h3>
                <p className="text-purple-700 text-sm mt-1">Select amenities to show on map</p>
              </div>
              <button
                onClick={() => setShowFilterMenu(false)}
                className="p-2 hover:bg-purple-300 rounded-xl transition-colors text-purple-700 hover:text-purple-900"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
              {[
                { key: 'gym' as const, label: 'Fitness Centers', icon: <FaDumbbell />, count: 12 },
                { key: 'park' as const, label: 'Parks & Recreation', icon: <FaTree />, count: 8 },
                { key: 'mall' as const, label: 'Shopping Malls', icon: <FaShoppingBag />, count: 5 },
                { key: 'school' as const, label: 'Schools', icon: <FaSchool />, count: 15 },
                { key: 'hospital' as const, label: 'Healthcare', icon: <FaHospital />, count: 3 },
                { key: 'parking' as const, label: 'Parking Lots', icon: <FaParking />, count: 20 },
                { key: 'dining' as const, label: 'Dining Options', icon: <FaUtensils />, count: 25 }
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
                onClick={() => setSelectedOptions({
                  gym: false,
                  park: false,
                  mall: false,
                  school: false,
                  hospital: false,
                  parking: false,
                  dining: false
                })}
                className="flex-1 px-4 py-3 text-purple-700 bg-white border border-purple-300 rounded-xl font-semibold hover:bg-purple-100 transition-colors"
              >
                Reset All
              </button>
              <button
                onClick={() => setShowFilterMenu(false)}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl font-semibold hover:from-purple-600 hover:to-purple-700 transition-all shadow-lg"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DetailsView;