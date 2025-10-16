import BottomNav from "../../components/BottomNav";
import { useState, useEffect } from 'react';
import SearchView from "../../views/SearchView";
import DetailsView from "../../views/DetailsView";
import MapView from "../../views/MapView";
import SettingsView from "../../views/SettingsView"; // Import SettingsView

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
  const [showSettings, setShowSettings] = useState(false); // Add settings state

  // Reset view state when tab changes
  useEffect(() => {
    setCurrentView('map');
    setSelectedLocation(null);
    setSearchQuery('');
    setShowSettings(false); 
  }, [activeTab]);

  const handleSearchClick = () => {
    if (activeTab === 'explore') {
      setCurrentView('search');
    }
  };

  const handleSearchQueryChange = (query: string) => {
    setSearchQuery(query);
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
    onTabChange(tabId);
  };

  // Settings handlers
  const handleShowSettings = () => {
    setShowSettings(true);
  };

  const handleSettingsBack = () => {
    setShowSettings(false);
  };

  const renderContent = () => {
    // If settings is shown, it takes precedence and appears as overlay
    if (showSettings) {
      return (
        <div className="fixed inset-0 z-50">
          <SettingsView onBack={handleSettingsBack} />
        </div>
      );
    }

    if (activeTab === 'explore') {
      if (currentView === 'search') {
        return (
          <SearchView 
            searchQuery={searchQuery}
            onBack={handleBackFromSearch}
            onViewDetails={handleViewDetails}
            onSearchQueryChange={handleSearchQueryChange}
            onSettingsClick={handleShowSettings} // Pass settings handler
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
      // Default: show MapView with search bar
      return (
        <MapView 
          onSearchClick={handleSearchClick}
          searchQuery={searchQuery}
          onSearchQueryChange={handleSearchQueryChange}
          onSettingsClick={handleShowSettings} // Pass settings handler
        />
      );
    }
    // Default: show children for other tabs
    return children;
  };

  return (
    <div 
      className="h-screen w-screen flex flex-col fixed top-0 left-0 right-0 bottom-0"
      style={{
        background: 'linear-gradient(135deg, #faf5ff 0%, #f0f9ff 100%)'
      }}
    >
      {/* Content Area - Dynamic based on current view */}
      <div className="flex-1 overflow-auto min-h-0 relative">
        {renderContent()}
      </div>
      
      {/* Fixed Bottom Navigation */}
      <div 
        className="flex-shrink-0 flex justify-center border-t border-purple-200"
        style={{
          background: 'linear-gradient(135deg, #faf5ff 0%, #f0f9ff 100%)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <div className="w-full max-w-lg mx-auto">
          <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />
        </div>
      </div>
    </div>
  );
}

export default PageLayout;