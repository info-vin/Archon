import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MenuIcon, XIcon, UserIcon, SettingsIcon, LogOutIcon, ShieldCheckIcon, LayoutGridIcon, PaletteIcon } from '../../components/Icons.tsx';
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

    return (
        <div className="flex h-screen bg-background text-foreground">
             <nav className={`fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border flex flex-col transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out md:relative md:translate-x-0`}>
                <div className="p-4 border-b border-border flex justify-between items-center bg-card/50 backdrop-blur">
                    <Link to="/dashboard" className="flex items-center transition-transform hover:scale-105 active:scale-95">
                        <BrandLogo className="w-8 h-8" />
                    </Link>
                     <button onClick={() => setIsSidebarOpen(false)} className="md:hidden p-1 hover:bg-secondary rounded-md" aria-label="Close sidebar">
                        <XIcon className="w-6 h-6" />
                    </button>
                </div>
                <ul className="flex-grow p-2">
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
                            <Link to="/team" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/team') ? 'bg-secondary' : ''}`}>
                                <UserIcon className="w-5 h-5 mr-3" />
                                Team Management
                            </Link>
                        </li>
                    )}
                    <li className="mb-2">
                        <Link to="/settings" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/settings') ? 'bg-secondary' : ''}`}>
                            <SettingsIcon className="w-5 h-5 mr-3" />
                            Settings
                        </Link>
                    </li>
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
                   <div className="flex items-center mb-4">
                       <UserAvatar name={user?.name || ''} className="w-10 h-10 mr-3" />
                       <div>
                           <p className="font-semibold">{user?.name}</p>
                           <p className="text-sm text-muted-foreground">{user?.email}</p>
                       </div>
                   </div>
                   <button onClick={logout} className="w-full flex items-center justify-center p-2 rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90">
                       <LogOutIcon className="w-5 h-5 mr-2" />
                       Logout
                   </button>
                </div>
            </nav>
            {isSidebarOpen && <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setIsSidebarOpen(false)}></div>}
            <main className="flex-1 flex flex-col overflow-y-auto bg-background">
                {/* Mobile Header */}
                <header className="md:hidden flex items-center justify-between p-4 border-b border-border bg-background/80 backdrop-blur">
                    <button onClick={() => setIsSidebarOpen(true)} aria-label="Open sidebar">
                        <MenuIcon className="h-6 w-6" />
                    </button>
                    <LiveClock />
                </header>

                {/* Desktop Top Bar (New) */}
                <header className="hidden md:flex items-center justify-end p-4 border-b border-border bg-background/60 backdrop-blur sticky top-0 z-30 h-16">
                    <LiveClock />
                </header>
                
                <div className="flex-1 p-4 md:p-8">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default MainLayout;
