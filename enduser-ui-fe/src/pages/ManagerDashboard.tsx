import React, { useState, useEffect } from 'react';
import { api } from '../services/api.ts';
import { useAuth } from '../hooks/useAuth.tsx';
import { SystemOverview } from '../types.ts';
import { CheckCircleIcon, RefreshCwIcon, AlertTriangleIcon, ActivityIcon } from '../components/Icons.tsx';

interface Alert {
    id: string;
    message: string;
    details: any;
    created_at: string;
}

export const ManagerDashboard: React.FC = () => {
    const { user } = useAuth();
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [systemHealth, setSystemHealth] = useState<SystemOverview | null>(null);
    const [loading, setLoading] = useState(true);
    const [processingId, setProcessingId] = useState<string | null>(null);

    const isAdmin = user?.role === 'admin' || user?.role === 'system_admin';

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [alertData, healthData] = await Promise.all([
                api.getManagerAlerts(),
                isAdmin ? api.getSystemOverview() : Promise.resolve(null)
            ]);
            setAlerts(alertData);
            setSystemHealth(healthData);
        } catch (e) {
            console.error("Dashboard data fetch failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const handleSentinelRun = async () => {
        if (!confirm("Run Sentinel Scan manually? This may take a few seconds.")) return;
        setLoading(true);
        try {
            await api.triggerSentinel();
            alert("Sentinel scan started!");
            // Wait a bit then refresh
            setTimeout(fetchData, 2000);
        } catch (e) {
            alert("Failed to run Sentinel: " + e);
            setLoading(false);
        }
    };

    const handleDispatch = async (alertId: string) => {
        setProcessingId(alertId);
        try {
            const res = await api.dispatchAlertTask(alertId);
            alert(`Task Dispatched! ID: ${res.task.id}`);
            // Optimistically remove or update alert
            setAlerts(prev => prev.filter(a => a.id !== alertId)); 
        } catch (e) {
            alert("Dispatch failed: " + JSON.stringify(e));
        } finally {
            setProcessingId(null);
        }
    };

    const handleSeedKnowledge = async () => {
        if (!confirm("Rebuild Knowledge Base? This will scan docs/ and re-index them.")) return;
        setLoading(true);
        try {
            const res = await api.seedKnowledgeBase();
            alert(`Seeding Complete!\nIndexed: ${res.indexed_count}\nTotal Scanned: ${res.total_files}`);
            if (isAdmin) fetchData(); // Refresh health stats too
        } catch (e) {
            alert("Seeding Failed: " +  (e as Error).message);
        } finally {
            setLoading(false);
        }
    };

    if (loading && alerts.length === 0) return <div className="p-8">Loading Manager Command Center...</div>;

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent uppercase tracking-tight">
                        {isAdmin ? 'System Architect' : 'Manager'} Command Center ({user?.name || 'Manager'})
                    </h1>
                    <p className="text-muted-foreground">{isAdmin ? 'System-wide Diagnostics & Operational Oversight' : 'Operational Oversight & Exception Handling'}</p>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={() => fetchData()}
                        className="p-2 text-muted-foreground hover:text-primary transition-colors"
                        title="Refresh Data"
                    >
                        <RefreshCwIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                    <button 
                        onClick={handleSentinelRun}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white text-sm font-medium transition-colors shadow-sm"
                    >
                        Run Sentinel Scan
                    </button>
                </div>
            </header>

            {/* Admin-only System Health Overview */}
            {isAdmin && systemHealth && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
                    <div className={`p-4 rounded-xl border ${systemHealth.status === 'healthy' ? 'bg-green-50/50 border-green-200' : 'bg-red-50/50 border-red-200'} flex items-center gap-4`}>
                        <div className={`p-2 rounded-lg ${systemHealth.status === 'healthy' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                            {systemHealth.status === 'healthy' ? <CheckCircleIcon className="w-6 h-6" /> : <AlertTriangleIcon className="w-6 h-6" />}
                        </div>
                        <div>
                            <div className="text-xs font-bold uppercase text-muted-foreground opacity-70">RAG Health</div>
                            <div className="text-lg font-bold">{systemHealth.rag.status.toUpperCase()}</div>
                        </div>
                    </div>
                    <div className="p-4 rounded-xl border bg-amber-50/50 border-amber-200 flex items-center gap-4">
                        <div className="p-2 rounded-lg bg-amber-100 text-amber-600">
                            <AlertTriangleIcon className="w-6 h-6" />
                        </div>
                        <div>
                            <div className="text-xs font-bold uppercase text-muted-foreground opacity-70">Errors (24h)</div>
                            <div className="text-lg font-bold">{systemHealth.errors_24h}</div>
                        </div>
                    </div>
                    <div className="p-4 rounded-xl border bg-indigo-50/50 border-indigo-200 flex items-center gap-4">
                        <div className="p-2 rounded-lg bg-indigo-100 text-indigo-600">
                            <ActivityIcon className="w-6 h-6" />
                        </div>
                        <div>
                            <div className="text-xs font-bold uppercase text-muted-foreground opacity-70">Active Agents</div>
                            <div className="text-lg font-bold">{systemHealth.active_agents.length}</div>
                        </div>
                    </div>
                    <div className="p-4 rounded-xl border bg-card border-border flex items-center gap-4">
                        <div className="p-2 rounded-lg bg-muted text-muted-foreground font-bold text-lg">
                            $
                        </div>
                        <div>
                            <div className="text-xs font-bold uppercase text-muted-foreground opacity-70">Token Cost (24h)</div>
                            <div className="text-lg font-bold">${systemHealth.cost_24h.toFixed(3)}</div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Alerts Feed */}
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <span className="text-red-500 animate-pulse">●</span> High Priority Alerts
                    </h2>
                    
                    {alerts.length === 0 ? (
                        <div className="p-12 border-2 border-dashed border-border rounded-xl text-center text-muted-foreground bg-muted/10">
                            No active alerts. Systems nominal.
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {alerts.map(alert => (
                                <div key={alert.id} className="bg-card border border-border p-4 rounded-xl shadow-sm hover:shadow-md transition-all flex flex-col md:flex-row gap-4 justify-between items-start md:items-center group">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="px-2 py-0.5 bg-red-500/10 text-red-400 text-xs font-bold uppercase rounded">
                                                {alert.details?.type || 'Alert'}
                                            </span>
                                            <span className="text-xs text-muted-foreground">
                                                {new Date(alert.created_at).toLocaleString()}
                                            </span>
                                        </div>
                                        <h3 className="font-medium text-foreground">{alert.message}</h3>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            {alert.details?.company && `Company: ${alert.details.company}`}
                                        </p>
                                    </div>
                                    
                                    <button
                                        onClick={() => handleDispatch(alert.id)}
                                        disabled={processingId === alert.id}
                                        className="w-full md:w-auto px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                                    >
                                        {processingId === alert.id ? (
                                            <RefreshCwIcon className="animate-spin w-4 h-4" />
                                        ) : (
                                            <>
                                                <span>Dispatch Task</span>
                                            </>
                                        )}
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Operational Metrics / Quick Actions */}
                <div className="space-y-6">
                    <div className="bg-card border border-border p-5 rounded-xl shadow-sm">
                        <h3 className="font-semibold mb-4 flex items-center gap-2">
                            <ActivityIcon className="w-4 h-4 text-primary" /> Workflow Status
                        </h3>
                         <div className="space-y-3">
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Stale Leads (&gt;14d)</span>
                                <span className="font-mono font-bold">{alerts.filter(a => a.details?.type === 'stale_lead').length}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Pending Approvals</span>
                                <span className="font-mono text-muted-foreground">--</span>
                            </div>
                         </div>
                    </div>

                     <div className="bg-card border border-border p-5 rounded-xl shadow-sm">
                        <h3 className="font-semibold mb-4">Scoring Rules Configuration</h3>
                         <p className="text-xs text-muted-foreground mb-4 italic">
                            Adjust dynamic thresholds for Sentinel analysis.
                         </p>
                         
                         <div className="border border-border rounded-lg overflow-hidden">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-muted/50 text-muted-foreground">
                                    <tr>
                                        <th className="px-3 py-2 font-medium">Rule</th>
                                        <th className="px-3 py-2 font-medium w-20">Weight</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {[
                                        { key: 'VITAL_CONTACT', label: 'Contact Info', default: 20 },
                                        { key: 'FUNDING_NEWS', label: 'Funding News', default: 30 },
                                        { key: 'JOB_URL', label: 'Hiring Signal', default: 15 },
                                    ].map((rule) => (
                                        <tr key={rule.key} className="bg-card">
                                            <td className="px-3 py-2">
                                                <div className="text-xs font-bold text-foreground">{rule.label}</div>
                                            </td>
                                            <td className="px-3 py-2">
                                                <input 
                                                    type="number" 
                                                    className="w-full bg-muted/30 border-none rounded px-2 py-1 text-xs font-mono"
                                                    defaultValue={rule.default}
                                                />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                         </div>
                         <button className="w-full mt-3 py-1.5 text-xs bg-muted hover:bg-muted/80 rounded transition-colors font-medium">
                            Save Thresholds
                         </button>
                    </div>

                    <div className="bg-card border border-border p-5 rounded-xl shadow-sm">
                        <h3 className="font-semibold mb-4 text-orange-500">System Maintenance</h3>
                         <p className="text-xs text-muted-foreground mb-4">
                            Manage Knowledge Base & RAG Indexing.
                         </p>
                         <button 
                            onClick={handleSeedKnowledge}
                            className="w-full py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-sm font-bold transition-all shadow-sm flex items-center justify-center gap-2"
                         >
                            <span>📚 REBUILD KNOWLEDGE</span>
                         </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
