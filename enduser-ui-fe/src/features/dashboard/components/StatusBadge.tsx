import React from 'react';
import { TaskStatus } from '../../../types';

interface StatusBadgeProps {
  status: TaskStatus;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const s = (status || 'todo').toLowerCase();
  const styles: Record<string, string> = {
    todo: 'bg-gray-200 text-gray-800',
    doing: 'bg-blue-200 text-blue-800',
    done: 'bg-green-200 text-green-800',
    review: 'bg-purple-200 text-purple-800',
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${styles[s] || 'bg-gray-100'}`}>
      {status}
    </span>
  );
};
