import React, { useEffect, useState } from 'react';
import { api } from '../../../services/api';
import { SystemOverview, AiUsageStats } from '../../../types';
import { XIcon, RefreshCwIcon } from '../../../components/Icons';

export const SystemHealthDashboard: React.FC = () => {
    const [overview, setOverview] = useState<SystemOverview | null>(null);
    const [aiStats, setAiStats] = useState<AiUsageStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [ov, ai] = await Promise.all([
                api.getSystemOverview(),
                api.getAiUsage()
            ]);
            setOverview(ov);
            setAiStats(ai);
        } catch (err: any) {
            setError(err.message || "Failed to load system health data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    if (loading) return (
        <div className="flex justify-center items-center h-64">
            <RefreshCwIcon className="animate-spin w-8 h-8 text-indigo-500" />
            <span className="ml-2 text-indigo-500 font-medium">Running Diagnostics...</span>
        </div>
    );

    if (error) return (
        <div className="p-6 bg-red-50 text-red-700 rounded-xl border border-red-200 flex items-center">
            <XIcon className="w-6 h-6 mr-3" />
            <div>
                <h3 className="font-bold">System Probe Failed</h3>
                <p className="text-sm">{error}</p>
                <button onClick={fetchData} className="mt-2 text-xs font-bold underline hover:text-red-900">Retry</button>
            </div>
        </div>
    );

    if (!overview || !aiStats) return null;

    return (
        <div className="space-y-6">
            {/* Top Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatusCard 
                    title="RAG Health" 
                    status={overview.status === 'healthy' ? 'good' : 'bad'}
                    value={overview.rag.status.toUpperCase()}
                    subtext={overview.rag.details?.errors ? `${overview.rag.details.errors.length} errors` : 'All systems nominal'}
                />
                <StatusCard 
                    title="Error Rate (24h)" 
                    status={overview.errors_24h > 0 ? 'warning' : 'good'}
                    value={overview.errors_24h.toString()}
                    subtext="Critical backend exceptions"
                />
                <StatusCard 
                    title="Active Agents" 
                    status="neutral"
                    value={overview.active_agents.length.toString()}
                    subtext={overview.active_agents.join(', ')}
                />
                <StatusCard 
                    title="Token Cost (24h)" 
                    status={overview.cost_24h > 10 ? 'warning' : 'neutral'}
                    value={`$${overview.cost_24h.toFixed(4)}`}
                    subtext={aiStats.is_real_data ? "Real-time usage" : "Estimated"}
                />
            </div>

            {/* Detailed Sections */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Cost Analysis */}
                <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                    <h3 className="text-lg font-bold mb-4">AI Cost Analysis (30 Days)</h3>
                    {aiStats.daily_costs && aiStats.daily_costs.length > 0 ? (
                        <div className="space-y-3">
                            {aiStats.daily_costs.slice(0, 5).map(day => (
                                <div key={day.date} className="flex justify-between items-center text-sm border-b border-border pb-2 last:border-0">
                                    <span className="font-mono text-muted-foreground">{day.date}</span>
                                    <div className="flex flex-col items-end">
                                        <span className="font-bold">${day.cost.toFixed(4)}</span>
                                        <span className="text-xs text-muted-foreground">{day.request_count} reqs • {day.models.length} models</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-muted-foreground italic">
                            No cost data recorded yet.
                        </div>
                    )}
                </div>

                {/* Agent Status */}
                <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                    <h3 className="text-lg font-bold mb-4">Agent Status</h3>
                    <div className="space-y-4">
                        <AgentRow name="Clockwork" role="Scheduler & Log Patrol" status="active" />
                        <AgentRow name="Sentinel" role="Business Logic Guard" status="active" />
                        <AgentRow name="Librarian" role="RAG Indexer" status="active" />
                        <AgentRow name="DevBot" role="Auto-Repair" status="standby" />
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatusCard: React.FC<{title: string, value: string, subtext: string, status: 'good'|'bad'|'warning'|'neutral'}> = ({title, value, subtext, status}) => {
    const colors = {
        good: 'bg-green-50 text-green-700 border-green-200',
        bad: 'bg-red-50 text-red-700 border-red-200',
        warning: 'bg-amber-50 text-amber-700 border-amber-200',
        neutral: 'bg-card text-foreground border-border'
    };
    
    return (
        <div className={`p-4 rounded-xl border ${colors[status]} shadow-sm flex flex-col`}>
            <span className="text-xs font-bold uppercase tracking-wider opacity-70 mb-1">{title}</span>
            <span className="text-2xl font-bold mb-1">{value}</span>
            <span className="text-xs opacity-80 truncate">{subtext}</span>
        </div>
    );
};

const AgentRow: React.FC<{name: string, role: string, status: 'active'|'standby'|'offline'}> = ({name, role, status}) => (
    <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${status === 'active' ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
            <div>
                <div className="font-bold text-sm">{name}</div>
                <div className="text-xs text-muted-foreground">{role}</div>
            </div>
        </div>
        <span className="text-xs font-mono uppercase bg-muted px-2 py-1 rounded">{status}</span>
    </div>
);
