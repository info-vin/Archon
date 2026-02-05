import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MenuIcon, XIcon, UserIcon, SettingsIcon, LogOutIcon, ShieldCheckIcon, LayoutGridIcon, PaletteIcon, FileTextIcon } from '../../components/Icons.tsx';
import LiveClock from '../../components/LiveClock.tsx';
import UserAvatar from '../../components/UserAvatar.tsx';
import { BrandLogo } from '../../components/BrandLogo.tsx';
import { useAuth } from '../../hooks/useAuth.tsx';
import { usePermission } from '../../features/auth/hooks/usePermission.ts';

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { user, logout, isAdmin } = useAuth();
    const { hasPermission } = usePermission();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const location = useLocation();

    const [cartCount, setCartCount] = useState(0);

    useEffect(() => {
        // Simple poll for cart count (shortlisted leads)
        const fetchCart = async () => {
            try {
               // We might need a lightweight API for this, but reusing getLeads for now
               // TODO: Optimize with specific endpoint
               // Using direct fetch to avoid circular deps if api.ts imports layout? Unlikely.
               // Assuming api is available via imports.
               // Actually we need to import api at top level.
               const { api } = await import('../../services/api.ts');
               const leads = await api.getLeads();
               const count = leads.filter((l: any) => l.status === 'shortlisted').length;
               setCartCount(count);
            } catch (e) {
                console.error("Failed to fetch cart count", e);
            }
        };
        
        if (hasPermission('leads:view:sales')) {
            fetchCart();
            // Poll every 10s to keep in sync
            const interval = setInterval(fetchCart, 10000);
            return () => clearInterval(interval);
        }
    }, [hasPermission]);

    return (
        <div className="flex h-screen bg-background text-foreground">
             <nav className={`fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border flex flex-col transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out md:relative md:translate-x-0`}>
                <div className="p-4 border-b border-border flex justify-between items-center bg-card/50 backdrop-blur">
                    <Link to="/dashboard" className="flex items-center transition-transform hover:scale-105 active:scale-95">
                        <BrandLogo className="w-8 h-8" />
                    </Link>
                    <button onClick={() => setIsSidebarOpen(false)} className="md:hidden p-1 hover:bg-secondary rounded-md ml-auto" aria-label="Close sidebar">
                        <XIcon className="w-6 h-6" />
                    </button>
                </div>
                {/* Desktop Navigation */}
                <ul className="flex-grow p-2" onClick={() => setIsSidebarOpen(false)}>
                    <li className="mb-2">
                        <Link to="/dashboard" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/dashboard') ? 'bg-secondary' : ''}`}>
                            <UserIcon className="w-5 h-5 mr-3" />
                            My Tasks
                        </Link>
                    </li>
                    {hasPermission('stats:view:own') && (
                        <li className="mb-2">
                            <Link to="/stats" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/stats') ? 'bg-secondary' : ''}`}>
                                <SettingsIcon className="w-5 h-5 mr-3" />
                                HR Dashboard
                            </Link>
                        </li>
                    )}
                    {hasPermission('leads:view:sales') && (
                        <li className="mb-2">
                            <Link to="/marketing" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/marketing') ? 'bg-secondary' : ''}`}>
                                <ShieldCheckIcon className="w-5 h-5 mr-3" />
                                Sales Intel
                            </Link>
                        </li>
                    )}
                    {hasPermission('leads:view:marketing') && (
                        <li className="mb-2">
                            <Link to="/brand" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/brand') ? 'bg-secondary' : ''}`}>
                                <PaletteIcon className="w-5 h-5 mr-3" />
                                Brand Hub
                            </Link>
                        </li>
                    )}
                    {hasPermission('user:manage:team') && (
                        <li className="mb-2">
                            <Link to="/approvals" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/approvals') ? 'bg-secondary' : ''}`}>
                                <FileTextIcon className="w-5 h-5 mr-3 text-indigo-500" />
                                Command Center
                            </Link>
                        </li>
                    )}
                    {hasPermission('user:manage:team') && (
                        <li className="mb-2">
                            <Link to="/team" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/team') ? 'bg-secondary' : ''}`}>
                                <UserIcon className="w-5 h-5 mr-3" />
                                Team Management
                            </Link>
                        </li>
                    )}
                    {/* UX-011: Settings moved to Profile Modal
                    <li className="mb-2">
                        <Link to="/settings" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/settings') ? 'bg-secondary' : ''}`}>
                            <SettingsIcon className="w-5 h-5 mr-3" />
                            Settings
                        </Link>
                    </li>
                    */}
                    {isAdmin && (
                         <li className="mb-2">
                            <Link to="/admin" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/admin') ? 'bg-secondary' : ''}`}>
                                <SettingsIcon className="w-5 h-5 mr-3" />
                                Admin Control Center
                            </Link>
                        </li>
                    )}
                </ul>
                <div className="p-4 border-t border-border">
                    <div className="mb-4">
                        <Link to="/landing" className="flex items-center p-2 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors">
                            <LayoutGridIcon className="w-5 h-5 mr-3" />
                            Back to Website
                        </Link>
                    </div>
                   <Link to="/settings" className="flex items-center mb-4 p-2 -mx-2 rounded-md hover:bg-secondary transition-colors group">
                       <UserAvatar name={user?.name || ''} role={user?.role} className="w-10 h-10 mr-3 group-hover:ring-2 ring-primary/20 transition-all" />
                       <div className="overflow-hidden">
                           <p className="font-semibold truncate">{user?.name}</p>
                           <p className="text-sm text-muted-foreground truncate">{user?.email}</p>
                       </div>
                   </Link>
                   <button onClick={logout} className="w-full flex items-center justify-center p-2 rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90">
                       <LogOutIcon className="w-5 h-5 mr-2" />
                       Logout
                   </button>
                </div>
            </nav>
            {isSidebarOpen && <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setIsSidebarOpen(false)}></div>}
            <main className="flex-1 flex flex-col overflow-y-auto bg-background pb-16 md:pb-0">
                {/* Mobile Header */}
                <header className="md:hidden flex items-center justify-between p-4 border-b border-border bg-background/80 backdrop-blur z-30 sticky top-0">
                    <LiveClock />
                    <UserAvatar name={user?.name || ''} role={user?.role} className="w-8 h-8" />
                </header>

                {/* Desktop Top Bar */}
                <header className="hidden md:flex items-center justify-end p-4 border-b border-border bg-background/60 backdrop-blur sticky top-0 z-30 h-16">
                    <LiveClock />
                </header>
                
                <div className="flex-1 p-4 md:p-8">
                    {children}
                </div>
            </main>

            {/* Mobile Bottom Navigation Bar */}
            <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-card border-t border-border flex justify-around items-center z-50 px-2 pb-safe">
                <Link to="/dashboard" className={`flex flex-col items-center justify-center p-2 rounded-lg ${location.pathname === '/dashboard' ? 'text-primary' : 'text-muted-foreground'}`}>
                    <LayoutGridIcon className="w-6 h-6" />
                    <span className="text-[10px] mt-1">Home</span>
                </Link>
                
                {hasPermission('leads:view:sales') && (
                    <Link to="/marketing" className={`flex flex-col items-center justify-center p-2 rounded-lg ${location.pathname.startsWith('/marketing') ? 'text-primary' : 'text-muted-foreground'}`}>
                        <ShieldCheckIcon className="w-6 h-6" />
                        <span className="text-[10px] mt-1">Leads</span>
                    </Link>
                )}

                {hasPermission('leads:view:sales') && (
                    <Link to="/sales-cart" className={`flex flex-col items-center justify-center p-2 rounded-lg ${location.pathname.startsWith('/sales-cart') ? 'text-primary' : 'text-muted-foreground'}`}>
                         {/* TODO: Add ShoppingCartIcon */}
                        <div className="relative">
                            <MenuIcon className="w-6 h-6 rotate-90" /> {/* Temporary Icon */}
                            {cartCount > 0 && <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-[9px] w-3 h-3 flex items-center justify-center rounded-full animate-bounce">{cartCount}</span>}
                        </div>
                        <span className="text-[10px] mt-1">Cart</span>
                    </Link>
                )}

                <button 
                    onClick={() => setIsSidebarOpen(true)}
                    className={`flex flex-col items-center justify-center p-2 rounded-lg ${isSidebarOpen ? 'text-primary' : 'text-muted-foreground'}`}
                >
                    <MenuIcon className="w-6 h-6" />
                    <span className="text-[10px] mt-1">Menu</span>
                </button>
            </nav>
        </div>
    );
};

export default MainLayout;
