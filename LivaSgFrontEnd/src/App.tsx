import { useState } from 'react';
import PageLayout from './Layouts/PageLayout/PageLayout';
import MapView from './views/MapView';
import ComparisonView from './views/ComparisonView';
import PreferenceView from './views/PreferenceView';

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
        return <PreferenceView onBack={handleBack}/>;
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