import { getHeaders, handleResponse } from './base';
import { JobData, AiHealthStatus, AlertItem, BlogPost, CrawlerTarget, DocumentVersion } from '../../types.ts';
import { NewBlogPostData } from './types';

export const opsApi = {
  async searchJobs(keyword: string): Promise<JobData[]> {
    const response = await fetch(`/api/marketing/jobs?keyword=${encodeURIComponent(keyword)}`, { headers: await getHeaders() });
    return handleResponse(response, 'Failed to search jobs');
  },

  async generatePitch(jobTitle: string, company: string, description: string): Promise<{ content: string; references: string[] }> {
    const response = await fetch('/api/marketing/generate-pitch', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify({ job_title: jobTitle, company, description })
    });
    return handleResponse(response, 'Failed to generate pitch');
  },

  async getSystemPrompts(): Promise<any[]> {
    const response = await fetch('/api/system/prompts', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch prompts');
  },

  async updateSystemPrompt(promptName: string, data: { content: string; description?: string }): Promise<any> {
    const response = await fetch(`/api/system/prompts/${promptName}`, {
        method: 'POST', 
        headers: await getHeaders(),
        body: JSON.stringify({ prompt: data.content, description: data.description })
    });
    return handleResponse(response, 'Failed to update system prompt');
  },

  async getSystemSettings(category?: string): Promise<any[]> {
    const query = category ? `?category=${category}` : '';
    const response = await fetch(`/api/system/settings${query}`, { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch settings');
  },

  async updateSystemSetting(key: string, data: { value: string; description?: string }): Promise<any> {
    const response = await fetch(`/api/system/settings/${key}`, {
        method: 'PATCH',
        headers: await getHeaders(),
        body: JSON.stringify(data)
    });
    return handleResponse(response, 'Failed to update setting');
  },

  async analyzeExtractionUrl(url: string): Promise<any> {
    const response = await fetch('/api/extraction/analyze', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify({ url })
    });
    return handleResponse(response, 'Analysis failed');
  },

  async getExtractionSchemas(): Promise<any[]> {
    const response = await fetch('/api/extraction/schemas', { headers: await getHeaders() });
    return handleResponse(response, "API Request failed");
  },

  async createExtractionSchema(data: any): Promise<any> {
    const response = await fetch('/api/extraction/schemas', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify(data)
    });
    return handleResponse(response, "API Request failed");
  },

  async deleteExtractionSchema(id: string): Promise<void> {
    const response = await fetch(`/api/extraction/schemas/${id}`, {
        method: 'DELETE',
        headers: await getHeaders()
    });
    await handleResponse(response, 'Failed to delete schema');
  },

  async runExtraction(url: string, schemaId: string): Promise<any> {
    const response = await fetch('/api/extraction/run', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify({ url, schema_id: schemaId })
    });
    return handleResponse(response, 'Extraction failed to start');
  },

  async getAiHealth(): Promise<AiHealthStatus> {
      const response = await fetch('/api/system/health/ai', { headers: await getHeaders() });
      return handleResponse(response, "API Request failed");
  },

  async getManagerAlerts(): Promise<AlertItem[]> {
      const response = await fetch('/api/logs/alerts', { headers: await getHeaders() });
      return handleResponse(response, "API Request failed");
  },

  async getAlerts(): Promise<AlertItem[]> {
      return this.getManagerAlerts();
  },

  async dispatchAlertTask(alertId: string, assigneeId?: string): Promise<any> {

      const response = await fetch('/api/tasks/generate-from-alert', {
          method: 'POST',
          headers: await getHeaders(),
          body: JSON.stringify({ alert_id: alertId, assignee_id: assigneeId })
      });
      return handleResponse(response, "API Request failed");
  },

  async seedKnowledgeBase(): Promise<{ indexed_count: number; total_files: number }> {
      console.log("Mocking seedKnowledgeBase/Rebuild Index...");
      await new Promise(resolve => setTimeout(resolve, 1000));
      return { indexed_count: 0, total_files: 0 };
  },

  async getVisitLogs(userId?: string): Promise<any[]> {
    const query = userId ? `?user_id=${userId}` : '';
    const response = await fetch(`/api/visit-logs/${query}`, { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch visit logs');
  },

  async createVisitLog(formData: FormData): Promise<any> {
    const headers = await getHeaders();
    delete headers['Content-Type']; 
    const response = await fetch('/api/visit-logs/', {
        method: 'POST',
        headers: headers,
        body: formData
    });
    return handleResponse(response, 'Failed to create visit log');
  },

  async getAttendanceStatus(): Promise<{ status: string; clock_in_time: string | null; location: string | null }> {
      const response = await fetch('/api/visit-logs/attendance/status', { headers: await getHeaders() });
      return handleResponse(response, 'Failed to fetch attendance status');
  },

  async clockIn(data: { latitude?: number; longitude?: number; location_name?: string; status: string }): Promise<void> {
      const response = await fetch('/api/visit-logs/attendance/clock-in', {
          method: 'POST',
          headers: await getHeaders(),
          body: JSON.stringify(data)
      });
      await handleResponse(response, 'Clock In failed');
  },

  async clockOut(): Promise<void> {
      const response = await fetch('/api/visit-logs/attendance/clock-out', {
          method: 'POST',
          headers: await getHeaders()
      });
      await handleResponse(response, 'Clock Out failed');
  },

  async getEthicsEvents(): Promise<any[]> {
    const response = await fetch('/api/ethics/events', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch ethics events');
  },

  async triggerSentinel(): Promise<any> {
    const response = await fetch('/api/marketing/manager/sentinel/run', {
        method: 'POST',
        headers: await getHeaders(),
    });
    return handleResponse(response, 'Sentinel trigger failed');
  },

  async getLeads(): Promise<any[]> {
    const response = await fetch('/api/marketing/leads', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch leads');
  },

  async createLead(leadData: any): Promise<any> {
    const response = await fetch('/api/marketing/leads', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify(leadData)
    });
    return handleResponse(response, 'Failed to create lead');
  },

  async updateLead(id: string, updates: any): Promise<any> {
    const response = await fetch(`/api/marketing/leads/${id}`, {
        method: 'PATCH',
        headers: await getHeaders(),
        body: JSON.stringify(updates)
    });
    return handleResponse(response, 'Failed to update lead');
  },

  async promoteLead(id: string, data: any): Promise<any> {
    const response = await fetch(`/api/marketing/leads/${id}/promote`, {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify(data)
    });
    return handleResponse(response, 'Failed to promote lead');
  },

  async resetLeads(): Promise<void> {
    const response = await fetch('/api/marketing/leads/reset', {
        method: 'POST',
        headers: await getHeaders()
    });
    await handleResponse(response, 'Failed to reset leads');
  },

  async getBlogPosts(): Promise<BlogPost[]> {
    const response = await fetch('/api/marketing/blog', { headers: await getHeaders() });
    const data = await handleResponse(response, 'Failed to fetch blog posts');
    return data.posts || [];
  },

  async getBlogPost(id: string): Promise<BlogPost> {
    const response = await fetch(`/api/marketing/blog/${id}`, { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch blog post');
  },

  async createBlogPost(data: NewBlogPostData): Promise<BlogPost> {
    const response = await fetch('/api/marketing/blog', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify(data)
    });
    return handleResponse(response, 'Failed to create blog post');
  },

  async updateBlogPost(id: string, data: Partial<BlogPost>): Promise<BlogPost> {
    const response = await fetch(`/api/marketing/blog/${id}`, {
        method: 'PATCH',
        headers: await getHeaders(),
        body: JSON.stringify(data)
    });
    return handleResponse(response, 'Failed to update blog post');
  },

  async deleteBlogPost(id: string): Promise<void> {
    const response = await fetch(`/api/marketing/blog/${id}`, {
        method: 'DELETE',
        headers: await getHeaders()
    });
    await handleResponse(response, 'Failed to delete blog post');
  },

  async draftBlogPost(data: any): Promise<any> {
    const response = await fetch('/api/marketing/blog/draft', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify(data)
    });
    return handleResponse(response, 'Failed to draft blog post');
  },

  async submitBlogPost(id: string): Promise<any> {
    const response = await fetch(`/api/marketing/blog/${id}/submit`, {
        method: 'POST',
        headers: await getHeaders()
    });
    return handleResponse(response, 'Failed to submit blog post');
  },

  async updateBlogPostStatus(id: string, status: string): Promise<void> {
    const response = await fetch(`/api/marketing/blog/${id}/status`, {
        method: 'PATCH',
        headers: await getHeaders(),
        body: JSON.stringify({ status })
    });
    await handleResponse(response, 'Failed to update blog status');
  },

  async uploadFile(file: File): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const headers = await getHeaders();
    delete headers['Content-Type'];
    const response = await fetch('/api/admin/upload', {
        method: 'POST',
        headers: headers,
        body: formData
    });
    return handleResponse(response, 'Upload failed');
  },

  async getKnowledgeItems(): Promise<any[]> {
    const response = await fetch('/api/knowledge', { headers: await getHeaders() });
    const data = await handleResponse(response, 'Failed to fetch knowledge');
    return data.items || [];
  },

  async getCrawlerTargets(): Promise<CrawlerTarget[]> {
    const response = await fetch('/api/admin/crawler-targets', { headers: await getHeaders() });
    const data = await handleResponse(response, 'Failed to fetch crawler targets');
    return data.targets || [];
  },

  async createCrawlerTarget(targetData: any): Promise<CrawlerTarget> {
    const response = await fetch('/api/admin/crawler-targets', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify(targetData)
    });
    return handleResponse(response, 'Failed to create crawler target');
  },

  async deleteCrawlerTarget(id: string): Promise<void> {
    const response = await fetch(`/api/admin/crawler-targets/${id}`, {
        method: 'DELETE',
        headers: await getHeaders()
    });
    await handleResponse(response, 'Failed to delete crawler target');
  },

  async getDocumentVersions(): Promise<DocumentVersion[]> {
    const response = await fetch('/api/admin/document-versions', { headers: await getHeaders() });
    const data = await handleResponse(response, 'Failed to fetch document versions');
    return data.versions || [];
  },

  async getConnectivityLogs(): Promise<any[]> {
    const response = await fetch('/api/system/logs/connectivity', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch connectivity logs');
  },

  async getContentSources(): Promise<any[]> {
    const response = await fetch('/api/marketing/content-sources', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch content sources');
  },

  async getContentContext(id: string, type: string): Promise<any> {
    const response = await fetch(`/api/marketing/content-context/${type}/${id}`, { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch content context');
  },

  async generateLogo(brandName: string): Promise<any> {
    const response = await fetch('/api/marketing/generate-logo', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify({ brand_name: brandName })
    });
    return handleResponse(response, 'Failed to generate logo');
  },

  async diagnoseFile(filePath: string): Promise<any> {
    const response = await fetch('/api/admin/diagnose', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify({ file_path: filePath })
    });
    return handleResponse(response, 'Diagnostic failed');
  }
};
