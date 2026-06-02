import { TaskStats, MemberPerformance, AiUsageStats, SystemOverview } from '../../types.ts';
import { callAPI } from './apiClient';

export const statsApi = {
  async getAgentXPStats(): Promise<any[]> {
    return await callAPI<any[]>('/api/stats/agent-xp');
  },

  async getTaskDistribution(): Promise<TaskStats[]> {
    return await callAPI<TaskStats[]>('/api/stats/tasks-by-status');
  },

  async getAiUsage(): Promise<AiUsageStats> {
    return await callAPI<AiUsageStats>('/api/stats/ai-usage');
  },

  async getSystemOverview(): Promise<SystemOverview> {
    return await callAPI<SystemOverview>('/api/stats/system-overview');
  },

  async getMemberPerformance(): Promise<MemberPerformance[]> {
    return await callAPI<MemberPerformance[]>('/api/stats/member-performance');
  },

  async getTokenUsageDetails(days: number = 7): Promise<any[]> {
    return await callAPI<any[]>(`/api/stats/token-usage/details?days=${days}`);
  },

  async getRecentTokenUsage(limit: number = 20): Promise<any[]> {
    return await callAPI<any[]>(`/api/stats/token-usage/recent?limit=${limit}`);
  },

  async getHealthTrend(): Promise<{ trend: any[]; audit: any[] }> {
    return await callAPI<{ trend: any[]; audit: any[] }>('/api/stats/health-trend');
  },

  async getCommanderTrends(): Promise<any[]> {
    return await callAPI<any[]>('/api/stats/commander-trends');
  },

  async getForceReadiness(): Promise<any> {
    return await callAPI<any>('/api/stats/force-readiness');
  },

  async getCollabSynergy(): Promise<any> {
    return await callAPI<any>('/api/stats/collab-synergy');
  },

  async getSlaReliability(): Promise<any> {
    return await callAPI<any>('/api/stats/sla-reliability');
  },

  async getEthicsAuditQueue(): Promise<any> {
    return await callAPI<any>('/api/stats/ethics-audit-queue');
  },

  async getKnowledgeRoi(): Promise<any> {
    return await callAPI<any>('/api/stats/knowledge-roi');
  },

  async getBusinessRisks(): Promise<any[]> {
    return await callAPI<any[]>('/api/stats/business-risks');
  },

  async getPendingApprovals(): Promise<{ blogs: any[]; leads: any[] }> {
    const data = await callAPI<any>('/api/marketing/approvals');
    // Ensure the data has the expected structure even if backend returns an array
    if (Array.isArray(data)) {
        return {
            blogs: data.filter(item => item.type === 'blog' || item.category === 'blog'),
            leads: data.filter(item => item.type === 'lead' || item.category === 'lead')
        };
    }
    return data || { blogs: [], leads: [] };
  },

  async processApproval(type: string, id: string, action: 'approve' | 'reject', reason?: string): Promise<any> {
    return await callAPI(`/api/marketing/approvals/${type}/${id}/${action}`, {
        method: 'POST',
        body: JSON.stringify({ notes: reason })
    });
  },

  async generateRejectReason(type: string, id: string): Promise<{ notes: string }> {
    return await callAPI<{ notes: string }>(`/api/marketing/approvals/reject-suggestion`, {
        method: 'POST',
        body: JSON.stringify({ item_type: type, item_id: id })
    });
  },

  async getMarketingTrends(): Promise<any[]> {
    return await callAPI<any[]>('/api/marketing/trends');
  },

  async getMarketStats(): Promise<any> {
    return await callAPI<any>('/api/marketing/stats');
  },

  async getMarketingIntelligence(): Promise<any> {
    return await callAPI<any>('/api/marketing/intelligence');
  },

  async rejectSuggestion(id: string): Promise<any> {
    return await callAPI(`/api/marketing/suggestions/${id}/reject`, {
        method: 'POST'
    });
  },

  async nanaBananaProxy(data: any): Promise<any> {
    return await callAPI('/api/proxy/nana-banana', {
        method: 'POST',
        body: JSON.stringify(data)
    });
  },

  async getConsolidatedNexusState(): Promise<any> {
    return await callAPI<any>('/api/stats/consolidated');
  }
};
