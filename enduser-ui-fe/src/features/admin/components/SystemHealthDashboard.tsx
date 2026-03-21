import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { SystemOverview, AiUsageStats } from '@/types';
import { XIcon, RefreshCwIcon, AlertTriangleIcon } from '@/components/Icons';

export const SystemHealthDashboard: React.FC = () => {
    const [overview, setOverview] = useState<SystemOverview | null>(null);
    const [aiStats, setAiStats] = useState<AiUsageStats | null>(null);
    const [connectivityLogs, setConnectivityLogs] = useState<any[]>([]);
    const [agentXp, setAgentXp] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [ov, ai, logs, xp] = await Promise.all([
                api.getSystemOverview(),
                api.getAiUsage(),
                api.getConnectivityLogs().catch(() => []),
                api.getAgentXPStats().catch(() => [])
            ]);
            setOverview(ov);
            setAiStats(ai);
            setConnectivityLogs(Array.isArray(logs) ? logs : []);
            setAgentXp(Array.isArray(xp) ? xp : []);
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

    return (
        <div className="space-y-6">
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
                                const xpData = agentXp.find((x: any) => x.name.toLowerCase() === agent.name.toLowerCase()) || { total_xp: 0, level: 'Intern' };
                                // Calculate ROI based on token usage service (Phase 4.6.15)
                                const agentCost = (aiStats?.daily_costs || []).reduce((acc, curr) => acc + (curr.agent_costs?.[agent.name] || 0), 0);
                                const roi = agentCost > 0 ? (xpData.total_xp / agentCost).toFixed(2) : 'N/A';
                                
                                return (
                                    <AgentRow 
                                        key={agent.id}
                                        name={agent.name} 
                                        role={agent.role} 
                                        status={agent.status} 
                                        xpData={xpData}
                                        cost={agentCost}
                                        roi={roi}
                                        isActive={agent.status === 'active'}
                                    />
                                );
                            })}
                        </div>
                    </div>
                    
                    <AiResilienceWidget />
                </div>
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

const AiResilienceWidget: React.FC = () => {
    const [health, setHealth] = React.useState<import('../../../types').AiHealthStatus | null>(null);

    React.useEffect(() => {
        api.getAiHealth().then(setHealth).catch(console.error);
    }, []);

    if (!health) return null;

    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
            <h3 className="text-lg font-bold mb-4 flex items-center justify-between">
                <span>AI Resilience Matrix</span>
                <span className={`text-xs px-2 py-1 rounded uppercase ${health.status === 'healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {health.status}
                </span>
            </h3>
            <div className="space-y-3">
                {health.models.map(m => (
                    <div key={`${m.agent}-${m.model}`} className="flex justify-between items-center text-sm">
                        <div>
                            <div className="font-bold">{m.agent}</div>
                            <div className="text-xs text-muted-foreground font-mono">{m.model}</div>
                        </div>
                        <div className="flex items-center gap-2">
                            {m.latency_ms && <span className="text-xs text-muted-foreground">{m.latency_ms}ms</span>}
                            <div className={`w-2 h-2 rounded-full ${m.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
                        </div>
                    </div>
                ))}
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

const AgentRow: React.FC<{name: string, role: string, status: 'active'|'standby'|'offline', xpData: any, cost: number, roi: string, isActive: boolean}> = ({name, role, status, xpData, cost, roi, isActive}) => (
    <div className="flex justify-between items-center border-b border-border/50 pb-3 last:border-0 last:pb-0">
        <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
            <div>
                <div className="font-bold text-sm flex items-center gap-2">
                    {name}
                    {xpData.level && <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">{xpData.level}</span>}
                </div>
                <div className="text-xs text-muted-foreground flex items-center gap-2">
                    {role}
                    {cost > 0 && <span className="text-[10px] text-emerald-600 font-bold border-l border-border pl-2">${cost.toFixed(2)} spent</span>}
                </div>
            </div>
        </div>
        <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-2">
                <span className="text-[10px] font-black text-indigo-500 uppercase">ROI: {roi}</span>
                <span className="text-xs font-mono uppercase bg-muted px-2 py-1 rounded">{status}</span>
            </div>
            <span className="text-xs font-bold text-indigo-600 font-mono">{xpData.total_xp} XP</span>
        </div>
    </div>
);
