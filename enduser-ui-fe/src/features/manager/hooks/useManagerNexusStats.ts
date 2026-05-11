import { useState, useCallback, useEffect } from 'react';
import { api } from '../../../services/api.ts';
import { SystemOverview, Employee, AlertItem } from '../../../types.ts';
import { useAuth } from '@/hooks/useAuth';

export type MetricCategory = 'integrity' | 'resources' | 'op_load' | 'sent_risks' | 'active_force' | 'ethics' | 'collab' | 'graph' | 'velocity' | 'prompts';

export interface ScoringRule {
    key: string;
    label: string;
    weight: number;
}

export interface RulesMetadata {
    version: string;
    updated_at: string;
    updated_by: string;
}

export const useManagerNexusStats = () => {
    const { user } = useAuth();
    
    // Status
    const [loading, setLoading] = useState(true);
    const [processingId, setProcessingId] = useState<string | null>(null);

    // Data States
    const [overview, setOverview] = useState<SystemOverview | null>(null);
    const [healthTrend, setHealthTrend] = useState<{ trend: any[], audit: any[] }>({ trend: [], audit: [] });
    const [team, setTeam] = useState<Employee[]>([]);
    const [approvals, setApprovals] = useState<{blogs: any[], leads: any[]}>({blogs: [], leads: []});
    const [alerts, setAlerts] = useState<AlertItem[]>([]);
    const [aiStats, setAiStats] = useState<any>(null);
    const [commanderTrends, setCommanderTrends] = useState<any[]>([]);
    const [forceReadiness, setForceReadiness] = useState<any>(null);
    const [businessRisks, setBusinessRisks] = useState<any[]>([]);
    const [collabSynergy, setCollabSynergy] = useState<any>(null);
    const [slaReliability, setSlaReliability] = useState<any>(null);
    const [ethicsAudit, setEthicsAudit] = useState<any>(null);
    const [knowledgeRoi, setKnowledgeRoi] = useState<any>(null);
    const [codeProposals, setCodeProposals] = useState<any[]>([]);

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

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const results = await Promise.allSettled([
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
                api.getKnowledgeRoi(),
                api.getPendingChanges()
            ]);

            const getData = <T>(index: number, fallback: T): T => {
                const res = results[index];
                if (res.status === 'fulfilled' && res.value !== null && res.value !== undefined) {
                    return res.value as T;
                }
                return fallback;
            };

            setOverview(getData(0, null));
            setTeam(getData(1, []));
            setApprovals(getData(2, { blogs: [], leads: [] }));
            setAlerts(getData(3, []));
            setAiStats(getData(4, null));
            const settings = getData(5, []);
            setCommanderTrends(getData(6, []));
            setForceReadiness(getData(7, null));
            setBusinessRisks(getData(8, []));
            setCollabSynergy(getData(9, null));
            setSlaReliability(getData(10, null));
            setEthicsAudit(getData(11, { violations: [], status: 'clear' }));
            setKnowledgeRoi(getData(12, { roi: 0, active_nodes: 0 }));
            setCodeProposals(getData(13, []) || []);

            if (settings && (settings as any[]).length > 0) {
                 try {
                     const parsedRules = JSON.parse((settings as any[])[0].value);
                     if (parsedRules.weights) setRules(parsedRules.weights);
                     if (parsedRules.version) setRulesMeta(prev => ({ ...prev, version: parsedRules.version, updated_by: parsedRules.updated_by }));
                 } catch (e) {
                     console.error("Failed to parse scoring rules", e);
                 }
            }
            
            // Separated for resilience
            api.getHealthTrend().then(data => {
                setHealthTrend(data);
            }).catch(e => console.error("Trend Load Failed", e));

        } catch (e) {
            console.error("Nexus Fatal Load Failure", e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleDispatch = async (alertId: string) => {
        setProcessingId(alertId);
        try {
            await api.generateTaskFromAlert(alertId);
            setAlerts(prev => prev.filter(a => a.id !== alertId)); 
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

    const handleRebuildIndex = async () => {
        if (!window.confirm("Rebuild Knowledge Base index? This consumes significant tokens.")) return;
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
            fetchData();
        } catch (e: any) {
            alert("Approval failed: " + e.message);
        } finally {
            setProcessingId(null);
        }
    };

    const handleCodeAction = async (id: string, action: 'approve' | 'reject') => {
        setProcessingId(id);
        try {
            if (action === 'approve') await api.approveChange(id);
            else await api.rejectChange(id);
            alert(action === 'approve' ? 'Change Applied' : 'Change Rejected');
            fetchData();
        } catch (err: any) {
            alert("Action failed: " + err.message);
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

    return {
        loading,
        processingId, setProcessingId,
        overview, healthTrend, team, approvals, alerts, aiStats,
        commanderTrends, forceReadiness, businessRisks, collabSynergy,
        slaReliability, ethicsAudit, knowledgeRoi, codeProposals,
        rules, setRules, rulesMeta, setRulesMeta,
        fetchData, handleDispatch, handleApprovePrompt, handleRebuildIndex,
        handleApproveContent, handleCodeAction, handleRuleChange, handleSaveRules
    };
};
