import { useState } from 'react';
import PageLayout from './Layouts/PageLayout/PageLayout';
import ComparisonView from './views/ComparisonView';
import PreferenceView from './views/PreferenceView';
import BookmarkView from './views/BookmarkView';

function App() {
  const [activeTab, setActiveTab] = useState('explore');

  const handleBack = () => {
    setActiveTab('explore'); // Go back to explore tab
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'comparison':
        return <ComparisonView onBack={handleBack} />;
      case 'preferences':
        return <PreferenceView onBack={handleBack}/>;
      case 'bookmarks':
        return <div className="p-4">Bookmarks View - Coming Soon</div>;
        return <BookmarkView onBack={handleBack} />;
        //return <div className="p-4">Bookmarks</div>;
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