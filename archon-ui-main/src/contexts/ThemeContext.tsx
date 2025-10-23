import React, { useEffect, useState } from 'react';
import { ThemeContext, Theme } from './useTheme';

export const ThemeProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  // Read from localStorage immediately to avoid flash
  const [theme, setTheme] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    return savedTheme || 'dark';
  });
  useEffect(() => {
    // Apply theme class to document element
    const root = window.document.documentElement;

    // Tailwind v4: Only toggle .dark class, don't add .light
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // Save to localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);
  return <ThemeContext.Provider value={{
    theme,
    setTheme
  }}>
      {children}
    </ThemeContext.Provider>;
};