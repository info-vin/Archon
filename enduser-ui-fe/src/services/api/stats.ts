import { getHeaders, handleResponse } from './base';
import { TaskStats, MemberPerformance, AiUsageStats, SystemOverview } from '../../types.ts';

export const statsApi = {
  async getAgentXPStats(): Promise<any[]> {
    const response = await fetch('/api/stats/agent-xp', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch XP stats');
  },

  async getTaskDistribution(): Promise<TaskStats[]> {
    const response = await fetch('/api/stats/tasks-by-status', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch task distribution');
  },

  async getAiUsage(): Promise<AiUsageStats> {
    const response = await fetch('/api/stats/ai-usage', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch AI usage');
  },

  async getSystemOverview(): Promise<SystemOverview> {
      const response = await fetch('/api/stats/system-overview', { headers: await getHeaders() });
      return handleResponse(response, 'Failed to fetch system overview');
  },

  async getMemberPerformance(): Promise<MemberPerformance[]> {
    const response = await fetch('/api/stats/member-performance', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch performance stats');
  },

  async getTokenUsageDetails(days: number = 7): Promise<any[]> {
    const response = await fetch(`/api/stats/token-usage/details?days=${days}`, {
        headers: await getHeaders()
    });
    return handleResponse(response, 'Failed to fetch usage details');
  },

  async getHealthTrend(): Promise<{ trend: any[]; audit: any[] }> {
    const response = await fetch('/api/stats/health-trend', { headers: await getHeaders() });
    return handleResponse(response, 'API Request failed');
  },

  async getCommanderTrends(): Promise<any[]> {
    const response = await fetch('/api/stats/commander-trends', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch commander trends');
  },

  async getForceReadiness(): Promise<any> {
    const response = await fetch('/api/stats/force-readiness', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch force readiness');
  },

  async getCollabSynergy(): Promise<any> {
    const response = await fetch('/api/stats/collab-synergy', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch collaboration synergy');
  },

  async getSlaReliability(): Promise<any> {
    const response = await fetch('/api/stats/sla-reliability', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch SLA reliability');
  },

  async getEthicsAuditQueue(): Promise<any> {
    const response = await fetch('/api/stats/ethics-audit-queue', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch ethics audit queue');
  },

  async getKnowledgeRoi(): Promise<any> {
    const response = await fetch('/api/stats/knowledge-roi', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch knowledge ROI');
  },

  async getBusinessRisks(): Promise<any[]> {
    const response = await fetch('/api/stats/business-risks', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch business risks');
  }
};
