import React, { useState, useEffect } from 'react';
import { Employee } from '../types';
import { 
    AlertTriangleIcon, ActivityIcon,
    ShieldCheckIcon, DatabaseIcon, UsersIcon, 
    GitCommitIcon, FileTextIcon,
    DollarSignIcon, ClockIcon,
    RefreshCwIcon
} from '../components/Icons';
import { ManageMemberModal } from '../features/team/components/ManageMemberModal';

import { PromptManagement } from '../features/admin/components/PromptManagement.tsx';
import { IntegrityAnalysis } from '../features/manager/components/IntegrityAnalysis.tsx';

import { useManagerNexusStats, MetricCategory } from '../features/manager/hooks/useManagerNexusStats';
import { Skeleton } from '../components/Skeleton';
import { DetailSection } from '../features/manager/components/DetailSection';
import { ResourceAudit } from '../features/manager/components/ResourceAudit';
import { OpLoadPanel } from '../features/manager/components/OpLoadPanel';
import { CollabMatrix } from '../features/manager/components/CollabMatrix';
import { SentinelRadar } from '../features/manager/components/SentinelRadar';
import { ActiveForce } from '../features/manager/components/ActiveForce';
import { KnowledgeROI } from '../features/manager/components/KnowledgeROI';
import { SlaReliability } from '../features/manager/components/SlaReliability';

// Nexus Components
import { NexusHeader } from '../features/manager/components/nexus/NexusHeader';
import { NexusFooter } from '../features/manager/components/nexus/NexusFooter';
import { NexusHUD } from '../features/manager/components/nexus/NexusHUD';
import { EthicsAuditPanel } from '../features/manager/components/nexus/EthicsAuditPanel';
import { NexusSpecPanel } from '../features/manager/components/nexus/NexusSpecPanel';
import { NexusEmptyState } from '../features/manager/components/nexus/NexusEmptyState';

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
        rules, rulesMeta, isSavingRules, totalRuleWeight,
        fetchData, handleDispatch, handleApprovePrompt, handleRebuildIndex,
        handleApproveContent, handleCodeAction, handleRuleChange, handleSaveRules
    } = useManagerNexusStats();

    useEffect(() => {
        fetch('/docs/nexus-spec.md')
            .then(res => res.text())
            .then(setSpecContent)
            .catch(err => console.error("Failed to load specs:", err));
    }, []);

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
                            isSavingRules={isSavingRules}
                            totalRuleWeight={totalRuleWeight}
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
                        <KnowledgeROI knowledgeRoi={knowledgeRoi} handleRebuildIndex={handleRebuildIndex} processingId={processingId} />
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
                        <EthicsAuditPanel
                            ethicsAudit={ethicsAudit}
                            handleDispatch={handleDispatch}
                            handleApprovePrompt={handleApprovePrompt}
                            processingId={processingId}
                        />
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
                return <NexusEmptyState />;
        }
    };


    return (
        <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 min-h-screen bg-gray-50/50 font-sans nexus-font-scope" style={{fontFamily: "'Inter', sans-serif"}}>
             <NexusHeader 
                onOpenSpec={() => setIsSpecOpen(true)} 
                dailyData={{
                    staleLeads: alerts?.length || 0,
                    pendingApprovals: (approvals?.blogs?.length || 0) + (approvals?.leads?.length || 0)
                }}
            />
            {/* HUD Grid */}
            <NexusHUD
                activeMetric={activeMetric}
                setActiveMetric={setActiveMetric}
                loading={loading}
                overview={overview}
                approvals={approvals}
                codeProposals={codeProposals}
                alerts={alerts}
                team={team}
                ethicsAudit={ethicsAudit}
                collabSynergy={collabSynergy}
                knowledgeRoi={knowledgeRoi}
                slaReliability={slaReliability}
            />

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

            <NexusFooter />

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
            <NexusSpecPanel
                isOpen={isSpecOpen}
                onClose={() => setIsSpecOpen(false)}
                specContent={specContent}
            />
        </div>
    );
};

export default ManagerNexus;
