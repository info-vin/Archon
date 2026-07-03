import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { SystemOverview, AiUsageStats } from '@/types';
import { XIcon, RefreshCwIcon, AlertTriangleIcon, ListIcon } from '@/components/Icons';
import TokenUsageTable, { TokenUsageDetail } from './TokenUsageTable';
import { ROIAnalyticsBadge } from './ROIAnalyticsBadge';
import { RAGPlayground } from './RAGPlayground';
import { AiResilienceWidget } from './AiResilienceWidget';
import { StatusCard } from './StatusCard';
import { AgentRow } from './AgentRow';
import { ClockworkJobsTable } from './ClockworkJobsTable';


export const SystemHealthDashboard: React.FC = () => {
    const [overview, setOverview] = useState<SystemOverview | null>(null);
    const [aiStats, setAiStats] = useState<AiUsageStats | null>(null);
    const [connectivityLogs, setConnectivityLogs] = useState<any[]>([]);
    const [agentXp, setAgentXp] = useState<any[]>([]);
    const [recentUsage, setRecentUsage] = useState<TokenUsageDetail[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            // Physically protect against partial API failures (404/500)
            const safeFetch = async (promise: Promise<any>) => {
                try { return await promise; } 
                catch (e) { console.warn("Partial Dashboard Fetch Failure:", e); return null; }
            };

            const [ov, ai, logs, xp, recent] = await Promise.all([
                safeFetch(api.getSystemOverview()),
                safeFetch(api.getAiUsage()),
                safeFetch(api.getConnectivityLogs()),
                safeFetch(api.getAgentXPStats()),
                safeFetch(api.getRecentTokenUsage())
            ]);
            
            if (ov) setOverview(ov);
            if (ai) setAiStats(ai);
            setConnectivityLogs(logs || []);
            setAgentXp(xp || []);
            setRecentUsage(recent || []);
            
            if (!ov && !ai) {
                throw new Error("Core health services are currently unreachable.");
            }
        } catch (err: any) {

            setError(err.message || "Failed to load system health data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    // PERFORMANCE: Precalculate lowercased agent names to prevent O(N*M) redundant string allocations during the render loop.
    const searchableAgentXpNames = React.useMemo(() => {
        return agentXp.map((x: any) => (x.name || '').toLowerCase());
    }, [agentXp]);

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

    return (
        <div className="space-y-6">
            {/* AI ROI & Cost Analytics (Phase 4.6.24 Realization) */}
            {aiStats && <ROIAnalyticsBadge data={aiStats as any} />}

            {/* Top Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatusCard 
                    title="RAG Health" 
                    status={overview?.status === 'healthy' ? 'good' : 'bad'}
                    value={overview?.rag?.status?.toUpperCase() || 'UNKNOWN'}
                    subtext={overview?.rag?.details?.errors ? `${overview.rag.details.errors.length} errors` : 'All systems nominal'}
                />
                <StatusCard 
                    title="Error Rate (24h)" 
                    status={(overview?.errors_24h || 0) > 0 ? 'warning' : 'good'}
                    value={(overview?.errors_24h || 0).toString()}
                    subtext="Critical backend exceptions"
                />
                <StatusCard 
                    title="Active Agents" 
                    status="neutral"
                    value={(overview?.active_agents || []).filter((a: any) => a.status === 'active').length.toString()}
                    subtext={`${(overview?.active_agents || []).length} registered system entities`}
                />
                <StatusCard 
                    title="Token Cost (24h)" 
                    status={(overview?.cost_24h || 0) > 10 ? 'warning' : 'neutral'}
                    value={`$${(overview?.cost_24h || 0).toFixed(4)}`}
                    subtext={aiStats?.is_real_data ? "Real-time usage" : "Estimated"}
                />
            </div>

            {/* Detailed Sections */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Cost Analysis */}
                <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                    <h3 className="text-lg font-bold mb-4">AI Cost Analysis (30 Days)</h3>
                    {(aiStats?.daily_costs || []).length > 0 ? (
                        <div className="space-y-3">
                            {aiStats?.daily_costs?.slice(0, 5).map(day => (
                                <div key={day.date} className="flex justify-between items-center text-sm border-b border-border pb-2 last:border-0">
                                    <span className="font-mono text-muted-foreground">{day.date}</span>
                                    <div className="flex flex-col items-end">
                                        <span className="font-bold">${day.cost.toFixed(4)}</span>
                                        <span className="text-xs text-muted-foreground">{day.request_count} reqs • {(day.models || []).length} models</span>
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

                {/* Agent Status (SSOT Driven) */}
                <div className="space-y-6">
                    <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold">Agent Status & XP</h3>
                        </div>
                        <div className="space-y-4">
                            {(overview?.active_agents || []).map((agent: any) => {
                                const agentNameLower = (agent.name || '').toLowerCase();
                                const agentIdLower = (agent.id || '').toLowerCase();

                                // Physically align with backend SSOT (Phase 4.6.15)
                                // We find the data in agentXp which now contains total_cost and roi_ratio
                                const xpData = agentXp.find((_, i) =>
                                    searchableAgentXpNames[i] === agentNameLower ||
                                    (searchableAgentXpNames[i].includes(agentIdLower))
                                ) || { total_xp: 0, total_cost: 0, roi_ratio: 0, level: 'Intern' };
                                
                                return (
                                    <div key={agent.id} className="flex flex-col gap-2">
                                        <AgentRow 
                                            name={agent.name} 
                                            role={agent.role} 
                                            status={agent.status} 
                                            xpData={xpData}
                                            cost={xpData.total_cost}
                                            roi={xpData.roi_ratio.toString()}
                                            isActive={agent.status === 'active'}
                                        />
                                        {agent.id.toLowerCase() === 'clockwork' && agent.jobs_snapshot && (
                                            <ClockworkJobsTable 
                                                jobs={agent.jobs_snapshot} 
                                                onJobTriggered={fetchData} 
                                            />
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                    
                    <AiResilienceWidget />
                </div>
            </div>

            {/* Industrial RAG Playground (Phase 4.6.26 Realization) */}
            <RAGPlayground />

            {/* Recent Token Transactions (Restored Feature - Phase 4.6.23) */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                    <ListIcon className="w-5 h-5 text-indigo-500" />
                    <h3 className="text-lg font-bold">Recent Token Transactions</h3>
                </div>
                {recentUsage.length > 0 ? (
                    <TokenUsageTable details={recentUsage} />
                ) : (
                    <div className="text-center py-12 text-muted-foreground italic border-2 border-dashed border-border rounded-xl">
                        No recent transactions found in token_usage table.
                    </div>
                )}
            </div>

            {/* AI Connectivity Exceptions (Admin Maintenance View) */}
            <div className="bg-card p-6 rounded-2xl border border-red-100 shadow-sm border-l-4 border-l-red-500">
                <h3 className="text-lg font-bold mb-4 text-red-700 flex items-center gap-2">
                    <AlertTriangleIcon className="w-5 h-5" />
                    AI Connectivity Exception Log
                </h3>
                <div className="space-y-2">
                    {(connectivityLogs || []).map((log: any) => (
                        <div key={log.id} className="p-3 bg-red-50/50 rounded-xl border border-red-100 flex justify-between items-center text-xs group hover:bg-red-50 transition-colors">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="font-black text-red-600 uppercase tracking-tighter bg-red-100 px-1.5 py-0.5 rounded">{log.source}</span>
                                    <span className="text-[10px] text-gray-400 font-mono">{new Date(log.created_at).toLocaleString()}</span>
                                </div>
                                <p className="text-gray-700 font-medium">{log.message}</p>
                                {log.details?.model && <p className="text-[10px] text-red-400 mt-1 font-mono">Target Model: {log.details.model}</p>}
                            </div>
                            <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                                <button className="text-red-600 font-bold hover:underline" onClick={() => alert(JSON.stringify(log.details, null, 2))}>Inspect</button>
                            </div>
                        </div>
                    ))}
                    {(connectivityLogs || []).length === 0 && (
                        <div className="text-center py-12 text-gray-400 italic text-sm">
                            No connectivity exceptions detected in the last window.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
