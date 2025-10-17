import React, { useState, useEffect } from 'react';
import { SunIcon, MoonIcon } from './Icons.tsx';

interface ThemeToggleProps {
    className?: string;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ className }) => {
    const [isDarkMode, setIsDarkMode] = useState(() => {
        if (localStorage.theme === 'dark') return true;
        if (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches) return true;
        return false;
    });

    useEffect(() => {
        if (isDarkMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [isDarkMode]);

    const buttonClasses = className ?? "p-2 rounded-md hover:bg-secondary transition-colors";

    return (
        <button onClick={() => setIsDarkMode(!isDarkMode)} className={buttonClasses} aria-label="Toggle theme">
            {isDarkMode ? <SunIcon className="w-5 h-5" /> : <MoonIcon className="w-5 h-5" />}
        </button>
    );
};

export default ThemeToggle;
