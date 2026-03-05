import React from 'react';

export interface DimensionBadgeProps {
  dimensions: number;
  className?: string;
}

export const DimensionBadge: React.FC<DimensionBadgeProps> = ({ dimensions, className = '' }) => {
  let colorClass = 'bg-blue-600';
  
  if (dimensions >= 3072) {
    colorClass = 'bg-purple-600';
  } else if (dimensions >= 1536) {
    colorClass = 'bg-indigo-600';
  } else if (dimensions >= 1024) {
    colorClass = 'bg-green-600';
  } else if (dimensions >= 768) {
    colorClass = 'bg-yellow-600';
  } else {
    colorClass = 'bg-gray-600';
  }

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium text-white ${colorClass} ${className}`}>
      {dimensions}D
    </span>
  );
};
