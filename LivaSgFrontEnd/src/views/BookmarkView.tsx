import { useState, useEffect } from 'react';
import { HiChevronLeft, HiSearch, HiBookmark, HiX, HiFilter } from 'react-icons/hi';

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
  const [filters, setFilters] = useState<Filters>({
    facilities: [],
    priceRange: [500, 3000000],
  });
  const [showFilter, setShowFilter] = useState(false);

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

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header - Centered */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        <div className="flex items-center justify-center w-full mb-3 relative">
          {/* Back button positioned absolutely on the left */}
          <button
            onClick={onBack}
            className="absolute left-0 text-purple-700 hover:text-purple-900 transition-colors"
          >
            <HiChevronLeft className="w-6 h-6" />
          </button>
          
          {/* Centered title and icon */}
          <div className="flex items-center text-purple-700">
            <HiBookmark className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Saved</h1>
          </div>
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
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-purple-400 hover:text-purple-600"
              >
                <HiX className="w-4 h-4" />
              </button>
            )}
          </div>
          
          {/* Filter button */}
          <button
            onClick={() => setShowFilter(!showFilter)}
            className="h-10 px-3 bg-purple-700 text-white rounded-lg flex items-center gap-1 hover:bg-purple-800"
          >
            <HiFilter className="w-5 h-5" />
          </button>
        </div>
      </div>
      
      {/* List of locations */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {locations.length === 0 ? (
          <p className="text-center text-purple-600">No saved locations</p>
        ) : (
          filteredLocations.map((loc) => (
            <div
              key={loc.id}
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