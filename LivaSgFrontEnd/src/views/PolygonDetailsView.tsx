import { HiChevronLeft, HiTrendingUp, HiStar, HiMap } from 'react-icons/hi';
import { useState } from 'react';
import OneMapInteractive from '../components/OneMapInteractive';

interface PolygonDetailsViewProps {
  polygon: {
    id: number;
    name: string;
    area: string;
    coordinates: [number, number][];
    avgPrice: number;
    priceRange: [number, number];
    growth: number;
    description: string;
    highlights: string[];
    stats: {
      totalListings: number;
      avgSize: number;
      popularTypes: string[];
    };
  };
  onBack: () => void;
}

const PolygonDetailsView = ({ polygon, onBack }: PolygonDetailsViewProps) => {
  const [mapCenter] = useState<[number, number]>(() => {
    // Calculate center of polygon
    const lats = polygon.coordinates.map(coord => coord[0]);
    const lngs = polygon.coordinates.map(coord => coord[1]);
    const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
    const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
    return [centerLat, centerLng];
  });

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center text-purple-700 hover:text-purple-900 transition-colors group"
          >
            <HiChevronLeft className="w-6 h-6 mr-2 group-hover:-translate-x-1 transition-transform" />
            <span className="font-semibold">Back to Map</span>
          </button>
        </div>
        
        <div className="mt-4">
          <h1 className="text-2xl font-bold text-gray-900">{polygon.name}</h1>
          <p className="text-gray-600 mt-2 flex items-center gap-2">
            <span className="bg-gradient-to-r from-purple-500 to-purple-600 text-white text-sm font-semibold px-3 py-1 rounded-full">
              {polygon.area}
            </span>
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto p-6 space-y-6">
          {/* Interactive Map */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-lg text-gray-900 flex items-center gap-2">
                <HiMap className="w-5 h-5 text-blue-500" />
                Area Overview
              </h2>
              <div className="text-sm text-gray-600 font-medium bg-gray-100 px-3 py-1 rounded-full">
                Interactive Map
              </div>
            </div>
            <div className="w-full h-96 rounded-xl border border-gray-100 overflow-hidden">
              <OneMapInteractive
                center={mapCenter}
                zoom={14}
                polygons={[
                  {
                    positions: polygon.coordinates,
                    color: '#8b5cf6',
                    fillColor: '#8b5cf6',
                    fillOpacity: 0.3,
                    popup: `<strong>${polygon.name}</strong><br/>Area: ${polygon.area}`
                  }
                ]}
                className="w-full h-full"
              />
            </div>
          </div>

          {/* Price Information */}
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl p-6 text-white shadow-lg">
            <h2 className="font-bold text-lg mb-6 flex items-center gap-2">
              <HiTrendingUp className="w-5 h-5" />
              Price Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-blue-200 text-sm mb-2">Price Range</div>
                <div className="font-bold text-2xl">
                  {formatPrice(polygon.priceRange[0])} - {formatPrice(polygon.priceRange[1])}
                </div>
              </div>
              <div className="text-center">
                <div className="text-blue-200 text-sm mb-2">Average PSF</div>
                <div className="font-bold text-2xl">
                  ${polygon.avgPrice.toLocaleString()} psf
                </div>
              </div>
              <div className="text-center">
                <div className="text-blue-200 text-sm mb-2">Annual Growth</div>
                <div className="flex items-center justify-center font-bold text-2xl text-green-300">
                  <HiTrendingUp className="w-5 h-5 mr-2" />
                  +{polygon.growth}%
                </div>
              </div>
            </div>
          </div>

          {/* Description & Statistics Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Description */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
              <h2 className="font-bold text-lg mb-4 text-gray-900 flex items-center gap-2">
                <HiStar className="w-5 h-5 text-yellow-500" />
                About this Area
              </h2>
              <p className="text-gray-700 leading-relaxed">{polygon.description}</p>
            </div>

            {/* Statistics */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
              <h2 className="font-bold text-lg mb-4 text-gray-900">Market Statistics</h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center pb-3 border-b border-gray-100">
                  <span className="text-gray-600">Total Listings</span>
                  <span className="font-bold text-gray-900">{polygon.stats.totalListings}</span>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-gray-100">
                  <span className="text-gray-600">Average Size</span>
                  <span className="font-bold text-gray-900">{polygon.stats.avgSize} sqft</span>
                </div>
                <div className="pt-2">
                  <span className="text-gray-600 block mb-2">Popular Property Types</span>
                  <div className="flex flex-wrap gap-2">
                    {polygon.stats.popularTypes.map((type, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-1 bg-purple-100 text-purple-800 text-sm font-semibold rounded-lg"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Highlights */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
            <h2 className="font-bold text-lg mb-4 text-gray-900">Area Highlights</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {polygon.highlights.map((highlight, index) => (
                <div key={index} className="flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors border border-gray-100">
                  <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-r from-green-500 to-green-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                    {index + 1}
                  </div>
                  <span className="text-gray-800 font-medium">{highlight}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Market Insights */}
          <div className="bg-gradient-to-r from-amber-500 to-amber-600 rounded-2xl p-6 text-white shadow-lg">
            <h2 className="font-bold text-lg mb-3 flex items-center gap-2">
              <HiTrendingUp className="w-5 h-5" />
              Investment Outlook
            </h2>
            <p className="text-amber-50 leading-relaxed">
              The {polygon.name} area has demonstrated strong market performance with a {polygon.growth}% 
              annual growth rate. With {polygon.stats.totalListings} active listings and an average price 
              of ${polygon.avgPrice.toLocaleString()} psf, this area offers excellent potential for both 
              investors and homeowners looking for long-term value appreciation in the {polygon.area} region.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PolygonDetailsView;
