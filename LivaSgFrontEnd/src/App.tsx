import { useState } from 'react';
import PageLayout from './Layouts/PageLayout/PageLayout';
import MapView from './views/MapView';
import ComparisonView from './views/ComparisonView';
import BookmarkView from './views/BookmarkView';

function App() {
  const [activeTab, setActiveTab] = useState('explore');

  const handleBack = () => {
    setActiveTab('explore'); // Go back to explore tab
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'explore':
        return <MapView />;
      case 'comparison':
        return <ComparisonView onBack={handleBack} />;
      case 'preferences':
        return <div className="p-4">Preferences Content - User settings</div>;
      case 'bookmarks':
        return <BookmarkView onBack={handleBack} />;
        //return <div className="p-4">Bookmarks</div>;
      default:
        return <MapView />;
    }
  };

  return (
    <PageLayout activeTab={activeTab} onTabChange={setActiveTab}>
      {renderContent()}
    </PageLayout>
  );
}

export default App;