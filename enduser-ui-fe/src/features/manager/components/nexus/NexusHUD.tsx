import React from 'react';
import { HUDCard } from '../HUDCard';
import { MetricCategory } from '../../hooks/useManagerNexusStats';

export interface NexusHUDProps {
    activeMetric: MetricCategory;
    setActiveMetric: (metric: MetricCategory) => void;
    loading: boolean;
    overview: any;
    approvals: any;
    codeProposals?: any[];
    alerts: any;
    team: any;
    ethicsAudit: any;
    collabSynergy: any;
    knowledgeRoi: any;
    slaReliability: any;
}

export const NexusHUD: React.FC<NexusHUDProps> = ({
    activeMetric,
    setActiveMetric,
    loading,
    overview,
    approvals,
    codeProposals = [],
    alerts,
    team,
    ethicsAudit,
    collabSynergy,
    knowledgeRoi,
    slaReliability
}) => {
    return (
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
                value={`${(approvals?.blogs?.length || 0) + (codeProposals?.length || 0)} Items`}
                sub="Decision Queue"
                active={activeMetric === 'op_load'}
                status={((approvals?.blogs?.length || 0) + (codeProposals?.length || 0)) > 0 ? "warning" : "good"}
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
                value={`${team.filter((m: any) => m.status === 'active').length} Online`}
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
    );
};
