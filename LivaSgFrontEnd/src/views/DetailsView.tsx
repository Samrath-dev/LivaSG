import { HiChevronLeft, HiMap, HiHome, HiTrendingUp } from 'react-icons/hi';
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

const DetailsView = ({ location, onBack }: DetailsViewProps) => {
  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

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
            <h2 className="font-bold text-lg mb-4 text-gray-900">Facilities Map</h2>
            <img
              src={facilitiesMapDummy}
              alt={`Facilities map for ${location.street}`}
              className="w-full rounded-xl object-contain"
              loading="lazy"
            />
          </div>

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