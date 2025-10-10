import { useState } from 'react';
import { HiFilter, HiChevronLeft, HiX, HiMap, HiHome, HiTrendingUp } from 'react-icons/hi';

interface SearchViewProps {
  searchQuery: string;
  onBack: () => void;
}

interface Filters {
  facilities: string[];
  priceRange: [number, number];
  propertyType: string[];
}

interface DistrictResult {
  id: number;
  name: string;
  district: string;
  priceRange: [number, number];
  avgPrice: number;
  facilities: string[];
  description: string;
  growth: number; // % price growth
  amenities: string[];
  propertyTypes: string[];
}

const SearchView = ({ searchQuery, onBack }: SearchViewProps) => {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    facilities: [],
    priceRange: [500000, 3000000],
    propertyType: []
  });

  const facilitiesList = [
    'Near MRT',
    'Good Schools',
    'Shopping Malls',
    'Parks',
    'Hawker Centres',
    'Healthcare',
    'Sports Facilities',
    'Community Centre'
  ];

  const propertyTypes = [
    'HDB',
    'Condo',
    'Landed',
    'Executive Condo',
    'Cluster House'
  ];

  // Singapore district data for home buyers
  const getDistrictResults = (): DistrictResult[] => {
    const districtData: Record<string, DistrictResult[]> = {
      'orchard': [
        { 
          id: 1, 
          name: 'Orchard Road Area', 
          district: 'District 9',
          priceRange: [2500000, 8000000],
          avgPrice: 3200,
          facilities: ['Luxury Shopping', 'Fine Dining', 'Entertainment'],
          description: 'Prime central location with luxury condominiums and excellent connectivity',
          growth: 5.2,
          amenities: ['ION Orchard', 'Takashimaya', 'Somerset MRT'],
          propertyTypes: ['Condo', 'Landed']
        },
        { 
          id: 2, 
          name: 'River Valley', 
          district: 'District 9',
          priceRange: [1800000, 5000000],
          avgPrice: 2400,
          facilities: ['Riverside', 'Dining', 'Central Location'],
          description: 'Upscale residential area with beautiful river views and central location',
          growth: 4.8,
          amenities: ['Great World City', 'Clarke Quay', 'Fort Canning'],
          propertyTypes: ['Condo', 'Landed']
        },
      ],
      'novena': [
        { 
          id: 3, 
          name: 'Novena', 
          district: 'District 11',
          priceRange: [1500000, 4000000],
          avgPrice: 2100,
          facilities: ['Medical Hub', 'Good Schools', 'Central Location'],
          description: 'Medical and educational hub with excellent transportation links',
          growth: 6.1,
          amenities: ['Mount Elizabeth Hospital', 'United Square', 'Novena MRT'],
          propertyTypes: ['Condo', 'HDB']
        },
      ],
      'marine': [
        { 
          id: 4, 
          name: 'Marine Parade', 
          district: 'District 15',
          priceRange: [1200000, 3500000],
          avgPrice: 1600,
          facilities: ['Seafront', 'Family-friendly', 'East Coast Park'],
          description: 'Popular seaside residential area with family-friendly amenities',
          growth: 4.3,
          amenities: ['East Coast Park', 'Parkway Parade', 'Katong Mall'],
          propertyTypes: ['HDB', 'Condo', 'Landed']
        },
      ],
      'bukit timah': [
        { 
          id: 5, 
          name: 'Bukit Timah', 
          district: 'District 10',
          priceRange: [3000000, 10000000],
          avgPrice: 2800,
          facilities: ['Prestigious Schools', 'Nature', 'Luxury Living'],
          description: 'Prestigious residential area with top schools and lush greenery',
          growth: 5.7,
          amenities: ['Botanic Gardens', 'Bukit Timah Plaza', 'Rail Mall'],
          propertyTypes: ['Landed', 'Condo']
        },
      ],
      'tampines': [
        { 
          id: 6, 
          name: 'Tampines', 
          district: 'District 18',
          priceRange: [400000, 1500000],
          avgPrice: 550,
          facilities: ['Self-contained Town', 'Family Amenities', 'Affordable'],
          description: 'Mature town with comprehensive amenities and family-friendly environment',
          growth: 3.2,
          amenities: ['Tampines Mall', 'Our Tampines Hub', 'Tampines MRT'],
          propertyTypes: ['HDB', 'Condo', 'Executive Condo']
        },
      ],
      'jurong': [
        { 
          id: 7, 
          name: 'Jurong East', 
          district: 'District 22',
          priceRange: [350000, 1200000],
          avgPrice: 480,
          facilities: ['Regional Centre', 'Future Growth', 'Affordable'],
          description: 'Regional centre with strong future growth potential and affordability',
          growth: 7.8,
          amenities: ['JEM', 'Westgate', 'Jurong East MRT'],
          propertyTypes: ['HDB', 'Condo']
        },
      ],
      'bishan': [
        { 
          id: 8, 
          name: 'Bishan', 
          district: 'District 20',
          priceRange: [600000, 1800000],
          avgPrice: 850,
          facilities: ['Central Location', 'Good Schools', 'Park Connector'],
          description: 'Central location with excellent schools and recreational facilities',
          growth: 4.5,
          amenities: ['Bishan Park', 'Junction 8', 'Bishan MRT'],
          propertyTypes: ['HDB', 'Condo']
        },
      ]
    };

    const searchTerm = searchQuery.toLowerCase();
    const results = Object.entries(districtData).find(([area]) => 
      searchTerm.includes(area)
    )?.[1] || [];

    // Apply filters
    return results.filter(district => {
      // Price filter - check if price range overlaps with filter range
      if (district.priceRange[1] < filters.priceRange[0] || district.priceRange[0] > filters.priceRange[1]) {
        return false;
      }
      
      // Facilities filter
      if (filters.facilities.length > 0) {
        const hasMatchingFacility = filters.facilities.some(filter => 
          district.facilities.some(facility => 
            facility.toLowerCase().includes(filter.toLowerCase())
          )
        );
        if (!hasMatchingFacility) return false;
      }
      
      // Property type filter
      if (filters.propertyType.length > 0) {
        const hasMatchingType = filters.propertyType.some(type => 
          district.propertyTypes.includes(type)
        );
        if (!hasMatchingType) return false;
      }
      
      return true;
    });
  };

  const handleFacilityToggle = (facility: string) => {
    setFilters(prev => ({
      ...prev,
      facilities: prev.facilities.includes(facility)
        ? prev.facilities.filter(f => f !== facility)
        : [...prev.facilities, facility]
    }));
  };

  const handlePropertyTypeToggle = (type: string) => {
    setFilters(prev => ({
      ...prev,
      propertyType: prev.propertyType.includes(type)
        ? prev.propertyType.filter(t => t !== type)
        : [...prev.propertyType, type]
    }));
  };

  const handlePriceChange = (min: number, max: number) => {
    setFilters(prev => ({
      ...prev,
      priceRange: [min, max]
    }));
  };

  const clearFilters = () => {
    setFilters({
      facilities: [],
      priceRange: [500000, 3000000],
      propertyType: []
    });
  };

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  const districtResults = getDistrictResults();

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
            <span className="font-medium">Back to Map</span>
          </button>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-4 py-2.5 rounded-xl border-2 transition-all duration-200 ${
              showFilters 
                ? 'bg-blue-600 text-white border-blue-600 shadow-lg' 
                : 'bg-white text-gray-700 border-gray-200 hover:border-blue-400 hover:shadow-md'
            }`}
          >
            <HiFilter className="w-5 h-5 mr-2" />
            <span className="font-semibold">Filters</span>
            {(filters.facilities.length > 0 || filters.propertyType.length > 0 || filters.priceRange[0] > 500000 || filters.priceRange[1] < 3000000) && (
              <span className="ml-2 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center font-bold">
                {filters.facilities.length + filters.propertyType.length + (filters.priceRange[0] > 500000 ? 1 : 0) + (filters.priceRange[1] < 3000000 ? 1 : 0)}
              </span>
            )}
          </button>
        </div>
        
        <div className="mt-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Property Districts
          </h1>
          <p className="text-gray-600 mt-1">
            Searching in <span className="font-semibold text-blue-600">"{searchQuery}"</span>
          </p>
          <div className="flex items-center mt-3">
            <HiHome className="w-4 h-4 text-gray-400 mr-2" />
            <span className="text-sm text-gray-500">
              {districtResults.length} {districtResults.length === 1 ? 'district' : 'districts'} found
            </span>
          </div>
        </div>
      </div>

      {/* Full-page Filters Overlay */}
      {showFilters && (
        <div className="fixed inset-0 bg-white z-50 flex flex-col">
          {/* Filters Header */}
          <div className="flex-shrink-0 border-b border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Property Filters</h2>
                <p className="text-gray-600 mt-1">Find your perfect neighborhood</p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={clearFilters}
                  className="text-blue-600 hover:text-blue-800 font-medium px-3 py-2 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  Clear All
                </button>
                <button
                  onClick={() => setShowFilters(false)}
                  className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
                >
                  <HiX className="w-6 h-6 text-gray-600" />
                </button>
              </div>
            </div>
          </div>

          {/* Filters Content */}
          <div className="flex-1 overflow-auto p-6">
            {/* Price Range Filter */}
            <div className="mb-12">
              <h3 className="font-bold text-lg mb-6 text-gray-900">Budget Range</h3>
              <div className="space-y-6">
                <div className="space-y-4">
                  <input
                    type="range"
                    min="500000"
                    max="5000000"
                    step="100000"
                    value={filters.priceRange[0]}
                    onChange={(e) => handlePriceChange(Number(e.target.value), filters.priceRange[1])}
                    className="w-full h-2 bg-gradient-to-r from-blue-500 to-gray-300 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-4 [&::-webkit-slider-thumb]:border-blue-500 [&::-webkit-slider-thumb]:shadow-lg"
                  />
                  <input
                    type="range"
                    min="500000"
                    max="5000000"
                    step="100000"
                    value={filters.priceRange[1]}
                    onChange={(e) => handlePriceChange(filters.priceRange[0], Number(e.target.value))}
                    className="w-full h-2 bg-gradient-to-r from-gray-300 to-blue-500 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-4 [&::-webkit-slider-thumb]:border-blue-500 [&::-webkit-slider-thumb]:shadow-lg"
                  />
                </div>
                <div className="flex justify-between items-center bg-gray-50 rounded-2xl p-4">
                  <div className="text-center">
                    <div className="text-sm text-gray-600 font-medium">Min Budget</div>
                    <div className="text-xl font-bold text-blue-600">{formatPrice(filters.priceRange[0])}</div>
                  </div>
                  <div className="text-gray-400 text-lg">—</div>
                  <div className="text-center">
                    <div className="text-sm text-gray-600 font-medium">Max Budget</div>
                    <div className="text-xl font-bold text-blue-600">{formatPrice(filters.priceRange[1])}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Property Type Filter */}
            <div className="mb-12">
              <h3 className="font-bold text-lg mb-6 text-gray-900">Property Type</h3>
              <div className="grid grid-cols-1 gap-3">
                {propertyTypes.map(type => (
                  <label key={type} className="flex items-center space-x-4 cursor-pointer p-4 rounded-xl border-2 border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all duration-200">
                    <input
                      type="checkbox"
                      checked={filters.propertyType.includes(type)}
                      onChange={() => handlePropertyTypeToggle(type)}
                      className="w-5 h-5 rounded border-2 border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
                    />
                    <span className="text-base font-semibold text-gray-800">{type}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Facilities Filter */}
            <div>
              <h3 className="font-bold text-lg mb-6 text-gray-900">Preferred Amenities</h3>
              <div className="grid grid-cols-1 gap-3">
                {facilitiesList.map(facility => (
                  <label key={facility} className="flex items-center space-x-4 cursor-pointer p-4 rounded-xl border-2 border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all duration-200">
                    <input
                      type="checkbox"
                      checked={filters.facilities.includes(facility)}
                      onChange={() => handleFacilityToggle(facility)}
                      className="w-5 h-5 rounded border-2 border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
                    />
                    <span className="text-base font-semibold text-gray-800">{facility}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Apply Filters Button */}
          <div className="flex-shrink-0 border-t border-gray-100 p-6">
            <button
              onClick={() => setShowFilters(false)}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-4 px-6 rounded-xl font-bold text-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              Show {districtResults.length} Districts
            </button>
          </div>
        </div>
      )}

      {/* District Results */}
      <div className="flex-1 overflow-auto bg-gray-50">
        <div className="p-6">
          {districtResults.length === 0 ? (
            <div className="text-center py-16">
              <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                <HiHome className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">No districts found</h3>
              <p className="text-gray-600 mb-6">
                No property districts match your search and filters
              </p>
              <div className="space-y-3 text-sm text-gray-500">
                <p>• Try searching for areas like "Orchard", "Marine Parade", or "Bukit Timah"</p>
                <p>• Adjust your budget range</p>
                <p>• Consider different property types</p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {districtResults.map(district => (
                <div key={district.id} className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
                  <div className="flex gap-6">
                    {/* District Badge */}
                    <div className="flex-shrink-0 w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                      <HiMap className="w-8 h-8 text-white" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-bold text-xl text-gray-900 mb-1">{district.name}</h3>
                          <div className="flex items-center gap-4 mb-2">
                            <span className="bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full">
                              {district.district}
                            </span>
                            <div className="flex items-center text-green-600">
                              <HiTrendingUp className="w-4 h-4 mr-1" />
                              <span className="text-sm font-semibold">+{district.growth}%</span>
                            </div>
                          </div>
                        </div>
                        
                        <button className="flex-shrink-0 bg-blue-600 text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-sm hover:shadow-md">
                          View Properties
                        </button>
                      </div>

                      <p className="text-gray-600 mb-4 leading-relaxed">{district.description}</p>

                      {/* Price Information */}
                      <div className="bg-gray-50 rounded-xl p-4 mb-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <div className="text-sm text-gray-600 mb-1">Price Range</div>
                            <div className="font-bold text-lg text-gray-900">
                              {formatPrice(district.priceRange[0])} - {formatPrice(district.priceRange[1])}
                            </div>
                          </div>
                          <div>
                            <div className="text-sm text-gray-600 mb-1">Avg PSF</div>
                            <div className="font-bold text-lg text-blue-600">
                              ${district.avgPrice} psf
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Key Information */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Property Types</h4>
                          <div className="flex flex-wrap gap-2">
                            {district.propertyTypes.map(type => (
                              <span
                                key={type}
                                className="inline-block bg-green-100 text-green-800 text-xs font-medium px-3 py-1.5 rounded-full"
                              >
                                {type}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Key Amenities</h4>
                          <div className="flex flex-wrap gap-2">
                            {district.amenities.slice(0, 3).map(amenity => (
                              <span
                                key={amenity}
                                className="inline-block bg-purple-100 text-purple-800 text-xs font-medium px-3 py-1.5 rounded-full"
                              >
                                {amenity}
                              </span>
                            ))}
                            {district.amenities.length > 3 && (
                              <span className="inline-block bg-gray-100 text-gray-600 text-xs font-medium px-3 py-1.5 rounded-full">
                                +{district.amenities.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchView;