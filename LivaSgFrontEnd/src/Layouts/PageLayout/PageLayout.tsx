import BottomNav from "../../components/BottomNav";
import { useState } from 'react';
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
    e.target.style.borderColor = '#3b82f6';
    e.target.style.boxShadow = '0 0 0 2px rgba(59, 130, 246, 0.1)';
    // Only show SearchView when search box is clicked in Explore tab
    if (activeTab === 'explore') {
      setCurrentView('search');
    }
  };

  const handleInputBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = '#d1d5db';
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

  const showSearchBar = activeTab === 'explore';

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
    <div style={{ 
      height: '100vh', 
      width: '100vw', 
      display: 'flex', 
      flexDirection: 'column',
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0
    }}>
      {/* Fixed Search Bar - Only show for Explore tab and when not in DetailsView */}
      {showSearchBar && currentView !== 'details' && (
        <div style={{
          flexShrink: 0,
          backgroundColor: 'white',
          borderBottom: '1px solid #e5e7eb',
          padding: '12px 16px'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px' 
          }}>
            {/* Search Input Container */}
            <form onSubmit={handleSearchSubmit} style={{ position: 'relative', flex: 1 }}>
              <HiSearch style={{ 
                position: 'absolute', 
                left: '12px', 
                top: '50%', 
                transform: 'translateY(-50%)', 
                color: '#9ca3af',
                width: '16px',
                height: '16px'
              }} />
              <input
                type="text"
                placeholder="Location Search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                onKeyDown={handleInputKeyDown}
                style={{
                  width: '100%',
                  paddingLeft: '40px',
                  paddingRight: searchQuery ? '40px' : '16px',
                  paddingTop: '8px',
                  paddingBottom: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  outline: 'none',
                  fontSize: '14px'
                }}
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={clearSearch}
                  style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: '#9ca3af',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer'
                  }}
                >
                  <HiX style={{ width: '16px', height: '16px' }} />
                </button>
              )}
            </form>

            {/* Settings Icon */}
            <button
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '8px',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#6b7280',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f3f4f6';
                e.currentTarget.style.color = '#374151';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = '#6b7280';
              }}
              onClick={() => {
                console.log('Settings clicked');
              }}
            >
              <HiCog style={{ width: '20px', height: '20px' }} />
            </button>
          </div>
        </div>
      )}
      
      {/* Content Area - Dynamic based on current view */}
      <div style={{ 
        flex: 1, 
        overflow: 'auto',
        minHeight: 0
      }}>
        {renderContent()}
      </div>
      
      {/* Fixed Bottom Navigation */}
      <div style={{
        flexShrink: 0,
        display: 'flex',
        justifyContent: 'center',
        backgroundColor: '#F5F0FA', // Changed from 'white' to pale purple
        borderTop: '1px solid #e5e7eb'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '500px',
          margin: '0 auto'
        }}>
          <BottomNav activeTab={activeTab} onTabChange={onTabChange} />
        </div>
      </div>
    </div>
  );
}

export default PageLayout;