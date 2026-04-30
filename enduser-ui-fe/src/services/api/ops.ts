import { JobData, AiHealthStatus, AlertItem, BlogPost, CrawlerTarget, DocumentVersion } from '../../types.ts';
import { NewBlogPostData } from './types';
import { callAPI } from './apiClient';

export const opsApi = {
  async searchJobs(keyword: string): Promise<JobData[]> {
    return await callAPI<JobData[]>(`/api/marketing/jobs?keyword=${encodeURIComponent(keyword)}`);
  },

  async generatePitch(jobTitle: string, company: string, description: string): Promise<{ content: string; references: string[] }> {
    return await callAPI<{ content: string; references: string[] }>('/api/marketing/generate-pitch', {
        method: 'POST',
        body: JSON.stringify({ job_title: jobTitle, company, description })
    });
  },

  async getSystemPrompts(): Promise<any[]> {
    return await callAPI<any[]>('/api/system/prompts');
  },

  async updateSystemPrompt(promptName: string, data: { content: string; description?: string }): Promise<any> {
    return await callAPI(`/api/system/prompts/${promptName}`, {
        method: 'POST', 
        body: JSON.stringify({ prompt: data.content, description: data.description })
    });
  },

  async getSystemSettings(category?: string): Promise<any[]> {
    const query = category ? `?category=${category}` : '';
    return await callAPI<any[]>(`/api/system/settings${query}`);
  },

  async updateSystemSetting(key: string, data: { value: string; description?: string }): Promise<any> {
    return await callAPI(`/api/system/settings/${key}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    });
  },

  async analyzeExtractionUrl(url: string): Promise<any> {
    return await callAPI('/api/extraction/analyze', {
        method: 'POST',
        body: JSON.stringify({ url })
    });
  },

  async getExtractionSchemas(): Promise<any[]> {
    return await callAPI<any[]>('/api/extraction/schemas');
  },

  async createExtractionSchema(data: any): Promise<any> {
    return await callAPI('/api/extraction/schemas', {
        method: 'POST',
        body: JSON.stringify(data)
    });
  },

  async deleteExtractionSchema(id: string): Promise<void> {
    await callAPI(`/api/extraction/schemas/${id}`, {
        method: 'DELETE'
    });
  },

  async runExtraction(url: string, schemaId: string): Promise<any> {
    return await callAPI('/api/extraction/run', {
        method: 'POST',
        body: JSON.stringify({ url, schema_id: schemaId })
    });
  },

  async getAiHealth(): Promise<AiHealthStatus> {
    return await callAPI<AiHealthStatus>('/api/system/health/ai');
  },

  async getManagerAlerts(): Promise<AlertItem[]> {
    return await callAPI<AlertItem[]>('/api/logs/alerts');
  },

  async getAlerts(): Promise<AlertItem[]> {
    return this.getManagerAlerts();
  },

  async dispatchAlertTask(alertId: string, assigneeId?: string): Promise<any> {
    return await callAPI('/api/tasks/generate-from-alert', {
        method: 'POST',
        body: JSON.stringify({ alert_id: alertId, assignee_id: assigneeId })
    });
  },

  async seedKnowledgeBase(): Promise<{ indexed_count: number; total_files: number }> {
    console.log("Rebuilding Knowledge Index...");
    await new Promise(resolve => setTimeout(resolve, 500));
    return { indexed_count: 0, total_files: 0 };
  },

  async getVisitLogs(userId?: string): Promise<any[]> {
    const query = userId ? `?user_id=${userId}` : '';
    return await callAPI<any[]>(`/api/visit-logs/${query}`);
  },

  async createVisitLog(formData: FormData): Promise<any> {
    return await callAPI('/api/visit-logs/', {
        method: 'POST',
        body: formData
    });
  },

  async getAttendanceStatus(): Promise<{ status: string; clock_in_time: string | null; location: string | null }> {
    return await callAPI<{ status: string; clock_in_time: string | null; location: string | null }>('/api/visit-logs/attendance/status');
  },

  async clockIn(data: { latitude?: number; longitude?: number; location_name?: string; status: string }): Promise<void> {
    await callAPI('/api/visit-logs/attendance/clock-in', {
        method: 'POST',
        body: JSON.stringify(data)
    });
  },

  async clockOut(): Promise<void> {
    await callAPI('/api/visit-logs/attendance/clock-out', {
        method: 'POST'
    });
  },

  async getEthicsEvents(): Promise<any[]> {
    return await callAPI<any[]>('/api/ethics/events');
  },

  async triggerSentinel(): Promise<any> {
    return await callAPI('/api/marketing/manager/sentinel/run', {
        method: 'POST'
    });
  },

  async getLeads(): Promise<any[]> {
    return await callAPI<any[]>('/api/marketing/leads', {
        headers: { 'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache' }
    });
  },

  async createLead(leadData: any): Promise<any> {
    return await callAPI('/api/marketing/leads', {
        method: 'POST',
        body: JSON.stringify(leadData)
    });
  },

  async updateLead(id: string, updates: any): Promise<any> {
    return await callAPI(`/api/marketing/leads/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(updates)
    });
  },

  async promoteLead(id: string, data: any): Promise<any> {
    return await callAPI(`/api/marketing/leads/${id}/promote`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
  },

  async resetLeads(): Promise<void> {
    await callAPI('/api/marketing/leads/reset', {
        method: 'POST'
    });
  },

  async getBlogPosts(): Promise<BlogPost[]> {
    const data = await callAPI<any>('/api/blogs');
    return Array.isArray(data) ? data : (data.blogs || data.posts || []);
  },

  async getBlogPost(id: string): Promise<BlogPost> {
    return await callAPI<BlogPost>(`/api/blogs/${id}`);
  },

  async createBlogPost(data: NewBlogPostData): Promise<BlogPost> {
    return await callAPI<BlogPost>('/api/blogs', {
        method: 'POST',
        body: JSON.stringify(data)
    });
  },

  async updateBlogPost(id: string, data: Partial<BlogPost>): Promise<BlogPost> {
    return await callAPI<BlogPost>(`/api/blogs/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    });
  },

  async deleteBlogPost(id: string): Promise<void> {
    await callAPI(`/api/blogs/${id}`, {
        method: 'DELETE'
    });
  },

  async draftBlogPost(data: any): Promise<any> {
    return await callAPI('/api/marketing/blog/draft', {
        method: 'POST',
        body: JSON.stringify(data)
    });
  },

  async submitBlogPost(id: string): Promise<any> {
    return await callAPI(`/api/blogs/${id}/submit`, {
        method: 'POST'
    });
  },

  async updateBlogPostStatus(id: string, status: string): Promise<void> {
    await callAPI(`/api/blogs/${id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status })
    });
  },

  async uploadFile(file: File): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append('file', file);
    return await callAPI<{ url: string }>('/api/admin/upload', {
        method: 'POST',
        body: formData
    });
  },

  async getKnowledgeItems(): Promise<any[]> {
    const data = await callAPI<any>('/api/knowledge');
    return data.items || [];
  },

  async searchKnowledgeItems(query: string, limit: number = 5): Promise<any[]> {
    return await callAPI<any[]>('/api/knowledge-items/search', {
        method: 'POST',
        body: JSON.stringify({ query, limit })
    });
  },

  async getCrawlerTargets(): Promise<CrawlerTarget[]> {
    const data = await callAPI<any>('/api/admin/crawler-targets');
    return data.targets || [];
  },

  async createCrawlerTarget(targetData: any): Promise<CrawlerTarget> {
    return await callAPI<CrawlerTarget>('/api/admin/crawler-targets', {
        method: 'POST',
        body: JSON.stringify(targetData)
    });
  },

  async deleteCrawlerTarget(id: string): Promise<void> {
    await callAPI(`/api/admin/crawler-targets/${id}`, {
        method: 'DELETE'
    });
  },

  async getDocumentVersions(): Promise<DocumentVersion[]> {
    const data = await callAPI<any>('/api/admin/document-versions');
    return data.versions || [];
  },

  async getConnectivityLogs(): Promise<any[]> {
    return await callAPI<any[]>('/api/system/logs/connectivity');
  },

  async getConnectivityLogsByType(type: string): Promise<any[]> {
    return await callAPI<any[]>(`/api/system/logs/connectivity?type=${type}`);
  },

  async getContentSources(): Promise<any[]> {
    return await callAPI<any[]>('/api/marketing/sources');
  },

  async getContentContext(id: string, type: string): Promise<any> {
    return await callAPI<any>(`/api/marketing/context/${id}?source_type=${type}`);
  },

  async generateLogo(brandName: string): Promise<any> {
    return await callAPI('/api/marketing/generate-logo', {
        method: 'POST',
        body: JSON.stringify({ style: brandName })
    });
  },

  async diagnoseFile(filePath: string): Promise<any> {
    return await callAPI('/api/admin/diagnose', {
        method: 'POST',
        body: JSON.stringify({ file_path: filePath })
    });
  }
};
