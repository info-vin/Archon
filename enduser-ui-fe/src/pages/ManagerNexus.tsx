import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { Employee } from '../types';
import { 
    CheckCircleIcon, AlertTriangleIcon, ActivityIcon, 
    ShieldCheckIcon, DatabaseIcon, UsersIcon, 
    GitCommitIcon, FileTextIcon,
    DollarSignIcon, ClockIcon, ZapIcon,
    XIcon,
    RefreshCwIcon
} from '../components/Icons';
import { ManageMemberModal } from '../features/team/components/ManageMemberModal';

import { PromptManagement } from '../features/admin/components/PromptManagement.tsx';
import { IntegrityAnalysis } from '../features/manager/components/IntegrityAnalysis.tsx';

import { useManagerNexusStats, MetricCategory } from '../features/manager/hooks/useManagerNexusStats';
import { Skeleton } from '../components/Skeleton';
import { HUDCard } from '../features/manager/components/HUDCard';
import { DetailSection } from '../features/manager/components/DetailSection';
import { ResourceAudit } from '../features/manager/components/ResourceAudit';
import { OpLoadPanel } from '../features/manager/components/OpLoadPanel';
import { CollabMatrix } from '../features/manager/components/CollabMatrix';
import { SentinelRadar } from '../features/manager/components/SentinelRadar';
import { ActiveForce } from '../features/manager/components/ActiveForce';
import { KnowledgeROI } from '../features/manager/components/KnowledgeROI';
import { SlaReliability } from '../features/manager/components/SlaReliability';

// --- Components ---

export const ManagerNexus: React.FC = () => {
    const [activeMetric, setActiveMetric] = useState<MetricCategory>('integrity');
    const [isMaximized, setIsMaximized] = useState(false);
    const [isSpecOpen, setIsSpecOpen] = useState(false);
    const [specContent, setSpecContent] = useState('');
    
    // Interaction States
    const [selectedMember, setSelectedMember] = useState<Employee | null>(null);

    const {
        loading,
        processingId, setProcessingId,
        overview, healthTrend, team, approvals, alerts, aiStats,
        commanderTrends, forceReadiness, businessRisks, collabSynergy,
        slaReliability, ethicsAudit, knowledgeRoi, codeProposals,
        rules, rulesMeta,
        fetchData, handleDispatch, handleApprovePrompt, handleRebuildIndex,
        handleApproveContent, handleCodeAction, handleRuleChange, handleSaveRules
    } = useManagerNexusStats();

    useEffect(() => {
        fetch('/docs/nexus-spec.md')
            .then(res => res.text())
            .then(setSpecContent)
            .catch(err => console.error("Failed to load specs:", err));
    }, []);

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
            const displayStr = typeof contentData === 'string' ? contentData : JSON.stringify(contentData, null, 2);

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
                        <IntegrityAnalysis healthTrend={healthTrend} isMaximized={isMaximized} />
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
                        <ResourceAudit aiStats={aiStats} isMaximized={isMaximized} />
                    </DetailSection>
                );

            case 'op_load':
                return (
                    <DetailSection title="Operational Load" subtitle="Approval & Review Queue" icon={<ActivityIcon className="w-5 h-5 text-indigo-600"/>}>
                        <OpLoadPanel 
                            commanderTrends={commanderTrends}
                            approvals={approvals}
                            codeProposals={codeProposals}
                            processingId={processingId}
                            setProcessingId={setProcessingId}
                            handleApproveContent={handleApproveContent}
                            handleCodeAction={handleCodeAction}
                            fetchData={fetchData}
                        />
                    </DetailSection>
                );

            case 'sent_risks':
                return (
                    <DetailSection title="Sentinel Risk Radar" subtitle="Business Logic Defense" icon={<AlertTriangleIcon className="w-5 h-5 text-indigo-600"/>}>
                        <SentinelRadar 
                            businessRisks={businessRisks}
                            processingId={processingId}
                            handleDispatch={handleDispatch}
                            rules={rules}
                            rulesMeta={rulesMeta}
                            handleRuleChange={handleRuleChange}
                            handleSaveRules={handleSaveRules}
                        />
                    </DetailSection>
                );

            case 'active_force':
                return (
                    <DetailSection title="Active Force" subtitle="Team Roster & Agent Status" icon={<UsersIcon className="w-5 h-5 text-indigo-600"/>}>
                        <ActiveForce 
                            forceReadiness={forceReadiness}
                            team={team}
                            overview={overview}
                            setSelectedMember={setSelectedMember}
                        />
                    </DetailSection>
                );

            case 'collab':
                return (
                    <DetailSection title="Collab Synergy" subtitle="Cross-Department Momentum (9x9)" icon={<GitCommitIcon className="w-5 h-5 text-indigo-600"/>}>
                        <CollabMatrix collabSynergy={collabSynergy} />
                    </DetailSection>
                );

            case 'graph':
                return (
                    <DetailSection title="Intelligence ROI & Graph" subtitle="60-Day Conversion Analysis (Bi-weekly)" icon={<DatabaseIcon className="w-5 h-5 text-indigo-600"/>}>
                        <KnowledgeROI knowledgeRoi={knowledgeRoi} handleRebuildIndex={handleRebuildIndex} />
                    </DetailSection>
                );

            case 'velocity':
                return (
                    <DetailSection title="SLA Reliability" subtitle="6-Month Strategic Trend (Bi-weekly)" icon={<ClockIcon className="w-5 h-5 text-indigo-600"/>}>
                        <SlaReliability slaReliability={slaReliability} />
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

            case 'prompts':
                return (
                    <DetailSection 
                        title="System Prompts" 
                        subtitle="Core Agent Instructions & Behavior Modeling" 
                        icon={<FileTextIcon className="w-5 h-5 text-indigo-600"/>}
                    >
                        <div className="bg-white/80 backdrop-blur border border-gray-100 rounded-3xl p-6 shadow-sm overflow-hidden h-full">
                            <PromptManagement isManagerMode={true} />
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


    return (
        <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 min-h-screen bg-gray-50/50 font-sans nexus-font-scope" style={{fontFamily: "'Inter', sans-serif"}}>
             <header className="flex justify-between items-end mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight flex items-center gap-3">Manager Nexus</h1>
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
                        <span>Dynamic Refresh</span>
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
                    loading={loading}
                />
                <HUDCard 
                    id="resources" label="Resources" 
                    value={`$${(overview?.cost_24h || 0).toFixed(2)}`} 
                    sub="Monthly Cap" 
                    active={activeMetric === 'resources'} 
                    status="neutral" 
                    onClick={setActiveMetric} 
                    tooltip="Token Usage & Cost vs Budget"
                    loading={loading}
                />
                <HUDCard 
                    id="op_load" label="Op Load" 
                    value={`${approvals.blogs.length + approvals.leads.length} Items`} 
                    sub="Decision Queue" 
                    active={activeMetric === 'op_load'} 
                    status={approvals.blogs.length > 0 ? "warning" : "good"} 
                    onClick={setActiveMetric}
                    tooltip="Pending Approvals & Reviews" 
                    loading={loading}
                />
                <HUDCard 
                    id="sent_risks" label="Sent Risks" 
                    value={`${alerts.length} Alerts`} 
                    sub="Exception Radar" 
                    active={activeMetric === 'sent_risks'} 
                    status={alerts.length > 0 ? "bad" : "good"} 
                    onClick={setActiveMetric} 
                    tooltip="Sentinel Generated Alerts"
                    loading={loading}
                />
                <HUDCard 
                    id="active_force" label="Act Force" 
                    value={`${team.filter(m=>m.status==='active').length} Online`} 
                    sub="Roster Status" 
                    active={activeMetric === 'active_force'} 
                    status="good" 
                    onClick={setActiveMetric} 
                    tooltip="Team & Agent Availability"
                    loading={loading}
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
                    loading={loading}
                />
                <HUDCard 
                    id="collab" label="Collab" 
                    value={collabSynergy?.snapshot ? `${collabSynergy.snapshot.momentum_pct > 0 ? '+' : ''}${collabSynergy.snapshot.momentum_pct}%` : "..."} 
                    sub={collabSynergy?.snapshot?.total_7d !== undefined ? `7D Total: ${collabSynergy.snapshot.total_7d}w` : "Team Synergy"}
                    active={activeMetric === 'collab'} 
                    status={collabSynergy?.snapshot?.momentum_pct >= 0 ? "good" : "warning"} 
                    onClick={setActiveMetric} 
                    tooltip={`Hot Bridge: ${collabSynergy?.snapshot?.hot_bridge || 'None'}`} 
                    loading={loading}
                />
                <HUDCard 
                    id="graph" label="Graph" 
                    value={knowledgeRoi?.overall_conversion !== undefined ? `${knowledgeRoi.overall_conversion}%` : "..."} 
                    sub={`${overview?.knowledge_stats?.total_nodes || 0} Total Nodes`} 
                    active={activeMetric === 'graph'} 
                    status={knowledgeRoi?.overall_conversion > 70 ? 'good' : knowledgeRoi?.overall_conversion > 30 ? 'warning' : 'bad'} 
                    onClick={setActiveMetric} 
                    tooltip="Intelligence ROI: Pages Saved vs URLs Scanned" 
                    loading={loading}
                />
                <HUDCard 
                    id="velocity" label="Reliability" 
                    value={slaReliability?.current_sla !== undefined ? `${slaReliability.current_sla}%` : "..."} 
                    sub="SLA Attainment" 
                    active={activeMetric === 'velocity'} 
                    status={slaReliability?.current_sla >= 95 ? "good" : "warning"} 
                    onClick={setActiveMetric} 
                    tooltip="6-Month Strategic Discipline Trend" 
                    loading={loading}
                />
                <HUDCard 
                    id="prompts" label="Prompts" 
                    value="System" 
                    sub="Management" 
                    active={activeMetric === 'prompts'} 
                    status="neutral" 
                    onClick={setActiveMetric} 
                    tooltip="System Prompts Management" 
                    loading={loading}
                />
            </div>

            {/* Dynamic Detail Area */}
            <div className="min-h-[400px]">
                {loading ? (
                    <DetailSection title="Loading Datacore..." subtitle="Synchronizing metrics from nodes..." icon={<RefreshCwIcon className="w-5 h-5 text-gray-400 animate-spin"/>}>
                        <div className="bg-white/80 rounded-3xl p-6 h-[400px] flex gap-4 w-full">
                            <Skeleton className="w-1/3 h-full rounded-2xl" />
                            <div className="w-2/3 flex flex-col gap-4">
                                <Skeleton className="w-full h-1/2 rounded-2xl" />
                                <Skeleton className="w-full h-1/2 rounded-2xl" />
                            </div>
                        </div>
                    </DetailSection>
                ) : (
                    renderDetail()
                )}
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
