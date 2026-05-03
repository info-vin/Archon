import { XIcon } from '@/components/Icons.tsx';
import { LeadsTimeline } from './LeadsTimeline';
import { Lead } from './LeadsCardStack.tsx';

interface HistoryDrawerProps {
    lead: Lead;
    onClose: () => void;
}

export const LeadHistoryDrawer = ({ lead, onClose }: HistoryDrawerProps) => {
    // Mock History Data
    const mockEvents: any[] = [
        { id: '1', type: 'creation', title: 'Lead Identified', description: `Sourced from ${lead.source}`, timestamp: new Date(Date.now() - 86400000 * 2).toISOString() },
        { id: '2', type: 'status_change', title: 'Qualified', description: 'Matched ICP criteria', timestamp: new Date(Date.now() - 86400000).toISOString() },
    ];

    return (
         <div className="fixed inset-0 bg-black/60 z-[70] flex items-end justify-center sm:items-center p-0 sm:p-4 animate-in fade-in duration-200" onClick={onClose}>
            <div 
                className="bg-white w-full max-w-md rounded-t-2xl sm:rounded-2xl p-6 shadow-2xl animate-in slide-in-from-bottom-full sm:zoom-in-95 duration-300 max-h-[80vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-bold">Activity Timeline</h3>
                    <button onClick={onClose} aria-label="Close timeline" className="focus-visible:ring-2 focus-visible:ring-indigo-500 rounded-full outline-none"><XIcon className="w-5 h-5 text-gray-400" /></button>
                </div>
                <LeadsTimeline events={mockEvents} />
            </div>
        </div>
    );
};
