import { Employee, EmployeeRole, Task, TaskStatus, TaskPriority, DocumentVersion, Project, BlogPost, AssignableUser, TaskStats, MemberPerformance, JobData } from '../types.ts';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// --- SUPABASE CLIENT SETUP ---
const getSupabaseConfig = () => {
    // 1. Try Environment Variables first (Docker/Vite injection)
    let url = import.meta.env.VITE_SUPABASE_URL;
    let key = import.meta.env.VITE_SUPABASE_ANON_KEY;
    
    // 2. Fallback to localStorage (User override)
    if (!url || !key) {
        url = localStorage.getItem('supabaseUrl') || "";
        key = localStorage.getItem('supabaseAnonKey') || "";
    }

    return { url: url || null, key: key || null };
};

const { url: supabaseUrl, key: supabaseAnonKey } = getSupabaseConfig();

export let supabase: SupabaseClient | null = null;

if (!supabaseUrl || !supabaseAnonKey || supabaseUrl === 'YOUR_SUPABASE_URL') {
    console.error("Supabase credentials are not set. API calls will fail.");
} else {
    try {
        supabase = createClient(supabaseUrl!, supabaseAnonKey!); 
    } catch (error) {
        console.error("Failed to initialize Supabase client:", error);
    }
}


// --- TYPES ---
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
  assigneeId?: string;
  due_date: string;
  priority: TaskPriority;
  knowledge_source_ids?: string[]; // IDs of knowledge sources to associate with the task
};

export type NewProjectData = {
  title: string;
  description?: string;
};

export type UpdateTaskData = Partial<Omit<NewTaskData, 'project_id'> & { assignee_id: string | null }>;

export type NewBlogPostData = Omit<BlogPost, 'id' | 'authorName' | 'publishDate'>;

// --- SUPABASE API IMPLEMENTATION ---
const supabaseApi = {
  /**
   * Internal helper to build headers with user role for RBAC
   */
  async _getHeaders(extraHeaders: Record<string, string> = {}): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...extraHeaders,
    };

    try {
      const user = await this.getCurrentUser();
      if (user?.role) {
        headers['X-User-Role'] = user.role;
      }
      
      // Attach Session Token for Backend Auth
      if (supabase) {
          const { data: { session } } = await supabase.auth.getSession();
          if (session?.access_token) {
              headers['Authorization'] = `Bearer ${session.access_token}`;
          }
      }
    } catch (e) {
      console.warn("Could not attach auth headers", e);
    }
    return headers;
  },

  async login(credentials: LoginCredentials): Promise<Employee | null> {
    const { data, error } = await supabase!.auth.signInWithPassword({
      email: credentials.email,
      password: credentials.password!,
    });
    if (error) throw new Error(error.message);
    if (data.user) return this.getCurrentUser();
    throw new Error("Login failed. Please check your credentials.");
  },
  async register(credentials: RegistrationData): Promise<Employee | null> {
    const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed.');
    }

    const data = await response.json();
    
    // Auto-login after registration is tricky without password transmission again.
    // Ideally backend registers AND logs in, returning a session token.
    // For now, we assume user needs to login manually or we auto-login with credentials provided.
    // To match previous behavior:
    return this.login({ email: credentials.email, password: credentials.password });
  },
  async adminCreateUser(userData: AdminNewUserData): Promise<Employee> {
    const response = await fetch('/api/admin/users', {
        method: 'POST',
        headers: await this._getHeaders(), // Admin role header will be attached if current user is admin
        body: JSON.stringify(userData)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create user.');
    }

    const data = await response.json();
    return data.profile;
  },
  async logout(): Promise<void> {
    const { error } = await supabase!.auth.signOut();
    if (error) throw new Error(error.message);
  },
  async getCurrentUser(): Promise<Employee | null> {
    if (!supabase) return null;

    let sessionUser: any = null;

    try {
      // Use Promise.race to enforce a strict timeout on Supabase Auth session check.
      // Increased to 5s for Docker environments which might be slower.
      const sessionResult: any = await Promise.race([
        supabase.auth.getSession(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Auth timeout')), 5000))
      ]);

      const { data: { session }, error: sessionError } = sessionResult;
      if (sessionError) throw new Error(sessionError.message);
      if (!session?.user) return null;
      sessionUser = session.user;
    } catch (e) {
      console.warn("Auth check failed or timed out, proceeding as unauthenticated:", e);
      return null;
    }

    // Secondary Try/Catch for Profile Fetching to prevent 406/RLS errors from logging out the user
    try {
      const { data: profile, error } = await supabase.from('profiles').select('*').eq('id', sessionUser.id).single();
      
      if (error) throw error;
      if (!profile) throw new Error("Profile missing");
      
      return profile as Employee;
    } catch (e: any) {
      console.warn('Profile not found or fetch failed (likely 406 or RLS), using auth metadata fallback:', e?.message);
      // Robust fallback: Return basic info from session so UI doesn't crash/hang
      return { 
        id: sessionUser.id, 
        email: sessionUser.email!, 
        name: sessionUser.user_metadata.name || sessionUser.email?.split('@')[0] || 'Authenticated User', 
        role: EmployeeRole.MEMBER, // Default role
        avatar: sessionUser.user_metadata.avatar_url || `https://i.pravatar.cc/150?u=${sessionUser.id}`,
        employeeId: 'TEMP-' + sessionUser.id.substring(0, 5),
        department: 'Unknown',
        position: 'User',
        status: 'active' 
      } as Employee;
    }
  },
  async getTasks(includeClosed: boolean = false): Promise<Task[]> {
    const response = await fetch(`/api/tasks?include_closed=${includeClosed}`, { headers: await this._getHeaders() });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch tasks.');
    }
    const data = await response.json();
    // DEFENSIVE: Always return an array even if backend returns paginated object or null
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object' && Array.isArray(data.tasks)) return data.tasks;
    return [];
  },
  async deleteTask(taskId: string): Promise<void> {
    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE',
        headers: await this._getHeaders()
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to archive task.');
    }
  },
  async getProjects(): Promise<Project[]> {
    const response = await fetch('/api/projects?include_computed_status=true', { headers: await this._getHeaders() });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch projects.');
    }
    const data = await response.json();
    // DEFENSIVE: Always return an array
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object' && Array.isArray(data.projects)) return data.projects;
    return [];
  },
  async createProject(projectData: NewProjectData): Promise<{ project: Project }> {
    const response = await fetch('/api/projects', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(projectData)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create project.');
    }
    return response.json();
  },
  async createTask(task_data: NewTaskData): Promise<Task> {
    // Map frontend camelCase to backend snake_case
    const { assigneeId, ...rest } = task_data;
    const payload = {
      ...rest,
      assignee_id: assigneeId,
      assignee: "User" // Default fallback name, backend will overwrite with real name if assignee_id is found
    };

    const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create task.');
    }
    const data = await response.json();
    return data.task;
  },
  async getKnowledgeItems(): Promise<any[]> {
    // TODO: Implement proper frontend pagination/infinite scroll.
    // Increased per_page to 1000 as a temporary mitigation for the "100 items limit" issue.
    const response = await fetch('/api/knowledge-items?per_page=1000', {
      headers: await this._getHeaders()
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail?.error || 'Failed to fetch knowledge items.');
    }
    const data = await response.json();
    return data.items || [];
  },
  async updateTask(taskId: string, updates: UpdateTaskData): Promise<Task> {
    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: await this._getHeaders(),
        body: JSON.stringify(updates)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail?.error || errorData.detail || errorData.message || 'Failed to update task.';
        throw new Error(typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage);
    }
    
    const data = await response.json();
    return data.task;
  },
  async refineTaskDescription(title: string, description: string): Promise<string> {
    const response = await fetch('/api/tasks/refine-description', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ title, description })
    });
    if (!response.ok) {
        throw new Error('Failed to refine task description.');
    }
    const data = await response.json();
    return data.refined_description;
  },
  async getEmployees(): Promise<Employee[]> {
    const response = await fetch('/api/users', { headers: await this._getHeaders() });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch employees.');
    }
    return response.json();
  },
  async getAssignableUsers(): Promise<AssignableUser[]> {
    // This function calls our own backend API, which has the RBAC logic.
    const response = await fetch('/api/assignable-users', { headers: await this._getHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch assignable users.');
    }
    return response.json();
  },
  async getAssignableAgents(): Promise<AssignableUser[]> {
    const response = await fetch('/api/agents/assignable', { headers: await this._getHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch assignable AI agents.');
    }
    return response.json();
  },
  async getDocumentVersions(): Promise<DocumentVersion[]> {
    const response = await fetch('/api/versions', { headers: await this._getHeaders() });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch document versions.');
    }
    return response.json();
  },
  async getBlogPosts(): Promise<BlogPost[]> {
    const response = await fetch('/api/blogs', { headers: await this._getHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch blog posts.');
    }
    const data = await response.json();
    
    // Defensive mapping to ensure camelCase and status inclusion
    return data.map((post: any) => ({
        ...post,
        id: post.id,
        title: post.title,
        excerpt: post.excerpt,
        content: post.content,
        authorName: post.authorName || post.author_name,
        publishDate: post.publishDate || post.publish_date,
        imageUrl: post.imageUrl || post.image_url,
        status: post.status || 'published' // Default if missing
    }));
  },

  async updateBlogPostStatus(postId: string, status: string): Promise<void> {
    const response = await fetch(`/api/marketing/blog/${postId}/status?status=${status}`, {
        method: 'PATCH',
        headers: await this._getHeaders()
    });
    if (!response.ok) throw new Error('Failed to update blog status');
  },

  async generateLogo(style: string): Promise<{ svg_content: string }> {
    const response = await fetch('/api/marketing/logo', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ style })
    });
    if (!response.ok) throw new Error('Failed to generate logo');
    return response.json();
  },

  async getMarketStats(): Promise<any> {
    const response = await fetch('/api/marketing/market-stats', {
        headers: await this._getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch market stats');
    return response.json();
  },

  async getLeads(): Promise<any[]> {
    const response = await fetch('/api/marketing/leads', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch leads');
    return response.json();
  },

  async promoteLead(leadId: string, data: { vendor_name: string; contact_email?: string; notes?: string }): Promise<void> {
    const response = await fetch(`/api/marketing/leads/${leadId}/promote`, {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to promote lead');
  },

  async resetPassword(userId: string, newPassword: string): Promise<void> {
    const response = await fetch(`/api/users/${userId}/reset-password`, {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ new_password: newPassword })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to reset password');
    }
  },

  async getPendingApprovals(): Promise<{ blogs: BlogPost[]; leads: any[] }> {
    const response = await fetch('/api/marketing/approvals', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch approvals');
    return response.json();
  },

  async processApproval(type: 'blog' | 'lead', id: string, action: 'approve' | 'reject'): Promise<void> {
    const response = await fetch(`/api/marketing/approvals/${type}/${id}/${action}`, {
        method: 'POST',
        headers: await this._getHeaders()
    });
    if (!response.ok) throw new Error('Approval action failed');
  },

  async getBlogPost(id: string): Promise<BlogPost> {
    const response = await fetch(`/api/blogs/${id}`, { headers: await this._getHeaders() });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch blog post.');
    }
    return response.json();
  },
  async createBlogPost(postData: NewBlogPostData): Promise<BlogPost> {
    const response = await fetch('/api/blogs', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(postData)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create blog post.');
    }
    return response.json();
  },
  async draftBlogPost(data: { topic: string; keywords?: string; tone?: string }): Promise<{ title: string; content: string; excerpt: string }> {
      const response = await fetch('/api/marketing/blog/draft', {
          method: 'POST',
          headers: await this._getHeaders(),
          body: JSON.stringify(data)
      });
      if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to generate draft.');
      }
      return response.json();
  },
  async updateBlogPost(postId: string, postData: Partial<NewBlogPostData>): Promise<BlogPost> {
    const response = await fetch(`/api/blogs/${postId}`, {
        method: 'PUT',
        headers: await this._getHeaders(),
        body: JSON.stringify(postData)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update blog post.');
    }
    return response.json();
  },
  async deleteBlogPost(postId: string): Promise<void> {
    const response = await fetch(`/api/blogs/${postId}`, {
        method: 'DELETE',
        headers: await this._getHeaders()
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete blog post.');
    }
  },
  async updateEmployee(employeeId: string, updates: Partial<Employee>): Promise<Employee> {
    const currentUser = await this.getCurrentUser();
    const isSelf = currentUser && currentUser.id === employeeId;
    
    // Determine endpoint based on whether we are updating ourselves or another user (as admin)
    const endpoint = isSelf ? '/api/users/me' : `/api/users/${employeeId}`;
    
    const response = await fetch(endpoint, {
        method: 'PUT',
        headers: await this._getHeaders(),
        body: JSON.stringify(updates)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail?.error || errorData.detail || 'Failed to update employee profile.');
    }
    
    const data = await response.json();
    return data.profile;
  },
  async updateUserEmail(newEmail: string): Promise<void> {
    const response = await fetch('/api/auth/email', {
        method: 'PUT',
        headers: await this._getHeaders(),
        body: JSON.stringify({ new_email: newEmail })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update email.');
    }
  },
  async updateUserPassword(newPassword: string): Promise<void> {
    const { error } = await supabase!.auth.updateUser({ password: newPassword });
    if (error) throw new Error(error.message);
  },

  // --- CHANGE PROPOSAL API ---
  async getPendingChanges(): Promise<any[]> {
    const response = await fetch('/api/changes', { headers: await this._getHeaders() });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch pending changes.');
    }
    return response.json();
  },

  async approveChange(changeId: string): Promise<any> {
    const response = await fetch(`/api/changes/${changeId}/approve`, {
        method: 'POST',
        headers: await this._getHeaders(),
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to approve change.');
    }
    return response.json();
  },

  async rejectChange(changeId: string): Promise<any> {
    const response = await fetch(`/api/changes/${changeId}/reject`, {
        method: 'POST',
        headers: await this._getHeaders(),
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reject change.');
    }
    return response.json();
  },

  // --- STATS & MARKETING API ---
  async getTaskDistribution(): Promise<TaskStats[]> {
    const response = await fetch('/api/stats/tasks-by-status', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch task stats');
    return response.json();
  },

  async getAiUsage(): Promise<{ total_budget: number; total_used: number; usage_percentage: number }> {
    const response = await fetch('/api/stats/ai-usage', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch AI usage');
    return response.json();
  },

  async getMemberPerformance(): Promise<MemberPerformance[]> {
    const response = await fetch('/api/stats/member-performance', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch performance stats');
    return response.json();
  },

  async searchJobs(keyword: string): Promise<JobData[]> {
    const response = await fetch(`/api/marketing/jobs?keyword=${encodeURIComponent(keyword)}`, { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to search jobs');
    return response.json();
  },

  async generatePitch(jobTitle: string, company: string, description: string): Promise<{ content: string; references: string[] }> {
    const response = await fetch('/api/marketing/generate-pitch', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ job_title: jobTitle, company, description })
    });
    if (!response.ok) {
         const error = await response.json().catch(() => ({}));
         throw new Error(error.detail?.error || 'Failed to generate pitch');
    }
    return response.json();
  },

  // --- SYSTEM PROMPT MANAGEMENT ---
  async getSystemPrompts(): Promise<any[]> {
    const response = await fetch('/api/system/prompts', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch system prompts');
    return response.json();
  },

  async updateSystemPrompt(promptName: string, data: { prompt: string; description?: string }): Promise<any> {
    const response = await fetch(`/api/system/prompts/${promptName}`, {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update system prompt');
    }
    return response.json();
  },
};

// Export the API
export const api = supabaseApi;
