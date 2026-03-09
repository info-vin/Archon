import { getHeaders, handleResponse } from './base';
import { JobData, AiHealthStatus, AlertItem } from '../../types.ts';

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

  async dispatchAlertTask(alertId: string, assigneeId?: string): Promise<any> {
      const response = await fetch('/api/tasks/generate-from-alert', {
          method: 'POST',
          headers: await getHeaders(),
          body: JSON.stringify({ alert_id: alertId, assignee_id: assigneeId })
      });
      return handleResponse(response, "API Request failed");
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
  }
};
