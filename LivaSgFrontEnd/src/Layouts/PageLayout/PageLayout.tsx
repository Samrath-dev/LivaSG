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
            
            {/* Bottom Navigation - Centered with max width */}
            <div style={{
                flexShrink: 0,
                display: 'flex',
                justifyContent: 'center',
                backgroundColor: 'white',
                borderTop: '1px solid #e5e7eb'
            }}>
                <div style={{
                    width: '100%',
                    maxWidth: '500px', // Adjust this value as needed
                    margin: '0 auto'
                }}>
                    <BottomNav activeTab={activeTab} onTabChange={onTabChange} />
                </div>
            </div>
        </div>
    );
}

export default PageLayout;