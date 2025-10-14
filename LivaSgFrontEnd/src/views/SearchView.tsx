import { useState, useEffect } from 'react';
import { HiFilter, HiChevronLeft, HiX, HiHome, HiSearch, HiCog } from 'react-icons/hi';

interface SearchViewProps {
  searchQuery: string;
  onBack: () => void;
  onViewDetails: (location: any) => void;
  onSearchQueryChange: (query: string) => void;
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

const SearchView = ({ searchQuery, onBack, onViewDetails, onSearchQueryChange }: SearchViewProps) => {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    facilities: [],
    priceRange: [500000, 3000000]
  });
  const [expandedLocation, setExpandedLocation] = useState<number | null>(null);
  const [locationResults, setLocationResults] = useState<LocationResult[]>([]);
  const [loading, setLoading] = useState(false);

  const facilitiesList = [
    'Near MRT',
    'Good Schools',
    'Shopping Malls',
    'Parks',
    'Hawker Centres',
    'Healthcare',
    'Sports Facilities'
  ];

  // Fetch filtered locations from backend
  const fetchFilteredLocations = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/search/filter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          facilities: filters.facilities,
          price_range: filters.priceRange,
          search_query: searchQuery
        }),
      });
      if (!response.ok) throw new Error('Failed to fetch locations');
      const data = await response.json();
      // Map backend fields to frontend fields
      const mappedData = data.map((loc: any) => ({
        ...loc,
        priceRange: loc.price_range,
        avgPrice: loc.avg_price,
      }));
      setLocationResults(mappedData);
    } catch (error) {
      setLocationResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFilteredLocations();
    // eslint-disable-next-line
  }, [filters, searchQuery]);

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

  const clearSearch = () => {
    onSearchQueryChange('');
  };

  const clearFilters = () => {
    setFilters({
      facilities: [],
      priceRange: [500000, 3000000]
    });
  };

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        {/* Title and Back Button */}
        <div className="flex items-center justify-between w-full mb-4">
          {/* Back Button */}
          <button
            onClick={onBack}
            className="text-purple-700 hover:text-purple-900 transition-colors"
          >
            <HiChevronLeft className="w-6 h-6" />
          </button>
          
          {/* Title */}
          <div className="flex items-center text-purple-700">
            <HiHome className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Search Locations</h1>
          </div>
          
          {/* Spacer for balance */}
          <div className="w-6"></div>
        </div>

        {/* Search Bar and Settings */}
        <div className="flex items-center gap-3 mb-3">
          {/* Search Bar */}
          <div className="flex-1">
            <div className="relative">
              <HiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-purple-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchQueryChange(e.target.value)}
                placeholder="Search for locations..."
                className="w-full pl-10 pr-10 py-3 border border-purple-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white text-purple-900 placeholder-purple-400"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-purple-400 hover:text-purple-600 transition-colors"
                >
                  <HiX className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>

          {/* Settings Gear Icon */}
          <button
            className="p-3 rounded-xl text-purple-600 hover:text-purple-800 hover:bg-purple-100 transition-all duration-200 border border-purple-200"
            onClick={() => {
              console.log('Settings clicked');
            }}
          >
            <HiCog className="w-5 h-5" />
          </button>
        </div>

        {/* Filters Button */}
        <div className="flex justify-between items-center">
          <div className="text-left">
            <p className="text-purple-600 text-sm">
              {locationResults.length} {locationResults.length === 1 ? 'location' : 'locations'} found
            </p>
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-4 py-2 rounded-xl border transition-all duration-200 font-semibold ${
              showFilters 
                ? 'bg-purple-600 text-white border-purple-600' 
                : 'bg-white text-purple-700 border-purple-300 hover:border-purple-500 hover:bg-purple-50'
            }`}
          >
            <HiFilter className="w-5 h-5 mr-2" />
            <span>Filters</span>
            {(filters.facilities.length > 0 || filters.priceRange[0] > 500000 || filters.priceRange[1] < 3000000) && (
              <span className="ml-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                {filters.facilities.length + (filters.priceRange[0] > 500000 ? 1 : 0) + (filters.priceRange[1] < 3000000 ? 1 : 0)}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Full-page Filters Overlay */}
      {showFilters && (
        <div className="fixed inset-0 z-50">
          {/* Grey Background Overlay */}
          <div className="absolute inset-0 bg-gray-600 bg-opacity-50" onClick={() => setShowFilters(false)} />
          
          {/* Filters Container */}
          <div className="absolute inset-0 flex items-start justify-center p-4 overflow-hidden">
            <div className="bg-white rounded-2xl w-full max-w-2xl mx-auto shadow-2xl border border-purple-200 max-h-[85vh] flex flex-col">
              {/* Filters Header */}
              <div className="flex-shrink-0 border-b border-purple-200 p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-purple-700">
                    <HiFilter className="w-5 h-5 mr-2" />
                    <h2 className="text-lg font-bold">Location Filters</h2>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={clearFilters}
                      className="text-purple-600 hover:text-purple-800 font-medium px-3 py-2 rounded-lg hover:bg-purple-50 transition-colors"
                    >
                      Clear All
                    </button>
                    <button
                      onClick={() => setShowFilters(false)}
                      className="p-2 hover:bg-purple-100 rounded-xl transition-colors text-purple-600 hover:text-purple-700"
                    >
                      <HiX className="w-6 h-6" />
                    </button>
                  </div>
                </div>
                <p className="text-purple-600 text-sm mt-1 text-left">
                  Find your perfect neighborhood
                </p>
              </div>

              {/* Filters Content - Scrollable */}
              <div className="flex-1 overflow-auto p-6">
                {/* Price Range Filter */}
                <div className="mb-8">
                  <h3 className="font-bold text-lg mb-4 text-purple-900 text-left">Budget Range</h3>
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <input
                        type="range"
                        min="500000"
                        max="5000000"
                        step="100000"
                        value={filters.priceRange[0]}
                        onChange={(e) => handlePriceChange(Number(e.target.value), filters.priceRange[1])}
                        className="w-full h-2 bg-gradient-to-r from-purple-500 to-purple-300 rounded-lg appearance-none cursor-pointer"
                      />
                      <input
                        type="range"
                        min="500000"
                        max="5000000"
                        step="100000"
                        value={filters.priceRange[1]}
                        onChange={(e) => handlePriceChange(filters.priceRange[0], Number(e.target.value))}
                        className="w-full h-2 bg-gradient-to-r from-purple-300 to-purple-500 rounded-lg appearance-none cursor-pointer"
                      />
                    </div>
                    <div className="flex justify-between items-center bg-purple-50 rounded-2xl p-4 border border-purple-200">
                      <div className="text-center">
                        <div className="text-sm text-purple-600 font-medium">Min Budget</div>
                        <div className="text-xl font-bold text-purple-600">{formatPrice(filters.priceRange[0])}</div>
                      </div>
                      <div className="text-purple-400 text-lg">—</div>
                      <div className="text-center">
                        <div className="text-sm text-purple-600 font-medium">Max Budget</div>
                        <div className="text-xl font-bold text-purple-600">{formatPrice(filters.priceRange[1])}</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Facilities Filter */}
                <div>
                  <h3 className="font-bold text-lg mb-4 text-purple-900 text-left">Preferred Amenities</h3>
                  <div className="grid grid-cols-1 gap-3">
                    {facilitiesList.map(facility => (
                      <label key={facility} className="flex items-center space-x-4 cursor-pointer p-4 rounded-xl border-2 border-purple-200 hover:border-purple-400 hover:bg-purple-50 transition-all duration-200 bg-white">
                        <div className={`relative w-6 h-6 rounded-xl border-2 transition-all cursor-pointer ${
                          filters.facilities.includes(facility) 
                            ? 'bg-purple-500 border-purple-500' 
                            : 'bg-white border-purple-300'
                        }`}>
                          {filters.facilities.includes(facility) && (
                            <svg className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                          <input
                            type="checkbox"
                            checked={filters.facilities.includes(facility)}
                            onChange={() => handleFacilityToggle(facility)}
                            className="hidden"
                          />
                        </div>
                        <span className="text-base font-semibold text-purple-800">{facility}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Apply Filters Button */}
              <div className="flex-shrink-0 border-t border-purple-200 p-6">
                <button
                  onClick={() => setShowFilters(false)}
                  className="w-full bg-purple-600 text-white py-4 px-6 rounded-xl font-bold text-lg hover:bg-purple-700 transition-all duration-200"
                >
                  Show {locationResults.length} Locations
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Location Results */}
      <div className="flex-1 overflow-auto bg-purple-50">
        <div className="p-4">
          {loading ? (
            <div className="text-center py-16">
              <div className="w-16 h-16 bg-purple-200 rounded-full flex items-center justify-center mx-auto mb-4">
                <HiHome className="w-8 h-8 text-purple-400 animate-pulse" />
              </div>
              <h3 className="text-lg font-bold text-purple-900 mb-2">Loading locations...</h3>
            </div>
          ) : locationResults.length === 0 ? (
            <div className="text-center py-16">
              <div className="w-16 h-16 bg-purple-200 rounded-full flex items-center justify-center mx-auto mb-4">
                <HiHome className="w-8 h-8 text-purple-400" />
              </div>
              <h3 className="text-lg font-bold text-purple-900 mb-2">No locations found</h3>
              <p className="text-purple-600 mb-6 text-sm">
                No property locations match your search and filters
              </p>
              <div className="space-y-2 text-sm text-purple-500 max-w-md mx-auto">
                <p>• Try searching for areas like "Bukit Panjang", "Tampines", or "Marine Parade"</p>
                <p>• Adjust your budget range</p>
                <p>• Try different amenity filters</p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {locationResults.map(location => (
                <div 
                  key={location.id} 
                  className="bg-white rounded-xl p-4 border border-purple-200 hover:border-purple-300 hover:shadow-md transition-all duration-200 cursor-pointer"
                  onClick={() => onViewDetails(location)}
                >
                  <div className="text-center">
                    <span className="text-purple-900 font-semibold text-lg">
                      {location.street}
                    </span>
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