import React, { useState, useEffect } from 'react';
import { api } from '../services/api.ts';
import { useAuth } from '../hooks/useAuth.tsx';

interface Alert {
    id: string;
    message: string;
    details: any;
    created_at: string;
}

export const ManagerDashboard: React.FC = () => {
    const { user } = useAuth();
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [processingId, setProcessingId] = useState<string | null>(null);

    useEffect(() => {
        fetchAlerts();
    }, []);

    const fetchAlerts = async () => {
        try {
            const data = await api.getManagerAlerts();
            setAlerts(data);
        } catch (e) {
            console.error(e);
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
            setTimeout(fetchAlerts, 2000);
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
        } catch (e) {
            alert("Seeding Failed: " +  (e as Error).message);
        } finally {
            setLoading(false);
        }
    };

    if (loading && alerts.length === 0) return <div className="p-8">Loading Manager Dashboard...</div>;

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <header className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
                        Manager Command Center ({user?.name || 'Manager'})
                    </h1>
                    <p className="text-muted-foreground">Operational Oversight & Exception Handling</p>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={handleSentinelRun}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white text-sm font-medium transition-colors"
                    >
                        Run Sentinel Scan
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Alerts Feed */}
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <span className="text-red-500">●</span> High Priority Alerts
                    </h2>
                    
                    {alerts.length === 0 ? (
                        <div className="p-12 border-2 border-dashed border-border rounded-xl text-center text-muted-foreground">
                            No active alerts. Systems normal.
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
                                            <>Processing...</>
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
                    <div className="bg-card border border-border p-5 rounded-xl">
                        <h3 className="font-semibold mb-4">Workflow Status</h3>
                         <div className="space-y-3">
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Stale Leads (&gt;14d)</span>
                                <span className="font-mono">{alerts.filter(a => a.details?.type === 'stale_lead').length}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Pending Approvals</span>
                                <span className="font-mono">--</span>
                            </div>
                         </div>
                    </div>

                     <div className="bg-card border border-border p-5 rounded-xl">
                        <h3 className="font-semibold mb-4">Scoring Rules</h3>
                         <p className="text-xs text-muted-foreground mb-4">
                            Dynamic thresholds used by Sentinel.
                         </p>
                         {/* Placeholder for Scoring Config Form - Phase 5 Enhancement */}
                         <div className="p-3 bg-muted/30 rounded text-xs font-mono">
                            SCORING_VITAL_CONTACT: 20<br/>
                            SCORING_NEWS_FUNDING: 30<br/>
                            SCORING_HAS_JOB_URL: 15
                         </div>
                         <button className="w-full mt-3 py-1.5 text-xs border border-border rounded hover:bg-muted">
                            Edit Rules
                         </button>
                    </div>

                    <div className="bg-card border border-border p-5 rounded-xl">
                        <h3 className="font-semibold mb-4 text-orange-500">System Maintenance</h3>
                         <p className="text-xs text-muted-foreground mb-4">
                            Manage Knowledge Base & Indexes.
                         </p>
                         <button 
                            onClick={handleSeedKnowledge}
                            className="w-full py-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                         >
                            <span>📚 Rebuild Knowledge Base</span>
                         </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
