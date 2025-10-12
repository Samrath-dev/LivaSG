import { HiChevronLeft, HiMap, HiHome, HiTrendingUp } from 'react-icons/hi';
import { useState } from 'react';
import { FaDumbbell, FaTree } from 'react-icons/fa';
import React, { isValidElement, cloneElement } from 'react';
import type { ReactNode } from 'react';
import facilitiesMapDummy from '../assets/facilitiesMapDummy.png';
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

  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [selectedOptions, setSelectedOptions] = useState<{ gym: boolean; park: boolean }>({
    gym: false,
    park: false
  });

  const toggleOption = (key: 'gym' | 'park') => {
    setSelectedOptions(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const FilterItem = ({ icon, label, checked, onChange, count, iconStyle, iconClassName }: FilterItemProps) => (
  <label className="flex items-center justify-between w-full">
    <div className="flex items-center gap-3">
      <span
        className={`flex-shrink-0 ${iconClassName ?? ''}`}
        style={{
          width: 'clamp(32px,10vw,48px)',
          height: 'clamp(32px,10vw,48px)',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          ...(iconStyle || {})
        }}>
        {isValidElement(icon)
          ? cloneElement(icon as React.ReactElement<any>, {
              className: `${(icon as any)?.props?.className ?? ''} w-full h-full`
            })
          : icon}
      </span>
      <span className="text-xl text-gray-700">{label}</span>
    </div>
    <div className="flex items-center gap-3">
      {count !== undefined && <span className="text-xs text-gray-500">{count}</span>}
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="h-8 w-8"
        aria-label={`Filter by ${label.toLowerCase()}`}
      />
    </div>
  </label>
);

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-100 p-6">
        <div className="flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
          >
            <HiChevronLeft className="w-6 h-6 mr-2" />
            <span className="font-medium">Back to Search</span>
          </button>
        </div>
        
        <div className="mt-4">
          <h1 className="text-2xl font-bold text-gray-900">{location.street}</h1>
          <p className="text-gray-600 mt-1">{location.area} • {location.district}</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="space-y-6">

          {/* Price History */}
          <div className="bg-green-50 rounded-2xl p-6 text-center">
            <h2 className="font-bold text-lg mb-4 text-gray-900">Price History</h2>
            <img
              src={priceGraphDummy}
              alt={`Price history for ${location.street}`}
              className="w-full rounded-xl object-contain"
              loading="lazy"
            />
          </div>

          {/* Facilities Map */}
          <div className="bg-amber-50 rounded-2xl p-6 text-center">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-bold text-lg mb-4 text-gray-900">Facilities Map</h2>

              <div>
                <button
                  onClick={() => setShowFilterMenu(s => !s)}
                  className="inline-flex items-center px-3 py-1.5 bg-white border rounded-lg text-sm text-gray-700 shadow-sm hover:bg-gray-50"
                >
                  Filters
                </button>
              </div>
            </div>

            <img
              src={facilitiesMapDummy}
              alt={`Facilities map for ${location.street}`}
              className="w-full rounded-xl object-contain"
              loading="lazy"
            />
          </div>

          {/* Facilities Map- Filter Submenu */}
          {showFilterMenu && (
            <div className="fixed inset-0 z-50 flex items-center justify-center"
              role="dialog"
              aria-modal="true"
            >

              {/* Overlay (Backdrop) */}
              <div
                className="absolute inset-0 bg-black bg-opacity-50"
                onClick={() => setShowFilterMenu(false)}
              />

              {/* Filter Menu */}
              <div
                className="relative bg-white rounded-lg w-[clamp(280px,75vw,800px)] max-w-full pt-[clamp(32px,2vw,40px)] px-[clamp(12px,2.5vw,24px)] pb-[clamp(12px,2.5vw,24px)] z-10 shadow-lg max-h-[90vh] overflow-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between mb-8 pb-2">
                  <h3 className="absolute left-1/2 flex items-center transform -translate-x-1/2 text-lg font-semibold text-gray-900 pointer-events-none">Filters</h3>
                  <button
                    onClick={() => setShowFilterMenu(false)}
                    className="absolute right-4 top-0 transform translate-y-1/4 text-gray-500 hover:text-white hover:bg-red-900 transition-colors duration-300 text-xl p-1 px-2"
                  >
                    ✕
                  </button>
                </div>

                {/* Filter Options */}
                <div className="flex flex-col gap-3">
                  {[
                    { key: 'gym' as const, label: 'Gym', icon: <FaDumbbell /> },
                    { key: 'park' as const, label: 'Park', icon: <FaTree /> }
                  ].map(f => (
                    <FilterItem
                      key={f.key}
                      icon={f.icon}
                      label={f.label}
                      checked={selectedOptions[f.key]}
                      onChange={() => toggleOption(f.key)}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Price Information */}
          <div className="bg-blue-50 rounded-2xl p-6">
            <h2 className="font-bold text-lg mb-4 text-gray-900">Price Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600 mb-1">Price Range</div>
                <div className="font-bold text-xl text-gray-900">
                  {formatPrice(location.priceRange[0])} - {formatPrice(location.priceRange[1])}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-1">Average PSF</div>
                <div className="font-bold text-xl text-blue-600">
                  ${location.avgPrice} psf
                </div>
              </div>
              <div className="flex items-center text-green-600">
                <HiTrendingUp className="w-5 h-5 mr-2" />
                <span className="font-semibold">+{location.growth}% growth</span>
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h2 className="font-bold text-lg mb-3 text-gray-900">About this Location</h2>
            <p className="text-gray-600 leading-relaxed">{location.description}</p>
          </div>

          {/* Key Features */}
          <div>
            <h2 className="font-bold text-lg mb-3 text-gray-900">Key Features</h2>
            <div className="flex flex-wrap gap-2">
              {location.facilities.map(facility => (
                <span
                  key={facility}
                  className="inline-block bg-green-100 text-green-800 text-sm font-medium px-3 py-2 rounded-full"
                >
                  {facility}
                </span>
              ))}
            </div>
          </div>

          {/* Nearby Amenities */}
          <div>
            <h2 className="font-bold text-lg mb-3 text-gray-900">Nearby Amenities</h2>
            <div className="space-y-3">
              {location.amenities.map((amenity, index) => (
                <div key={index} className="flex items-center text-gray-700">
                  <div className="w-3 h-3 bg-blue-500 rounded-full mr-4"></div>
                  {amenity}
                </div>
              ))}
            </div>
          </div>

          {/* Market Insights */}
          <div className="bg-yellow-50 rounded-2xl p-6">
            <h2 className="font-bold text-lg mb-2 text-gray-900">Market Insights</h2>
            <p className="text-yellow-800">
              Properties in {location.street} have shown consistent growth of {location.growth}% annually, 
              making it a promising investment opportunity in the {location.area} area.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailsView;