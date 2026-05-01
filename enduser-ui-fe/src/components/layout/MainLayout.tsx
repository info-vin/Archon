import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MenuIcon, UserIcon, SettingsIcon, LogOutIcon, ShieldCheckIcon, LayoutGridIcon, PaletteIcon, CheckCircleIcon } from '../../components/Icons.tsx';
import LiveClock from '../../components/LiveClock.tsx';
import UserAvatar from '../../components/UserAvatar.tsx';
import { BrandLogo } from '../../components/BrandLogo.tsx';
import { useAuth } from '@/hooks/useAuth';
import { usePermission } from '../../features/auth/hooks/usePermission.ts';

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { user, logout, isAdmin } = useAuth();
    const { hasPermission } = usePermission();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const location = useLocation();

    // Resizable Sidebar State
    const [sidebarWidth, setSidebarWidth] = useState(256); // Default w-64
    const [isResizing, setIsResizing] = useState(false);
    const isCollapsed = sidebarWidth < 120;

    const [cartCount, setCartCount] = useState(0);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isResizing) return;
            // Limit width between 72px (icon only) and 400px
            const newWidth = Math.min(Math.max(e.clientX, 72), 400); 
            setSidebarWidth(newWidth);
        };
        const handleMouseUp = () => setIsResizing(false);

        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        } else {
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
        
        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing]);

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
        
        if (hasPermission('leads:view:all')) {
            fetchCart();
            // Poll every 10s to keep in sync
            const interval = setInterval(fetchCart, 10000);
            return () => clearInterval(interval);
        }
    }, [hasPermission]);

    return (
        <div className="flex flex-col md:flex-row h-[100dvh] md:h-screen bg-background text-foreground overflow-hidden">
            <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-background focus:text-foreground focus:ring-2 focus:ring-primary focus:outline-none">
                Skip to content
            </a>
             <nav 
                style={{ width: isSidebarOpen ? '256px' : (window.innerWidth >= 768 ? `${sidebarWidth}px` : '256px') }}
                className={`fixed inset-y-0 left-0 z-50 bg-card border-r border-border flex flex-col transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 ${isResizing ? '' : 'transition-transform duration-300 ease-in-out'}`}
             >
                {/* Resizer Handle */}
                <div 
                    className="hidden md:block absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-primary/50 active:bg-primary z-50 transition-colors"
                    onMouseDown={(e) => { e.preventDefault(); setIsResizing(true); }}
                />

                <div className={`p-6 border-b border-border flex ${isCollapsed ? 'justify-center' : 'justify-between'} items-center bg-card/50 backdrop-blur`}>
                    <Link to={user?.role?.toLowerCase() === 'marketing' ? "/brand" : "/dashboard"} className="flex items-center transition-transform hover:scale-105 active:scale-95">
                        <BrandLogo className="w-10 h-10" />
                    </Link>
                </div>
                {/* Desktop Navigation */}
                <ul className="flex-grow p-2 overflow-y-auto overflow-x-hidden" onClick={() => setIsSidebarOpen(false)}>
                    <li className="mb-2 w-full">
                        <Link to="/dashboard" title={isCollapsed ? "My Tasks" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px] text-center' : 'items-center p-2'} rounded-md hover:bg-secondary ${location.pathname === '/dashboard' ? 'bg-secondary' : ''} transition-all`}>
                            <UserIcon className={`w-5 h-5 ${isCollapsed ? 'mb-1' : 'mr-3'}`} />
                            <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>My Tasks</span>
                        </Link>
                    </li>
                    {hasPermission('stats:view:own') && (
                        <li className="mb-2 w-full">
                            <Link to="/stats" title={isCollapsed ? "HR Dashboard" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px] text-center' : 'items-center p-2'} rounded-md hover:bg-secondary ${location.pathname.startsWith('/stats') ? 'bg-secondary' : ''} transition-all`}>
                                <SettingsIcon className={`w-5 h-5 text-cyan-500 dark:text-cyan-400 ${isCollapsed ? 'mb-1' : 'mr-3'}`} />
                                <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>HR Dashboard</span>
                            </Link>
                        </li>
                    )}
                    {hasPermission('leads:view:all') && (
                        <li className="mb-2 w-full">
                            <Link to="/marketing" title={isCollapsed ? "Sales Intel" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px] text-center' : 'items-center p-2'} rounded-md hover:bg-secondary ${location.pathname.startsWith('/marketing') ? 'bg-secondary' : ''} transition-all`}>
                                <ShieldCheckIcon className={`w-5 h-5 text-blue-500 dark:text-blue-400 ${isCollapsed ? 'mb-1' : 'mr-3'}`} />
                                <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>Sales Intel</span>
                            </Link>
                        </li>
                    )}
                    {hasPermission('brand:manage') && (
                        <li className="mb-2 w-full">
                            <Link to="/brand" title={isCollapsed ? "Brand Hub" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px] text-center' : 'items-center p-2'} rounded-md hover:bg-secondary ${location.pathname.startsWith('/brand') ? 'bg-secondary' : ''} transition-all`}>
                                <PaletteIcon className={`w-5 h-5 text-purple-500 dark:text-purple-400 ${isCollapsed ? 'mb-1' : 'mr-3'}`} />
                                <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>Brand Hub</span>
                            </Link>
                        </li>
                    )}
                    {/* Charlie (Manager) specific features */}
                    {hasPermission('user:manage:team') && (
                        <>
                            <li className="mb-2 w-full">
                                <Link to="/approvals" title={isCollapsed ? "Approvals" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px] text-center' : 'items-center p-2'} rounded-md hover:bg-secondary ${location.pathname.startsWith('/approvals') ? 'bg-secondary' : ''} transition-all`}>
                                    <CheckCircleIcon className={`w-5 h-5 text-indigo-500 dark:text-indigo-400 ${isCollapsed ? 'mb-1' : 'mr-3'}`} />
                                    <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>Approvals</span>
                                </Link>
                            </li>
                            <li className="mb-2 w-full">
                                <Link to="/nexus" title={isCollapsed ? "Nexus Command" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px] text-center' : 'items-center p-2'} rounded-md hover:bg-secondary ${location.pathname.startsWith('/nexus') ? 'bg-secondary' : ''} transition-all`}>
                                    <LayoutGridIcon className={`w-5 h-5 text-amber-500 dark:text-amber-400 ${isCollapsed ? 'mb-1' : 'mr-3'}`} />
                                    <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>Nexus Command</span>
                                </Link>
                            </li>
                            <li className="mb-2 w-full">
                                <Link to="/team" title={isCollapsed ? "Team Management" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px] text-center' : 'items-center p-2'} rounded-md hover:bg-secondary ${location.pathname.startsWith('/team') ? 'bg-secondary' : ''} transition-all`}>
                                    <UserIcon className={`w-5 h-5 text-amber-500 dark:text-amber-400 ${isCollapsed ? 'mb-1' : 'mr-3'}`} />
                                    <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>Team Management</span>
                                </Link>
                            </li>
                        </>
                    )}
                    {(isAdmin || hasPermission('user:manage') || user?.role?.toLowerCase() === 'admin' || user?.role?.toLowerCase() === 'system_admin') && (
                         <li className="mb-2 w-full">
                            <Link to="/admin" title={isCollapsed ? "Admin Control" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px] text-center' : 'items-center p-2'} rounded-md hover:bg-secondary ${location.pathname.startsWith('/admin') ? 'bg-secondary' : ''} transition-all`}>
                                <SettingsIcon className={`w-5 h-5 text-rose-500 dark:text-rose-400 ${isCollapsed ? 'mb-1' : 'mr-3'}`} />
                                <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>Admin Control</span>
                            </Link>
                        </li>
                    )}
                </ul>
                <div className={`p-4 border-t border-border flex flex-col ${isCollapsed ? 'items-center' : ''}`}>
                    <div className="mb-4 w-full">
                        <Link to="/landing" title={isCollapsed ? "Website" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px] text-center' : 'items-center p-2'} rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors`}>
                            <LayoutGridIcon className={`w-5 h-5 ${isCollapsed ? 'mb-1' : 'mr-3'}`} />
                            <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>Website</span>
                        </Link>
                    </div>
                   <Link to="/settings" title={isCollapsed ? "Profile" : undefined} className={`flex ${isCollapsed ? 'flex-col items-center justify-center mb-4 text-center' : 'items-center mb-4 p-2 -mx-2'} rounded-md hover:bg-secondary transition-colors group`}>
                       <UserAvatar name={user?.name || ''} role={user?.role} className={`w-10 h-10 ${isCollapsed ? 'mb-1' : 'mr-3'} group-hover:ring-2 ring-primary/20 transition-all`} />
                       {!isCollapsed && (
                           <div className="overflow-hidden flex-1">
                               <p className="font-semibold truncate leading-tight">{user?.name}</p>
                               <div className="flex items-center gap-2 mt-1">
                                   <p className="text-[10px] text-muted-foreground truncate max-w-[100px]">{user?.email}</p>
                                   <div className="px-1.5 py-0.5 bg-indigo-500 text-white text-[7px] font-bold rounded uppercase shrink-0">
                                       {user?.role}
                                   </div>
                               </div>
                           </div>
                       )}
                   </Link>
                   <button onClick={logout} title={isCollapsed ? "Logout" : undefined} className={`w-full flex ${isCollapsed ? 'flex-col items-center justify-center p-2 text-[10px]' : 'items-center justify-center p-2'} rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-all`}>
                       <LogOutIcon className={`w-5 h-5 ${isCollapsed ? 'mb-1' : 'mr-2'}`} />
                       <span className={`${isCollapsed ? 'leading-tight' : 'truncate'}`}>Logout</span>
                   </button>
                </div>
            </nav>
            {isSidebarOpen && <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setIsSidebarOpen(false)}></div>}
            <main id="main-content" className={`flex-1 flex flex-col ${location.pathname === '/brand' ? 'h-screen overflow-hidden' : 'overflow-y-auto overscroll-contain'} bg-background pb-16 md:pb-0`}>
                {/* Mobile Header */}
                <header className="md:hidden flex items-center justify-between p-6 border-b border-border bg-background/80 backdrop-blur z-30 sticky top-0">
                    <LiveClock />
                    <UserAvatar name={user?.name || ''} role={user?.role} className="w-10 h-10 ring-2 ring-primary/20" />
                </header>

                {/* Desktop Top Bar */}
                <header className="hidden md:flex items-center justify-end p-6 border-b border-border bg-background/60 backdrop-blur sticky top-0 z-30 h-20">
                    <LiveClock />
                </header>
                
                <div className={`flex-1 ${location.pathname === '/brand' || location.pathname === '/approvals' ? 'p-0 overflow-hidden' : 'p-4 md:p-8'}`}>
                    {children}
                </div>
            </main>

            {/* Mobile Bottom Navigation Bar */}
            <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-card border-t border-border flex justify-around items-center z-50 px-2 pb-safe">
                <Link to="/dashboard" className={`flex flex-col items-center justify-center p-2 rounded-lg ${location.pathname === '/dashboard' ? 'text-primary' : 'text-muted-foreground'}`}>
                    <LayoutGridIcon className="w-6 h-6" />
                    <span className="text-[10px] mt-1">Home</span>
                </Link>
                
                {hasPermission('leads:view:all') && (
                    <Link to="/marketing" className={`flex flex-col items-center justify-center p-2 rounded-lg ${location.pathname.startsWith('/marketing') ? 'text-primary' : 'text-muted-foreground'}`}>
                        <ShieldCheckIcon className="w-6 h-6 text-blue-500 dark:text-blue-400" />
                        <span className="text-[10px] mt-1">Leads</span>
                    </Link>
                )}

                {hasPermission('leads:view:all') && (
                    <Link to="/sales-cart" className={`flex flex-col items-center justify-center p-2 rounded-lg ${location.pathname.startsWith('/sales-cart') ? 'text-primary' : 'text-muted-foreground'}`}>
                         {/* TODO: Add ShoppingCartIcon */}
                        <div className="relative">
                            <MenuIcon className="w-6 h-6 rotate-90 text-blue-500 dark:text-blue-400" /> {/* Temporary Icon */}
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
