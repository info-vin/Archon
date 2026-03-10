import { getHeaders, handleResponse } from './base';
import { Task, Project } from '../../types.ts';
import { NewTaskData, NewProjectData, UpdateTaskData } from './types';

export const tasksApi = {
  async getTasks(includeClosed: boolean = false, includeUnassigned: boolean = false, assigneeId?: string, perPage: number = 50): Promise<Task[]> {
    const queryParams = new URLSearchParams({
        include_closed: includeClosed.toString(),
        include_unassigned: includeUnassigned.toString(),
        per_page: perPage.toString()
    });
    if (assigneeId) queryParams.append('assignee_id', assigneeId);

    const response = await fetch(`/api/tasks?${queryParams.toString()}`, { headers: await getHeaders() });
    const data = await handleResponse(response, 'Failed to fetch tasks');
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object' && Array.isArray(data.tasks)) return data.tasks;
    return [];
  },

  async deleteTask(taskId: string): Promise<void> {
    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE',
        headers: await getHeaders()
    });
    await handleResponse(response, 'Failed to archive task');
  },

  async getProjects(): Promise<Project[]> {
    const response = await fetch('/api/projects?include_computed_status=true', { headers: await getHeaders() });
    const data = await handleResponse(response, 'Failed to fetch projects');
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object' && Array.isArray(data.projects)) return data.projects;
    return [];
  },

  async createProject(projectData: NewProjectData): Promise<{ project: Project }> {
    const response = await fetch('/api/projects', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify(projectData)
    });
    return handleResponse(response, 'Failed to create project');
  },

  async createTask(task_data: NewTaskData): Promise<Task> {
    const { assigneeId, ...rest } = task_data;
    const payload = {
      ...rest,
      assignee_id: assigneeId,
      is_recurring: task_data.is_recurring,
      crawler_target_id: task_data.crawler_target_id,
      schedule_config: task_data.schedule_config
    };

    const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify(payload)
    });
    return handleResponse(response, 'Failed to create task');
  },

  async updateTask(taskId: string, updates: UpdateTaskData): Promise<Task> {
    const { assigneeId, ...rest } = updates;
    const payload = { ...rest, assignee_id: assigneeId };
    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: await getHeaders(),
        body: JSON.stringify(payload)
    });
    return handleResponse(response, 'Failed to update task');
  },

  async refineTaskDescription(title: string, description: string): Promise<string> {
    const response = await fetch('/api/tasks/refine-description', {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify({ title, description })
    });
    const data = await handleResponse(response, 'Failed to refine task');
    return data.refined_description;
  },

  async generateTaskFromAlert(alertId: string, assigneeId?: string): Promise<any> {
    const response = await fetch(`/api/marketing/manager/alerts/${alertId}/dispatch`, {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify({ assignee_id: assigneeId })
    });
    return handleResponse(response, 'Failed to generate task from alert');
  },

  async getPendingChanges(): Promise<any[]> {
    const response = await fetch('/api/changes', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch pending changes');
  },

  async approveChange(changeId: string): Promise<any> {
    const response = await fetch(`/api/changes/${changeId}/approve`, {
        method: 'POST',
        headers: await getHeaders(),
    });
    return handleResponse(response, 'Failed to approve change');
  },

  async rejectChange(changeId: string): Promise<any> {
    const response = await fetch(`/api/changes/${changeId}/reject`, {
        method: 'POST',
        headers: await getHeaders(),
    });
    return handleResponse(response, 'Failed to reject change');
  },

  async approvePromptChange(versionId: string): Promise<any> {
    const response = await fetch(`/api/stats/approve-prompt-change/${versionId}`, {
        method: 'POST',
        headers: await getHeaders()
    });
    return handleResponse(response, 'Failed to approve prompt change');
  }
};
