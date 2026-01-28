
import React from 'react';
import { TableIcon } from '../Icons';

interface EmptyStateProps {
    title: string;
    description: string;
    actionLabel?: string;
    onAction?: () => void;
    icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ 
    title, 
    description, 
    actionLabel, 
    onAction, 
    icon = <TableIcon className="w-12 h-12 text-gray-300" /> 
}) => {
    return (
        <div className="flex flex-col items-center justify-center p-12 text-center bg-gray-50/50 rounded-2xl border-2 border-dashed border-gray-200">
            <div className="mb-4 p-4 bg-white rounded-full shadow-sm">
                {icon}
            </div>
            <h3 className="text-lg font-bold text-gray-800">{title}</h3>
            <p className="text-sm text-gray-500 mt-1 max-w-xs mx-auto">{description}</p>
            {actionLabel && onAction && (
                <button 
                    onClick={onAction}
                    className="mt-6 px-6 py-2 bg-white border border-gray-300 rounded-lg text-sm font-bold text-gray-700 hover:bg-gray-50 transition-all shadow-sm active:scale-95"
                >
                    {actionLabel}
                </button>
            )}
        </div>
    );
};
