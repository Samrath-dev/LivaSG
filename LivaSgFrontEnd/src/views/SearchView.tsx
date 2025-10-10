import { useState, useEffect } from 'react';
import { HiFilter, HiChevronLeft, HiX, HiHome } from 'react-icons/hi';

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

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Compact Header */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        <div className="flex items-center justify-between w-full mb-3">
          {/* Compact Back button */}
          <button
            onClick={onBack}
            className="flex items-center text-purple-700 hover:text-purple-900 transition-colors text-sm"
          >
            <HiChevronLeft className="w-5 h-5 mr-1" />
            <span className="font-medium">Back to Map</span>
          </button>
          
          {/* Compact Filters button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-3 py-2 rounded-lg border transition-all duration-200 text-sm ${
              showFilters 
                ? 'bg-purple-600 text-white border-purple-600' 
                : 'bg-white text-purple-700 border-purple-300 hover:border-purple-500 hover:bg-purple-50'
            }`}
          >
            <HiFilter className="w-4 h-4 mr-1" />
            <span className="font-semibold">Filters</span>
            {(filters.facilities.length > 0 || filters.priceRange[0] > 500000 || filters.priceRange[1] < 3000000) && (
              <span className="ml-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
                {filters.facilities.length + (filters.priceRange[0] > 500000 ? 1 : 0) + (filters.priceRange[1] < 3000000 ? 1 : 0)}
              </span>
            )}
          </button>
        </div>
        
        {/* Compact Search Info */}
        <div>
          <p className="text-purple-700 font-semibold text-lg">
            Searching in <span className="text-purple-600">"{searchQuery}"</span>
          </p>
          <div className="flex items-center mt-1">
            <HiHome className="w-3 h-3 text-purple-400 mr-1" />
            <span className="text-xs text-purple-600">
              {locationResults.length} {locationResults.length === 1 ? 'location' : 'locations'} found
            </span>
          </div>
        </div>
      </div>

      {/* Full-page Filters Overlay */}
      {showFilters && (
        <div className="fixed inset-0 bg-white z-50 flex flex-col">
          {/* Filters Header */}
          <div className="flex-shrink-0 border-b border-purple-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-purple-900">Location Filters</h2>
                <p className="text-purple-600 mt-1">Find your perfect neighborhood</p>
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
                  className="p-2 hover:bg-purple-100 rounded-xl transition-colors"
                >
                  <HiX className="w-6 h-6 text-purple-600" />
                </button>
              </div>
            </div>
          </div>

          {/* Filters Content */}
          <div className="flex-1 overflow-auto p-6">
            {/* Price Range Filter */}
            <div className="mb-12">
              <h3 className="font-bold text-lg mb-6 text-purple-900">Budget Range</h3>
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
                <div className="flex justify-between items-center bg-purple-50 rounded-2xl p-4">
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
              <h3 className="font-bold text-lg mb-6 text-purple-900">Preferred Amenities</h3>
              <div className="grid grid-cols-1 gap-3">
                {facilitiesList.map(facility => (
                  <label key={facility} className="flex items-center space-x-4 cursor-pointer p-4 rounded-xl border-2 border-purple-200 hover:border-purple-400 hover:bg-purple-50 transition-all duration-200">
                    <input
                      type="checkbox"
                      checked={filters.facilities.includes(facility)}
                      onChange={() => handleFacilityToggle(facility)}
                      className="w-5 h-5 rounded border-2 border-purple-300 text-purple-600 focus:ring-purple-500 focus:ring-2"
                    />
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
              className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white py-4 px-6 rounded-xl font-bold text-lg hover:from-purple-700 hover:to-purple-800 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              Show {locationResults.length} Locations
            </button>
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
              <div className="space-y-2 text-xs text-purple-500">
                <p>• Try searching for areas like "Bukit Panjang", "Tampines", or "Marine Parade"</p>
                <p>• Adjust your budget range</p>
                <p>• Try different amenity filters</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {locationResults.map(location => (
                <div 
                  key={location.id} 
                  className="bg-purple-100 rounded-xl p-4 border border-purple-200 hover:bg-purple-200 transition-all duration-200 cursor-pointer shadow-sm hover:shadow-md"
                  onClick={() => onViewDetails(location)}
                >
                  <div className="text-center">
                    <span className="text-purple-800 font-semibold text-lg">
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