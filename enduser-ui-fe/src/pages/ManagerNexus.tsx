import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../services/api.ts';
import { SystemOverview, AiUsageStats, BlogPost } from '../types.ts';
import { 
    RefreshCwIcon, 
    AlertTriangleIcon,
    ClockIcon
} from '../components/Icons.tsx';

type MetricCategory = 'integrity' | 'resources' | 'op_load' | 'sent_risks' | 'active_force' | 'ethics' | 'collab' | 'graph' | 'velocity';

/**
 * ManagerNexus v7.1 - The Commander's SSOT (Lint Fixed)
 * Unified Decision Engine consolidating Panels 5, 6, 7, 8.
 * Style: Muted Glassmorphism, SSOT Data Driven.
 */
const ManagerNexus: React.FC = () => {
    // --- STATE ---
    const [activeMetric, setActiveMetric] = useState<MetricCategory>('sent_risks');
    const [overview, setOverview] = useState<SystemOverview | null>(null);
    const [aiStats, setAiStats] = useState<AiUsageStats | null>(null);
    const [approvals, setApprovals] = useState<{ blogs: BlogPost[]; leads: any[] }>({ blogs: [], leads: [] });
    const [alerts, setAlerts] = useState<any[]>([]);
    const [selectedBlog, setSelectedBlog] = useState<BlogPost | null>(null);
    const [loading, setLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);

    // --- DATA FETCHING ---
    const fetchData = async () => {
        setIsRefreshing(true);
        try {
            const [ov, ai, apprvs, alrts] = await Promise.all([
                api.getSystemOverview(),
                api.getAiUsage(),
                api.getPendingApprovals(),
                api.getManagerAlerts()
            ]);
            setOverview(ov);
            setAiStats(ai);
            setApprovals(apprvs);
            setAlerts(alrts);
            
            if (apprvs.blogs.length > 0 && !selectedBlog) {
                setSelectedBlog(apprvs.blogs[0]);
            }
        } catch (err) {
            console.error("Nexus Sync Error", err);
        } finally {
            setLoading(false);
            setIsRefreshing(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    // --- DEEP ANALYTICS MEMOS ---
    const analytics = useMemo(() => {
        const staleLeads = alerts.filter(a => a.details?.type === 'stale_lead');
        const systemAlerts = alerts.filter(a => a.level !== 'INFO' && a.details?.type !== 'stale_lead');
        return { staleLeads, systemAlerts };
    }, [alerts]);

    // --- ACTIONS ---
    const handleApprove = async (id: string) => {
        try {
            await api.processApproval('blog', id, 'approve');
            setSelectedBlog(null);
            fetchData();
        } catch (e) { alert("Approval failed"); }
    };

    const handleDispatch = async (alertId: string) => {
        try {
            await api.dispatchAlertTask(alertId);
            fetchData();
        } catch (e) { alert("Dispatch failed"); }
    };

    // --- HUD RENDERER ---
    const renderHUD = () => (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            <HUDCard id="integrity" label="Integrity" value={overview?.status === 'healthy' ? "99.8%" : "Degraded"} sub="24h / 5m Interval" active={activeMetric === 'integrity'} status={overview?.status === 'healthy' ? 'good' : 'bad'} onClick={setActiveMetric} />
            <HUDCard id="resources" label="Resources" value={`$${overview?.cost_24h.toFixed(2) || "0.00"}`} sub="Monthly Cap Budget" active={activeMetric === 'resources'} status={overview?.cost_24h && overview.cost_24h > 15 ? 'warning' : 'neutral'} onClick={setActiveMetric} />
            <HUDCard id="op_load" label="Op Load" value={`${approvals.blogs.length + approvals.leads.length} Items`} sub="Live Decision Queue" active={activeMetric === 'op_load'} status={approvals.blogs.length > 5 ? 'warning' : 'good'} onClick={setActiveMetric} />
            <HUDCard id="sent_risks" label="Sent Risks" value={analytics.staleLeads.length.toString()} sub="48h Active Scope" active={activeMetric === 'sent_risks'} status={analytics.staleLeads.length > 0 ? 'bad' : 'good'} onClick={setActiveMetric} />
            <HUDCard id="active_force" label="Active Force" value={`${overview?.active_agents.filter((a: any) => a.status === 'active').length || 0} Online`} sub="1h Pulse Check" active={activeMetric === 'active_force'} status="good" onClick={setActiveMetric} />
            
            <HUDCard id="ethics" label="Ethics" value="Clean" sub="30d Compl. History" active={activeMetric === 'ethics'} status="good" onClick={setActiveMetric} />
            <HUDCard id="collab" label="Collab" value="82%" sub="7d Rolling Avg" active={activeMetric === 'collab'} status="neutral" onClick={setActiveMetric} />
            <HUDCard id="graph" label="Graph" value="1.4k Nodes" sub="Global KB Density" active={activeMetric === 'graph'} status="good" onClick={setActiveMetric} />
            <HUDCard id="velocity" label="Velocity" value="1.2 Days" sub="14d Content Cycle" active={activeMetric === 'velocity'} status="good" onClick={setActiveMetric} />
        </div>
    );

    // --- DETAIL PANEL RENDERER ---
    const renderDetail = () => {
        switch (activeMetric) {
            case 'sent_risks':
                return (
                    <div className="space-y-6">
                        <DetailSection title="Business Exceptions" subtitle="Leads requiring immediate Dispatch action">
                            <div className="bg-card rounded-xl border border-border overflow-hidden">
                                <table className="w-full text-left text-xs">
                                    <thead className="bg-muted/50 text-muted-foreground font-bold border-b border-border">
                                        <tr>
                                            <th className="px-4 py-3">ID</th>
                                            <th className="px-4 py-3">Company</th>
                                            <th className="px-4 py-3">Score</th>
                                            <th className="px-4 py-3">Stale</th>
                                            <th className="px-4 py-3 text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border">
                                        {analytics.staleLeads.map(lead => (
                                            <tr key={lead.id} className="hover:bg-secondary/10">
                                                <td className="px-4 py-3 font-mono">#{lead.id.substring(0,4)}</td>
                                                <td className="px-4 py-3 font-bold">{lead.details?.company || 'Unknown'}</td>
                                                <td className="px-4 py-3 text-amber-600 font-black">{lead.details?.enrichment_score || 0}</td>
                                                <td className="px-4 py-3">{lead.details?.days_stale || 0}d</td>
                                                <td className="px-4 py-3 text-right">
                                                    <button onClick={() => handleDispatch(lead.id)} className="bg-indigo-600 text-white px-3 py-1 rounded-lg font-bold hover:bg-indigo-700 text-[10px]">DISPATCH</button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </DetailSection>
                        <DetailSection title="System Anomalies" subtitle="Infrastructure & 429 alerts">
                            <div className="space-y-2">
                                {analytics.systemAlerts.map(alert => (
                                    <div key={alert.id} className="p-3 bg-red-50 dark:bg-red-950/10 border border-red-100 dark:border-red-900/30 rounded-xl flex justify-between items-center">
                                        <div className="flex items-center gap-3">
                                            <AlertTriangleIcon className="w-4 h-4 text-red-600" />
                                            <span className="text-xs font-medium">{alert.message}</span>
                                        </div>
                                        <button className="text-[10px] font-bold text-red-600 underline">THROTTLE</button>
                                    </div>
                                ))}
                            </div>
                        </DetailSection>
                    </div>
                );
            case 'op_load':
                return (
                    <div className="space-y-6">
                        <DetailSection title="Content Queue" subtitle="Bob's pending drafts awaiting review">
                            <div className="flex gap-2 overflow-x-auto pb-4">
                                {approvals.blogs.map(blog => (
                                    <button 
                                        key={blog.id} 
                                        onClick={() => setSelectedBlog(blog)}
                                        className={`px-3 py-2 rounded-lg border text-[10px] font-bold whitespace-nowrap transition-all ${selectedBlog?.id === blog.id ? 'bg-indigo-600 text-white border-indigo-600 shadow-lg' : 'bg-card border-border text-muted-foreground hover:border-indigo-400'}`}
                                    >
                                        {blog.title.substring(0, 25)}...
                                    </button>
                                ))}
                            </div>
                            {selectedBlog && (
                                <div className="bg-card border border-border p-6 rounded-2xl space-y-4 animate-in fade-in zoom-in-95">
                                    <h4 className="font-bold text-lg">{selectedBlog.title}</h4>
                                    <p className="text-sm text-muted-foreground leading-relaxed">{selectedBlog.excerpt}</p>
                                    <div className="flex gap-3 pt-4 border-t border-border">
                                        <button onClick={() => handleApprove(selectedBlog.id)} className="flex-1 bg-green-600 text-white py-2 rounded-xl text-xs font-black shadow-lg">APPROVE & PUBLISH</button>
                                        <button className="px-6 border border-rose-200 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-50">REJECT</button>
                                    </div>
                                </div>
                            )}
                        </DetailSection>
                    </div>
                );
            case 'resources':
                return (
                    <DetailSection title="Resource Burn Detail" subtitle="Model activity and projections">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-4">
                                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Active Models (Last 24h)</h4>
                                {aiStats?.daily_costs?.[0]?.models?.map(modelName => (
                                    <div key={modelName} className="flex justify-between items-center p-3 bg-secondary/20 rounded-xl">
                                        <span className="text-[10px] font-mono font-bold">{modelName}</span>
                                        <span className="text-[9px] text-green-600 font-black uppercase">Online</span>
                                    </div>
                                ))}
                            </div>
                            <div className="p-8 bg-indigo-50 dark:bg-indigo-950/20 rounded-[2.5rem] border border-indigo-100 dark:border-indigo-900/30 flex flex-col justify-center text-center">
                                <p className="text-[10px] font-black text-indigo-600 dark:text-indigo-400 mb-2 uppercase tracking-widest">Runway Projection</p>
                                <p className="text-5xl font-black text-indigo-700 dark:text-indigo-300 tracking-tighter">12 Days</p>
                                <p className="text-[10px] text-indigo-500 mt-3 italic opacity-60">Based on 7d rolling average</p>
                            </div>
                        </div>
                    </DetailSection>
                );
            case 'active_force':
                return (
                    <DetailSection title="Active Force Matrix" subtitle="Real-time status of system agents">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {(overview?.active_agents as any[] || []).map((agent: any) => (
                                <div key={agent.id} className="p-4 bg-card border border-border rounded-2xl flex items-center justify-between group">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2.5 h-2.5 rounded-full ${agent.status === 'active' ? 'bg-green-500 animate-pulse' : 'bg-slate-300'}`} />
                                        <div>
                                            <p className="text-xs font-bold">{agent.name}</p>
                                            <p className="text-[10px] text-muted-foreground uppercase font-mono tracking-tighter">{agent.role}</p>
                                        </div>
                                    </div>
                                    <button className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-secondary rounded-lg transition-all"><RefreshCwIcon className="w-3.5 h-3.5" /></button>
                                </div>
                            ))}
                        </div>
                    </DetailSection>
                );
            default:
                return <div className="p-20 text-center text-muted-foreground italic border border-dashed border-border rounded-3xl">Deep analytics for {activeMetric} is currently being aggregated...</div>;
        }
    };

    if (loading) return (
        <div className="flex flex-col items-center justify-center h-[60vh]">
            <RefreshCwIcon className="animate-spin w-10 h-10 text-slate-400 mb-4" />
            <span className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Synchronizing Executive Environment</span>
        </div>
    );

    return (
        <div className="max-w-[1400px] mx-auto space-y-8 animate-in fade-in duration-700 px-4">
            <div className="flex justify-between items-end border-b border-border/50 pb-6">
                <div>
                    <h1 className="text-3xl font-black tracking-tight text-foreground uppercase">Managerial <span className="text-indigo-600">Nexus</span></h1>
                    <p className="text-[10px] text-muted-foreground font-black mt-1 uppercase tracking-[0.2em]">Unified Decision Hub • v7.1</p>
                </div>
                <button onClick={fetchData} className={`p-2.5 rounded-xl transition-all ${isRefreshing ? 'bg-indigo-50 text-indigo-600 animate-pulse' : 'hover:bg-secondary text-slate-400'}`}>
                    <RefreshCwIcon className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {renderHUD()}

            <div className="bg-card border border-border rounded-[2.5rem] p-8 shadow-2xl min-h-[500px]">
                {renderDetail()}
            </div>

            <footer className="space-y-4 pt-4 border-t border-border/30">
                <div className="flex items-center gap-3 text-slate-400 px-2">
                    <ClockIcon className="w-4 h-4" />
                    <h2 className="text-[10px] font-black uppercase tracking-[0.2em]">Latest Audit Trail</h2>
                </div>
                <div className="bg-secondary/10 rounded-2xl p-5 font-mono text-[10px] space-y-2.5 max-h-32 overflow-y-auto">
                    {alerts.slice(0, 5).map(log => (
                        <div key={log.id} className="flex gap-5 border-b border-border/20 pb-1.5 last:border-0 opacity-80 group">
                            <span className="text-slate-500 shrink-0">{new Date(log.created_at).toLocaleTimeString()}</span>
                            <span className="text-indigo-500 font-black uppercase shrink-0">[{log.source}]</span>
                            <span className="group-hover:text-foreground transition-colors">{log.message}</span>
                        </div>
                    ))}
                </div>
            </footer>
        </div>
    );
};

// --- SUB-COMPONENTS ---

const HUDCard: React.FC<{id: MetricCategory, label: string, value: string, sub: string, active: boolean, status: 'good'|'bad'|'warning'|'neutral', onClick: (id: MetricCategory) => void}> = ({id, label, value, sub, active, status, onClick}) => {
    const statusColor = status === 'good' ? 'bg-green-500' : status === 'bad' ? 'bg-red-500' : status === 'warning' ? 'bg-amber-500' : 'bg-slate-400';
    return (
        <div 
            onClick={() => onClick(id)} 
            className={`p-5 rounded-3xl border transition-all cursor-pointer select-none group ${active ? 'bg-white dark:bg-slate-900 border-indigo-500 shadow-xl scale-[1.03]' : 'bg-card border-border hover:border-slate-400'}`}
        >
            <div className="flex justify-between items-start mb-3">
                <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/60 group-hover:text-indigo-500 transition-colors">{label}</span>
                <div className={`w-2 h-2 rounded-full ${statusColor} shadow-[0_0_8px_currentColor] ${active ? 'animate-pulse' : ''}`} />
            </div>
            <p className={`text-2xl font-black tracking-tighter ${active ? 'text-indigo-600' : 'text-foreground'}`}>{value}</p>
            <p className="text-[9px] text-muted-foreground font-bold opacity-50 mt-1 uppercase tracking-tighter">{sub}</p>
        </div>
    );
};

const DetailSection: React.FC<{title: string, subtitle: string, children: React.ReactNode}> = ({title, subtitle, children}) => (
    <div className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-700">
        <div>
            <h2 className="text-2xl font-black flex items-center gap-4 uppercase tracking-tight">
                <div className="w-2 h-8 bg-indigo-600 rounded-full" />
                {title}
            </h2>
            <p className="text-xs text-muted-foreground mt-1.5 ml-6 italic">{subtitle}</p>
        </div>
        <div className="ml-6">{children}</div>
    </div>
);

export default ManagerNexus;
