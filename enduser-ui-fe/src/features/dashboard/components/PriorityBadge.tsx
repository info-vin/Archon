import React from 'react';
import { TaskPriority } from '../../../types';

interface PriorityBadgeProps {
  priority: TaskPriority;
  variant?: 'badge' | 'indicator' | 'stripe';
}

const config: Record<string, { dot: string; text: string; bg: string; stripe: string }> = {
  high: { dot: 'bg-red-500', text: 'text-red-700', bg: 'bg-red-50', stripe: 'bg-red-500' },
  medium: { dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50', stripe: 'bg-amber-500' },
  low: { dot: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50', stripe: 'bg-green-500' },
  critical: { dot: 'bg-purple-600', text: 'text-purple-700', bg: 'bg-purple-50', stripe: 'bg-purple-600' },
};

// ⚡ Bolt Optimization:
// Wrapped PriorityBadge in React.memo to prevent unnecessary re-renders in list views (ListView, TableView, KanbanView).
// Since this component is purely presentational and relies on primitive props (priority string),
// memoization reduces CPU overhead (e.g., repeated .toLowerCase() and .replace() calls) when parent state updates.
export const PriorityBadge: React.FC<PriorityBadgeProps> = React.memo(({ priority, variant = 'badge' }) => {
  const p = (priority || 'low').toLowerCase();
  
  const style = config[p] || { dot: 'bg-gray-400', text: 'text-gray-700', bg: 'bg-gray-100', stripe: 'bg-gray-400' };

  if (variant === 'stripe') return <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${style.stripe}`} />;
  if (variant === 'indicator') return <span className={`${style.text.replace('700', '500')} mr-2`}>●</span>;
  
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${style.bg} ${style.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
      {priority}
    </span>
  );
});
