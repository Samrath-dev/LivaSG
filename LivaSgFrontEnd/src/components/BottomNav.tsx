import { 
  HiLocationMarker, 
  HiChartBar, 
  HiUser, 
  HiBookmark,
} from "react-icons/hi";

interface BottomNavProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

const BottomNav = ({ activeTab, onTabChange }: BottomNavProps) => {
  const tabs = [
    { id: 'explore', label: 'Explore', icon: HiLocationMarker },
    { id: 'comparison', label: 'Compare', icon: HiChartBar },
    { id: 'preferences', label: 'Profile', icon: HiUser },
    { id: 'bookmarks', label: 'Saved', icon: HiBookmark },
  ];

  return (
    <div className="w-full bg-white border-t border-gray-200">
      <nav className="w-full">
        <div className="flex justify-between items-stretch w-full">
          {tabs.map((tab) => {
            const IconComponent = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`relative flex flex-col items-center justify-center flex-1 py-3 px-0 transition-all duration-300 min-w-0 ${
                  isActive 
                    ? 'text-blue-600' 
                    : 'text-gray-500 hover:text-blue-500'
                }`}
              >
                {isActive && (
                  <div className="absolute inset-0 bg-blue-100 rounded-md transition-all duration-300 mx-1"></div>
                )}
                
                <div className="relative z-10 mb-1">
                  <IconComponent 
                    className={`w-5 h-5 transition-transform duration-300 ${
                      isActive ? 'scale-110 text-blue-600' : 'scale-100 text-gray-400'
                    }`} 
                  />
                </div>
                
                <span className={`text-xs transition-all duration-300 relative z-10 leading-tight ${
                  isActive ? 'text-blue-600 font-semibold' : 'text-gray-500'
                }`}>
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
};

export default BottomNav;