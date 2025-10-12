import BottomNav from "../../components/BottomNav";
import { useState, useEffect } from 'react';
import { HiSearch, HiX, HiCog } from "react-icons/hi";
import SearchView from "../../views/SearchView";
import DetailsView from "../../views/DetailsView";

interface PageLayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tabId: string) => void;
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
}

type ViewState = 'map' | 'search' | 'details';

function PageLayout({ children, activeTab, onTabChange }: PageLayoutProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentView, setCurrentView] = useState<ViewState>('map');
  const [selectedLocation, setSelectedLocation] = useState<LocationData | null>(null);

  // Reset view state when tab changes
  useEffect(() => {
    setCurrentView('map');
    setSelectedLocation(null);
    setSearchQuery('');
  }, [activeTab]);

  const clearSearch = () => {
    setSearchQuery('');
    setCurrentView('map');
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim() && activeTab === 'explore') {
      setCurrentView('search');
    }
  };

  const handleInputFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = '#8b5cf6';
    e.target.style.boxShadow = '0 0 0 2px rgba(139, 92, 246, 0.1)';
    // Only show SearchView when search box is clicked in Explore tab
    if (activeTab === 'explore') {
      setCurrentView('search');
    }
  };

  const handleInputBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = '#d8b4fe';
    e.target.style.boxShadow = 'none';
  };

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (searchQuery.trim() && activeTab === 'explore') {
        setCurrentView('search');
      }
    }
  };

  const handleViewDetails = (location: LocationData) => {
    setSelectedLocation(location);
    setCurrentView('details');
  };

  const handleBackFromDetails = () => {
    setCurrentView('search');
  };

  const handleBackFromSearch = () => {
    setCurrentView('map');
  };

  const handleTabChange = (tabId: string) => {
    // This will trigger the useEffect above to reset the view state
    onTabChange(tabId);
  };

  const showSearchBar = activeTab === 'explore' && currentView !== 'details';

  const renderContent = () => {
    // Only show SearchView if in Explore tab and currentView is 'search'
    if (activeTab === 'explore' && currentView === 'search') {
      return (
        <SearchView 
          searchQuery={searchQuery}
          onBack={handleBackFromSearch}
          onViewDetails={handleViewDetails}
        />
      );
    }
    if (currentView === 'details') {
      return selectedLocation ? (
        <DetailsView 
          location={selectedLocation}
          onBack={handleBackFromDetails}
        />
      ) : (
        <div>Error: No location selected</div>
      );
    }
    // Default: show children (e.g., MapView, ComparisonView, etc.)
    return children;
  };

  return (
    <div className="h-screen w-screen flex flex-col fixed top-0 left-0 right-0 bottom-0 bg-purple-50">
      {/* Fixed Search Bar - Only show for Explore tab and when not in DetailsView */}
      {showSearchBar && (
        <div className="flex-shrink-0 bg-purple-100 border-b border-purple-200 p-3">
          <div className="flex items-center gap-3">
            {/* Search Input Container */}
            <form onSubmit={handleSearchSubmit} className="relative flex-1">
              <HiSearch className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-purple-400" />
              <input
                type="text"
                placeholder="Search locations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                onKeyDown={handleInputKeyDown}
                className="w-full pl-10 pr-10 py-2 border border-purple-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white text-purple-900 placeholder-purple-400"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-10 top-1/2 transform -translate-y-1/2 text-purple-400 hover:text-purple-600 transition-colors"
                >
                  <HiX className="w-4 h-4" />
                </button>
              )}
            </form>

            {/* Settings Icon */}
            <button
              className="p-2 rounded-xl text-purple-600 hover:text-purple-800 hover:bg-purple-200 transition-all duration-200"
              onClick={() => {
                console.log('Settings clicked');
              }}
            >
              <HiCog className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
      
      {/* Content Area - Dynamic based on current view */}
      <div className="flex-1 overflow-auto min-h-0">
        {renderContent()}
      </div>
      
      {/* Fixed Bottom Navigation */}
      <div className="flex-shrink-0 flex justify-center bg-purple-100 border-t border-purple-200">
        <div className="w-full max-w-lg mx-auto">
          <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />
        </div>
      </div>
    </div>
  );
}

export default PageLayout;