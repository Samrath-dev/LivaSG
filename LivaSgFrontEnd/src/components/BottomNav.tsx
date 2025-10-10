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
    <div className="w-full bg-white border-t border-gray-200 safe-area-bottom">
      <nav className="w-full">
        <div className="flex justify-between items-stretch w-full">
          {tabs.map((tab) => {
            const IconComponent = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`relative flex flex-col items-center justify-center flex-1 transition-all duration-300 min-w-0 ${
                  isActive 
                    ? 'text-blue-600' 
                    : 'text-gray-500 hover:text-blue-500'
                } 
                /* Responsive padding */
                py-2 xs:py-3 sm:py-4
                /* Responsive spacing */
                px-0 xs:px-1 sm:px-2`}
              >
                {/* Active background - responsive rounded corners */}
                {isActive && (
                  <div className="absolute inset-0 bg-blue-100 transition-all duration-300 
                    mx-0.5 xs:mx-1 sm:mx-2 
                    rounded-none xs:rounded-md sm:rounded-lg"></div>
                )}
                
                {/* Icon container with responsive margin */}
                <div className="relative z-10 mb-0.5 xs:mb-1 sm:mb-1.5">
                  <IconComponent 
                    className={`transition-transform duration-300 ${
                      isActive ? 'scale-110 text-blue-600' : 'scale-100 text-gray-400'
                    }
                    /* Responsive icon sizes */
                    w-4 h-4 xs:w-4 xs:h-4 sm:w-5 sm:h-5 md:w-6 md:h-6`} 
                  />
                </div>
                
                {/* Label with responsive text sizing */}
                <span className={`transition-all duration-300 relative z-10 leading-tight ${
                  isActive ? 'text-blue-600 font-semibold' : 'text-gray-500'
                }
                /* Responsive text sizes */
                text-[10px] xs:text-[11px] sm:text-xs md:text-sm
                /* Responsive line height */
                leading-none xs:leading-tight sm:leading-tight`}>
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