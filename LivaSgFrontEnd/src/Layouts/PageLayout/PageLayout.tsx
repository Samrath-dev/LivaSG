import BottomNav from "../../components/BottomNav";

interface PageLayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

function PageLayout({ children, activeTab, onTabChange }: PageLayoutProps) {
    return (
        <div style={{ 
            height: '100vh', 
            width: '100vw', 
            display: 'flex', 
            flexDirection: 'column',
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0
        }}>
            {/* Content Area - This will scroll */}
            <div style={{ 
                flex: 1, 
                overflow: 'auto',
                minHeight: 0
            }}>
                {children}
            </div>
            
            {/* Bottom Navigation - Always fixed at bottom */}
            <div style={{
                flexShrink: 0
            }}>
                <BottomNav activeTab={activeTab} onTabChange={onTabChange} />
            </div>
        </div>
    );
}

export default PageLayout;;