import { useState } from 'react';
import PageLayout from './Layouts/PageLayout/PageLayout';
import MapView from './views/MapView';
import ComparisonView from './views/ComparisonView';

function App() {
  const [activeTab, setActiveTab] = useState('explore');

  const renderContent = () => {
    switch (activeTab) {
      case 'explore':
        return <MapView />;
      case 'comparison':
        return <ComparisonView />;
      case 'preferences':
        return <div className="p-4">Preferences Content - User settings</div>;
      case 'bookmarks':
        return <div className="p-4">Bookmarks</div>;
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