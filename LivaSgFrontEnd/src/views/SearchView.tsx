import { useState, useEffect } from 'react';
import { HiFilter, HiChevronLeft, HiX, HiHome, HiSearch, HiCog } from 'react-icons/hi';
import { FaSubway, FaSchool, FaShoppingBag, FaTree, FaUtensils, FaHospital, FaDumbbell } from 'react-icons/fa';
import SpecificView from './SpecificView'; // Import SpecificView

interface SearchViewProps {
  searchQuery: string;
  onBack: () => void;
  onViewDetails: (location: any) => void;
  onSearchQueryChange: (query: string) => void;
  onSettingsClick: () => void;
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
  latitude?: number;
  longitude?: number;
  lat?: number;
  lng?: number;
  coordinates?: [number, number][]; // Add coordinates for SpecificView
}

const SearchView = ({ searchQuery, onBack, onViewDetails, onSearchQueryChange, onSettingsClick }: SearchViewProps) => {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    facilities: [],
    priceRange: [500000, 3000000]
  });
  const [locationResults, setLocationResults] = useState<LocationResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<LocationResult | null>(null); // New state for SpecificView

  const facilitiesList = [
    { key: 'mrt', label: 'Near MRT', icon: <FaSubway />, count: 15 },
    { key: 'schools', label: 'Good Schools', icon: <FaSchool />, count: 12 },
    { key: 'malls', label: 'Shopping Malls', icon: <FaShoppingBag />, count: 8 },
    { key: 'parks', label: 'Parks', icon: <FaTree />, count: 10 },
    { key: 'hawker', label: 'Hawker Centres', icon: <FaUtensils />, count: 20 },
    { key: 'healthcare', label: 'Healthcare', icon: <FaHospital />, count: 6 },
    { key: 'sports', label: 'Sports Facilities', icon: <FaDumbbell />, count: 7 }
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
      // Map backend fields to frontend fields and add mock coordinates
      const mappedData = data.map((loc: any) => ({
        ...loc,
        priceRange: loc.price_range,
        avgPrice: loc.avg_price,
        // Add mock coordinates for the area (you can replace this with actual coordinates from your backend)
        coordinates: generateMockCoordinates(loc.area)
      }));
      setLocationResults(mappedData);
    } catch (error) {
      setLocationResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Generate mock coordinates for an area (replace with actual data from your backend)
  const generateMockCoordinates = (areaName: string): [number, number][] => {
    // Simple hash function to generate consistent coordinates based on area name
    const hash = areaName.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    
    const baseLat = 1.3521 + (hash % 100) / 1000;
    const baseLng = 103.8198 + (hash % 100) / 1000;
    
    // Return a simple polygon (square) around the base coordinates
    return [
      [baseLat - 0.01, baseLng - 0.01],
      [baseLat - 0.01, baseLng + 0.01],
      [baseLat + 0.01, baseLng + 0.01],
      [baseLat + 0.01, baseLng - 0.01],
      [baseLat - 0.01, baseLng - 0.01] // Close the polygon
    ];
  };

  useEffect(() => {
    // Debounce the API call - wait 500ms after user stops typing
    const debounceTimer = setTimeout(() => {
      fetchFilteredLocations();
    }, 500);

    // Cleanup: cancel the timer if searchQuery or filters change again
    return () => clearTimeout(debounceTimer);
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

  // Handle location click - open SpecificView
  const handleLocationClick = (location: LocationResult) => {
    setSelectedLocation(location);
  };

  // Handle back from SpecificView
  const handleBackFromSpecific = () => {
    setSelectedLocation(null);
  };

  // Handle rating click in SpecificView
  const handleRatingClick = (areaName: string, coordinates: [number, number][]) => {
    console.log('Opening rating for:', areaName);
    // You can add your rating logic here
  };

  // Handle details click in SpecificView
  const handleDetailsClick = (areaName: string, coordinates: [number, number][]) => {
    console.log('Opening details for:', areaName);
    // You can add your details logic here
  };

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  const FilterItem = ({ icon, label, checked, onChange, count }: any) => (
    <label className="flex items-center justify-between w-full p-4 rounded-xl hover:bg-purple-50 transition-colors cursor-pointer border border-purple-200 bg-white">
      <div className="flex items-center gap-4">
        <span
          className={`flex-shrink-0 p-3 rounded-xl border-2 ${
            checked ? 'border-purple-500 text-purple-600 bg-purple-50' : 'border-purple-300 text-purple-400 bg-white'
          }`}
          style={{
            width: '52px',
            height: '52px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
          {icon}
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

  // Render SpecificView if a location is selected
  if (selectedLocation && selectedLocation.coordinates) {
    return (
      <SpecificView
        areaName={selectedLocation.area}
        coordinates={selectedLocation.coordinates}
        onBack={handleBackFromSpecific}
        onRatingClick={handleRatingClick}
        onDetailsClick={handleDetailsClick}
      />
    );
  }

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
            onClick={onSettingsClick}
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
        <div className="fixed inset-0 z-50 bg-gray-600 bg-opacity-50 flex items-start justify-center p-4 overflow-auto"
          role="dialog"
          aria-modal="true"
        >
          <div
            className="relative bg-white rounded-2xl w-full max-w-md mx-auto shadow-2xl mt-20 mb-8 border border-gray-300"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Pale Purple Header */}
            <div className="flex items-center justify-between p-6 border-b border-purple-200 bg-gradient-to-r from-purple-100 to-purple-200 text-purple-900 rounded-t-2xl">
              <div>
                <h3 className="text-xl font-bold">Search Filters</h3>
                <p className="text-purple-700 text-sm mt-1">Refine your location search</p>
              </div>
              <button
                onClick={() => setShowFilters(false)}
                className="p-2 hover:bg-purple-300 rounded-xl transition-colors text-purple-700 hover:text-purple-900"
              >
                <HiX className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6 max-h-96 overflow-y-auto">
              {/* Price Range Filter */}
              <div>
                <h3 className="font-bold text-lg mb-4 text-gray-900">Budget Range</h3>
                <div className="space-y-4">
                  <div className="space-y-3">
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
                <h3 className="font-bold text-lg mb-4 text-gray-900">Preferred Amenities</h3>
                <div className="space-y-3">
                  {facilitiesList.map(facility => (
                    <FilterItem
                      key={facility.key}
                      icon={facility.icon}
                      label={facility.label}
                      checked={filters.facilities.includes(facility.label)}
                      onChange={() => handleFacilityToggle(facility.label)}
                      count={facility.count}
                    />
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 p-6 border-t border-purple-200 bg-purple-50 rounded-b-2xl">
              <button
                onClick={clearFilters}
                className="flex-1 px-4 py-3 text-purple-700 bg-white border border-purple-300 rounded-xl font-semibold hover:bg-purple-100 transition-colors"
              >
                Reset All
              </button>
              <button
                onClick={() => setShowFilters(false)}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl font-semibold hover:from-purple-600 hover:to-purple-700 transition-all shadow-lg"
              >
                Apply Filters
              </button>
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
                  onClick={() => handleLocationClick(location)}
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