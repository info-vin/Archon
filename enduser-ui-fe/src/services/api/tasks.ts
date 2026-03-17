import { Task, Project } from '../../types.ts';
import { NewTaskData, NewProjectData, UpdateTaskData } from './types';
import { callAPI } from './apiClient';

export const tasksApi = {
  async getTasks(includeClosed: boolean = false, includeUnassigned: boolean = false, assigneeId?: string, perPage: number = 50): Promise<Task[]> {
    const queryParams = new URLSearchParams({
        include_closed: includeClosed.toString(),
        include_unassigned: includeUnassigned.toString(),
        per_page: perPage.toString()
    });
    if (assigneeId) queryParams.append('assignee_id', assigneeId);

    const data = await callAPI<any>(`/api/tasks?${queryParams.toString()}`);
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object' && Array.isArray(data.tasks)) return data.tasks;
    return [];
  },

  async deleteTask(taskId: string): Promise<void> {
    await callAPI(`/api/tasks/${taskId}`, {
        method: 'DELETE'
    });
  },

  async getProjects(): Promise<Project[]> {
    const data = await callAPI<any>('/api/projects?include_computed_status=true');
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object' && Array.isArray(data.projects)) return data.projects;
    return [];
  },

  async createProject(projectData: NewProjectData): Promise<{ project: Project }> {
    return await callAPI<{ project: Project }>('/api/projects', {
        method: 'POST',
        body: JSON.stringify(projectData)
    });
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

    return await callAPI<Task>('/api/tasks', {
        method: 'POST',
        body: JSON.stringify(payload)
    });
  },

  async updateTask(taskId: string, updates: UpdateTaskData): Promise<Task> {
    const { assigneeId, ...rest } = updates;
    const payload = { ...rest, assignee_id: assigneeId };
    return await callAPI<Task>(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload)
    });
  },

  async refineTaskDescription(title: string, description: string): Promise<string> {
    const data = await callAPI<{ refined_description: string }>('/api/tasks/refine-description', {
        method: 'POST',
        body: JSON.stringify({ title, description })
    });
    return data.refined_description;
  },

  async generateTaskFromAlert(alertId: string, assigneeId?: string): Promise<any> {
    return await callAPI(`/api/marketing/manager/alerts/${alertId}/dispatch`, {
        method: 'POST',
        body: JSON.stringify({ assignee_id: assigneeId })
    });
  },

  async getPendingChanges(): Promise<any[]> {
    return await callAPI<any[]>('/api/changes');
  },

  async approveChange(changeId: string): Promise<any> {
    return await callAPI(`/api/changes/${changeId}/approve`, {
        method: 'POST'
    });
  },

  async rejectChange(changeId: string): Promise<any> {
    return await callAPI(`/api/changes/${changeId}/reject`, {
        method: 'POST'
    });
  },

  async approvePromptChange(versionId: string): Promise<any> {
    return await callAPI(`/api/stats/approve-prompt-change/${versionId}`, {
        method: 'POST'
    });
  }
};
