import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api.ts';
import { useAuth } from '../hooks/useAuth.tsx';
import { SystemOverview, AlertItem } from '../types.ts';
import { CheckCircleIcon, RefreshCwIcon, AlertTriangleIcon, ActivityIcon, ShieldCheckIcon, DatabaseIcon, PlusIcon, FileTextIcon, XIcon, MaximizeIcon, MinimizeIcon } from '../components/Icons.tsx';

    // ... (Imports stay same, assuming at top)

    // Expanded Types
    interface ScoringRule {
        key: string;
        label: string;
        weight: number;
    }

    interface RulesMetadata {
        version: string;
        updated_at: string;
        updated_by: string;
    }

    export const ManagerDashboard: React.FC = () => {
        const { user } = useAuth();
        const [alerts, setAlerts] = useState<AlertItem[]>([]);
        const [systemHealth, setSystemHealth] = useState<SystemOverview | null>(null);
        const [loading, setLoading] = useState(true);
        const [seedingLoading, setSeedingLoading] = useState(false); // Specific loading for seeding
        const [processingId, setProcessingId] = useState<string | null>(null);
        
        // Spec Modal State
        const [isSpecOpen, setIsSpecOpen] = useState(false);
        const [isSpecMaximized, setIsSpecMaximized] = useState(false);
        const [specContent, setSpecContent] = useState('');

        // Diagnostic State (1.7)
        const [diagnosticPath, setDiagnosticPath] = useState('python/src/server/api_routes/projects_api.py');
        const [diagnosticResult, setDiagnosticResult] = useState<any>(null);
        const [isDiagnosing, setIsDiagnosing] = useState(false);
        
        // Scoring Rules State
        const [rules, setRules] = useState<ScoringRule[]>([
            { key: 'VITAL_CONTACT', label: 'Contact Info', weight: 20 },
            { key: 'FUNDING_NEWS', label: 'Funding News', weight: 30 },
            { key: 'JOB_URL', label: 'Hiring Signal', weight: 15 },
             { key: 'TECH_STACK', label: 'Tech Stack Match', weight: 35 },
        ]);
        const [rulesMeta, setRulesMeta] = useState<RulesMetadata>({
            version: 'v1.0.2',
            updated_at: new Date().toISOString(),
            updated_by: 'System Default'
        });
        const [newRuleLabel, setNewRuleLabel] = useState('');
        
        // Expansion State
        const [expandedCard, setExpandedCard] = useState<string | null>(null);

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
                setTimeout(fetchData, 2000); // Wait for async jobs
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
                setAlerts(prev => prev.filter(a => a.id !== alertId)); 
            } catch (e) {
                alert("Dispatch failed: " + JSON.stringify(e));
            } finally {
                setProcessingId(null);
            }
        };

        const handleSeedKnowledge = async () => {
            if (!confirm("Rebuild Knowledge Base? This will scan docs/ and re-index them.")) return;
            setSeedingLoading(true); // UI Feedback Loop Start
            try {
                const res = await api.seedKnowledgeBase();
                // Success Feedback
                alert(`✅ Rebuild Complete!\n\nIndexed: ${res.indexed_count} documents\nTotal Scanned: ${res.total_files} files`);
                if (isAdmin) fetchData();
            } catch (e) {
                alert("❌ Seeding Failed: " +  (e as Error).message);
            } finally {
                setSeedingLoading(false); // UI Feedback Loop End
            }
        };

        const handleViewSpecs = async () => {
            setIsSpecOpen(true);
            try {
                // Fetch spec from public folder
                const response = await fetch('/docs/nexus-spec.md');
                if (response.ok) {
                    const text = await response.text();
                    setSpecContent(text);
                } else {
                    setSpecContent("Failed to load docs/nexus-spec.md. Please check the public directory.");
                }
            } catch (e) {
                setSpecContent(`Error loading specs: ${e}`);
            }
        };

        const handleRunDiagnostic = async () => {
            setIsDiagnosing(true);
            setDiagnosticResult(null);
            try {
                const res = await api.diagnoseFile(diagnosticPath);
                setDiagnosticResult(res);
            } catch (e: any) {
                alert(`Diagnostic failed: ${e.message}`);
            } finally {
                setIsDiagnosing(false);
            }
        };

        // Scoring Rules Logic
        const totalWeight = rules.reduce((sum, r) => sum + r.weight, 0);
        
        const handleWeightChange = (key: string, val: number) => {
            setRules(prev => prev.map(r => r.key === key ? { ...r, weight: val } : r));
        };

        const handleAddRule = () => {
            if (!newRuleLabel) return;
            const newKey = newRuleLabel.toUpperCase().replace(/\s+/g, '_');
            setRules(prev => [...prev, { key: newKey, label: newRuleLabel, weight: 0 }]);
            setNewRuleLabel('');
        };

        const handleSaveRules = () => {
            if (totalWeight !== 100) {
                alert(`❌ Validation Failed: Total weight must be exactly 100%. Current: ${totalWeight}%`);
                return;
            }
            setRulesMeta({
                version: `v1.0.${parseInt(rulesMeta.version.split('.').pop() || '0') + 1}`,
                updated_at: new Date().toISOString(),
                updated_by: user?.name || 'Admin'
            });
            alert("✅ Rules Configuration Saved successfully!");
        };

        if (loading && alerts.length === 0) return <div className="p-12 text-center text-gray-500 animate-pulse">Initializing Command Center...</div>;

        return (
            <div className="p-6 max-w-7xl mx-auto space-y-8 font-sans bg-gray-50/30 min-h-screen">
                {/* Header Section */}
                <header className="flex flex-col md:flex-row justify-between items-start md:items-end bg-white p-6 rounded-3xl shadow-sm border border-gray-100 gap-4">
                    <div>
                         <div className="flex items-center gap-2 text-indigo-600 mb-1">
                            <ActivityIcon className="w-4 h-4" />
                            <span className="text-[10px] font-black uppercase tracking-widest">Management Console</span>
                        </div>
                        <h1 className="text-3xl font-black text-gray-900 tracking-tight">
                            Command Center
                        </h1>
                        <p className="text-sm text-gray-500 mt-1">Operational Oversight & Exception Handling</p>
                    </div>
                    <div className="flex gap-2">
                         <button 
                            onClick={handleViewSpecs}
                            className="px-6 py-3 bg-white border border-indigo-200 text-indigo-600 hover:bg-indigo-50 rounded-2xl text-sm font-bold transition-all shadow-sm active:scale-95 flex items-center gap-2"
                        >
                            <FileTextIcon className="w-4 h-4" />
                            View Specs
                        </button>
                         <button 
                            onClick={handleSentinelRun}
                            disabled={loading}
                            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-2xl text-white text-sm font-bold transition-all shadow-lg shadow-indigo-200 active:scale-95 disabled:opacity-50 flex items-center gap-2"
                        >
                            {loading ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <ShieldCheckIcon className="w-4 h-4" />}
                            Run Sentinel
                        </button>
                        <button 
                            onClick={() => fetchData()}
                            className="p-3 bg-white border border-gray-200 rounded-2xl text-gray-500 hover:text-indigo-600 hover:border-indigo-600 transition-all shadow-sm hover:rotate-180 duration-500"
                            title="Refresh Data"
                        >
                            <RefreshCwIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </header>

                {/* Admin-only System Health Overview (Expandable) */}
                {isAdmin && systemHealth && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
                        {/* RAG Health Card */}
                        <div 
                            onClick={() => setExpandedCard(expandedCard === 'rag' ? null : 'rag')}
                            className={`p-6 rounded-3xl border transition-all cursor-pointer hover:shadow-md ${systemHealth.rag.status === 'healthy' ? 'bg-white border-green-100 ring-4 ring-green-50/50' : 'bg-red-50 border-red-200'} ${expandedCard === 'rag' ? 'md:col-span-2 row-span-2' : ''}`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <div className={`p-2 rounded-xl ${systemHealth.rag.status === 'healthy' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                                    {systemHealth.rag.status === 'healthy' ? <CheckCircleIcon className="w-6 h-6" /> : <AlertTriangleIcon className="w-6 h-6" />}
                                </div>
                                <ActivityIcon className="w-4 h-4 text-gray-400" />
                            </div>
                            <div>
                                <div className="text-xs font-black uppercase text-gray-400 tracking-wider">RAG Health</div>
                                <div className="text-2xl font-black text-gray-800">{systemHealth.rag.status.toUpperCase()}</div>
                            </div>
                            
                            {/* Expanded Content */}
                            {expandedCard === 'rag' && (
                                <div className="mt-6 pt-6 border-t border-gray-100 animate-in fade-in">
                                    <h4 className="font-bold text-sm mb-3">Vector DB Statistics</h4>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between p-2 bg-gray-50 rounded-lg">
                                            <span>Document Count</span>
                                            <span className="font-mono font-bold">1,240</span>
                                        </div>
                                        <div className="flex justify-between p-2 bg-gray-50 rounded-lg">
                                            <span>Index Latency</span>
                                            <span className="font-mono font-bold text-green-600">45ms</span>
                                        </div>
                                        <div className="flex justify-between p-2 bg-gray-50 rounded-lg">
                                            <span>Embeddings Model</span>
                                            <span className="font-mono font-bold">text-embedding-004</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Errors Card */}
                        <div className="p-6 rounded-3xl border bg-white border-gray-100 hover:shadow-md transition-all">
                             <div className="flex items-center justify-between mb-2">
                                <div className="p-2 rounded-xl bg-amber-100 text-amber-600">
                                    <AlertTriangleIcon className="w-6 h-6" />
                                </div>
                            </div>
                            <div>
                                <div className="text-xs font-black uppercase text-gray-400 tracking-wider">Errors (24h)</div>
                                <div className="text-2xl font-black text-gray-800">{systemHealth.errors_24h}</div>
                            </div>
                        </div>

                        {/* Agents Card (Expandable) - Human/AI Split */}
                        <div 
                             onClick={() => setExpandedCard(expandedCard === 'agents' ? null : 'agents')}
                             className={`p-6 rounded-3xl border bg-white border-gray-100 hover:shadow-md transition-all cursor-pointer ${expandedCard === 'agents' ? 'md:col-span-2 row-span-2' : ''}`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <div className="p-2 rounded-xl bg-indigo-100 text-indigo-600">
                                    <ActivityIcon className="w-6 h-6" />
                                </div>
                                <div className="text-[10px] bg-indigo-50 text-indigo-600 px-2 py-1 rounded-full font-bold">ACTIVE</div>
                            </div>
                            <div>
                                <div className="text-xs font-black uppercase text-gray-400 tracking-wider">Active Agents</div>
                                <div className="text-2xl font-black text-gray-800">{systemHealth.active_agents.length}</div>
                            </div>

                             {expandedCard === 'agents' && (
                                <div className="mt-6 pt-6 border-t border-gray-100 animate-in fade-in">
                                    <table className="w-full text-sm text-left">
                                        <thead className="text-xs text-gray-400 bg-gray-50 uppercase">
                                            <tr>
                                                <th className="px-3 py-2 rounded-l-lg">Agent</th>
                                                <th className="px-3 py-2">Type</th>
                                                <th className="px-3 py-2 rounded-r-lg">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-100">
                                            <tr><td className="px-3 py-2 font-bold text-indigo-600">Sentinel</td><td className="px-3 py-2 text-xs">AI Service</td><td className="px-3 py-2 text-green-500 font-bold">Running</td></tr>
                                            <tr><td className="px-3 py-2 font-bold text-indigo-600">Librarian</td><td className="px-3 py-2 text-xs">RAG worker</td><td className="px-3 py-2 text-green-500 font-bold">Idle</td></tr>
                                            <tr><td className="px-3 py-2 font-bold text-gray-700">Alice</td><td className="px-3 py-2 text-xs">Human</td><td className="px-3 py-2 text-amber-500 font-bold">Away</td></tr>
                                            <tr><td className="px-3 py-2 font-bold text-gray-700">Bob</td><td className="px-3 py-2 text-xs">Human</td><td className="px-3 py-2 text-green-500 font-bold">Online</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>

                         {/* Compliance Logs Card (Expandable) */}
                         <div 
                             onClick={() => setExpandedCard(expandedCard === 'compliance' ? null : 'compliance')}
                             className={`p-6 rounded-3xl border bg-white border-gray-100 hover:shadow-md transition-all cursor-pointer ${expandedCard === 'compliance' ? 'md:col-span-4' : ''}`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <div className="p-2 rounded-xl bg-slate-100 text-slate-600">
                                    <ShieldCheckIcon className="w-6 h-6" />
                                </div>
                            </div>
                            <div>
                                <div className="text-xs font-black uppercase text-gray-400 tracking-wider">Compliance Logs</div>
                                <div className="text-2xl font-black text-gray-800">Safe</div>
                            </div>
                             {expandedCard === 'compliance' && (
                                <div className="mt-6 pt-6 border-t border-gray-100 animate-in fade-in">
                                     <h4 className="font-bold text-sm mb-3">Recent Security & Ethics Checks</h4>
                                     <div className="bg-slate-900 rounded-xl p-4 overflow-hidden font-mono text-xs text-green-400 shadow-inner">
                                        <div className="flex border-b border-slate-700 pb-2 mb-2 text-slate-500">
                                            <span className="w-24">TIME</span>
                                            <span className="w-24">USER</span>
                                            <span className="flex-1">ACTION</span>
                                            <span className="w-24 text-right">RESULT</span>
                                        </div>
                                        <div className="space-y-2 max-h-48 overflow-y-auto">
                                            <div className="flex">
                                                <span className="w-24 text-slate-500">10:42 AM</span>
                                                <span className="w-24 text-blue-400">Bob</span>
                                                <span className="flex-1 text-slate-300">Draft Blog "Merger Secrets"</span>
                                                <span className="w-24 text-right text-red-500 font-bold">BLOCKED</span>
                                            </div>
                                             <div className="flex">
                                                <span className="w-24 text-slate-500">09:15 AM</span>
                                                <span className="w-24 text-purple-400">Alice</span>
                                                <span className="flex-1 text-slate-300">Export Customer Emails</span>
                                                <span className="w-24 text-right text-red-500 font-bold">BLOCKED</span>
                                            </div>
                                             <div className="flex">
                                                <span className="w-24 text-slate-500">08:55 AM</span>
                                                <span className="w-24 text-indigo-400">System</span>
                                                <span className="flex-1 text-slate-300">Daily Sentinel Scan</span>
                                                <span className="w-24 text-right text-green-500 font-bold">PASS</span>
                                            </div>
                                        </div>
                                     </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Alerts Feed */}
                    <div className="lg:col-span-2 space-y-4">
                        <h2 className="text-xl font-black flex items-center gap-2 text-gray-800">
                            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span> Priority Signals
                        </h2>
                        
                        {alerts.length === 0 ? (
                            <div className="p-12 border-2 border-dashed border-gray-200 rounded-3xl text-center text-gray-400 bg-white">
                                All quiet on the western front.
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {alerts.map(alert => (
                                    <div key={alert.id} className="bg-white border border-gray-100 p-6 rounded-3xl shadow-sm hover:shadow-xl transition-all flex flex-col md:flex-row gap-4 justify-between items-start md:items-center group">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="px-3 py-1 bg-red-50 text-red-600 text-[10px] font-black uppercase tracking-widest rounded-lg">
                                                    {alert.details?.type || 'Alert'}
                                                </span>
                                                <span className="text-xs text-gray-400 font-mono">
                                                    {new Date(alert.created_at).toLocaleString()}
                                                </span>
                                            </div>
                                            <h3 className="text-lg font-bold text-gray-800 leading-tight">{alert.message}</h3>
                                            <p className="text-sm text-gray-500 mt-1">
                                                {alert.details?.company && `Target: ${alert.details.company}`}
                                            </p>
                                        </div>
                                        
                                        <button
                                            onClick={() => handleDispatch(alert.id)}
                                            disabled={processingId === alert.id}
                                            className="w-full md:w-auto px-6 py-4 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 rounded-2xl text-sm font-bold disabled:opacity-50 flex items-center justify-center gap-2 transition-colors active:scale-95"
                                        >
                                            {processingId === alert.id ? (
                                                <RefreshCwIcon className="animate-spin w-4 h-4" />
                                            ) : (
                                                <>
                                                    <img src="/icons/spark.svg" className="w-4 h-4 opacity-50" onError={(e) => e.currentTarget.style.display = 'none'} />
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
                        {/* Scoring Rules Configuration */}
                         <div className="bg-white border border-gray-100 p-6 rounded-3xl shadow-sm">
                            <h3 className="font-bold text-gray-800 mb-1">Scoring Logic</h3>
                             <p className="text-xs text-gray-400 mb-6">
                                Sentinel AI weighting parameters.
                             </p>
                             
                             {/* Metadata Display */}
                             <div className="flex justify-between text-[10px] text-gray-400 mb-4 bg-gray-50 p-2 rounded-lg font-mono">
                                 <span>{rulesMeta.version}</span>
                                 <span>Last: {new Date(rulesMeta.updated_at).toLocaleDateString()}</span>
                             </div>

                             <div className="space-y-3 mb-6">
                                {rules.map((rule) => (
                                    <div key={rule.key} className="flex items-center gap-3">
                                         <div className="flex-1">
                                            <div className="text-xs font-bold text-gray-700">{rule.label}</div>
                                            <div className="h-1.5 bg-gray-100 rounded-full mt-1 overflow-hidden">
                                                <div className="h-full bg-indigo-500 rounded-full transition-all duration-500" style={{ width: `${rule.weight}%` }}></div>
                                            </div>
                                         </div>
                                         <input 
                                            type="number" 
                                            className="w-16 bg-gray-50 border-none rounded-lg px-2 py-1 text-xs font-bold text-right"
                                            value={rule.weight}
                                            onChange={(e) => handleWeightChange(rule.key, parseInt(e.target.value) || 0)}
                                        />
                                    </div>
                                ))}
                             </div>
                             
                             <div className="flex gap-2 mb-4">
                                 <input 
                                    type="text" 
                                    placeholder="New Rule..."
                                    className="flex-1 bg-gray-50 border-none rounded-xl px-3 py-2 text-xs"
                                    value={newRuleLabel}
                                    onChange={(e) => setNewRuleLabel(e.target.value)}
                                 />
                                 <button onClick={handleAddRule} className="p-2 bg-gray-100 hover:bg-gray-200 rounded-xl text-gray-600">
                                     <PlusIcon className="w-4 h-4" />
                                 </button>
                             </div>

                             <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-100">
                                <span className={`text-xs font-bold ${totalWeight === 100 ? 'text-green-500' : 'text-red-500'}`}>
                                    Total: {totalWeight}%
                                </span>
                                <button 
                                    onClick={handleSaveRules}
                                    className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-100"
                                >
                                    Save Config
                                </button>
                             </div>
                        </div>

                        {/* Knowledge Base Maintenance */}
                        <div className="bg-white border border-gray-100 p-6 rounded-3xl shadow-sm relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-10">
                                <DatabaseIcon className="w-24 h-24 text-orange-500" />
                            </div>
                            <h3 className="font-bold text-gray-800 mb-1 z-10 relative">Knowledge Graph</h3>
                             <p className="text-xs text-gray-400 mb-6 z-10 relative">
                                RAG Index maintenance.
                             </p>
                             <button 
                                onClick={handleSeedKnowledge}
                                disabled={seedingLoading}
                                className="w-full py-4 bg-orange-500 hover:bg-orange-600 text-white rounded-2xl text-sm font-bold transition-all shadow-lg shadow-orange-200 flex items-center justify-center gap-2 z-10 relative active:scale-95 disabled:opacity-70 disabled:grayscale"
                             >
                                {seedingLoading ? (
                                    <>
                                        <RefreshCwIcon className="animate-spin w-5 h-5" />
                                        <span>Indexing Docs...</span>
                                    </>
                                ) : (
                                    <span>📚 REBUILD INDEX</span>
                                )}
                             </button>
                        </div>

                        {/* Technical Advisory Diagnostic (1.7 - Admin Only) */}
                        {isAdmin && (
                            <div className="bg-white border border-gray-100 p-6 rounded-3xl shadow-sm">
                                <h3 className="font-bold text-gray-800 mb-1">Technical Advisory</h3>
                                <p className="text-xs text-gray-400 mb-6">Refactoring severity grading (L1-L3).</p>
                                
                                <div className="space-y-4">
                                    <input 
                                        type="text" 
                                        value={diagnosticPath}
                                        onChange={(e) => setDiagnosticPath(e.target.value)}
                                        className="w-full p-3 bg-gray-50 border-none rounded-xl text-xs font-mono"
                                        placeholder="File path..."
                                    />
                                    <button 
                                        onClick={handleRunDiagnostic}
                                        disabled={isDiagnosing}
                                        className="w-full py-3 bg-slate-900 hover:bg-black text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2"
                                    >
                                        {isDiagnosing ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <ActivityIcon className="w-4 h-4" />}
                                        START DIAGNOSTIC
                                    </button>

                                    {diagnosticResult && (
                                        <div className={`p-4 rounded-2xl animate-in fade-in zoom-in-95 duration-300 ${
                                            diagnosticResult.severity_level === 3 ? 'bg-red-50 border border-red-100' :
                                            diagnosticResult.severity_level === 2 ? 'bg-amber-50 border border-amber-100' :
                                            'bg-green-50 border border-green-100'
                                        }`}>
                                            <div className="flex items-center gap-2 mb-2">
                                                <div className={`w-2 h-2 rounded-full ${
                                                    diagnosticResult.severity_level === 3 ? 'bg-red-500' :
                                                    diagnosticResult.severity_level === 2 ? 'bg-amber-500' :
                                                    'bg-green-500'
                                                }`} />
                                                <span className="text-[10px] font-black uppercase tracking-widest">
                                                    Level {diagnosticResult.severity_level}
                                                </span>
                                            </div>
                                            <p className="text-xs font-bold text-gray-800 mb-1">{diagnosticResult.advice}</p>
                                            <div className="text-[10px] text-gray-500 font-mono">
                                                Lines: {diagnosticResult.line_count} | SQL: {diagnosticResult.has_direct_sql ? 'YES' : 'NO'}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Specs Slide-over Panel */}
                {isSpecOpen && (
                    <>
                        <div 
                            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[60] transition-opacity"
                            onClick={() => setIsSpecOpen(false)}
                        />
                        <div 
                            className={`fixed inset-y-0 right-0 z-[70] bg-white dark:bg-slate-900 shadow-2xl transition-all duration-500 ease-in-out transform ${
                                isSpecMaximized ? 'w-full md:w-3/4' : 'w-full md:w-1/2 lg:w-1/3'
                            }`}
                        >
                            <div className="h-full flex flex-col">
                                <div className="p-6 border-b border-gray-100 dark:border-slate-800 flex justify-between items-center bg-gray-50/50 dark:bg-slate-800/50">
                                    <div>
                                        <h3 className="text-xl font-black text-gray-900 dark:text-white flex items-center gap-2">
                                            <ShieldCheckIcon className="w-5 h-5 text-indigo-600" />
                                            Metrics Definition
                                        </h3>
                                        <p className="text-xs text-gray-500">docs/nexus-spec.md</p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button 
                                            onClick={() => setIsSpecMaximized(!isSpecMaximized)}
                                            className="p-2 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-lg text-gray-500 transition-colors"
                                            title={isSpecMaximized ? "Minimize" : "Maximize"}
                                        >
                                            {isSpecMaximized ? <MinimizeIcon className="w-5 h-5" /> : <MaximizeIcon className="w-5 h-5" />}
                                        </button>
                                        <button 
                                            onClick={() => setIsSpecOpen(false)}
                                            className="p-2 hover:bg-red-50 hover:text-red-600 rounded-lg text-gray-400 transition-colors"
                                        >
                                            <XIcon className="w-6 h-6" />
                                        </button>
                                    </div>
                                </div>
                                
                                <div className="flex-1 overflow-y-auto p-8 prose prose-indigo max-w-none dark:prose-invert">
                                    <ReactMarkdown>{specContent || 'Loading specifications...'}</ReactMarkdown>
                                </div>

                                <div className="p-6 border-t border-gray-100 dark:border-slate-800 bg-gray-50/30">
                                    <button 
                                        onClick={() => setIsSpecOpen(false)}
                                        className="w-full py-3 bg-gray-900 dark:bg-slate-700 text-white rounded-xl font-bold hover:bg-gray-800 transition-all active:scale-[0.98]"
                                    >
                                        CLOSE REFERENCE
                                    </button>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        );
    };

