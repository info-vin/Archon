import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { SystemOverview, Employee, AlertItem } from '../types';
import { 
    CheckCircleIcon, AlertTriangleIcon, ActivityIcon, 
    ShieldCheckIcon, DatabaseIcon, UsersIcon, 
    GitCommitIcon, SearchIcon, FileTextIcon,
    DollarSignIcon, ClockIcon, ZapIcon,
    MaximizeIcon, MinimizeIcon, SparklesIcon, XIcon
} from '../components/Icons';
import { ManageMemberModal } from '../features/team/components/ManageMemberModal';
import UserAvatar from '../components/UserAvatar';

import { 
    Line, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip, ResponsiveContainer, AreaChart, Area,
    ReferenceLine, Label
} from 'recharts';

// --- Types ---
type MetricCategory = 'integrity' | 'resources' | 'op_load' | 'sent_risks' | 'active_force' | 'ethics' | 'collab' | 'graph' | 'velocity';

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

// --- Components ---

const DetailSection: React.FC<{
    title: string, 
    subtitle: string, 
    children: React.ReactNode, 
    icon?: React.ReactNode,
    isMaximized?: boolean,
    onToggleMaximize?: () => void
}> = ({title, subtitle, children, icon, isMaximized, onToggleMaximize}) => (
    <div className={`
        bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden animate-in slide-in-from-bottom-4 duration-500
        ${isMaximized ? 'fixed inset-4 z-[60] shadow-2xl flex flex-col' : ''}
    `}>
        <div className="p-6 border-b border-gray-50 flex items-start justify-between bg-gray-50/30">
            <div>
                <h3 className={`font-black text-gray-800 tracking-tight flex items-center gap-2 ${isMaximized ? 'text-2xl' : 'text-lg'}`}>
                    {icon} {title}
                </h3>
                <p className={`text-gray-500 font-medium mt-1 uppercase tracking-wide ${isMaximized ? 'text-sm' : 'text-xs'}`}>{subtitle}</p>
            </div>
            {onToggleMaximize && (
                <button 
                    onClick={onToggleMaximize}
                    className="p-2 hover:bg-gray-200/50 rounded-full transition-colors text-gray-400 hover:text-indigo-600"
                >
                    {isMaximized ? <MinimizeIcon className="w-6 h-6" /> : <MaximizeIcon className="w-5 h-5" />}
                </button>
            )}
        </div>
        <div className={`p-6 ${isMaximized ? 'flex-1 overflow-y-auto' : ''}`}>
            {children}
        </div>
    </div>
);

const HUDCard: React.FC<{
    id: MetricCategory, 
    label: string, 
    value: string, 
    sub: string, 
    active: boolean, 
    status: 'good'|'bad'|'warning'|'neutral', 
    onClick: (id: MetricCategory) => void,
    tooltip?: string
}> = ({id, label, value, sub, active, status, onClick, tooltip}) => {
    const statusColor = status === 'good' ? 'bg-green-500' : status === 'bad' ? 'bg-red-500' : status === 'warning' ? 'bg-amber-500' : 'bg-slate-400';
    return (
        <div 
            onClick={() => onClick(id)} 
            className={`group relative p-5 rounded-3xl border transition-all cursor-pointer select-none ${
                active 
                ? 'bg-white border-indigo-500 shadow-xl scale-[1.02] ring-4 ring-indigo-50/50' 
                : 'bg-white border-gray-100 hover:border-gray-300 hover:shadow-md'
            }`}
        >
            <div className="flex justify-between items-start mb-3">
                <span className={`text-[10px] font-black uppercase tracking-widest transition-colors ${active ? 'text-indigo-600' : 'text-gray-400 group-hover:text-indigo-500'}`}>
                    {label}
                </span>
                <div className={`w-2 h-2 rounded-full ${statusColor} shadow-[0_0_8px_currentColor] ${active ? 'animate-pulse' : ''}`} />
            </div>
            <p className={`text-2xl font-black tracking-tighter ${active ? 'text-indigo-600' : 'text-gray-800'}`}>
                {value}
            </p>
            <p className="text-[9px] text-gray-400 font-bold opacity-60 mt-1 uppercase tracking-tighter truncate">
                {sub}
            </p>
            
            {/* Tooltip */}
            {tooltip && (
                <div className="absolute opacity-0 group-hover:opacity-100 transition-opacity bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-[10px] rounded-lg whitespace-nowrap pointer-events-none z-10">
                    {tooltip}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                </div>
            )}
        </div>
    );
};

export const ManagerNexus: React.FC = () => {
    const { user } = useAuth();
    const [activeMetric, setActiveMetric] = useState<MetricCategory>('integrity');
    const [isMaximized, setIsMaximized] = useState(false);
    const [loading, setLoading] = useState(true);
    const [isSpecOpen, setIsSpecOpen] = useState(false);
    const [specContent, setSpecContent] = useState('');
    
    // Data States
    const [overview, setOverview] = useState<SystemOverview | null>(null);
    const [healthTrend, setHealthTrend] = useState<{ trend: any[], audit: any[] }>({ trend: [], audit: [] });
    const [team, setTeam] = useState<Employee[]>([]);
    const [approvals, setApprovals] = useState<{blogs: any[], leads: any[]}>({blogs: [], leads: []});
    const [alerts, setAlerts] = useState<AlertItem[]>([]);
    const [aiStats, setAiStats] = useState<any>(null);

    // Interaction States
    const [processingId, setProcessingId] = useState<string | null>(null);
    const [selectedMember, setSelectedMember] = useState<Employee | null>(null);
    const [selectedContent, setSelectedContent] = useState<any | null>(null);
    const [rejectReason, setRejectReason] = useState('');
    const [isRejecting, setIsRejecting] = useState(false);
    const [opLoadTab, setOpLoadTab] = useState<'content' | 'devops'>('content');

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

    useEffect(() => {
        fetchData();
        fetch('/docs/nexus-spec.md')
            .then(res => res.text())
            .then(setSpecContent)
            .catch(err => console.error("Failed to load specs:", err));
    }, []);

    const [commanderTrends, setCommanderTrends] = useState<any[]>([]);
    const [forceReadiness, setForceReadiness] = useState<any>(null);
    const [businessRisks, setBusinessRisks] = useState<any[]>([]);
    const [collabSynergy, setCollabSynergy] = useState<any>(null);
    const [slaReliability, setSlaReliability] = useState<any>(null);
    const [ethicsAudit, setEthicsAudit] = useState<any>(null);
    const [knowledgeRoi, setKnowledgeRoi] = useState<any>(null);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [sys, emp, app, alr, ai, settings, trends, force, risks, collab, sla, ethics, kroi] = await Promise.all([
                api.getSystemOverview(),
                api.getEmployees(),
                api.getPendingApprovals(),
                api.getManagerAlerts(),
                api.getAiUsage(),
                api.getSystemSettings('marketing_scoring'),
                api.getCommanderTrends(),
                api.getForceReadiness(),
                api.getBusinessRisks(),
                api.getCollabSynergy(),
                api.getSlaReliability(),
                api.getEthicsAuditQueue(),
                api.getKnowledgeRoi()
            ]);
            setOverview(sys);
            setTeam(emp);
            setApprovals(app);
            setAlerts(alr);
            setAiStats(ai);
            setCommanderTrends(trends);
            setForceReadiness(force);
            setBusinessRisks(risks);
            setCollabSynergy(collab);
            setSlaReliability(sla);
            setEthicsAudit(ethics);
            setKnowledgeRoi(kroi);

            if (settings && settings.length > 0) {
                 try {
                     const parsedRules = JSON.parse(settings[0].value);
                     if (parsedRules.weights) setRules(parsedRules.weights);
                     if (parsedRules.version) setRulesMeta(prev => ({ ...prev, version: parsedRules.version, updated_by: parsedRules.updated_by }));
                 } catch (e) {
                     console.error("Failed to parse scoring rules", e);
                 }
            }
            
            // Separated for resilience
            api.getHealthTrend().then(data => {
                console.log("📈 Nexus Health Trend Loaded:", data.trend.length, "points");
                setHealthTrend(data);
            }).catch(e => console.error("Trend Load Failed", e));

        } catch (e) {
            console.error("Nexus Load Failed", e);
        } finally {
            setLoading(false);
        }
    };

    // --- Handlers ---
    
    const handleDispatch = async (alertId: string) => {
        setProcessingId(alertId);
        try {
            await api.generateTaskFromAlert(alertId);
            setAlerts(prev => prev.filter(a => a.id !== alertId)); 
            // Also refresh ethicsAudit if the ID came from there
            if (ethicsAudit?.violations.some((v: any) => v.id === alertId)) {
                fetchData();
            }
            alert(`Smart Task dispatched! Context enriched by AI.`);
        } catch (e: any) {
            alert("Dispatch failed: " + e.message);
        } finally {
            setProcessingId(null);
        }
    };

    const handleApprovePrompt = async (versionId: string) => {
        setProcessingId(versionId);
        try {
            await api.approvePromptChange(versionId);
            fetchData();
            alert("Prompt change approved and finalized.");
        } catch (e: any) {
            alert("Approval failed: " + e.message);
        } finally {
            setProcessingId(null);
        }
    };

    const handleViewDiff = (item: any) => {
        try {
            if (!item) return;
            
            let contentData = item.content;
            if (typeof item.content === 'string') {
                try {
                    contentData = JSON.parse(item.content);
                } catch (e) {
                    contentData = { raw: item.content };
                }
            }

            const summary = item.change_summary || "Strategic Prompt Update";
            const field = item.field_name || "Prompt Config";
            const author = item.created_by || "System";
            
            // Safe stringify for display
            const displayStr = typeof contentData === 'string' 
                ? contentData 
                : JSON.stringify(contentData, null, 2);

            alert(
                `[ AUDIT VIEW: PROMPT CHANGE ]\n` +
                `----------------------------------\n` +
                `Target: ${item.document_id}\n` +
                `Author: ${author}\n` +
                `Field:  ${field}\n` +
                `Summary: ${summary}\n\n` +
                `NEW CONTENT PREVIEW:\n` +
                `${displayStr.slice(0, 400)}${displayStr.length > 400 ? '...' : ''}`
            );
        } catch (err) {
            console.error("ViewDiff Failed:", err);
            alert("Unable to preview this change. The data format might be incompatible.");
        }
    };

    const handleRebuildIndex = async () => {
        if (!confirm("Rebuild Knowledge Base index? This consumes significant tokens.")) return;
        setProcessingId('rebuild_index');
        try {
            const res = await api.seedKnowledgeBase();
            alert(`Rebuild Complete! Indexed: ${res.indexed_count} docs.`);
        } catch (e: any) {
            alert("Rebuild failed: " + e.message);
        } finally {
            setProcessingId(null);
        }
    };

    const handleApproveContent = async (id: string, type: 'blog' | 'lead') => {
        setProcessingId(id);
        try {
            await api.processApproval(type, id, 'approve');
            fetchData(); // Refresh all
            setSelectedContent(null);
        } catch (e: any) {
            alert("Approval failed: " + e.message);
        } finally {
            setProcessingId(null);
        }
    };

    const handleRejectContent = async () => {
        if (!selectedContent) return;
        setProcessingId(selectedContent.id);
        try {
            // FIX: Pass the actual rejection reason to the backend
            await api.processApproval('blog', selectedContent.id, 'reject', rejectReason); 
            alert("Content Returned. Bob has been notified with your instructions.");
            fetchData();
            setSelectedContent(null);
            setIsRejecting(false);
            setRejectReason('');
        } catch (e: any) {
            alert("Rejection failed: " + e.message);
        } finally {
            setProcessingId(null);
        }
    };

    const handleRuleChange = (key: string, val: number) => {
        setRules(prev => prev.map(r => r.key === key ? { ...r, weight: val } : r));
    };

    const handleSaveRules = async () => {
        const total = rules.reduce((acc, r) => acc + r.weight, 0);
        if (total !== 100) return alert(`Total weight must be 100%. Current: ${total}%`);
        
        const newMeta = {
            version: `v1.0.${parseInt(rulesMeta.version.split('.').pop() || '0') + 1}`,
            updated_at: new Date().toISOString(),
            updated_by: user?.name || 'Admin'
        };

        const payload = {
            weights: rules,
            ...newMeta
        };

        try {
            await api.updateSystemSetting('marketing_scoring', { 
                value: JSON.stringify(payload),
                description: `Updated by ${user?.name}`
            });
            setRulesMeta(newMeta);
            alert("Scoring Rules Saved to Database!");
        } catch (e: any) {
            alert("Failed to save rules: " + e.message);
        }
    };

    // --- Renders ---

    const renderDetail = () => {
        switch (activeMetric) {
            case 'integrity':
                return (
                    <DetailSection 
                        title="System Integrity Analysis" 
                        subtitle="RAG Vector Quality & Node Alignment (30D)" 
                        icon={<ShieldCheckIcon className="w-5 h-5 text-indigo-600"/>}
                        isMaximized={isMaximized}
                        onToggleMaximize={() => setIsMaximized(!isMaximized)}
                    >
                        <div className="space-y-8">
                            {/* Professional Chart Section */}
                            <div className="bg-white rounded-3xl border border-gray-100 p-6 shadow-sm">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h4 className={`font-black text-gray-800 uppercase tracking-tight ${isMaximized ? 'text-lg' : 'text-sm'}`}>Health Variance Trend</h4>
                                        <p className="text-[10px] text-gray-400 font-bold uppercase mt-0.5">Y-Axis: Integrity Score (%) | X-Axis: 30 Day Timeline</p>
                                    </div>
                                    <div className="flex gap-4">
                                        <div className="flex items-center gap-1.5"><div className="w-3 h-0.5 bg-indigo-600" /><span className="text-[10px] font-bold text-gray-500 uppercase">Daily Avg</span></div>
                                        <div className="flex items-center gap-1.5"><div className="w-3 h-0.5 bg-gray-300 border-t border-dashed border-gray-400" /><span className="text-[10px] font-bold text-gray-500 uppercase">Monthly Baseline</span></div>
                                    </div>
                                </div>
                                
                                <div className={`${isMaximized ? 'h-[500px]' : 'h-[320px]'} w-full transition-all duration-500`} key={`${activeMetric}-${isMaximized}`}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={healthTrend.trend.length > 0 ? healthTrend.trend : [{date: '', daily: 100, baseline: 100}]}>
                                            <defs>
                                                <linearGradient id="colorDaily" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#f1f5f9" />
                                            <XAxis 
                                                dataKey="date" 
                                                axisLine={false} 
                                                tickLine={false} 
                                                interval={0}
                                                tick={(props) => {
                                                    const { x, y, payload, index } = props;
                                                    // 每 7 天顯示一次標籤 (0, 7, 14, 21, 28)
                                                    if (index % 7 !== 0 && index !== healthTrend.trend.length - 1) return <g/>;
                                                    return (
                                                        <text x={x} y={(Number(y) || 0) + 12} fontSize={10} fontWeight={800} fill="#94a3b8" textAnchor="middle" className="uppercase">
                                                            {payload.value}
                                                        </text>
                                                    );
                                                }}
                                            />
                                            <YAxis 
                                                domain={['dataMin - 1', 100]} 
                                                axisLine={false} 
                                                tickLine={false} 
                                                tick={{fontSize: 10, fontWeight: 700, fill: '#94a3b8'}}
                                                dx={-10}
                                                ticks={[90, 92, 94, 96, 98, 100]} // 指定專業刻度
                                            />
                                            <ReTooltip 
                                                contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: 'bold'}}
                                                cursor={{stroke: '#4f46e5', strokeWidth: 1, strokeDasharray: '4 4'}}
                                            />
                                            <Area 
                                                type="monotone" 
                                                dataKey="daily" 
                                                stroke="#4f46e5" 
                                                strokeWidth={3} 
                                                fillOpacity={1} 
                                                fill="url(#colorDaily)" 
                                                animationDuration={1500}
                                                dot={{ r: 2, fill: '#4f46e5', strokeWidth: 2, stroke: '#fff' }}
                                                activeDot={{ r: 6, strokeWidth: 0 }}
                                            />
                                            <Line 
                                                type="monotone" 
                                                dataKey="baseline" 
                                                stroke="#cbd5e1" 
                                                strokeDasharray="5 5" 
                                                strokeWidth={2} 
                                                dot={false}
                                                animationDuration={2000}
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Real Integrity Audit Trail */}
                            <div className="space-y-4">
                                <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest px-1">System Health Audit Trail</h4>
                                <div className="bg-gray-50 rounded-3xl border border-gray-100 divide-y divide-gray-200 overflow-hidden">
                                    {healthTrend.audit.length > 0 ? healthTrend.audit.map((log: any, idx: number) => {
                                        const details = log.details || {};
                                        const total = details.total_sources || 0;
                                        const indexed = details.indexed_sources || 0;
                                        const score = details.score || 0;
                                        const dbOk = details.db_connected !== false;
                                        const searchOk = details.search_active !== false;
                                        
                                        return (
                                            <div key={idx} className="p-4 flex justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                                                <div>
                                                    <div className="text-sm font-bold text-gray-800">
                                                        Integrity Audit: {score}%
                                                    </div>
                                                    <div className="flex gap-3 mt-1 text-[9px] font-black uppercase tracking-tighter">
                                                        <span className={indexed/total >= 0.95 ? 'text-green-600' : 'text-amber-600'}>Align: {indexed}/{total}</span>
                                                        <span className={dbOk ? 'text-green-600' : 'text-red-600'}>DB: {dbOk ? 'READY' : 'LOST'}</span>
                                                        <span className={searchOk ? 'text-green-600' : 'text-red-600'}>Search: {searchOk ? 'ACTIVE' : 'FAIL'}</span>
                                                    </div>
                                                    <div className="text-[10px] text-gray-400 font-mono mt-2">
                                                        {new Date(log.created_at).toLocaleString()} | Operator: Clockwork
                                                    </div>
                                                </div>
                                                <span className={`text-[10px] font-black px-2.5 py-1 rounded-full ${
                                                    log.level === 'INFO' ? 'text-green-600 bg-green-50' : 'text-amber-600 bg-amber-50'
                                                }`}>
                                                    {log.level}
                                                </span>
                                            </div>
                                        );
                                    }) : (
                                        <div className="p-12 text-center text-gray-400 text-xs font-bold uppercase italic">
                                            No recent health events found
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </DetailSection>
                );

            case 'resources':
                return (
                    <DetailSection 
                        title="Synergy & Resource Audit" 
                        subtitle="Human-Bot Collaboration Window & Budget Burn-up" 
                        icon={<DollarSignIcon className="w-5 h-5 text-indigo-600"/>}
                        isMaximized={isMaximized}
                        onToggleMaximize={() => setIsMaximized(!isMaximized)}
                    >
                        <div className="space-y-8">
                            {/* 1. Monetary Burn-up Chart - Style Matched to Integrity */}
                            <div className="bg-white rounded-3xl border border-gray-100 p-6 shadow-sm">
                                <div className="flex justify-between items-center mb-6">
                                    <div>
                                        <h4 className={`font-black text-gray-800 uppercase tracking-tight ${isMaximized ? 'text-lg' : 'text-sm'}`}>Monetary Burn-up</h4>
                                        <p className="text-[10px] text-gray-400 font-bold uppercase mt-0.5">Y-Axis: Cumulative USD | X-Axis: 30 Day Timeline</p>
                                    </div>
                                    <div className="text-right">
                                        <div className={`font-black text-indigo-600 tracking-tighter ${isMaximized ? 'text-3xl' : 'text-xl'}`}>${aiStats?.total_monthly_usd?.toFixed(2)}</div>
                                        <div className="text-[8px] font-black text-gray-400 uppercase">{(aiStats?.total_monthly_tokens / 1000000).toFixed(2)}M Tokens Transferred</div>
                                    </div>
                                </div>
                                
                                <div className={`${isMaximized ? 'h-[450px]' : 'h-[280px]'} w-full transition-all duration-500`} key={`burn-${activeMetric}-${isMaximized}`}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={aiStats?.burn_trend || []}>
                                            <defs>
                                                <linearGradient id="colorBurn" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#f1f5f9" />
                                            <XAxis 
                                                dataKey="date" 
                                                axisLine={false} 
                                                tickLine={false} 
                                                tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}}
                                                interval={6}
                                            />
                                            <YAxis 
                                                domain={[0, 'auto']}
                                                axisLine={false} 
                                                tickLine={false} 
                                                tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}}
                                                dx={-5}
                                            />
                                            <ReTooltip 
                                                contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: 'bold'}}
                                            />
                                            <Area 
                                                type="monotone" 
                                                dataKey="cost" 
                                                stroke="#4f46e5" 
                                                strokeWidth={3} 
                                                fillOpacity={1} 
                                                fill="url(#colorBurn)" 
                                                animationDuration={1500}
                                            />
                                            {/* Budget Reference Line */}
                                            <Line 
                                                type="monotone" 
                                                dataKey={() => aiStats?.budget_limit} 
                                                stroke="#ef4444" 
                                                strokeDasharray="10 10" 
                                                strokeWidth={2} 
                                                dot={false}
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="mt-4 flex gap-4 text-[9px] font-black uppercase text-gray-400">
                                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-indigo-500 rounded-full" /> Actual Spend</div>
                                    <div className="flex items-center gap-1.5"><div className="w-3 h-0.5 bg-red-400 border-t border-dashed" /> Budget Cap (${aiStats?.budget_limit})</div>
                                </div>
                            </div>

                            {/* 2. Team Synergy Matrix - Style Matched to Integrity Audit */}
                            <div className="space-y-4">
                                <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest px-1">Collaboration Efficiency Matrix</h4>
                                <div className="bg-gray-50 rounded-3xl border border-gray-100 divide-y divide-gray-200 overflow-hidden shadow-sm">
                                    {aiStats?.team?.map((member: any) => (
                                        <div key={member.name} className="p-5 bg-white hover:bg-gray-50 transition-colors">
                                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                                                <div className="flex items-center gap-4 min-w-[180px]">
                                                    <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 text-xs font-black">
                                                        {member.name.substring(0, 2).toUpperCase()}
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-bold text-gray-800">{member.name}</div>
                                                        <div className="text-[9px] font-black text-indigo-500 uppercase tracking-tighter">{member.role}</div>
                                                    </div>
                                                </div>
                                                
                                                <div className="flex-1">
                                                    <div className="flex justify-between text-[8px] font-black text-gray-400 mb-1.5 uppercase tracking-tighter">
                                                        <span>Duty Window</span>
                                                        <span className="text-indigo-600">Avg Assist: {member.avg_window}h/day</span>
                                                    </div>
                                                    <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                                                        <div 
                                                            className="h-full bg-indigo-500 rounded-full shadow-[0_0_8px_rgba(79,70,229,0.2)]"
                                                            style={{ width: `${Math.min(100, (member.avg_window / 12) * 100)}%` }}
                                                        />
                                                    </div>
                                                </div>

                                                <div className="text-right min-w-[100px]">
                                                    <div className="text-sm font-black text-gray-800">${member.total_cost.toFixed(2)}</div>
                                                    <div className="text-[9px] font-bold text-gray-400 uppercase">{(member.total_tokens / 1000).toFixed(0)}k tkns</div>
                                                </div>
                                            </div>
                                            
                                            <div className="mt-4 flex flex-wrap gap-2">
                                                {member.task_distribution.map((task: any) => (
                                                    <span key={task.type} className={`px-2 py-0.5 text-[8px] font-black rounded-md uppercase tracking-tighter border ${
                                                        task.type === 'Crawler/Research' 
                                                        ? 'bg-amber-50 text-amber-600 border-amber-100' 
                                                        : 'bg-indigo-50 text-indigo-600 border-indigo-100'
                                                    }`}>
                                                        {task.type}: {task.count} ops | {(task.tokens / 1000).toFixed(1)}k tkns
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </DetailSection>
                );

            case 'op_load':
                return (
                    <DetailSection title="Operational Load" subtitle="Approval & Review Queue" icon={<ActivityIcon className="w-5 h-5 text-indigo-600"/>}>
                        {/* 30-Day Trend Insight (GAP-028 Dashboard) */}
                        <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 mb-8 min-h-[300px] flex flex-col">
                            <h4 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                                <SparklesIcon className="w-3 h-3" /> 30-Day Performance Pulse (Daily)
                            </h4>
                            <div className="flex-1 min-h-[220px]">
                                {commanderTrends && commanderTrends.length > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%" minHeight={220}>
                                        <AreaChart data={commanderTrends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                            <defs>
                                                <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                                </linearGradient>
                                            </defs>
                                            <XAxis 
                                                dataKey="date" 
                                                axisLine={false} 
                                                tickLine={false} 
                                                fontSize={10} 
                                                interval={Math.max(0, Math.floor(commanderTrends.length / 3))} 
                                                tick={{fill: '#94a3b8'}}
                                            />
                                            <YAxis yAxisId="left" hide />
                                            <YAxis yAxisId="right" hide domain={[0, 24]} />
                                            <ReTooltip 
                                                contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}}
                                            />
                                            <Area yAxisId="left" type="monotone" dataKey="bob_tokens" stroke="#6366f1" fillOpacity={1} fill="url(#colorTokens)" strokeWidth={2} name="Bob's Tokens" isAnimationActive={false} />
                                            <Area yAxisId="right" type="monotone" dataKey="decision_hours" stroke="#f59e0b" fill="transparent" strokeWidth={2} strokeDasharray="5 5" name="Decision Gap (Hrs)" isAnimationActive={false} />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-full flex items-center justify-center text-muted-foreground italic text-xs">
                                        No performance data recorded in the last 30 days.
                                    </div>
                                )}
                            </div>
                            {commanderTrends && commanderTrends.length > 0 && (
                                <div className="flex justify-center gap-6 mt-4">
                                    <span className="flex items-center gap-2 text-[10px] font-bold text-indigo-600"><div className="w-2 h-2 rounded-full bg-indigo-600"/> Cumulative Tokens</span>
                                    <span className="flex items-center gap-2 text-[10px] font-bold text-amber-600"><div className="w-2 h-2 border-t-2 border-amber-600 border-dashed w-4"/> Wait Time (Max 24h)</span>
                                </div>
                            )}
                        </div>

                        <div className="flex gap-4 mb-6 border-b border-gray-100 pb-2">
                            <button 
                                onClick={() => setOpLoadTab('content')}
                                className={`pb-2 text-sm font-bold transition-colors ${opLoadTab === 'content' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
                            >
                                Content ({approvals.blogs.length})
                            </button>
                            <button 
                                onClick={() => setOpLoadTab('devops')}
                                className={`pb-2 text-sm font-bold transition-colors ${opLoadTab === 'devops' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
                            >
                                DevOps (0)
                            </button>
                        </div>

                        {opLoadTab === 'content' && (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <div className="lg:col-span-1 space-y-2">
                                    {approvals.blogs.map((blog: any) => (
                                        <div 
                                            key={blog.id}
                                            onClick={() => setSelectedContent(blog)}
                                            className={`p-4 rounded-xl border cursor-pointer transition-all ${
                                                selectedContent?.id === blog.id 
                                                ? 'bg-indigo-50 border-indigo-200 shadow-sm' 
                                                : 'bg-white border-gray-100 hover:border-indigo-100'
                                            }`}
                                        >
                                            <h4 className="font-bold text-gray-800 text-sm line-clamp-1">{blog.title}</h4>
                                            <p className="text-xs text-gray-500 mt-1 flex justify-between">
                                                <span>{blog.author || 'Bob'}</span>
                                                <span className="font-mono">{new Date(blog.created_at).toLocaleDateString()}</span>
                                            </p>
                                        </div>
                                    ))}
                                    {approvals.blogs.length === 0 && <div className="text-center py-8 text-gray-400 text-sm">No content pending review.</div>}
                                </div>
                                <div className="lg:col-span-2">
                                    {selectedContent ? (
                                        <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100 h-full">
                                            <div className="flex justify-between items-start mb-4">
                                                <div className="flex-1">
                                                    <h3 className="text-xl font-black text-gray-900">{selectedContent.title}</h3>
                                                    <div className="flex items-center gap-3 mt-2">
                                                        <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest ${selectedContent.ai_score < 80 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
                                                            AI SCORE: {selectedContent.ai_score || 85}%
                                                        </span>
                                                        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Drafted by Bob</span>
                                                    </div>
                                                </div>
                                                <span className="px-2 py-1 bg-white rounded-lg text-xs font-bold border border-gray-200 shadow-sm">Draft</span>
                                            </div>
                                            
                                            {/* Preview Placeholder */}
                                            <div className="aspect-video bg-gray-200 rounded-xl mb-4 flex items-center justify-center text-gray-400">
                                                <img src={selectedContent.image_url} alt="Preview" className="w-full h-full object-cover rounded-xl" onError={(e) => e.currentTarget.style.display = 'none'} />
                                                <span className="absolute">Image Preview</span>
                                            </div>

                                            <p className="text-sm text-gray-600 leading-relaxed mb-6 font-serif">
                                                {selectedContent.excerpt}...
                                            </p>

                                            {isRejecting ? (
                                                <div className="bg-white p-4 rounded-xl border border-red-100 animate-in fade-in">
                                                    <h5 className="text-xs font-black text-red-500 uppercase mb-2">Rejection Reason</h5>
                                                    <textarea 
                                                        className="w-full text-sm p-3 bg-gray-50 rounded-lg border-0 focus:ring-2 focus:ring-red-500/20 mb-3"
                                                        rows={3}
                                                        placeholder="Explain why this content needs revision..."
                                                        value={rejectReason}
                                                        onChange={e => setRejectReason(e.target.value)}
                                                    />
                                                    <div className="flex gap-2 justify-end">
                                                        <button onClick={() => setIsRejecting(false)} className="px-3 py-1.5 text-xs font-bold text-gray-500">Cancel</button>
                                                        <button onClick={handleRejectContent} className="px-3 py-1.5 bg-red-500 text-white text-xs font-bold rounded-lg hover:bg-red-600">Confim Reject</button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="flex gap-3">
                                                    <button 
                                                        onClick={() => handleApproveContent(selectedContent.id, 'blog')}
                                                        disabled={!!processingId}
                                                        className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 rounded-xl font-bold shadow-lg shadow-green-200 transition-all active:scale-95 flex items-center justify-center gap-2"
                                                    >
                                                        <CheckCircleIcon className="w-4 h-4" /> Approve & Publish
                                                    </button>
                                                    <button 
                                                        onClick={() => setIsRejecting(true)}
                                                        className="px-6 bg-white border border-red-200 text-red-600 py-3 rounded-xl font-bold hover:bg-red-50 transition-colors"
                                                    >
                                                        Reject
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="h-full flex items-center justify-center text-gray-300 font-bold border-2 border-dashed border-gray-200 rounded-2xl">
                                            Select an item to preview
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {opLoadTab === 'devops' && (
                            <div className="text-center py-12 text-gray-400">
                                <GitCommitIcon className="w-12 h-12 mx-auto mb-3 opacity-20" />
                                <p className="text-sm">No infrastructure proposals pending.</p>
                            </div>
                        )}
                    </DetailSection>
                );

            case 'sent_risks':
                return (
                    <DetailSection title="Sentinel Risk Radar" subtitle="Business Logic Defense" icon={<AlertTriangleIcon className="w-5 h-5 text-indigo-600"/>}>
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            <div className="lg:col-span-2">
                                <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4">Actionable Threats ({businessRisks.length})</h4>
                                <div className="space-y-3">
                                    {businessRisks.map(alert => (
                                        <div key={alert.id} className="bg-white border-l-4 border-l-red-500 border-y border-r border-gray-100 p-4 rounded-r-xl flex items-center justify-between group hover:shadow-md transition-all">
                                            <div className="flex items-center gap-4">
                                                <div className="bg-red-50 p-3 rounded-xl text-red-600">
                                                    <ZapIcon className="w-5 h-5" />
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-[10px] font-black px-2 py-0.5 bg-red-100 text-red-700 rounded uppercase tracking-tighter">{alert.details?.type?.replace('_', ' ') || 'RISK'}</span>
                                                        <span className="text-[10px] text-gray-400 font-mono">{new Date(alert.created_at).toLocaleDateString()}</span>
                                                    </div>
                                                    <h5 className="font-bold text-gray-800 text-sm mt-1">{alert.message}</h5>
                                                    <p className="text-[10px] text-gray-500 italic mt-0.5">{alert.details?.company || alert.details?.title || 'System context attached'}</p>
                                                </div>
                                            </div>
                                            <button 
                                                onClick={() => handleDispatch(alert.id)}
                                                disabled={processingId === alert.id}
                                                className="px-5 py-2.5 bg-red-600 text-white rounded-xl text-xs font-black hover:bg-red-700 shadow-lg shadow-red-100 transition-all active:scale-95 disabled:opacity-50"
                                            >
                                                {processingId === alert.id ? '...' : 'DISPATCH'}
                                            </button>
                                        </div>
                                    ))}
                                    {businessRisks.length === 0 && (
                                        <div className="py-16 bg-green-50/30 border-2 border-dashed border-green-100 rounded-3xl flex flex-col items-center justify-center text-center">
                                            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-4">
                                                <CheckCircleIcon className="w-8 h-8" />
                                            </div>
                                            <h4 className="text-lg font-black text-green-800">ALL SYSTEMS NOMINAL</h4>
                                            <p className="text-xs text-green-600 mt-1 max-w-[240px]">Sentinel Radar reports zero business logic anomalies in the last 30 days.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                            
                            <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100">
                                <div className="flex justify-between items-center mb-4">
                                    <h4 className="text-xs font-black text-gray-500 uppercase tracking-widest">Scoring Config</h4>
                                    <span className="text-[10px] font-mono text-gray-400">{rulesMeta.version}</span>
                                </div>
                                <div className="space-y-4 mb-6">
                                    {rules.map(rule => (
                                        <div key={rule.key}>
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className="font-bold text-gray-700">{rule.label}</span>
                                                <span className="font-mono text-gray-500">{rule.weight}%</span>
                                            </div>
                                            <input 
                                                type="range" 
                                                min="0" max="100" 
                                                value={rule.weight}
                                                onChange={e => handleRuleChange(rule.key, parseInt(e.target.value))}
                                                className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                            />
                                        </div>
                                    ))}
                                </div>
                                <div className="flex justify-between items-center pt-4 border-t border-gray-200">
                                    <span className={`text-xs font-bold ${rules.reduce((a,b)=>a+b.weight,0) === 100 ? 'text-green-500' : 'text-red-500'}`}>
                                        Total: {rules.reduce((a,b)=>a+b.weight,0)}%
                                    </span>
                                    <button onClick={handleSaveRules} className="text-xs font-bold text-indigo-600 hover:underline">Save Changes</button>
                                </div>
                            </div>
                        </div>
                    </DetailSection>
                );

            case 'active_force':
                return (
                    <DetailSection title="Active Force" subtitle="Team Roster & Agent Status" icon={<UsersIcon className="w-5 h-5 text-indigo-600"/>}>
                        {/* Combat Power HUD (GAP-030) - Style Synchronized */}
                        <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 mb-8 min-h-[300px] flex flex-col">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-1 flex items-center gap-2">
                                            <ZapIcon className="w-3 h-3 text-indigo-500" /> 90-Day Combat Power vs. Average Baseline
                                        </h4>
                                        <p className="text-xl font-black text-gray-800">Rating: <span className="text-indigo-600">A+ ⚡</span></p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-[10px] font-black text-gray-400 uppercase">Automation Rate</p>
                                        <p className="text-lg font-black text-indigo-600">{forceReadiness?.automation_rate || 68}%</p>
                                    </div>
                                </div>
                                
                                <div className="flex-1 min-h-[220px]">
                                    {forceReadiness?.trend && forceReadiness.trend.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={220}>
                                            <AreaChart data={forceReadiness.trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                                <defs>
                                                    <linearGradient id="colorActualForce" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#f1f5f9" />
                                                <XAxis 
                                                    dataKey="date" 
                                                    axisLine={false} 
                                                    tickLine={false} 
                                                    tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}}
                                                    interval={8} 
                                                />
                                                <YAxis 
                                                    axisLine={false} 
                                                    tickLine={false} 
                                                    tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}}
                                                    domain={[0, 'auto']}
                                                />
                                                <ReTooltip 
                                                    contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: 'bold'}}
                                                />
                                                {/* Explicit Baseline Reference */}
                                                <ReferenceLine 
                                                    y={forceReadiness?.baseline || 0} 
                                                    stroke="#ef4444" 
                                                    strokeDasharray="5 5" 
                                                    strokeWidth={2}
                                                >
                                                    <Label value={`Avg: ${forceReadiness?.baseline}`} position="top" fill="#ef4444" fontSize={10} fontWeight="bold" />
                                                </ReferenceLine>

                                                <Area 
                                                    type="monotone" 
                                                    dataKey="actual" 
                                                    stroke="#4f46e5" 
                                                    fillOpacity={1} 
                                                    fill="url(#colorActualForce)" 
                                                    strokeWidth={3} 
                                                    name="Daily Output" 
                                                    isAnimationActive={false}
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                ) : (
                                    <div className="h-full flex items-center justify-center text-gray-400 italic text-xs">
                                        Initializing combat power sensors...
                                    </div>
                                )}
                            </div>
                            <div className="flex justify-center gap-6 mt-4 border-t border-gray-100 pt-4">
                                <span className="flex items-center gap-2 text-[9px] font-black text-indigo-600 uppercase tracking-widest"><div className="w-2 h-2 rounded-full bg-indigo-600"/> Current Output</span>
                                <span className="flex items-center gap-2 text-[9px] font-black text-gray-400 uppercase tracking-widest"><div className="w-2 h-2 border-t-2 border-gray-400 border-dashed w-4"/> 90-Day Baseline</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {team.map(member => (
                                <div key={member.id} className="p-4 bg-white border border-gray-100 rounded-2xl flex items-center justify-between hover:border-indigo-200 transition-all">
                                    <div className="flex items-center gap-3">
                                        <UserAvatar name={member.name} role={member.role} />
                                        <div>
                                            <h4 className="font-bold text-gray-800 text-sm">{member.name}</h4>
                                            <div className="flex items-center gap-1.5">
                                                <div className={`w-1.5 h-1.5 rounded-full ${member.status === 'active' ? 'bg-green-500' : 'bg-amber-500'}`} />
                                                <span className="text-xs text-gray-500 uppercase">{member.role}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <button 
                                        onClick={() => setSelectedMember(member)}
                                        className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                    >
                                        <SearchIcon className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                            {/* Agent Cards - Dynamic */}
                            {overview?.active_agents?.map((agent: any) => (
                                <div key={agent.id} className="p-4 bg-indigo-50/50 border border-indigo-100 rounded-2xl flex items-center justify-between opacity-80">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white"><ZapIcon className="w-4 h-4"/></div>
                                        <div>
                                            <h4 className="font-bold text-indigo-900 text-sm">{agent.name}</h4>
                                            <p className="text-[10px] text-indigo-600 uppercase">{agent.role || 'AI Agent'}</p>
                                        </div>
                                    </div>
                                    <span className={`px-2 py-1 text-[10px] font-bold rounded ${agent.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-500'}`}>
                                        {agent.status === 'active' ? 'ONLINE' : 'STANDBY'}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </DetailSection>
                );

            case 'collab':
                return (
                    <DetailSection title="Collab Synergy" subtitle="Cross-Department Momentum (9x9)" icon={<GitCommitIcon className="w-5 h-5 text-indigo-600"/>}>
                        <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm">
                            <div className="overflow-x-auto">
                                <div className="min-w-[1000px]">
                                    {/* Matrix Header */}
                                    <div className="grid grid-cols-10 bg-gray-50 border-b border-gray-100">
                                        <div className="p-4 text-[9px] font-black text-gray-400 uppercase border-r italic">Origin \ Target</div>
                                        {collabSynergy?.nodes.map((node: string) => (
                                            <div key={node} className="p-4 text-center text-[9px] font-black text-gray-500 uppercase tracking-widest truncate">{node}</div>
                                        ))}
                                    </div>
                                    {/* Matrix Rows */}
                                    {collabSynergy?.matrix.map((row: any) => (
                                        <div key={row.from} className="grid grid-cols-10 border-b border-gray-50 group hover:bg-indigo-50/20 transition-colors">
                                            <div className="p-4 bg-gray-50/50 border-r border-gray-100 text-xs font-bold text-gray-700">{row.from}</div>
                                            {row.interactions.map((cell: any, idx: number) => (
                                                <div key={idx} className="p-3 flex flex-col justify-center gap-1.5 relative border-r border-gray-50 last:border-r-0">
                                                    {row.from !== cell.to ? (
                                                        <>
                                                            {/* 30D Baseline (Gray Bar) */}
                                                            <div className="h-1 w-full bg-gray-100 rounded-full overflow-hidden">
                                                                <div 
                                                                    className="h-full bg-slate-300" 
                                                                    style={{ width: `${Math.min(100, (cell.avg_30d / 10) * 100)}%` }} 
                                                                />
                                                            </div>
                                                            {/* 7D Actual (Indigo Bar) */}
                                                            <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                                                                <div 
                                                                    className="h-full bg-indigo-500" 
                                                                    style={{ width: `${Math.min(100, (cell.actual_7d / 10) * 100)}%` }} 
                                                                />
                                                            </div>
                                                            <div className="flex justify-between items-center text-[8px] font-black text-gray-400 mt-1">
                                                                <span>{cell.actual_7d}w</span>
                                                                <span className={cell.actual_7d > cell.avg_30d ? 'text-green-500' : 'text-gray-300'}>
                                                                    {cell.actual_7d > cell.avg_30d ? '▲' : '▼'}
                                                                </span>
                                                            </div>
                                                        </>
                                                    ) : (
                                                        <div className="absolute inset-0 bg-gray-50/30 opacity-50" />
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <div className="mt-6 flex justify-center gap-8">
                            <div className="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                                <div className="w-3 h-1 bg-slate-300 rounded-full" /> 30D Average (Baseline)
                            </div>
                            <div className="flex items-center gap-2 text-[10px] font-black text-indigo-600 uppercase tracking-widest">
                                <div className="w-3 h-1.5 bg-indigo-500 rounded-full" /> 7D Actual (Momentum)
                            </div>
                        </div>
                    </DetailSection>
                );

            case 'graph':
                return (
                    <DetailSection title="Intelligence ROI & Graph" subtitle="60-Day Conversion Analysis (Bi-weekly)" icon={<DatabaseIcon className="w-5 h-5 text-indigo-600"/>}>
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            <div className="lg:col-span-2">
                                {/* 60-Day ROI Trend Chart */}
                                <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 mb-6">
                                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                                        <SparklesIcon className="w-3 h-3 text-indigo-500" /> Intelligence Yield (Conversion %)
                                    </h4>
                                    <div className="h-[250px]">
                                        {knowledgeRoi?.trend && knowledgeRoi.trend.length > 0 ? (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart data={knowledgeRoi.trend}>
                                                    <defs>
                                                        <linearGradient id="colorROI" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                                        </linearGradient>
                                                    </defs>
                                                    <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#f1f5f9" />
                                                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}} interval={0} />
                                                    <YAxis axisLine={false} tickLine={false} tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}} domain={[0, 100]} unit="%" />
                                                    <ReTooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontSize: '12px'}} />
                                                    <Area type="monotone" dataKey="conversion" stroke="#4f46e5" fillOpacity={1} fill="url(#colorROI)" strokeWidth={3} name="Conv %" isAnimationActive={false} />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        ) : (
                                            <div className="h-full flex items-center justify-center text-gray-400 italic text-xs">Waiting for Knowledge Sensors...</div>
                                        )}
                                    </div>
                                </div>

                                {/* Domain ROI Table */}
                                <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden">
                                    <table className="w-full text-left text-xs">
                                        <thead className="bg-gray-50 border-b border-gray-100">
                                            <tr>
                                                <th className="p-4 text-[10px] font-black text-gray-400 uppercase">Source Domain</th>
                                                <th className="p-4 text-[10px] font-black text-gray-400 uppercase">Conversion</th>
                                                <th className="p-4 text-[10px] font-black text-gray-400 uppercase text-right">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-gray-50">
                                            {knowledgeRoi?.top_domains?.map((dom: any) => (
                                                <tr key={dom.domain} className="group hover:bg-gray-50/50 transition-colors">
                                                    <td className="p-4">
                                                        <p className="font-bold text-gray-800">{dom.domain}</p>
                                                        <p className="text-[9px] text-gray-400">{dom.yield} Nodes Ingested</p>
                                                    </td>
                                                    <td className="p-4">
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-16 h-1 bg-gray-100 rounded-full overflow-hidden">
                                                                <div 
                                                                    className={`h-full ${dom.severity === 'good' ? 'bg-green-500' : dom.severity === 'warning' ? 'bg-amber-500' : 'bg-red-500'}`}
                                                                    style={{ width: `${dom.conversion}%` }}
                                                                />
                                                            </div>
                                                            <span className="text-[10px] font-black text-gray-600">{dom.conversion}%</span>
                                                        </div>
                                                    </td>
                                                    <td className="p-4 text-right">
                                                        <button className="text-[9px] font-black text-indigo-600 uppercase hover:underline">Block</button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
                                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-4">RAG Control Lever</h4>
                                    <div className="space-y-4 text-xs">
                                        <div className="flex justify-between items-center pb-2 border-b border-gray-50">
                                            <span className="text-gray-500">Embedding</span>
                                            <span className="font-bold">v3-small</span>
                                        </div>
                                        <div className="flex justify-between items-center pb-2 border-b border-gray-50">
                                            <span className="text-gray-500">Precision</span>
                                            <span className="font-bold text-green-600">92% ✨</span>
                                        </div>
                                    </div>
                                    <button 
                                        onClick={handleRebuildIndex}
                                        className="w-full mt-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-black text-[10px] uppercase shadow-lg shadow-indigo-100"
                                    >
                                        TRIGGER FULL RE-INDEX
                                    </button>
                                </div>
                            </div>
                        </div>
                    </DetailSection>
                );

            case 'velocity':
                return (
                    <DetailSection title="SLA Reliability" subtitle="6-Month Strategic Trend (Bi-weekly)" icon={<ClockIcon className="w-5 h-5 text-indigo-600"/>}>
                        <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 mb-8 min-h-[300px] flex flex-col">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-1 flex items-center gap-2">
                                        <SparklesIcon className="w-3 h-3 text-indigo-500" /> Strategic Discipline Trend (180 Days)
                                    </h4>
                                    <p className="text-xl font-black text-gray-800">Current Health: <span className={(slaReliability?.current_sla || 0) >= 95 ? 'text-green-600' : 'text-amber-600'}>{slaReliability?.current_sla || 0}%</span></p>
                                </div>
                                <div className="text-right">
                                    <p className="text-[10px] font-black text-gray-400 uppercase">Target SLA</p>
                                    <p className="text-lg font-black text-gray-300">95.0%</p>
                                </div>
                            </div>
                            <div className="flex-1 min-h-[220px]">
                                {slaReliability?.trend && slaReliability.trend.length > 0 ? (
                                    <ResponsiveContainer width="100%" height={220}>
                                        <AreaChart data={slaReliability.trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                            <defs>
                                                <linearGradient id="colorSLA" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#f1f5f9" />
                                            <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}} interval={1} />
                                            <YAxis axisLine={false} tickLine={false} tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}} domain={[80, 100]} />
                                            <ReTooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontSize: '12px'}} />
                                            <Area type="monotone" dataKey="rate" stroke="#4f46e5" fillOpacity={1} fill="url(#colorSLA)" strokeWidth={3} name="SLA %" isAnimationActive={false} />
                                            <ReferenceLine y={95} stroke="#10b981" strokeDasharray="3 3" strokeWidth={1}>
                                                <Label value="Goal" position="right" fill="#10b981" fontSize={9} fontWeight="bold" />
                                            </ReferenceLine>
                                        </AreaChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-full flex items-center justify-center text-gray-400 italic text-xs">Calibrating long-term reliability sensors...</div>
                                )}
                            </div>
                        </div>
                    </DetailSection>
                );

            case 'ethics':
                return (
                    <DetailSection title="Ethics & Prompt Audit" subtitle="Compliance Resolution Center" icon={<ShieldCheckIcon className="w-5 h-5 text-indigo-600"/>}>
                        <div className="space-y-6">
                            <div className="bg-indigo-50/30 border border-indigo-100 rounded-3xl p-6">
                                <h4 className="text-xs font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2">
                                    <ZapIcon className="w-3 h-3" /> Actionable Safety Queue ({ethicsAudit?.total_pending || 0})
                                </h4>
                                
                                <div className="space-y-4">
                                    {/* 1. Ethics Violations (Sentinel) */}
                                    {ethicsAudit?.violations.map((v: any) => (
                                        <div key={v.id} className="bg-white border border-red-100 p-4 rounded-2xl flex items-center justify-between shadow-sm hover:shadow-md transition-all">
                                            <div className="flex items-center gap-4">
                                                <div className="bg-red-50 p-3 rounded-xl text-red-600">
                                                    <ShieldCheckIcon className="w-5 h-5" />
                                                </div>
                                                <div>
                                                    <span className="text-[10px] font-black px-2 py-0.5 bg-red-100 text-red-700 rounded uppercase">Safety Intercept</span>
                                                    <h5 className="font-bold text-gray-800 text-sm mt-1">{v.event_type}: {v.description}</h5>
                                                    <p className="text-[10px] text-gray-400 font-mono mt-0.5">Attempted Input: {v.raw_input?.slice(0, 50)}...</p>
                                                </div>
                                            </div>
                                            <button 
                                                onClick={() => handleDispatch(v.id)}
                                                className="px-4 py-2 bg-red-600 text-white rounded-xl text-[10px] font-black hover:bg-red-700 transition-all"
                                            >
                                                DISPATCH INVESTIGATION
                                            </button>
                                        </div>
                                    ))}

                                    {/* 2. Prompt Changes (Librarian) */}
                                    {ethicsAudit?.pending_versions.map((p: any) => (
                                        <div key={p.id} className="bg-white border border-amber-100 p-4 rounded-2xl flex items-center justify-between shadow-sm hover:shadow-md transition-all">
                                            <div className="flex items-center gap-4">
                                                <div className="bg-amber-50 p-3 rounded-xl text-amber-600">
                                                    <FileTextIcon className="w-5 h-5" />
                                                </div>
                                                <div>
                                                    <span className="text-[10px] font-black px-2 py-0.5 bg-amber-100 text-amber-700 rounded uppercase">Prompt Change</span>
                                                    <h5 className="font-bold text-gray-800 text-sm mt-1">{p.document_id} (v{p.version_number})</h5>
                                                    <p className="text-[10px] text-gray-400 font-mono mt-0.5">Changed by {p.created_by} | {p.change_summary}</p>
                                                </div>
                                            </div>
                                            <div className="flex gap-2">
                                                <button 
                                                    onClick={() => handleViewDiff(p)}
                                                    className="px-4 py-2 bg-slate-100 text-slate-600 rounded-xl text-[10px] font-black hover:bg-slate-200"
                                                >
                                                    VIEW DIFF
                                                </button>
                                                <button 
                                                    onClick={() => handleApprovePrompt(p.id)}
                                                    disabled={processingId === p.id}
                                                    className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-[10px] font-black hover:bg-indigo-700"
                                                >
                                                    {processingId === p.id ? '...' : 'APPROVE'}
                                                </button>
                                            </div>
                                        </div>
                                    ))}

                                    {ethicsAudit?.total_pending === 0 && (
                                        <div className="py-12 flex flex-col items-center justify-center text-center text-green-600 opacity-60">
                                            <CheckCircleIcon className="w-12 h-12 mb-2" />
                                            <p className="text-sm font-black uppercase tracking-widest">Compliance Nominal</p>
                                            <p className="text-[10px]">No unauthorized prompt changes or safety leaks detected.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </DetailSection>
                );

            default:
                return (
                    <div className="p-12 text-center text-gray-400 bg-white rounded-3xl border border-dashed border-gray-200">
                        <ActivityIcon className="w-12 h-12 mx-auto mb-4 opacity-20" />
                        <p>Select a metric above to view details.</p>
                    </div>
                );
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center text-gray-400 animate-pulse">Initializing Nexus...</div>;

    return (
        <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 min-h-screen bg-gray-50/50 font-sans nexus-font-scope" style={{fontFamily: "'Inter', sans-serif"}}>
             <header className="flex justify-between items-end mb-8">
                <div>
                    <h1 className="text-3xl font-black text-gray-900 tracking-tight">Manager Nexus</h1>
                    <p className="text-sm text-gray-500 mt-1 font-medium">Command & Control v7.1</p>
                </div>
                <div className="flex items-center gap-4">
                    <button 
                        onClick={() => setIsSpecOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-600 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-amber-100 transition-all active:scale-95 border border-amber-100"
                    >
                        <FileTextIcon className="w-4 h-4" />
                        View Specs
                    </button>
                    <div className="flex gap-2 text-xs font-bold text-gray-400 bg-white px-3 py-1.5 rounded-lg border border-gray-100 shadow-sm">
                        <ClockIcon className="w-4 h-4" />
                        <span>Auto-refresh: 5m</span>
                    </div>
                </div>
            </header>

            {/* HUD Grid */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <HUDCard 
                    id="integrity" label="Integrity" 
                    value={overview?.integrity_score !== undefined ? `${overview.integrity_score}%` : "..."}
                    sub="System Health" 
                    active={activeMetric === 'integrity'} 
                    status={overview?.status === 'healthy' ? 'good' : 'bad'} 
                    onClick={setActiveMetric} 
                    tooltip="RAG Vector DB Health"
                />
                <HUDCard 
                    id="resources" label="Resources" 
                    value={`$${(overview?.cost_24h || 0).toFixed(2)}`} 
                    sub="Monthly Cap" 
                    active={activeMetric === 'resources'} 
                    status="neutral" 
                    onClick={setActiveMetric} 
                    tooltip="Token Usage & Cost vs Budget"
                />
                <HUDCard 
                    id="op_load" label="Op Load" 
                    value={`${approvals.blogs.length + approvals.leads.length} Items`} 
                    sub="Decision Queue" 
                    active={activeMetric === 'op_load'} 
                    status={approvals.blogs.length > 0 ? "warning" : "good"} 
                    onClick={setActiveMetric}
                    tooltip="Pending Approvals & Reviews" 
                />
                <HUDCard 
                    id="sent_risks" label="Sent Risks" 
                    value={`${alerts.length} Alerts`} 
                    sub="Exception Radar" 
                    active={activeMetric === 'sent_risks'} 
                    status={alerts.length > 0 ? "bad" : "good"} 
                    onClick={setActiveMetric} 
                    tooltip="Sentinel Generated Alerts"
                />
                <HUDCard 
                    id="active_force" label="Act Force" 
                    value={`${team.filter(m=>m.status==='active').length} Online`} 
                    sub="Roster Status" 
                    active={activeMetric === 'active_force'} 
                    status="good" 
                    onClick={setActiveMetric} 
                    tooltip="Team & Agent Availability"
                />
                {/* Secondary Metrics Row */}
                <HUDCard 
                    id="ethics" label="Ethics" 
                    value={ethicsAudit?.total_pending > 0 ? `${ethicsAudit.total_pending} Actions` : "Secure"} 
                    sub={ethicsAudit?.total_pending > 0 ? `${ethicsAudit.violations.length} Risks | ${ethicsAudit.pending_versions.length} Changes` : "System Nominal"} 
                    active={activeMetric === 'ethics'} 
                    status={ethicsAudit?.total_pending > 0 ? 'bad' : 'good'} 
                    onClick={setActiveMetric} 
                    tooltip="Safety violations & Prompt audit queue" 
                />
                <HUDCard 
                    id="collab" label="Collab" 
                    value={collabSynergy?.snapshot ? `${collabSynergy.snapshot.momentum_pct > 0 ? '+' : ''}${collabSynergy.snapshot.momentum_pct}%` : "..."} 
                    sub={collabSynergy?.snapshot?.total_7d !== undefined ? `7D Total: ${collabSynergy.snapshot.total_7d}w` : "Team Synergy"}
                    active={activeMetric === 'collab'} 
                    status={collabSynergy?.snapshot?.momentum_pct >= 0 ? "good" : "warning"} 
                    onClick={setActiveMetric} 
                    tooltip={`Hot Bridge: ${collabSynergy?.snapshot?.hot_bridge || 'None'}`} 
                />
                <HUDCard 
                    id="graph" label="Graph" 
                    value={knowledgeRoi?.overall_conversion !== undefined ? `${knowledgeRoi.overall_conversion}%` : "..."} 
                    sub={`${overview?.knowledge_stats?.total_nodes || 0} Total Nodes`} 
                    active={activeMetric === 'graph'} 
                    status={knowledgeRoi?.overall_conversion > 70 ? 'good' : knowledgeRoi?.overall_conversion > 30 ? 'warning' : 'bad'} 
                    onClick={setActiveMetric} 
                    tooltip="Intelligence ROI: Pages Saved vs URLs Scanned" 
                />
                <HUDCard 
                    id="velocity" label="Reliability" 
                    value={slaReliability?.current_sla !== undefined ? `${slaReliability.current_sla}%` : "..."} 
                    sub="SLA Attainment" 
                    active={activeMetric === 'velocity'} 
                    status={slaReliability?.current_sla >= 95 ? "good" : "warning"} 
                    onClick={setActiveMetric} 
                    tooltip="6-Month Strategic Discipline Trend" 
                />
            </div>

            {/* Dynamic Detail Area */}
            <div className="min-h-[400px]">
                {renderDetail()}
            </div>

            {/* Footer Field Guide */}
            <footer className="mt-12 pt-8 border-t border-gray-200 text-xs text-gray-400 grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                    <h5 className="font-bold text-gray-500 uppercase tracking-widest mb-2">Metrics Definition</h5>
                    <ul className="space-y-1">
                        <li>• <strong className="text-gray-600">Reliability:</strong> 6-month strategic SLA attainment (Bi-weekly).</li>
                        <li>• <strong className="text-gray-600">ROI:</strong> 60-day intelligence yield (Pages Saved / URLs Scanned).</li>
                    </ul>
                </div>
                <div>
                     <h5 className="font-bold text-gray-500 uppercase tracking-widest mb-2">Color Codes</h5>
                     <ul className="space-y-1">
                        <li className="flex items-center gap-2"><div className="w-2 h-2 bg-green-500 rounded-full"></div> Optimal Range</li>
                        <li className="flex items-center gap-2"><div className="w-2 h-2 bg-amber-500 rounded-full"></div> Warning / Action Needed</li>
                        <li className="flex items-center gap-2"><div className="w-2 h-2 bg-red-500 rounded-full"></div> Critical Exception</li>
                     </ul>
                </div>
                <div>
                    <h5 className="font-bold text-gray-500 uppercase tracking-widest mb-2">System Info</h5>
                    <p>ManagerNexus v7.1 | Build 2026.02.12</p>
                    <p className="mt-1">© Archon Intelligence Systems</p>
                </div>
            </footer>

            {/* Member Management Modal */}
            {selectedMember && (
                <ManageMemberModal 
                    member={selectedMember} 
                    onClose={() => setSelectedMember(null)} 
                    onSuccess={() => {
                        setSelectedMember(null);
                        fetchData();
                    }} 
                />
            )}

            {/* Nexus Spec Slide-over Panel */}
            <AnimatePresence>
                {isSpecOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsSpecOpen(false)}
                            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[70]"
                        />
                        {/* Panel */}
                        <motion.aside 
                            initial={{ x: '100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed inset-y-0 right-0 w-full max-w-xl bg-white dark:bg-slate-900 shadow-2xl z-[80] overflow-hidden flex flex-col"
                        >
                            <div className="p-6 border-b border-gray-100 dark:border-slate-800 flex justify-between items-center bg-amber-50/30 dark:bg-amber-900/10">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-amber-500 rounded-lg text-white">
                                        <FileTextIcon className="w-5 h-5" />
                                    </div>
                                    <h2 className="text-lg font-black text-gray-900 dark:text-white uppercase tracking-tight">Nexus Metrics Spec</h2>
                                </div>
                                <button onClick={() => setIsSpecOpen(false)} className="p-2 hover:bg-gray-200/50 dark:hover:bg-slate-800 rounded-full transition-colors text-gray-400">
                                    <XIcon className="w-6 h-6" />
                                </button>
                            </div>
                            <div className="flex-1 overflow-y-auto p-8 prose prose-slate dark:prose-invert max-w-none prose-headings:font-black prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg">
                                <ReactMarkdown>{specContent}</ReactMarkdown>
                            </div>
                            <div className="p-6 border-t border-gray-100 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-950/50 flex justify-end">
                                <button 
                                    onClick={() => setIsSpecOpen(false)}
                                    className="px-6 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl font-bold text-sm hover:scale-105 transition-transform"
                                >
                                    Close Spec
                                </button>
                            </div>
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};

export default ManagerNexus;
