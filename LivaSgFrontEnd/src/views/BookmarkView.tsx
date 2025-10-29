import { useState, useEffect } from 'react';
import { HiChevronLeft, HiSearch, HiBookmark, HiX, HiFilter } from 'react-icons/hi';
import { FaSubway, FaSchool, FaShoppingBag, FaTree, FaUtensils, FaHospital, FaDumbbell } from 'react-icons/fa';
import DetailsView from './DetailsView';
import SpecificView from './SpecificView';

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
}

const BookmarkView = ({ onBack }: BookmarkViewProps) => {
  const [locations, setLocations] = useState<LocationData[]>([]);
  const [savedLocations, setSavedLocations] = useState<number[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    facilities: [],
  });
  const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(null);
  const [showSpecificView, setShowSpecificView] = useState(false);
  const [selectedAreaData, setSelectedAreaData] = useState<{
    areaName: string;
    coordinates: [number, number][];
  } | null>(null);
  const [showRemoveConfirmation, setShowRemoveConfirmation] = useState<number | null>(null);

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
    
    // Load saved locations from localStorage or initialize with some saved locations
    const initialSavedLocations = [1, 2]; // Default saved locations
    setSavedLocations(initialSavedLocations);
  }, []);

  // Mock coordinates for different areas - you can replace with actual coordinates
  const getAreaCoordinates = (areaName: string): [number, number][] => {
    const coordinatesMap: { [key: string]: [number, number][] } = {
      "Marine Parade": [
        [1.3025, 103.9028],
        [1.3035, 103.9128],
        [1.3125, 103.9128],
        [1.3125, 103.9028]
      ],
      "Orchard": [
        [1.3045, 103.8328],
        [1.3045, 103.8428],
        [1.3145, 103.8428],
        [1.3145, 103.8328]
      ],
      "Tampines": [
        [1.3521, 103.9452],
        [1.3521, 103.9552],
        [1.3621, 103.9552],
        [1.3621, 103.9452]
      ]
    };
    
    return coordinatesMap[areaName] || [
      [1.3521, 103.8198],
      [1.3521, 103.8298],
      [1.3621, 103.8298],
      [1.3621, 103.8198]
    ];
  };

  // Handle location click - route to SpecificView
  const handleLocationClick = (location: LocationData) => {
    const coordinates = getAreaCoordinates(location.area);
    setSelectedAreaData({
      areaName: location.area,
      coordinates: coordinates
    });
    setShowSpecificView(true);
  };

  // Handle back from SpecificView
  const handleBackFromSpecificView = () => {
    setShowSpecificView(false);
    setSelectedAreaData(null);
  };

  // Handle rating click in SpecificView
  const handleRatingClick = (areaName: string, coordinates: [number, number][]) => {
    console.log('Rating clicked for:', areaName);
    // This will be handled within SpecificView
  };

  // Handle details click in SpecificView
  const handleDetailsClick = (areaName: string, coordinates: [number, number][]) => {
    console.log('Details clicked for:', areaName);
    // This will be handled within SpecificView
  };

  // Show confirmation dialog before removing
  const handleRemoveClick = (locationId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    setShowRemoveConfirmation(locationId);
  };

  // Confirm removal
  const confirmRemoveLocation = (locationId: number) => {
    setSavedLocations(prev => prev.filter(id => id !== locationId));
    setShowRemoveConfirmation(null);
  };

  // Cancel removal
  const cancelRemoveLocation = () => {
    setShowRemoveConfirmation(null);
  };

  // Check if a location is saved
  const isLocationSaved = (locationId: number) => {
    return savedLocations.includes(locationId);
  };

  const facilitiesList = [
    { key: 'mrt', label: 'Near MRT', icon: <FaSubway />, count: 15 },
    { key: 'schools', label: 'Good Schools', icon: <FaSchool />, count: 12 },
    { key: 'malls', label: 'Shopping Malls', icon: <FaShoppingBag />, count: 8 },
    { key: 'parks', label: 'Parks', icon: <FaTree />, count: 10 },
    { key: 'hawker', label: 'Hawker Centres', icon: <FaUtensils />, count: 20 },
    { key: 'healthcare', label: 'Healthcare', icon: <FaHospital />, count: 6 },
    { key: 'sports', label: 'Sports Facilities', icon: <FaDumbbell />, count: 7 }
  ];
  
  const handleFacilityToggle = (facility: string) => {
    setFilters((prevFilters) => {
      const facilities = prevFilters.facilities.includes(facility)
        ? prevFilters.facilities.filter((f) => f !== facility)
        : [...prevFilters.facilities, facility];
      return { ...prevFilters, facilities };
    });
  };

  const clearFilters = () => {
    setFilters({
      facilities: [],
    });
  };

  // Only show saved locations that match filters
  const filteredLocations = locations.filter((loc) => {
    // Only show saved locations
    if (!savedLocations.includes(loc.id)) {
      return false;
    }

    // Search filters
    const matchesSearch =
      loc.street.toLowerCase().includes(searchTerm.toLowerCase()) ||
      loc.area.toLowerCase().includes(searchTerm.toLowerCase()) ||
      loc.district.toLowerCase().includes(searchTerm.toLowerCase());

    // Facilities filter
    const matchesFacilities =
      filters.facilities.length === 0 ||
      filters.facilities.every((f) => loc.facilities.includes(f));

    return matchesSearch && matchesFacilities;
  });

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
  if (showSpecificView && selectedAreaData) {
    return (
      <SpecificView
        areaName={selectedAreaData.areaName}
        coordinates={selectedAreaData.coordinates}
        onBack={handleBackFromSpecificView}
        onRatingClick={handleRatingClick}
        onDetailsClick={handleDetailsClick}
      />
    );
  }

  // Render DetailsView if a location is selected (keeping this for backward compatibility)
  if (selectedLocation) {
    return (
      <DetailsView
        location={selectedLocation}
        onBack={() => setSelectedLocation(null)}
      />
    );
  }

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        <div className="flex items-center justify-between w-full mb-3">
          <button
            onClick={onBack}
            className="text-purple-700 hover:text-purple-900 transition-colors"
          >
            <HiChevronLeft className="w-6 h-6" />
          </button>
          
          <div className="absolute left-1/2 transform -translate-x-1/2 flex items-center text-purple-700">
            <HiBookmark className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Saved Locations</h1>
          </div>
          
          <div className="w-6"></div>
        </div>
        
        <p className="text-purple-600 text-sm text-center">
          {savedLocations.length} saved location{savedLocations.length !== 1 ? 's' : ''}
        </p>
      </div>   

      {/* Search and Filter button */}
      <div className="flex-shrink-0 p-4 bg-purple-50">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <HiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-purple-400" />
            <input
              type="text"
              placeholder="Search saved locations..."
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
            {filters.facilities.length > 0 && (
              <span className="ml-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                {filters.facilities.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Filter Overlay */}
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
                <h3 className="text-xl font-bold">Saved Locations Filters</h3>
                <p className="text-purple-700 text-sm mt-1">Refine your saved locations</p>
              </div>
              <button
                onClick={() => setShowFilters(false)}
                className="p-2 hover:bg-purple-300 rounded-xl transition-colors text-purple-700 hover:text-purple-900"
              >
                <HiX className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6 max-h-96 overflow-y-auto">
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

      {/* Remove Confirmation Dialog */}
      {showRemoveConfirmation && (
        <div className="fixed inset-0 z-50 bg-gray-600 bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-sm mx-auto shadow-2xl border border-gray-300 p-6">
            <div className="text-center">
              <HiBookmark className="w-12 h-12 mx-auto mb-4 text-purple-500" />
              <h3 className="text-xl font-bold text-gray-900 mb-2">Remove from Saved?</h3>
              <p className="text-gray-600 mb-6">
                This location will be removed from your saved locations. You can save it again later if needed.
              </p>
              
              <div className="flex gap-3">
                <button
                  onClick={cancelRemoveLocation}
                  className="flex-1 px-4 py-3 text-purple-700 bg-white border border-purple-300 rounded-xl font-semibold hover:bg-purple-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => confirmRemoveLocation(showRemoveConfirmation)}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl font-semibold hover:from-purple-600 hover:to-purple-700 transition-all shadow-lg"
                >
                  Remove
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* List of saved locations - Simplified */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {savedLocations.length === 0 ? (
          <div className="text-center text-purple-600 py-8">
            <HiBookmark className="w-12 h-12 mx-auto mb-4 text-purple-400" />
            <p className="text-lg font-bold">You have no saved locations</p>
            <p className="text-sm">Start bookmarking your favorite locations to see them here!</p>
          </div>
        ) : filteredLocations.length === 0 ? (
          filters.facilities.length > 0 ? (
            <div className="text-center text-purple-600 py-8">
              <p className="text-lg font-bold">No saved locations match your filters</p>
              <p className="text-sm">Try adjusting your filters to find more locations.</p>
            </div>
          ) : searchTerm ? (
            <div className="text-center text-purple-600 py-8">
              <p className="text-lg font-bold">No saved locations match your search</p>
              <p className="text-sm">Try searching with different keywords.</p>
            </div>
          ) : (
            <div className="text-center text-purple-600 py-8">
              <p className="text-lg font-bold">No locations found</p>
            </div>
          )
        ) : (
          filteredLocations.map((loc) => (
            <div
              key={loc.id}
              onClick={() => handleLocationClick(loc)}
              className="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer border border-purple-100"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h2 className="font-bold text-purple-800 text-lg">{loc.street}</h2>
                  <p className="text-sm text-purple-700">{loc.area} • {loc.district}</p>
                  <p className="text-sm text-purple-600 mt-1">{loc.description}</p>
                </div>
                
                {/* Remove Button */}
                <button
                  onClick={(e) => handleRemoveClick(loc.id, e)}
                  className="ml-4 p-2 rounded-full transition-all duration-200 bg-purple-100 text-purple-600 hover:bg-purple-200 hover:text-purple-700"
                  title="Remove from saved locations"
                >
                  <HiBookmark className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default BookmarkView;