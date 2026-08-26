import React, { useState, useEffect } from 'react';
import { SunIcon, MoonIcon } from './Icons.tsx';

interface ThemeToggleProps {
    className?: string;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ className }) => {
    const [isDarkMode, setIsDarkMode] = useState(() => {
        if (typeof window !== 'undefined' && typeof localStorage !== 'undefined' && localStorage.theme === 'dark') return true;
        if (typeof window !== 'undefined' && typeof localStorage !== 'undefined' && !('theme' in localStorage) && window.matchMedia?.('(prefers-color-scheme: dark)')?.matches) return true;
        return false;
    });

    useEffect(() => {
        if (isDarkMode) {
            document.documentElement.classList.add('dark');
            if (typeof localStorage !== 'undefined') localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            if (typeof localStorage !== 'undefined') localStorage.setItem('theme', 'light');
        }
    }, [isDarkMode]);

    const buttonClasses = className ?? "p-2 rounded-md hover:bg-secondary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

    return (
        <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className={buttonClasses}
            aria-label={isDarkMode ? "Switch to light theme" : "Switch to dark theme"}
            title={isDarkMode ? "Switch to light theme" : "Switch to dark theme"}
            aria-pressed={isDarkMode}
        >
            {isDarkMode ? <SunIcon className="w-5 h-5" /> : <MoonIcon className="w-5 h-5" />}
        </button>
    );
};

export default ThemeToggle;
