import React, { useState, useEffect } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { MenuIcon, XIcon } from '../../components/Icons.tsx';
import ThemeToggle from '../../components/ThemeToggle.tsx';
import { BrandLogo } from '../../components/BrandLogo.tsx';
import { useAuth } from '../../hooks/useAuth.tsx';

const PublicLayout: React.FC = () => {
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isMobileMenuOpen]);

  const navLinks = [
    { name: 'Home', path: '/landing' },
    { name: 'Solutions', path: '/solutions' },
    { name: 'Blog', path: '/blog' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <header className="sticky top-0 z-40 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-14 max-w-screen-2xl items-center justify-between px-4">
          <Link to="/landing" className="mr-6 flex items-center space-x-2">
            <BrandLogo className="w-8 h-8" />
          </Link>
          <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
            {navLinks.map(link => (
              <Link
                key={link.name}
                to={link.path}
                className={`transition-colors hover:text-primary ${location.pathname === link.path ? 'text-primary' : 'text-muted-foreground'}`}
              >
                {link.name}
              </Link>
            ))}
          </nav>
          <div className="flex items-center justify-end space-x-2">
            <ThemeToggle />
            {isAuthenticated ? (
                <Link
                    to="/dashboard"
                    className="hidden md:inline-flex px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-semibold hover:bg-primary/90 transition-colors"
                >
                    Go to Dashboard
                </Link>
            ) : (
                <Link
                to="/auth"
                className="hidden md:inline-flex px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-semibold hover:bg-primary/90 transition-colors"
                >
                Login
                </Link>
            )}
            
            <button 
              className="md:hidden p-2"
              onClick={() => setIsMobileMenuOpen(true)}
              aria-label="Open menu"
            >
                <MenuIcon className="h-6 w-6" />
            </button>
          </div>
        </div>
      </header>
      
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
          role="dialog"
          aria-modal="true"
        >
          <div 
            className="fixed top-0 right-0 h-full w-full max-w-xs bg-card p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <BrandLogo className="w-8 h-8" />
              <button onClick={() => setIsMobileMenuOpen(false)} className="p-1 -mr-1" aria-label="Close menu">
                <XIcon className="h-6 w-6" />
              </button>
            </div>
            <nav className="mt-6 flex flex-col space-y-1">
              {navLinks.map(link => (
                <Link
                  key={link.name}
                  to={link.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`block px-3 py-2 rounded-md text-lg font-medium transition-colors hover:text-primary ${location.pathname === link.path ? 'text-primary' : 'text-foreground'}`}
                >
                  {link.name}
                </Link>
              ))}
            </nav>
            <div className="mt-6 pt-6 border-t border-border">
                {isAuthenticated ? (
                     <Link
                     to="/dashboard"
                     onClick={() => setIsMobileMenuOpen(false)}
                     className="flex items-center justify-center w-full px-4 py-2 bg-primary text-primary-foreground rounded-md font-semibold hover:bg-primary/90 transition-colors"
                 >
                     Go to Dashboard
                 </Link>
                ) : (
                    <Link
                    to="/auth"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="flex items-center justify-center w-full px-4 py-2 bg-primary text-primary-foreground rounded-md font-semibold hover:bg-primary/90 transition-colors"
                >
                    Login
                </Link>
                )}
            </div>
          </div>
        </div>
      )}

      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="py-6 md:px-8 md:py-0 border-t border-border">
          <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row py-4 mx-auto">
              <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
                  Built for efficiency. Inspired by Vik and Arc.
              </p>
          </div>
      </footer>
    </div>
  );
};

export default PublicLayout;
