export enum EmployeeRole {
  SYSTEM_ADMIN = 'system_admin',
  PROJECT_MANAGER = 'project_manager',
  SENIOR_MEMBER = 'senior_member',
  MEMBER = 'member',
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
}

export interface Project {
  id: string;
  title: string;
  description: string;
  status: 'planning' | 'active' | 'completed' | 'on_hold';
  projectManagerId: string;
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
  task_order: number;
  priority: TaskPriority;
  due_date: string; // ISO string
  created_at: string; // ISO string
  updated_at: string; // ISO string
  attachments?: { filename: string; url: string }[];
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
    authorName: string;
    publishDate: string; // ISO String
    imageUrl: string;
}

export interface AssignableUser {
  id: string;
  name: string;
  role: string;
}