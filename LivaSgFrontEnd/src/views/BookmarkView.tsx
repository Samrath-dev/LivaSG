import { useState, useEffect } from 'react';
import { HiChevronLeft, HiSearch, HiBookmark, HiX, HiFilter } from 'react-icons/hi';
import DetailsView from './DetailsView';

interface BookmarkViewProps {
  onBack: () => void;
}

interface LocationData {
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
  transitScore: number;
  schoolScore: number;
  amenitiesScore: number;
}

interface Filters {
  facilities: string[];
  priceRange: [number, number];
}


const BookmarkView = ({ onBack }: BookmarkViewProps) => {
  const [locations, setLocations] = useState<LocationData[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    facilities: [],
    priceRange: [500, 3000000],
  });
  const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(null);

  // Mock data for demonstration - replace with actual API calls
  useEffect(() => {
    const mockLocations: LocationData[] = [
      {
        id: 1,
        street: "Marine Parade Road",
        area: "Marine Parade",
        district: "D15",
        priceRange: [1200000, 2500000],
        avgPrice: 1500,
        facilities: ['Near MRT', 'Good Schools', 'Shopping Malls', 'Parks'],
        description: "Waterfront living with excellent amenities and schools.",
        growth: 12.5,
        amenities: ["East Coast Park", "Parkway Parade", "Marine Parade MRT"],
        transitScore: 85,
        schoolScore: 90,
        amenitiesScore: 95
      },
      {
        id: 2,
        street: "Orchard Road",
        area: "Orchard",
        district: "D9",
        priceRange: [2000000, 5000000],
        avgPrice: 2800,
        facilities: ['Near MRT', 'Shopping Malls', 'Healthcare', 'Parks'],
        description: "Prime district with luxury shopping and central location.",
        growth: 8.2,
        amenities: ["ION Orchard", "Takashimaya", "Orchard MRT"],
        transitScore: 95,
        schoolScore: 75,
        amenitiesScore: 98
      },
      {
        id: 3,
        street: "Tampines Street 42",
        area: "Tampines",
        district: "D18",
        priceRange: [600000, 1200000],
        avgPrice: 850,
        facilities: ['Near MRT', 'Good Schools', 'Shopping Malls', 'Sports Facilities'],
        description: "Family-friendly neighborhood with great facilities.",
        growth: 15.3,
        amenities: ["Tampines Mall", "Our Tampines Hub", "Tampines MRT"],
        transitScore: 80,
        schoolScore: 85,
        amenitiesScore: 88
      }
    ];
    setLocations(mockLocations);
  }, []);

  const facilitiesList = [
    'Near MRT',
    'Good Schools',
    'Shopping Malls',
    'Parks',
    'Hawker Centres',
    'Healthcare',
    'Sports Facilities'
  ];
  
  const handleFacilityToggle = (facility: string) => {
    setFilters((prevFilters) => {
      const facilities = prevFilters.facilities.includes(facility)
        ? prevFilters.facilities.filter((f) => f !== facility)
        : [...prevFilters.facilities, facility];
      return { ...prevFilters, facilities };
    });
  };

  const handlePriceChange = (min: number, max: number) => {
    setFilters((prevFilters) => ({
      ...prevFilters,
      priceRange: [min, max],
    }));
  };

  const clearFilters = () => {
    setFilters({
      facilities: [],
      priceRange: [500, 3000000],
    });
  };

  const filteredLocations = locations.filter((loc) => {
    // Search filters
    const matchesSearch =
      loc.street.toLowerCase().includes(searchTerm.toLowerCase()) ||
      loc.area.toLowerCase().includes(searchTerm.toLowerCase()) ||
      loc.district.toLowerCase().includes(searchTerm.toLowerCase());

    // Facilities filter
    const matchesFacilities =
      filters.facilities.length === 0 ||
      filters.facilities.every((f) => loc.facilities.includes(f));

    // Price filter
    const matchesPrice =
      loc.avgPrice >= filters.priceRange[0] && loc.avgPrice <= filters.priceRange[1];

    return matchesSearch && matchesFacilities && matchesPrice;
  });

       // Render DetailsView if a location is selected
    if (selectedLocation) {
      return (
        <DetailsView
          location={selectedLocation}
          onBack={() => setSelectedLocation(null)} // Go back to the bookmark list
        />
      );
    }

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
            <div className="flex items-center justify-between w-full mb-3">
              {/* Simple back arrow button - no background, no circle */}
              <button
                onClick={onBack}
                className="text-purple-700 hover:text-purple-900 transition-colors"
              >
                <HiChevronLeft className="w-6 h-6" />
              </button>
              
              <div className="absolute left-1/2 transform -translate-x-1/2 flex items-center text-purple-700"> {/* center the header text */}
                <HiBookmark className="w-5 h-5 mr-2" />
                <h1 className="text-lg font-bold">Saved</h1>
              </div>
              
              <div className="w-6"></div> {/* Spacer for balance */}
            </div>
            
            <p className="text-purple-600 text-sm text-center">
              View saved locations
            </p>
          </div>   

          {/* Search and Filter button */}
          <div className="flex-shrink-0 p-4 bg-purple-50">
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <HiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-purple-400" />
                  <input
                    type="text"
                    placeholder="Search locations..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 rounded-lg border border-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  {searchTerm && (
                    <button
                      onClick={() => setSearchTerm('')}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-purple-400 hover:text-purple-600">
                      <HiX className="w-4 h-4" />
                    </button>
                  )}
              </div>
              
              {/* Filter button */}
              <div className="flex justify-between items-center">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={'h-10 px-3 bg-purple-700 text-white rounded-lg flex items-center gap-1 hover:bg-purple-800'}
                >
                  <HiFilter className="w-5 h-5" />
                  {(filters.facilities.length > 0 || filters.priceRange[0] > 500000 || filters.priceRange[1] < 3000000) && (
                    <span className="ml-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                      {filters.facilities.length + (filters.priceRange[0] > 500000 ? 1 : 0) + (filters.priceRange[1] < 3000000 ? 1 : 0)}
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Filter Menu */}
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
                      Show {filteredLocations.length} Locations
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
      
      {/* List of locations */}
          <div className="flex-1 overflow-auto p-4 space-y-4">
            {locations.length === 0 ? (
              // No saved locations
              <div className="text-center text-purple-600">
                <p className="text-lg font-bold">You have no saved locations</p>
                <p className="text-sm">Start bookmarking your favorite locations to see them here!</p>
              </div>
            ) : filteredLocations.length === 0 ? (
              // No locations matching filters
              filters.facilities.length > 0 || filters.priceRange[0] > 500000 || filters.priceRange[1] < 3000000 ? (
                <div className="text-center text-purple-600">
                  <p className="text-lg font-bold">No locations match your filters</p>
                  <p className="text-sm">Try adjusting your filters to find more locations.</p>
                </div>
              ) : searchTerm ? (
                // No locations matching the keyword search
                <div className="text-center text-purple-600">
                  <p className="text-lg font-bold">No locations match your search</p>
                  <p className="text-sm">Try searching with different keywords.</p>
                </div>
              ) : (
                // Default fallback (Edgecase)
                <div className="text-center text-purple-600">
                  <p className="text-lg font-bold">No locations found</p>
                </div>
              )
            ) : (
              // Display filtered locations
              filteredLocations.map((loc) => (
                <div
                  key={loc.id}
                  onClick={() => setSelectedLocation(loc)}
                  className="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
                >
                  <h2 className="font-bold text-purple-800">{loc.street}</h2>
                  <p className="text-sm text-purple-700">{loc.area} • {loc.district}</p>
                  <p className="text-sm text-purple-600 mt-1">{loc.description}</p>
                </div>
              ))
            )}
          </div>
      
        </div>
      );
};

export default BookmarkView;