import { useState, useEffect } from 'react';
import PageLayout from './Layouts/PageLayout/PageLayout';
import ComparisonView from './views/ComparisonView';
import PreferenceView from './views/PreferenceView';
import BookmarkView from './views/BookmarkView';
import LaunchView from './views/LaunchView';

function App() {
  const [activeTab, setActiveTab] = useState('explore');
  const [showOnboarding, setShowOnboarding] = useState(true);

  useEffect(() => {
    // Check if onboarding was already completed in this session
    const hasCompletedOnboardingInSession = sessionStorage.getItem('hasCompletedOnboardingInSession');
    if (hasCompletedOnboardingInSession === 'true') {
      setShowOnboarding(false);
    }
  }, []);

  const handleBack = () => {
    setActiveTab('explore');
  };

  const handleOnboardingComplete = () => {
    // Save to sessionStorage (survives refreshes but not browser close)
    sessionStorage.setItem('hasCompletedOnboardingInSession', 'true');
    setShowOnboarding(false);
  };

  const handleOnboardingSkip = () => {
    // Save to sessionStorage (survives refreshes but not browser close)
    sessionStorage.setItem('hasCompletedOnboardingInSession', 'true');
    setShowOnboarding(false);
  };

  const renderContent = () => {
    if (showOnboarding) {
      return (
        <LaunchView 
          onComplete={handleOnboardingComplete}
          onSkip={handleOnboardingSkip}
        />
      );
    }

    switch (activeTab) {
      case 'comparison':
        return <ComparisonView onBack={handleBack} />;
      case 'preferences':
        return <PreferenceView onBack={handleBack}/>;
      case 'bookmarks':
        return <BookmarkView onBack={handleBack} />;
      default:
        return null;
    }
  };

  if (showOnboarding) {
    return renderContent();
  }

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