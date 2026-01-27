export enum EmployeeRole {
  SYSTEM_ADMIN = 'system_admin',
  ADMIN = 'admin',
  MANAGER = 'manager',
  PROJECT_MANAGER = 'project_manager', // Legacy, treat as MANAGER
  SENIOR_MEMBER = 'senior_member', // Legacy, treat as MEMBER
  MEMBER = 'member',
  EMPLOYEE = 'employee', // Alias for MEMBER
  SALES = 'sales',
  MARKETING = 'marketing',
  VIEWER = 'viewer',
  AI_AGENT = 'ai_agent'
}

export enum TaskStatus {
  TODO = 'todo',
  DOING = 'doing',
  REVIEW = 'review',
  DONE = 'done'
}

export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export type PermissionScope =
  | 'task:create' | 'task:read:own' | 'task:read:team' | 'task:read:all'
  | 'task:update:own' | 'task:update:team' | 'task:update:all'
  | 'agent:trigger:dev' | 'agent:trigger:mkt' | 'agent:trigger:know'
  | 'code:approve' | 'content:publish'
  | 'stats:view:own' | 'stats:view:team' | 'stats:view:all'
  | 'leads:view:all' | 'leads:view:sales' | 'leads:view:marketing'
  | 'user:manage' | 'user:manage:team' | 'mcp:manage';

export interface Employee {
  id: string;
  employeeId: string;
  name: string;
  email: string;
  department: string;
  position: string;
  status: 'active' | 'inactive' | 'suspended';
  role: EmployeeRole;
  avatar: string;
  permissions?: string[];
}

export interface Project {
  id: string;
  title: string;
  description: string;
  status: 'planning' | 'active' | 'completed' | 'on_hold';
  projectManagerId: string;
  computed_status?: 'not_started' | 'in_progress' | 'completed' | null;
}

export interface ProjectAssignment {
  id: string;
  projectId: string;
  employeeId: string;
  role: 'manager' | 'member' | 'viewer';
  isActive: boolean;
}

export interface Task {
  id: string;
  project_id: string;
  parent_task_id?: string;
  title: string;
  description: string;
  status: TaskStatus;
  assignee?: string; // Changed from assigneeId to match DB schema (TEXT field)
  assignee_id?: string | null;
  task_order: number;
  priority: TaskPriority;
  due_date: string; // ISO string
  created_at: string; // ISO string
  updated_at: string; // ISO string
  completed_at?: string; // ISO string
  sources?: {
    source_id: string;
    type: string;
    title?: string;
    url?: string;
  }[];
  attachments?: {
    file_name: string;
    url: string;
    description?: string;
    uploaded_at?: string;
  }[];
}

export interface NewTaskData {
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id: string | null;
  due_date: string;
  project_id: string;
  knowledge_source_ids?: string[];
}

export interface UpdateTaskData extends Partial<NewTaskData> {
  id: string;
}

// Replaced AuditLog with DocumentVersion to match the provided SQL schema
export interface DocumentVersion {
  id: string;
  project_id: string | null;
  task_id: string | null;
  field_name: string;
  version_number: number;
  content: any; // JSONB
  change_summary: string | null;
  change_type: string;
  created_by: string;
  created_at: string;
}

export interface BlogPost {
    id: string;
    title: string;
    excerpt: string;
    content?: string;
    authorName: string;
    publishDate: string; // ISO String
    imageUrl: string;
    status: 'draft' | 'review' | 'published';
}

export interface AssignableUser {

  id: string;

  name: string;

  role: string;

}



export interface TaskStats {

    name: string;

    value: number;

}



export interface MemberPerformance {

    name: string;

    completed_tasks: number;

}



export interface JobData {



    title: string;



    company: string;



    location?: string;



    salary?: string;



    url?: string;



    description?: string;

    description_full?: string;

    skills?: string[];



    source: string;



    identified_need?: string; // AI inferred business need



}
