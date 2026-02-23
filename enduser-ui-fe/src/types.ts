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
  permission_overrides?: Record<string, boolean>;
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
  is_recurring?: boolean;
  crawler_target_id?: string | null;
  schedule_config?: any;
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
  assigneeId: string | null;
  due_date: string;
  project_id: string;
  knowledge_source_ids?: string[];
  is_recurring?: boolean;
  crawler_target_id?: string | null;
  schedule_config?: any;
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
    hashtags?: string;
    authorName: string;
    publishDate: string; // ISO String
    imageUrl: string;
    status: 'draft' | 'review' | 'published' | 'changes_requested';
    ai_score?: number;
    review_notes?: string;
}

export interface AssignableUser {
  id: string;
  name: string;
  role: string;
  tools?: string[];
  description?: string;
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

export interface SystemOverview {
    status: 'healthy' | 'degraded' | 'unknown';
    rag: {
        status: string;
        details?: any;
    };
    integrity_score?: number;
    errors_24h: number;
    active_agents: { id: string; name: string; role?: string; status: string }[];
    cost_24h: number;
    knowledge_stats?: { total_nodes: number; total_chunks: number };
    ethics_status?: { violations_24h: number };
    collab_score?: number;
    velocity_score?: number;
    velocity_in_days?: number;
    timestamp: string;
}

export interface AiUsageStats {
    total_budget: number;
    total_used: number;
    usage_percentage: number;
    usage_by_user: {
        name: string;
        calls: number;
        tokens: number;
    }[];
    // New fields for Admin
    total_cost_usd?: number;
    daily_costs?: {
        date: string;
        cost: number;
        request_count: number;
        models: string[];
    }[];
    is_real_data?: boolean;
}

export interface AlertItem {
    id: string;
    level: string;
    message: string;
    details?: {
        company?: string;
        enrichment_score?: number;
        days_stale?: number;
        status?: string;
        [key: string]: any;
    };
    created_at: string;
}

export type ApprovalItem = BlogPost | any; // Union type for stronger typing later

export interface ModelHealth {
    model: string;
    agent: string;
    provider: string;
    status: 'healthy' | 'offline';
    latency_ms: number | null;
}

export interface AiHealthStatus {
    status: 'healthy' | 'degraded' | 'unhealthy';
    models: ModelHealth[];
    timestamp: string;
    error?: string;
}
