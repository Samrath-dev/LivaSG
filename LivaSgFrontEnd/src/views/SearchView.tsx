import { useState } from 'react';
import { HiFilter, HiChevronLeft, HiX, HiMap, HiHome, HiTrendingUp, HiChevronDown, HiChevronRight } from 'react-icons/hi';

interface SearchViewProps {
  searchQuery: string;
  onBack: () => void;
  onViewDetails: (location: any) => void;
}

interface Filters {
  facilities: string[];
  priceRange: [number, number];
}

interface LocationResult {
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
  showDetails?: boolean;
}

const SearchView = ({ searchQuery, onBack, onViewDetails }: SearchViewProps) => {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    facilities: [],
    priceRange: [500000, 3000000]
  });
  const [expandedLocation, setExpandedLocation] = useState<number | null>(null);

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

  // Singapore street-level location data
  const getLocationResults = (): LocationResult[] => {
    const locationData: Record<string, LocationResult[]> = {
      'orchard': [
        { 
          id: 1, 
          street: 'Orchard Boulevard',
          area: 'Orchard',
          district: 'District 9',
          priceRange: [2800000, 8500000],
          avgPrice: 3400,
          facilities: ['Luxury Shopping', 'Fine Dining', 'Entertainment'],
          description: 'Prestigious address along Orchard Road with luxury condominiums and excellent connectivity to shopping malls and entertainment hubs.',
          growth: 5.2,
          amenities: ['ION Orchard', 'Wheelock Place', 'Orchard MRT'],
        },
        { 
          id: 2, 
          street: 'Scotts Road',
          area: 'Orchard',
          district: 'District 9',
          priceRange: [2200000, 6000000],
          avgPrice: 2900,
          facilities: ['Shopping', 'Hotels', 'Central Location'],
          description: 'Prime location with luxury hotels, shopping centers, and high-end residential developments.',
          growth: 4.9,
          amenities: ['Scotts Square', 'Far East Plaza', 'Newton MRT'],
        },
      ],
      'bukit panjang': [
        { 
          id: 3, 
          street: 'Fajar Road',
          area: 'Bukit Panjang',
          district: 'District 23',
          priceRange: [450000, 1200000],
          avgPrice: 680,
          facilities: ['LRT Access', 'Schools', 'Community Facilities'],
          description: 'Family-friendly neighborhood with good amenities and convenient LRT connectivity to Bukit Panjang town center.',
          growth: 3.8,
          amenities: ['Fajar LRT', 'Bukit Panjang Plaza', 'West Spring Primary'],
        },
        { 
          id: 4, 
          street: 'Segar Road',
          area: 'Bukit Panjang',
          district: 'District 23',
          priceRange: [480000, 1300000],
          avgPrice: 720,
          facilities: ['Parks', 'Shopping', 'Transport Hub'],
          description: 'Well-established residential area with proximity to Bukit Panjang Integrated Transport Hub and recreational facilities.',
          growth: 4.1,
          amenities: ['Bukit Panjang ITH', 'Segar LRT', 'Junction 10'],
        },
        { 
          id: 5, 
          street: 'Petir Road',
          area: 'Bukit Panjang',
          district: 'District 23',
          priceRange: [420000, 1100000],
          avgPrice: 650,
          facilities: ['Nature', 'Schools', 'Affordable'],
          description: 'Quiet residential street near Chestnut Nature Park with affordable housing options and good schools.',
          growth: 3.5,
          amenities: ['Chestnut Nature Park', 'Greenridge Shopping', 'St. Joseph Institution'],
        },
      ],
      'tampines': [
        { 
          id: 6, 
          street: 'Tampines Street 11',
          area: 'Tampines',
          district: 'District 18',
          priceRange: [380000, 950000],
          avgPrice: 520,
          facilities: ['Town Centre', 'Schools', 'Recreation'],
          description: 'Central location in Tampines town with easy access to all amenities and excellent family facilities.',
          growth: 3.2,
          amenities: ['Tampines Mall', 'Tampines MRT', 'Our Tampines Hub'],
        },
        { 
          id: 7, 
          street: 'Tampines Avenue 7',
          area: 'Tampines',
          district: 'District 18',
          priceRange: [420000, 1100000],
          avgPrice: 580,
          facilities: ['Parks', 'Sports', 'Community'],
          description: 'Quieter part of Tampines with proximity to Tampines Eco Green and various sports facilities.',
          growth: 3.6,
          amenities: ['Tampines Eco Green', 'Safra Tampines', 'Tampines North CC'],
        },
      ],
      'jurong': [
        { 
          id: 8, 
          street: 'Jurong East Street 13',
          area: 'Jurong East',
          district: 'District 22',
          priceRange: [350000, 900000],
          avgPrice: 480,
          facilities: ['Regional Centre', 'Future Growth', 'Transport'],
          description: 'Heart of Jurong East regional centre with excellent connectivity and future growth potential from Jurong Lake District development.',
          growth: 7.8,
          amenities: ['Jurong East MRT', 'JEM Mall', 'Westgate'],
        },
        { 
          id: 9, 
          street: 'Jurong West Street 65',
          area: 'Jurong West',
          district: 'District 22',
          priceRange: [320000, 850000],
          avgPrice: 450,
          facilities: ['Schools', 'Community', 'Affordable'],
          description: 'Mature residential area with established community facilities and good educational institutions.',
          growth: 4.2,
          amenities: ['Pioneer Mall', 'Boon Lay MRT', 'Jurong West Sports Centre'],
        },
      ],
      'marine parade': [
        { 
          id: 10, 
          street: 'Marine Parade Road',
          area: 'Marine Parade',
          district: 'District 15',
          priceRange: [1300000, 3800000],
          avgPrice: 1650,
          facilities: ['Seafront', 'Family-friendly', 'East Coast'],
          description: 'Prime seafront location with panoramic sea views and direct access to East Coast Park.',
          growth: 4.3,
          amenities: ['East Coast Park', 'Parkway Parade', 'Katong Mall'],
        },
        { 
          id: 11, 
          street: 'East Coast Road',
          area: 'Marine Parade',
          district: 'District 15',
          priceRange: [1100000, 3200000],
          avgPrice: 1450,
          facilities: ['Dining', 'Heritage', 'Community'],
          description: 'Historic Katong area with rich Peranakan heritage, famous eateries, and charming shophouses.',
          growth: 4.0,
          amenities: ['Katong I12', 'Roxy Square', 'Marine Parade CC'],
        },
      ]
    };

    const searchTerm = searchQuery.toLowerCase();
    const results = Object.entries(locationData).find(([area]) => 
      searchTerm.includes(area)
    )?.[1] || [];

    // Apply filters
    return results.filter(location => {
      // Price filter
      if (location.priceRange[1] < filters.priceRange[0] || location.priceRange[0] > filters.priceRange[1]) {
        return false;
      }
      
      // Facilities filter
      if (filters.facilities.length > 0) {
        const hasMatchingFacility = filters.facilities.some(filter => 
          location.facilities.some(facility => 
            facility.toLowerCase().includes(filter.toLowerCase())
          )
        );
        if (!hasMatchingFacility) return false;
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

  const handlePriceChange = (min: number, max: number) => {
    setFilters(prev => ({
      ...prev,
      priceRange: [min, max]
    }));
  };

  const clearFilters = () => {
    setFilters({
      facilities: [],
      priceRange: [500000, 3000000]
    });
  };

  const toggleLocationDetails = (locationId: number) => {
    setExpandedLocation(expandedLocation === locationId ? null : locationId);
  };

  const handleViewDetails = (location: LocationResult) => {
    onViewDetails(location);
  };

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  const locationResults = getLocationResults();

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
            {(filters.facilities.length > 0 || filters.priceRange[0] > 500000 || filters.priceRange[1] < 3000000) && (
              <span className="ml-2 bg-red-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center font-bold">
                {filters.facilities.length + (filters.priceRange[0] > 500000 ? 1 : 0) + (filters.priceRange[1] < 3000000 ? 1 : 0)}
              </span>
            )}
          </button>
        </div>
        
        <div className="mt-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Property Locations
          </h1>
          <p className="text-gray-600 mt-1">
            Searching in <span className="font-semibold text-blue-600">"{searchQuery}"</span>
          </p>
          <div className="flex items-center mt-3">
            <HiHome className="w-4 h-4 text-gray-400 mr-2" />
            <span className="text-sm text-gray-500">
              {locationResults.length} {locationResults.length === 1 ? 'location' : 'locations'} found
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
                <h2 className="text-2xl font-bold text-gray-900">Location Filters</h2>
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
              Show {locationResults.length} Locations
            </button>
          </div>
        </div>
      )}

      {/* Location Results */}
      <div className="flex-1 overflow-auto bg-gray-50">
        <div className="p-6">
          {locationResults.length === 0 ? (
            <div className="text-center py-16">
              <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                <HiHome className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">No locations found</h3>
              <p className="text-gray-600 mb-6">
                No property locations match your search and filters
              </p>
              <div className="space-y-3 text-sm text-gray-500">
                <p>• Try searching for areas like "Bukit Panjang", "Tampines", or "Marine Parade"</p>
                <p>• Adjust your budget range</p>
                <p>• Try different amenity filters</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {locationResults.map(location => (
                <div key={location.id} className="bg-white rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 border border-gray-100 overflow-hidden">
                  {/* Location Header - Always Visible */}
                  <div 
                    className="p-6 cursor-pointer"
                    onClick={() => toggleLocationDetails(location.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-bold text-xl text-gray-900">{location.street}</h3>
                          <span className="bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full">
                            {location.district}
                          </span>
                        </div>
                        <p className="text-gray-600 mb-3">{location.area}</p>
                        
                        <div className="flex items-center gap-6">
                          <div>
                            <div className="text-sm text-gray-600 mb-1">Price Range</div>
                            <div className="font-bold text-lg text-gray-900">
                              {formatPrice(location.priceRange[0])} - {formatPrice(location.priceRange[1])}
                            </div>
                          </div>
                          <div>
                            <div className="text-sm text-gray-600 mb-1">Avg PSF</div>
                            <div className="font-bold text-lg text-blue-600">
                              ${location.avgPrice} psf
                            </div>
                          </div>
                          <div className="flex items-center text-green-600">
                            <HiTrendingUp className="w-4 h-4 mr-1" />
                            <span className="text-sm font-semibold">+{location.growth}%</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewDetails(location);
                          }}
                          className="flex-shrink-0 bg-blue-600 text-white px-4 py-2 rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-sm hover:shadow-md"
                        >
                          View Details
                        </button>
                        {expandedLocation === location.id ? (
                          <HiChevronDown className="w-5 h-5 text-gray-400" />
                        ) : (
                          <HiChevronRight className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Expandable Details */}
                  {expandedLocation === location.id && (
                    <div className="border-t border-gray-100 p-6 bg-gray-50">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-3">About this Location</h4>
                          <p className="text-gray-600 leading-relaxed">{location.description}</p>
                          
                          <div className="mt-4">
                            <h4 className="font-semibold text-gray-900 mb-2">Key Features</h4>
                            <div className="flex flex-wrap gap-2">
                              {location.facilities.map(facility => (
                                <span
                                  key={facility}
                                  className="inline-block bg-green-100 text-green-800 text-xs font-medium px-3 py-1.5 rounded-full"
                                >
                                  {facility}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-3">Nearby Amenities</h4>
                          <div className="space-y-2">
                            {location.amenities.map((amenity, index) => (
                              <div key={index} className="flex items-center text-gray-600">
                                <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                                {amenity}
                              </div>
                            ))}
                          </div>
                          
                          <div className="mt-6 p-4 bg-blue-50 rounded-xl">
                            <div className="text-sm text-blue-800">
                              <strong>Market Insight:</strong> Properties in {location.street} have shown consistent growth over the past 3 years.
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
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