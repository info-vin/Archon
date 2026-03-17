import React from 'react';
import { FileTextIcon, ClockIcon } from '../../../../components/Icons';

export interface NexusHeaderProps {
    onOpenSpec: () => void;
}

export const NexusHeader: React.FC<NexusHeaderProps> = ({ onOpenSpec }) => {
    return (
        <header className="flex justify-between items-end mb-8">
            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight flex items-center gap-3">Manager Nexus</h1>
                <p className="text-sm text-gray-500 mt-1 font-medium">Command & Control v7.1</p>
            </div>
            <div className="flex items-center gap-4">
                <button
                    onClick={onOpenSpec}
                    className="flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-600 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-amber-100 transition-all active:scale-95 border border-amber-100"
                >
                    <FileTextIcon className="w-4 h-4" />
                    View Specs
                </button>
                <div className="flex gap-2 text-xs font-bold text-gray-400 bg-white px-3 py-1.5 rounded-lg border border-gray-100 shadow-sm">
                    <ClockIcon className="w-4 h-4" />
                    <span>Dynamic Refresh</span>
                </div>
            </div>
        </header>
    );
};
