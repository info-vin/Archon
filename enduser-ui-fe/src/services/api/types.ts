import { EmployeeRole, TaskStatus, TaskPriority, BlogPost } from '../../types.ts';

export type LoginCredentials = {
  email: string;
  password?: string;
};

export type RegistrationData = {
  name: string;
  email: string;
  password?: string;
};

export type AdminNewUserData = {
  name: string;
  email: string;
  password: string;
  role: EmployeeRole;
  status: 'active' | 'inactive' | 'suspended';
};

export type NewTaskData = {
  project_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  assigneeId?: string | null;
  due_date: string;
  priority: TaskPriority;
  knowledge_source_ids?: string[];
  is_recurring?: boolean;
  crawler_target_id?: string | null;
  schedule_config?: any;
};

export type NewProjectData = {
  title: string;
  description?: string;
};

export type UpdateTaskData = Partial<Omit<NewTaskData, 'project_id'> & { assigneeId: string | null; status: TaskStatus }>;

export type NewBlogPostData = Omit<BlogPost, 'id' | 'publishDate'> & { authorName?: string, publishDate?: string };
