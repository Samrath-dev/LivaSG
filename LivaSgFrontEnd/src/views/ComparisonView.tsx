import { useState, useEffect } from 'react';
import { HiChevronLeft, HiSearch, HiChartBar } from 'react-icons/hi';
import CompareLocations from './CompareLocations';

interface ComparisonViewProps {
  onBack: () => void;
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
  transitScore: number;
  schoolScore: number;
  amenitiesScore: number;
}

const ComparisonView = ({ onBack }: ComparisonViewProps) => {
  const [location1, setLocation1] = useState<LocationResult | null>(null);
  const [location2, setLocation2] = useState<LocationResult | null>(null);
  const [searchQuery1, setSearchQuery1] = useState('');
  const [searchQuery2, setSearchQuery2] = useState('');
  const [searchResults1, setSearchResults1] = useState<LocationResult[]>([]);
  const [searchResults2, setSearchResults2] = useState<LocationResult[]>([]);
  const [loading1, setLoading1] = useState(false);
  const [loading2, setLoading2] = useState(false);
  const [compareLocations, setCompareLocations] = useState(false);

  // Mock data for demonstration - replace with actual API calls
  const mockLocations: LocationResult[] = [
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

  // Suggested locations (top 3 by growth rate)
  const suggestedLocations = mockLocations
    .sort((a, b) => b.growth - a.growth)
    .slice(0, 3);

  const searchLocations = async (query: string, setResults: React.Dispatch<React.SetStateAction<LocationResult[]>>, setLoading: React.Dispatch<React.SetStateAction<boolean>>) => {
    setLoading(true);
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 300));
      const filtered = mockLocations.filter(loc =>
        loc.street.toLowerCase().includes(query.toLowerCase()) ||
        loc.area.toLowerCase().includes(query.toLowerCase()) ||
        loc.district.toLowerCase().includes(query.toLowerCase())
      );
      setResults(filtered);
    } catch (error) {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (searchQuery1.length > 0) {
      searchLocations(searchQuery1, setSearchResults1, setLoading1);
    } else {
      setSearchResults1([]);
    }
  }, [searchQuery1]);

  useEffect(() => {
    if (searchQuery2.length > 0) {
      searchLocations(searchQuery2, setSearchResults2, setLoading2);
    } else {
      setSearchResults2([]);
    }
  }, [searchQuery2]);

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  const renderSearchBox = (index: number) => {
    const query = index === 0 ? searchQuery1 : searchQuery2;
    const setQuery = index === 0 ? setSearchQuery1 : setSearchQuery2;
    const results = index === 0 ? searchResults1 : searchResults2;
    const loading = index === 0 ? loading1 : loading2;
    const setLocation = index === 0 ? setLocation1 : setLocation2;
    const currentLocation = index === 0 ? location1 : location2;
    const alreadySelectedId = index === 0 ? (location2 ? location2.id : null) : (location1 ? location1.id : null);

    if (currentLocation) {
      return (
        <div className="flex-1 bg-white rounded-2xl p-6 border-2 border-purple-200 transition-all duration-300">
          <div className="text-center">
            <h3 className="text-xl font-bold text-purple-900 mb-2">{currentLocation.street}</h3>
            <p className="text-purple-700 mb-3">{currentLocation.area}, {currentLocation.district}</p>
            <div className="text-sm text-purple-600">
              {formatPrice(currentLocation.priceRange[0])} - {formatPrice(currentLocation.priceRange[1])}
            </div>
            <div className="text-sm text-green-600 font-semibold mt-1">
              +{currentLocation.growth}% Growth
            </div>
          </div>
          <button
            onClick={() => setLocation(null)}
            className="w-full mt-4 bg-red-100 text-red-700 py-2 rounded-xl font-semibold hover:bg-red-200 transition-colors"
          >
            Remove
          </button>
        </div>
      );
    }

    return (
      <div className="flex-1 bg-purple-50 rounded-2xl p-6 border-2 border-purple-300 border-dashed transition-all duration-300">
        {/* Search Bar */}
        <div className="relative mb-4">
          <HiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search for location ${index + 1}...`}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        {/* Search Results */}
        <div className="max-h-64 overflow-auto">
          {loading ? (
            <div className="text-center py-4">
              <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-gray-600 text-sm mt-2">Searching...</p>
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-2">
              {results.map(location => {
                const disabled = alreadySelectedId !== null && location.id === alreadySelectedId;
                return (
                  <div
                    key={location.id}
                    onClick={() => {
                      if (disabled) return;
                      setLocation(location);
                      setQuery('');
                    }}
                    className={
                      `p-3 rounded-lg border border-gray-200 transition-colors ` +
                      (disabled
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-60'
                        : 'bg-white hover:border-purple-300 hover:bg-purple-50 cursor-pointer')
                    }
                  >
                    <div className={`font-semibold ${disabled ? 'text-gray-600' : 'text-purple-900'}`}>{location.street}</div>
                    <div className={`text-sm ${disabled ? 'text-gray-500' : 'text-purple-700'}`}>{location.area}, {location.district}</div>
                    <div className="flex justify-between items-center mt-1">
                      <div className={`text-xs ${disabled ? 'text-gray-500' : 'text-purple-600'}`}>
                        {formatPrice(location.priceRange[0])} - {formatPrice(location.priceRange[1])}
                      </div>
                      <div className={`text-xs ${disabled ? 'text-gray-500' : 'text-green-600'} font-semibold`}>
                        +{location.growth}% ↗
                      </div>
                    </div>
                    {disabled && (
                      <div className="mt-2 text-xs text-center text-gray-500">Already selected in the other slot</div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : query.length > 0 ? (
            <div className="text-center py-4">
              <HiSearch className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600 text-sm">No locations found</p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-purple-700 font-medium text-sm">Suggested Locations:</p>
              {suggestedLocations.map(location => {
                const disabled = alreadySelectedId !== null && location.id === alreadySelectedId;
                return (
                  <div
                    key={location.id}
                    onClick={() => {
                      if (disabled) return;
                      setLocation(location);
                    }}
                    className={
                      `p-3 rounded-lg border border-gray-200 transition-colors ` +
                      (disabled
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-60'
                        : 'bg-white hover:border-purple-300 hover:bg-purple-50 cursor-pointer')
                    }
                  >
                    <div className={`font-semibold ${disabled ? 'text-gray-600' : 'text-purple-900'}`}>{location.street}</div>
                    <div className={`text-sm ${disabled ? 'text-gray-500' : 'text-purple-700'}`}>{location.area}, {location.district}</div>
                    <div className="flex justify-between items-center mt-1">
                      <div className={`text-xs ${disabled ? 'text-gray-500' : 'text-purple-600'}`}>
                        {formatPrice(location.priceRange[0])} - {formatPrice(location.priceRange[1])}
                      </div>
                      <div className={`text-xs ${disabled ? 'text-gray-500' : 'text-green-600'} font-semibold`}>
                        +{location.growth}% ↗
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    );
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
          
          <div className="flex items-center text-purple-700">
            <HiChartBar className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Compare Locations</h1>
          </div>
          
          <div className="w-6"></div> {/* Spacer for balance */}
        </div>
        
        <p className="text-purple-600 text-sm text-center">
          Select two locations to compare their features and amenities
        </p>
      </div>

      {/* Comparison Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="flex flex-col lg:flex-row gap-6 max-w-6xl mx-auto">
          {renderSearchBox(0)}
          
          {/* VS Separator */}
          {location1 && location2 && (
            <div className="flex items-center justify-center lg:flex-col lg:justify-center lg:py-8">
              <div className="bg-purple-600 text-white px-4 py-2 rounded-full font-bold text-sm">
                VS
              </div>
            </div>
          )}
          
          {renderSearchBox(1)}
        </div>

        {/* Compare Button */}
        {location1 && location2 && (
          <div className="mt-8 text-center">
            <button 
              onClick ={() => setCompareLocations(true)}
              disabled={location1.id === location2.id}
              className={
                `px-8 py-3 rounded-xl font-semibold text-lg transition-colors ` +
                (location1.id === location2.id
                  ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                  : 'bg-purple-600 text-white hover:bg-purple-700')
              }
            >
              Compare Locations
            </button>
          </div>
        )}
      </div>
      {/* delegate modal to CompareLocations component */}
      {compareLocations && location1 && location2 && (
        <CompareLocations
          location1={location1}
          location2={location2}
          onClose={() => setCompareLocations(false)}
        />
      )}
    </div>
  );
};

export default ComparisonView;