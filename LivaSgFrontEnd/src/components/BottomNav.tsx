import { useState } from 'react';
import { 
  HiLocationMarker, 
  HiChartBar, 
  HiUser, 
  HiBookmark,
} from "react-icons/hi";
import MapView from '../views/MapView';

const BottomTabs = () => {
  const [activeTab, setActiveTab] = useState('explore');

  const tabs = [
    {
      id: 'explore',
      label: 'Explore',
      icon: HiLocationMarker,
      content: <MapView />,
    },
    {
      id: 'comparison',
      label: 'Compare',
      icon: HiChartBar,
      content: <div className="p-4">Comparison Content</div>,
    },
    {
      id: 'preferences',
      label: 'Profile',
      icon: HiUser,
      content: <div className="p-4">Preferences Content - User settings</div>,
    },
    {
      id: 'bookmarks',
      label: 'Saved',
      icon: HiBookmark,
      content: <div className="p-4">Bookmarks Content - Saved items</div>,
    },
  ];

  const activeTabContent = tabs.find(tab => tab.id === activeTab)?.content;

  return (
    <div className="w-full max-w-sm h-full bg-white flex flex-col">
      {/* Main Content - grows to fill available space */}
      <div className="flex-1 overflow-auto">
        {activeTabContent}
      </div>

      {/* Bottom Tabs - permanently at bottom */}
      <div className="bg-white border-t border-gray-200">
        <div className="flex justify-between items-stretch px-1">
          {tabs.map((tab) => {
            const IconComponent = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative flex flex-col items-center justify-center flex-1 py-2 px-0 transition-all duration-300 min-w-0 ${
                  isActive 
                    ? 'text-blue-600' 
                    : 'text-gray-500 hover:text-blue-500'
                }`}
              >
                {/* Active background */}
                {isActive && (
                  <div className="absolute inset-0 bg-blue-100 rounded-md transition-all duration-300"></div>
                )}
                
                {/* Icon */}
                <div className="relative z-10 mb-0.5">
                  <IconComponent 
                    className={`w-4 h-4 transition-transform duration-300 ${
                      isActive ? 'scale-110 text-blue-600' : 'scale-100 text-gray-400'
                    }`} 
                  />
                </div>
                
                {/* Label */}
                <span className={`text-[9px] transition-all duration-300 relative z-10 leading-tight ${
                  isActive ? 'text-blue-600 font-semibold' : 'text-gray-500'
                }`}>
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default BottomTabs;