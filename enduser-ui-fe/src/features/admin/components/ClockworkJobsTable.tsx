import React, { useState } from 'react';
import { api } from '@/services/api';
import { ClockIcon } from '@/components/Icons';

const PlayIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <polygon points="5 3 19 12 5 21 5 3"/>
    </svg>
);

interface JobSnapshot {
    id: string;
    name: string;
    type: string;
    last_run: string | null;
    next_run: string | null;
    status: string;
}

interface ClockworkJobsTableProps {
    jobs: JobSnapshot[];
    onJobTriggered: () => void;
}

export const ClockworkJobsTable: React.FC<ClockworkJobsTableProps> = ({ jobs, onJobTriggered }) => {
    const [triggeringId, setTriggeringId] = useState<string | null>(null);

    const handleRunNow = async (jobId: string) => {
        setTriggeringId(jobId);
        try {
            await api.triggerClockworkJob(jobId);
            // Artificial delay to let the UI show loading state
            setTimeout(() => {
                setTriggeringId(null);
                onJobTriggered(); // Refresh dashboard
            }, 1000);
        } catch (error: any) {
            alert(`Failed to trigger job: ${error.message}`);
            setTriggeringId(null);
        }
    };

    const formatTime = (isoString: string | null) => {
        if (!isoString) return '-';
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const getTypeColor = (type: string) => {
        if (type === 'stateless_patrol') return 'bg-blue-100 text-blue-700 border-blue-200';
        if (type === 'stateful_biweekly') return 'bg-purple-100 text-purple-700 border-purple-200';
        return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    };

    return (
        <div className="mt-4 border border-border rounded-xl overflow-hidden bg-background">
            <div className="bg-muted/30 px-4 py-2 border-b border-border flex items-center gap-2">
                <ClockIcon className="w-4 h-4 text-indigo-500" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Clockwork Schedule Manifesto (Phase 5.1.15)</h4>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="bg-muted/10">
                        <tr>
                            <th className="px-4 py-2 text-xs font-semibold text-muted-foreground">Job Name</th>
                            <th className="px-4 py-2 text-xs font-semibold text-muted-foreground">Type</th>
                            <th className="px-4 py-2 text-xs font-semibold text-muted-foreground">Last Run</th>
                            <th className="px-4 py-2 text-xs font-semibold text-muted-foreground">Next Run</th>
                            <th className="px-4 py-2 text-xs font-semibold text-muted-foreground text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {jobs.map((job) => (
                            <tr key={job.id} className="hover:bg-muted/5 transition-colors">
                                <td className="px-4 py-2 font-medium text-foreground text-xs">
                                    <div className="flex items-center gap-2">
                                        <div className={`w-1.5 h-1.5 rounded-full ${job.status === 'scheduled' ? 'bg-amber-400' : 'bg-green-500'}`} />
                                        {job.name}
                                    </div>
                                </td>
                                <td className="px-4 py-2">
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded border uppercase tracking-tighter ${getTypeColor(job.type)}`}>
                                        {job.type.replace('_', ' ')}
                                    </span>
                                </td>
                                <td className="px-4 py-2 text-xs text-muted-foreground font-mono">
                                    {formatTime(job.last_run)}
                                </td>
                                <td className="px-4 py-2 text-xs text-muted-foreground font-mono">
                                    {formatTime(job.next_run)}
                                </td>
                                <td className="px-4 py-2 text-right">
                                    <button 
                                        onClick={() => handleRunNow(job.id)}
                                        disabled={triggeringId === job.id}
                                        className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-bold uppercase rounded bg-indigo-50 text-indigo-600 hover:bg-indigo-100 transition-colors disabled:opacity-50"
                                    >
                                        {triggeringId === job.id ? (
                                            <>
                                                <ClockIcon className="w-3 h-3 animate-spin" />
                                                Running
                                            </>
                                        ) : (
                                            <>
                                                <PlayIcon className="w-3 h-3" />
                                                Run Now
                                            </>
                                        )}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
