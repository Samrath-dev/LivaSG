import { useState } from 'react';
import { HiChevronLeft, HiSearch, HiChartBar, HiPlus } from 'react-icons/hi';
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
  // dynamic slots: start with two slots (may be null if not selected)
  const [selectedLocations, setSelectedLocations] = useState<(LocationResult | null)[]>([null, null]);
  const [searchQueries, setSearchQueries] = useState<string[]>(['', '']);
  const [searchResults, setSearchResults] = useState<LocationResult[][]>([[], []]);
  const [loading, setLoading] = useState<boolean[]>([false, false]);
  const [compareOpen, setCompareOpen] = useState(false);

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
    },
    {
      id: 4,
      street: "TEST1",
      area: "Bishan",
      district: "D21",
      priceRange: [100000, 900000],
      avgPrice: 1200,
      facilities: ['Near MRT', 'Good Schools', 'Shopping Malls', 'Sports Facilities'],
      description: "Family-friendly neighborhood with great facilities.",
      growth: 18.4,
      amenities: ["Tampines Mall", "Our Tampines Hub", "Tampines MRT"],
      transitScore: 90,
      schoolScore: 60,
      amenitiesScore: 43
    },
    {
      id: 5,
      street: "TEST2",
      area: "Changi",
      district: "D22",
      priceRange: [300000, 1700000],
      avgPrice: 620,
      facilities: ['Near MRT', 'Good Schools', 'Shopping Malls', 'Sports Facilities'],
      description: "Family-friendly neighborhood with great facilities.",
      growth: 2.3,
      amenities: ["Tampines Mall", "Our Tampines Hub", "Tampines MRT"],
      transitScore: 95,
      schoolScore: 75,
      amenitiesScore: 65
    },
    {
      id: 6,
      street: "TEST3",
      area: "Atlantis",
      district: "D23",
      priceRange: [800000, 900000],
      avgPrice: 1500,
      facilities: ['Near MRT', 'Good Schools', 'Shopping Malls', 'Sports Facilities'],
      description: "Family-friendly neighborhood with great facilities.",
      growth: 35.6,
      amenities: ["Tampines Mall", "Our Tampines Hub", "Tampines MRT"],
      transitScore: 100,
      schoolScore: 70,
      amenitiesScore: 75
    }
  ];

  // Suggested locations (top 3 by growth rate)
  const suggestedLocations = mockLocations
    .slice()
    .sort((a, b) => b.growth - a.growth)
    .slice(0, 3);

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${(price / 1000).toFixed(0)}K`;
  };

  // Helpers to update per-slot arrays
  const setSlotLocation = (index: number, loc: LocationResult | null) => {
    setSelectedLocations(prev => {
      const copy = [...prev];
      copy[index] = loc;
      return copy;
    });
    // clear the search query/results for that slot
    setSearchQueries(prev => {
      const q = [...prev];
      q[index] = '';
      return q;
    });
    setSearchResults(prev => {
      const r = [...prev];
      r[index] = [];
      return r;
    });
    setLoading(prev => {
      const l = [...prev];
      l[index] = false;
      return l;
    });
  };

  const addSlot = () => {
    setSelectedLocations(prev => (prev.length < 5 ? [...prev, null] : prev));
    setSearchQueries(prev => (prev.length < 5 ? [...prev, ''] : prev));
    setSearchResults(prev => (prev.length < 5 ? [...prev, []] : prev));
    setLoading(prev => (prev.length < 5 ? [...prev, false] : prev));
  };

  const searchLocations = async (index: number, query: string) => {
    setLoading(prev => {
      const copy = [...prev];
      copy[index] = true;
      return copy;
    });
    try {
      await new Promise(resolve => setTimeout(resolve, 250));
      const filtered = mockLocations.filter(loc =>
        loc.street.toLowerCase().includes(query.toLowerCase()) ||
        loc.area.toLowerCase().includes(query.toLowerCase()) ||
        loc.district.toLowerCase().includes(query.toLowerCase())
      );
      setSearchResults(prev => {
        const copy = [...prev];
        copy[index] = filtered;
        return copy;
      });
    } catch {
      setSearchResults(prev => {
        const copy = [...prev];
        copy[index] = [];
        return copy;
      });
    } finally {
      setLoading(prev => {
        const copy = [...prev];
        copy[index] = false;
        return copy;
      });
    }
  };

  const renderSearchBox = (index: number) => {
    const query = searchQueries[index] ?? '';
    const results = searchResults[index] ?? [];
    const isLoading = loading[index] ?? false;
    const currentLocation = selectedLocations[index] ?? null;

    // prevent selecting same location twice
    const otherSelectedIds = selectedLocations
      .map((s, i) => (i === index ? null : s?.id ?? null))
      .filter(Boolean) as number[];

    if (currentLocation) {
      return (
        <div key={index} className="flex-1 bg-white rounded-2xl p-6 border-2 border-purple-200 transition-all duration-300">
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
            onClick={() => setSlotLocation(index, null)}
            className="w-full mt-4 bg-red-100 text-red-700 py-2 rounded-xl font-semibold hover:bg-red-200 transition-colors"
          >
            Remove
          </button>
        </div>
      );
    }

    return (
      <div key={index} className="flex-1 bg-purple-50 rounded-2xl p-6 border-2 border-purple-300 border-dashed transition-all duration-300">
        <div className="relative mb-4">
          <HiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              const v = e.target.value;
              setSearchQueries(prev => {
                const copy = [...prev];
                copy[index] = v;
                return copy;
              });
              if (v.length > 0) searchLocations(index, v);
              else setSearchResults(prev => {
                const copy = [...prev];
                copy[index] = [];
                return copy;
              });
            }}
            placeholder={`Search for location ${index + 1}...`}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        <div className="max-h-64 overflow-auto">
          {isLoading ? (
            <div className="text-center py-4">
              <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-gray-600 text-sm mt-2">Searching...</p>
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-2">
              {results.map(location => {
                const disabled = otherSelectedIds.includes(location.id);
                return (
                  <div
                    key={location.id}
                    onClick={() => {
                      if (disabled) return;
                      setSlotLocation(index, location);
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
                      <div className="mt-2 text-xs text-center text-gray-500">Already selected in another slot</div>
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
                const disabled = otherSelectedIds.includes(location.id);
                return (
                  <div
                    key={location.id}
                    onClick={() => { if (!disabled) setSlotLocation(index, location); }}
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

  const nonNullSelected = selectedLocations.filter((l): l is LocationResult => l !== null);
  const canCompare = nonNullSelected.length >= 2;

  return (
    <div className="h-full flex flex-col bg-purple-50">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-purple-200 bg-white p-4">
        <div className="flex items-center justify-between w-full mb-3">
          <button onClick={onBack} className="text-purple-700 hover:text-purple-900 transition-colors">
            <HiChevronLeft className="w-6 h-6" />
          </button>

          <div className="flex items-center text-purple-700">
            <HiChartBar className="w-5 h-5 mr-2" />
            <h1 className="text-lg font-bold">Compare Locations</h1>
          </div>

          <div className="w-6" />
        </div>

        <p className="text-purple-600 text-sm text-center">
          Select two or more locations to compare their features and amenities
        </p>
      </div>

      {/* Comparison Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="flex flex-col lg:flex-row gap-6 max-w-6xl mx-auto">
          {selectedLocations.map((_, i) => renderSearchBox(i))}
        </div>

        {/* Controls: Compare button always visible; + button to add slots */}
        <div className="mt-8 flex items-center justify-center gap-4">
          <button
            onClick={() => setCompareOpen(true)}
            disabled={!canCompare}
            className={
              `px-6 py-3 rounded-xl font-semibold text-lg transition-colors ` +
              (!canCompare
                ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700')
            }
          >
            Compare Locations
          </button>

          <button
            onClick={addSlot}
            disabled={selectedLocations.length >= 5}
            title={selectedLocations.length >= 5 ? 'Maximum 5 locations' : 'Add another location'}
            className={
              `flex items-center gap-2 px-4 py-2 rounded-xl border transition ` +
              (selectedLocations.length >= 5
                ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                : 'bg-white text-purple-700 border-purple-200 hover:bg-purple-50')
            }
          >
            <HiPlus className="w-5 h-5" />
            <span className="font-medium">Add</span>
          </button>
        </div>
      </div>

      {/* Compare modal */}
      {compareOpen && (
        <CompareLocations
          locations={nonNullSelected.length ? nonNullSelected : mockLocations.slice(0, 5)}
          onClose={() => setCompareOpen(false)}
        />
      )}
    </div>
  );
};

export default ComparisonView;