import React from 'react';
import { ActivityIcon } from '../../../../components/Icons';

export const NexusEmptyState: React.FC = () => {
    return (
        <div className="p-12 text-center text-gray-400 bg-white rounded-3xl border border-dashed border-gray-200">
            <ActivityIcon className="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p>Select a metric above to view details.</p>
        </div>
    );
};
