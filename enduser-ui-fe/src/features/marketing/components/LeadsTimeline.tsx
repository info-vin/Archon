import React from 'react';
import { CheckCircleIcon, ClockIcon, MapPinIcon, UserIcon } from '@/components/Icons';

// PERFORMANCE: Hoist Intl.DateTimeFormat to avoid expensive instantiations inside the render loop
const dateFormatter = new Intl.DateTimeFormat();
const safeFormatTimelineDate = (dateVal: any) => {
    const d = new Date(dateVal);
    return isNaN(d.getTime()) ? 'Invalid Date' : dateFormatter.format(d);
};

interface TimelineEvent {
    id: string;
    type: 'creation' | 'interaction' | 'status_change' | 'visit';
    title: string;
    description: string;
    timestamp: string;
    user?: string;
}

interface LeadsTimelineProps {
    events: TimelineEvent[];
}

export const LeadsTimeline: React.FC<LeadsTimelineProps> = ({ events }) => {
    // Sort events by date descending
    // PERFORMANCE: Pre-calculate timestamps and useMemo to prevent sorting on every render
    const sortedEvents = React.useMemo(() => {
        const timestamps = new Map<TimelineEvent, number>();
        for (const e of events) {
            timestamps.set(e, new Date(e.timestamp).getTime());
        }
        return [...events].sort((a, b) => (timestamps.get(b) ?? 0) - (timestamps.get(a) ?? 0));
    }, [events]);

    return (
        <div className="relative pl-6 border-l-2 border-gray-200 space-y-8 my-6">
            {sortedEvents.map((event) => {
                let Icon = UserIcon;
                let colorClass = "bg-gray-100 text-gray-500";

                if (event.type === 'creation') {
                    Icon = CheckCircleIcon;
                    colorClass = "bg-green-100 text-green-600";
                } else if (event.type === 'visit') {
                    Icon = MapPinIcon;
                    colorClass = "bg-indigo-100 text-indigo-600";
                } else if (event.type === 'status_change') {
                    Icon = ClockIcon;
                    colorClass = "bg-amber-100 text-amber-600";
                }

                return (
                    <div key={event.id} className="relative group">
                        {/* Dot */}
                        <div className={`absolute -left-[33px] top-0 w-8 h-8 rounded-full border-4 border-white shadow-sm flex items-center justify-center ${colorClass}`}>
                            <Icon className="w-4 h-4" />
                        </div>

                        {/* Content */}
                        <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-1">
                                <h4 className="font-bold text-gray-800">{event.title}</h4>
                                <span className="text-xs text-gray-400 font-mono">
                                {safeFormatTimelineDate(event.timestamp)}
                                </span>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{event.description}</p>
                            {event.user && (
                                <div className="flex items-center gap-1 text-xs text-gray-400">
                                    <UserIcon className="w-3 h-3" />
                                    {event.user}
                                </div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
};
