import { useState } from 'react';
import PageLayout from './Layouts/PageLayout/PageLayout';
import ComparisonView from './views/ComparisonView';
import PreferenceView from './views/PreferenceView';
import BookmarkView from './views/BookmarkView';
import SettingsView from './views/SettingsView'; // Import SettingsView

function App() {
  const [activeTab, setActiveTab] = useState('explore');
  const [showSettings, setShowSettings] = useState(false); // Add state for settings

  const handleBack = () => {
    setActiveTab('explore'); // Go back to explore tab
    setShowSettings(false); // Also hide settings when going back
  };

  const handleSettingsBack = () => {
    setShowSettings(false); // Hide settings and return to previous view
  };

  const renderContent = () => {
    // If settings is shown, it takes precedence over everything else
    if (showSettings) {
      return <SettingsView onBack={handleSettingsBack} />;
    }

    // Otherwise render the normal tab content
    switch (activeTab) {
      case 'comparison':
        return <ComparisonView onBack={handleBack} />;
      case 'preferences':
        return <PreferenceView onBack={handleBack}/>;
      case 'bookmarks':
        return <BookmarkView onBack={handleBack} />;
      default:
        // For explore tab, PageLayout will handle MapView/SearchView/DetailsView
        return null;
    }
  };

  return (
    <PageLayout 
      activeTab={activeTab} 
      onTabChange={setActiveTab}
    >
      {renderContent()}
    </PageLayout>
  );
}

export default App;