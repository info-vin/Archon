import React from 'react';
export const Card: React.FC<React.HTMLAttributes<HTMLDivElement> & {
  children: React.ReactNode;
  accentColor?: 'purple' | 'green' | 'pink' | 'blue' | 'cyan' | 'orange' | 'none';
  variant?: 'default' | 'bordered';
}> = ({
  children,
  accentColor = 'none',
  variant = 'default',
  className = '',
  ...props
}) => {
  const variantClasses = {
    default: 'border',
    bordered: 'border'
  };
  return <div className={`
        relative p-4 rounded-md backdrop-blur-md
        bg-gradient-to-b from-white/80 to-white/60 dark:from-white/10 dark:to-black/30
        ${variantClasses[variant]} ${accentColorMap[accentColor].border}
        shadow-[0_10px_30px_-15px_rgba(0,0,0,0.1)] dark:shadow-[0_10px_30px_-15px_rgba(0,0,0,0.7)]
        hover:shadow-[0_15px_40px_-15px_rgba(0,0,0,0.2)] dark:hover:shadow-[0_15px_40px_-15px_rgba(0,0,0,0.9)]
        transition-all duration-300
        ${accentColor !== 'none' ? `
          before:content-[""] before:absolute before:top-[0px] before:left-[1px] before:right-[1px] before:h-[2px] 
          before:rounded-t-[4px]
          ${accentColorMap[accentColor].line} ${accentColorMap[accentColor].glow}
          after:content-[""] after:absolute after:top-0 after:left-0 after:right-0 after:h-16
          after:bg-gradient-to-b ${accentColorMap[accentColor].gradientFrom} ${accentColorMap[accentColor].gradientTo}
          after:rounded-t-md after:pointer-events-none
        ` : ''}
        ${className}
      `} {...props}>
      <div className="relative z-10">{children}</div>
    </div>;
};