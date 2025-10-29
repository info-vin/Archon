import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../../contexts/useTheme';
interface ThemeToggleProps {
  accentColor?: 'purple' | 'green' | 'pink' | 'blue';
}
export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  accentColor = 'blue'
}) => {
  const {
    theme,
    setTheme
  } = useTheme();
  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };
  import { accentColorMap } from '@/features/ui/primitives/accent-colors';
  return <button onClick={toggleTheme} className={`
        relative p-2 rounded-md backdrop-blur-md 
        bg-gradient-to-b ${accentColorMap[accentColor].bg}
        border ${accentColorMap[accentColor].border} ${accentColorMap[accentColor].hover}
        ${accentColorMap[accentColor].text}
        shadow-[0_0_10px_rgba(0,0,0,0.05)] dark:shadow-[0_0_10px_rgba(0,0,0,0.3)]
        transition-all duration-300 flex items-center justify-center
      `} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
      {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>;
};