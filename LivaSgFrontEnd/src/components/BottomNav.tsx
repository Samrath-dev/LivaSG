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

const PURPLE_BG = '#F5F0FA';

const BottomNav = ({ activeTab, onTabChange }: BottomNavProps) => {
  const tabs = [
    { id: 'explore', label: 'Explore', icon: HiLocationMarker },
    { id: 'comparison', label: 'Compare', icon: HiChartBar },
    { id: 'preferences', label: 'Preferred', icon: HiUser },
    { id: 'bookmarks', label: 'Saved', icon: HiBookmark },
  ];

  return (
    <div
      className="w-full border-t border-gray-200 safe-area-bottom"
      style={{ backgroundColor: PURPLE_BG, height: '80px' }} // Increased height here
    >
      <nav className="w-full h-full">
        <div
          className="flex justify-between items-center w-full h-full"
          style={{ display: 'flex', flexDirection: 'row', width: '100%', height: '100%' }}
        >
          {tabs.map((tab) => {
            const IconComponent = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                style={{
                  backgroundColor: PURPLE_BG,
                  color: isActive ? '#4F2C6F' : '#7C5A99',
                  borderRadius: '16px',
                  margin: '4px',
                  boxShadow: isActive ? '0 2px 8px rgba(79,44,111,0.08)' : 'none',
                  border: isActive ? '2px solid #4F2C6F' : '2px solid transparent',
                  transition: 'all 0.2s',
                  minWidth: 0,
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '18px 0', // Increased padding for taller buttons
                  position: 'relative',
                  gap: '8px',
                  height: '100%',
                }}
              >
                <IconComponent
                  style={{
                    width: 26,
                    height: 26,
                    color: isActive ? '#4F2C6F' : '#7C5A99',
                    transition: 'transform 0.2s',
                    transform: isActive ? 'scale(1.15)' : 'scale(1)',
                  }}
                />
                <span
                  style={{
                    fontSize: '14px',
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? '#4F2C6F' : '#7C5A99',
                    zIndex: 1,
                  }}
                >
                  {tab.label}
                </span>
                {isActive && (
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background: 'rgba(255,255,255,0.18)',
                      borderRadius: '16px',
                      zIndex: 0,
                    }}
                  />
                )}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
};

export default BottomNav;