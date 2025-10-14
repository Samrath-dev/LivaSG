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
    { id: 'preferences', label: 'Preferred', icon: HiUser },
    { id: 'bookmarks', label: 'Saved', icon: HiBookmark },
  ];

  return (
    <div
      className="w-full border-t border-purple-200 safe-area-bottom"
      style={{ 
        background: 'linear-gradient(135deg, #faf5ff 0%, #f0f9ff 100%)', 
        height: '80px',
        backdropFilter: 'blur(10px)'
      }}
    >
      <nav className="w-full h-full">
        <div
          className="flex justify-between items-center w-full h-full px-2"
        >
          {tabs.map((tab) => {
            const IconComponent = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                style={{
                  background: isActive 
                    ? 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' 
                    : 'transparent',
                  color: isActive ? '#ffffff' : '#6d28d9',
                  borderRadius: '16px',
                  margin: '4px',
                  boxShadow: isActive ? '0 4px 12px rgba(139, 92, 246, 0.3)' : 'none',
                  border: isActive ? 'none' : '2px solid transparent',
                  transition: 'all 0.3s ease-in-out',
                  minWidth: 0,
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '12px 0',
                  position: 'relative',
                  gap: '4px',
                  height: '100%',
                }}
                className="hover:bg-purple-50 hover:border-purple-300"
              >
                <IconComponent
                  style={{
                    width: 24,
                    height: 24,
                    color: isActive ? '#ffffff' : '#6d28d9',
                    transition: 'all 0.3s ease-in-out',
                    transform: isActive ? 'scale(1.1)' : 'scale(1)',
                  }}
                />
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: isActive ? 600 : 500,
                    color: isActive ? '#ffffff' : '#6d28d9',
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
                      background: 'rgba(255, 255, 255, 0.2)',
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