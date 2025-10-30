import { useState, useEffect } from 'react';
import { HiChevronLeft, HiSearch, HiChartBar, HiPlus, HiMinus } from 'react-icons/hi';
import AnalysisView from './AnalysisView';

const MAXSLOTS = 5;
const MINSLOTS = 2;

interface ComparisonViewProps {
  onBack: () => void;
}

interface LocationResult {
  id: number;
  street: string;
  area: string;
  district: string;
  facilities: string[];
  description: string;
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

  // Suggested locations
  const [suggestedLocations, setSuggestedLocations] = useState<LocationResult[]>([]);

  useEffect(() => {
    let cancelled = false;
    const fetchSuggestions = async () => {
      try {
        const res = await fetch('http://localhost:8000/search/filter', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            facilities: [],
            price_range: [0, 99999999],
            search_query: ''
          })
        });
        if (!res.ok) throw new Error('Failed to fetch suggestions');
        const json = await res.json();
        const mapped = (json || []).map((loc: any) => ({
          ...loc,
          transitScore: Number(loc.transit_score ?? loc.transitScore ?? 0),
          schoolScore: Number(loc.school_score ?? loc.schoolScore ?? 0),
          amenitiesScore: Number(loc.amenities_score ?? loc.amenitiesScore ?? 0),
        })) as LocationResult[];

        if (cancelled) return;
        setSuggestedLocations(mapped.slice(0, 3));
      } catch (err) {
        console.warn('fetchSuggestions error', err);
      }
    };
    fetchSuggestions();
    return () => { cancelled = true; };
  }, []);

  // Create a unique identifier for each location
  const getLocationKey = (location: LocationResult): string => {
    return `${location.area}-${location.street}`.toLowerCase();
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
    setSelectedLocations(prev => (prev.length < MAXSLOTS ? [...prev, null] : prev));
    setSearchQueries(prev => (prev.length < MAXSLOTS ? [...prev, ''] : prev));
    setSearchResults(prev => (prev.length < MAXSLOTS ? [...prev, []] : prev));
    setLoading(prev => (prev.length < MAXSLOTS ? [...prev, false] : prev));
  };

  const removeSlot = () => {
    setSelectedLocations(prev => (prev.length > MINSLOTS ? prev.slice(0, -1) : prev));
    setSearchQueries(prev => (prev.length > MINSLOTS ? prev.slice(0, -1) : prev));
    setSearchResults(prev => (prev.length > MINSLOTS ? prev.slice(0, -1) : prev));
    setLoading(prev => (prev.length > MINSLOTS ? prev.slice(0, -1) : prev));
  };

  const searchLocations = async (index: number, query: string) => {
    setLoading(prev => { const copy = [...prev]; copy[index] = true; return copy; });
    try {
      const response = await fetch('http://localhost:8000/search/filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          facilities: [],          // keep empty or expose filters if you add UI later
          price_range: [0, 99999999],
          search_query: query
        })
      });
      if (!response.ok) throw new Error('Failed to fetch locations');
      const json = await response.json();
      const mapped = (json || []).map((loc: any) => ({
        ...loc,
        transitScore: Number(loc.transit_score ?? loc.transitScore ?? 0),
        schoolScore: Number(loc.school_score ?? loc.schoolScore ?? 0),
        amenitiesScore: Number(loc.amenities_score ?? loc.amenitiesScore ?? 0),
      })) as LocationResult[];

      setSearchResults(prev => { const copy = [...prev]; copy[index] = mapped; return copy; });
    } catch (err) {
      console.warn('searchLocations error', err);
      setSearchResults(prev => { const copy = [...prev]; copy[index] = []; return copy; });
    } finally {
      setLoading(prev => { const copy = [...prev]; copy[index] = false; return copy; });
    }
  };

  const renderSearchBox = (index: number) => {
    const query = searchQueries[index] ?? '';
    const results = searchResults[index] ?? [];
    const isLoading = loading[index] ?? false;
    const currentLocation = selectedLocations[index] ?? null;

    // prevent selecting same location twice using unique location key
    const otherSelectedKeys = selectedLocations
      .map((s, i) => (i === index ? null : s ? getLocationKey(s) : null))
      .filter(Boolean) as string[];

    if (currentLocation) {
      return (
        <div key={index} className="flex-1 bg-white rounded-2xl p-6 border-2 border-purple-200 transition-all duration-300">
          <div className="text-center">
            <h3 className="text-xl font-bold text-purple-900 mb-2">{currentLocation.street}</h3>
            <p className="text-purple-700 mb-3">{currentLocation.area}, {currentLocation.district}</p>
            <div className="text-sm text-purple-600">
              {currentLocation.facilities.slice(0, 3).join(', ')}
              {currentLocation.facilities.length > 3 && '...'}
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
                const locationKey = getLocationKey(location);
                const disabled = otherSelectedKeys.includes(locationKey);
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
                    <div className="text-xs text-purple-600 mt-1">
                      {location.facilities.slice(0, 2).join(', ')}
                      {location.facilities.length > 2 && '...'}
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
                const locationKey = getLocationKey(location);
                const disabled = otherSelectedKeys.includes(locationKey);
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
                    <div className="text-xs text-purple-600 mt-1">
                      {location.facilities.slice(0, 2).join(', ')}
                      {location.facilities.length > 2 && '...'}
                    </div>
                    {disabled && (
                      <div className="mt-2 text-xs text-center text-gray-500">Already selected in another slot</div>
                    )}
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
  const allSlotsFilled = nonNullSelected.length === selectedLocations.length;
  const canCompare = allSlotsFilled && nonNullSelected.length >= 2;

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
            onClick={removeSlot}
            disabled={selectedLocations.length <= 2}
            title={selectedLocations.length <= 2 ? 'Minimum 2 locations' : 'Remove last location'}
            className={
              `flex items-center gap-2 px-4 py-2 rounded-xl border transition ` +
              (selectedLocations.length <= 2
                ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                : 'bg-red-600 text-white border-red-700 hover:bg-red-700')
            }
          >
            <HiMinus className="w-5 h-5" />
            <span className="font-medium">Slots</span>
          </button>

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
                : 'bg-green-600 text-white border-green-700 hover:bg-green-700')
            }
          >
            <HiPlus className="w-5 h-5" />
            <span className="font-medium">Slots</span>
          </button>
        </div>
      </div>

      {/* Compare modal */}
      {compareOpen && (
        <AnalysisView
          locations={nonNullSelected.length ? nonNullSelected : suggestedLocations.slice(0, 5)}
          onClose={() => setCompareOpen(false)}
        />
      )}
    </div>
  );
};

export default ComparisonView;