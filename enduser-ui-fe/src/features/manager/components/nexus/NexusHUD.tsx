import React from 'react';
import { HUDCard } from '../HUDCard';
import { MetricCategory } from '../../hooks/useManagerNexusStats';

export interface NexusHUDProps {
    activeMetric: MetricCategory;
    setActiveMetric: (metric: MetricCategory) => void;
    loading: boolean;
    overview: any;
    alerts: any;
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
    alerts,
    ethicsAudit,
    collabSynergy,
    knowledgeRoi,
    slaReliability
}) => {
    const alertCount = alerts?.length || 0;
    const ethicsPending = ethicsAudit?.total_pending || 0;
    const totalRiskAndEthics = alertCount + ethicsPending;

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <HUDCard
                id="integrity" label="Integrity"
                value={overview?.integrity_score !== undefined ? `${overview.integrity_score}%` : "..."}
                sub={`${overview?.knowledge_stats?.total_nodes ?? 0} Nodes Indexed`}
                active={activeMetric === 'integrity'}
                status={overview?.rag?.status === 'healthy' ? 'good' : 'bad'}
                onClick={setActiveMetric}
                tooltip="RAG Vector DB Health & Indexed Nodes"
                loading={loading}
            />
            <HUDCard
                id="resources" label="Resources"
                value={`$${(overview?.cost_24h || 0).toFixed(4)}`}
                sub="24H Token Cost"
                active={activeMetric === 'resources'}
                status="neutral"
                onClick={setActiveMetric}
                tooltip="24H Token Usage & Monthly Budget Burn-up"
                loading={loading}
            />
            <HUDCard
                id="risk_ethics" label="Risk & Ethics"
                value={totalRiskAndEthics > 0 ? `${totalRiskAndEthics} Alerts` : "Secure"}
                sub={`${alertCount} Risks | ${ethicsPending} Audit`}
                active={activeMetric === 'risk_ethics'}
                status={totalRiskAndEthics > 0 ? "bad" : "good"}
                onClick={setActiveMetric}
                tooltip="Sentinel Alerts, Safety Violations & Prompt Audits"
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
                sub="Knowledge ROI"
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
        </div>
    );
};
