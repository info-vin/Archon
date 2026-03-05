import React from 'react';

export interface StatusBadgeProps {
  level: 'full' | 'partial' | 'limited';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ level, className = '' }) => {
  const badgeConfig = {
    full: { color: 'bg-green-500', text: 'Archon Ready', icon: '✓' },
    partial: { color: 'bg-orange-500', text: 'Partial Support', icon: '◐' },
    limited: { color: 'bg-red-500', text: 'Limited', icon: '◯' }
  };

  const config = badgeConfig[level];

  return (
    <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium text-white ${config.color} ${className}`}>
      <span className="mr-1">{config.icon}</span>
      {config.text}
    </div>
  );
};
