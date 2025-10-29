import React from 'react';
import { accentColorMap } from '@/features/ui/primitives/accent-colors';
export const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement> & {
  accentColor?: 'purple' | 'green' | 'pink' | 'blue';
  icon?: React.ReactNode;
  label?: string;
}> = ({
  accentColor = 'purple',
  icon,
  label,
  className = '',
  ...props
}) => {
  return <div className="w-full">
      {label && <label className="block text-gray-600 dark:text-zinc-400 text-sm mb-1.5">
          {label}
        </label>}
      <div className={`
        flex items-center backdrop-blur-md bg-gradient-to-b dark:from-white/10 dark:to-black/30 from-white/80 to-white/60 
        border dark:border-zinc-800/80 border-gray-200 rounded-md px-3 py-2
        transition-all duration-200 ${accentColorMap[accentColor]}
      `}>
        {icon && <div className="mr-2 text-gray-500 dark:text-zinc-500">{icon}</div>}
        <input className={`
            w-full bg-transparent text-gray-800 dark:text-white placeholder:text-gray-400 dark:placeholder:text-zinc-600
            focus:outline-none ${className}
          `} {...props} />
      </div>
    </div>;
};