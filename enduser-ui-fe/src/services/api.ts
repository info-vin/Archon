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
  status: TaskStatus;
  assigneeId?: string | null;
  due_date: string;
  priority: TaskPriority;
  knowledge_source_ids?: string[]; // IDs of knowledge sources to associate with the task
};

export type NewProjectData = {
  title: string;
  description?: string;
};

export type UpdateTaskData = Partial<Omit<NewTaskData, 'project_id'> & { assigneeId: string | null; status: TaskStatus }>;

export type NewBlogPostData = Omit<BlogPost, 'id' | 'publishDate'> & { authorName?: string, publishDate?: string };

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

    await response.json();
    
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
      const sessionResult: any = await Promise.race([
        supabase.auth.getSession(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Auth timeout')), 5000))
      ]);

      const { data: { session }, error: sessionError } = sessionResult;
      if (sessionError) throw new Error(sessionError.message);
      if (!session?.user) return null;
      sessionUser = session.user;
    } catch (e) {
      console.warn("[api.ts] Auth check failed or timed out:", e);
      return null;
    }

    // Secondary Try/Catch for Profile Fetching
    try {
      const { data: profile, error } = await supabase.from('profiles').select('*').eq('id', sessionUser.id).maybeSingle();
      
      if (error) throw error;
      if (!profile) throw new Error("Profile missing in public.profiles");
      
      return profile as Employee;
    } catch (e: any) {
      // Sync with Backend dependencies.py logic: Check user_metadata for role
      const metadataRole = sessionUser.user_metadata?.role || EmployeeRole.MEMBER;
      
      console.warn(`[api.ts] Profile fetch failed (${e?.message}), falling back to metadata role: ${metadataRole}`);
      
      return { 
        id: sessionUser.id, 
        email: sessionUser.email!, 
        name: sessionUser.user_metadata.name || sessionUser.email?.split('@')[0] || 'Authenticated User', 
        role: metadataRole as EmployeeRole, 
        avatar: sessionUser.user_metadata.avatar_url || `https://i.pravatar.cc/150?u=${sessionUser.id}`,
        employeeId: 'TEMP-' + sessionUser.id.substring(0, 5),
        department: 'Unknown',
        position: 'User',
        status: 'active' 
      } as Employee;
    }
  },
  async getTasks(includeClosed: boolean = false, includeUnassigned: boolean = false, assigneeId?: string, perPage: number = 50): Promise<Task[]> {
    const queryParams = new URLSearchParams({
        include_closed: includeClosed.toString(),
        include_unassigned: includeUnassigned.toString(),
        per_page: perPage.toString()
    });
    if (assigneeId) queryParams.append('assignee_id', assigneeId);

    const response = await fetch(`/api/tasks?${queryParams.toString()}`, { headers: await this._getHeaders() });
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
    const { assigneeId, ...rest } = updates;
    const payload = {
        ...rest,
        ...(assigneeId !== undefined ? { assignee_id: assigneeId } : {})
    };

    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: await this._getHeaders(),
        body: JSON.stringify(payload)
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
    const response = await fetch('/api/version/documents', { headers: await this._getHeaders() });
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

  async getMarketingTrends(): Promise<any> {
    const response = await fetch('/api/marketing/trends', {
        headers: await this._getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch marketing trends');
    return response.json();
  },

  async getLeads(): Promise<any[]> {
    const response = await fetch('/api/marketing/leads', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch leads');
    return response.json();
  },

  async createLead(leadData: any): Promise<any> {
    const response = await fetch('/api/marketing/leads', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(leadData)
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create lead');
    }
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

  async updateLead(leadId: string, updates: { status?: string; enrichment_status?: string }): Promise<void> {
    const response = await fetch(`/api/marketing/leads/${leadId}`, {
        method: 'PATCH',
        headers: await this._getHeaders(),
        body: JSON.stringify(updates)
    });
    if (!response.ok) throw new Error('Failed to update lead');
  },

  async resetLeads(): Promise<void> {
    const response = await fetch('/api/marketing/leads/reset', {
        method: 'DELETE',
        headers: await this._getHeaders()
    });
    if (!response.ok) {
        let errorMsg = 'Failed to reset leads';
        try {
            const err = await response.json();
            if (err.detail) errorMsg = err.detail;
        } catch (e) { /* ignore parse error */ }
        throw new Error(errorMsg);
    }
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

  async rejectSuggestion(blogPostId: string): Promise<{ suggested_reason: string }> {
      const response = await fetch('/api/marketing/approvals/reject-suggestion', {
          method: 'POST',
          headers: await this._getHeaders(),
          body: JSON.stringify({ blog_post_id: blogPostId })
      });
      if (!response.ok) throw new Error('Failed to generate rejection suggestion');
      return response.json();
  },

  async processApproval(type: 'blog' | 'lead', id: string, action: 'approve' | 'reject', reviewNotes?: string): Promise<void> {
    const payload: any = {};
    if (reviewNotes) payload.review_notes = reviewNotes;

    const response = await fetch(`/api/marketing/approvals/${type}/${id}/${action}`, {
        method: 'POST',
        headers: await this._getHeaders(),
        body: Object.keys(payload).length > 0 ? JSON.stringify(payload) : undefined
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
  async draftBlogPost(data: { 
    topic: string; 
    keywords?: string; 
    tone?: string; 
    context_source_id?: string; 
    context_type?: string;
    industry?: string[];
    style?: string[];
    length?: string;
    charts?: string[];
  }): Promise<{ title: string; content: string; excerpt: string; references: string[]; used_prompt?: string }> {
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

  async submitBlogPost(postId: string): Promise<any> {
      const response = await fetch(`/api/marketing/blog/${postId}/submit`, {
          method: 'POST',
          headers: await this._getHeaders()
      });
      if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to submit blog post.');
      }
      return response.json();
  },

  async getContentSources(): Promise<any[]> {
    const response = await fetch('/api/marketing/sources', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch content sources');
    return response.json();
  },

  async getContentContext(sourceId: string, sourceType: string = 'lead'): Promise<any> {
    const response = await fetch(`/api/marketing/context/${sourceId}?source_type=${sourceType}`, { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch content context');
    return response.json();
  },

  async nanaBananaProxy(payload: any): Promise<{ image_url: string }> {
    const response = await fetch('/api/marketing/nana-banana', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error('Nana Banana generation failed');
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
    const response = await fetch(`/api/admin/users/${employeeId}`, {
        method: 'PATCH',
        headers: await this._getHeaders(),
        body: JSON.stringify(updates)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update employee.');
    }
    const data = await response.json();
    return data.profile;
  },

  async getSystemPermissions(): Promise<string[]> {
    const response = await fetch('/api/auth/permissions', {
        headers: await this._getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch system permissions');
    const data = await response.json();
    return data.permissions;
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

  async getAiUsage(): Promise<import('../types.ts').AiUsageStats> {
    const response = await fetch('/api/stats/ai-usage', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch AI usage');
    return response.json();
  },

  async getSystemOverview(): Promise<import('../types.ts').SystemOverview> {
      const response = await fetch('/api/stats/system-overview', { headers: await this._getHeaders() });
      if (!response.ok) throw new Error('Failed to fetch system overview');
      return response.json();
  },

  async getMemberPerformance(): Promise<MemberPerformance[]> {
    const response = await fetch('/api/stats/member-performance', { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch performance stats');
    return response.json();
  },

  async getTokenUsageDetails(days: number = 7): Promise<any[]> {
    const response = await fetch(`/api/stats/token-usage/details?days=${days}`, {
        headers: await this._getHeaders()
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch token usage details.');
    }
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

  async updateSystemPrompt(promptName: string, data: { content: string; description?: string }): Promise<any> {
    const response = await fetch(`/api/system/prompts/${promptName}`, {
        method: 'POST', // Backend uses POST for update to match legacy behavior
        headers: await this._getHeaders(),
        body: JSON.stringify({ prompt: data.content, description: data.description })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update system prompt');
    }
    return response.json();
  },

  // --- SYSTEM SETTINGS MANAGEMENT ---
  async getSystemSettings(category?: string): Promise<any[]> {
    const query = category ? `?category=${category}` : '';
    const response = await fetch(`/api/system/settings${query}`, { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch system settings');
    return response.json();
  },

  async updateSystemSetting(key: string, data: { value: string; description?: string }): Promise<any> {
    const response = await fetch(`/api/system/settings/${key}`, {
        method: 'PATCH',
        headers: await this._getHeaders(),
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update system setting');
    }
    return response.json();
  },

  // --- DATA EXTRACTION SCHEMAS (GAP-018) ---
  async analyzeExtractionUrl(url: string): Promise<any> {
    const response = await fetch('/api/extraction/analyze', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ url })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Analysis failed');
    }
    return response.json();
  },

  async getExtractionSchemas(): Promise<any[]> {
    const response = await fetch('/api/extraction/schemas', {
        headers: await this._getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch schemas');
    return response.json();
  },

  async createExtractionSchema(data: any): Promise<any> {
    const response = await fetch('/api/extraction/schemas', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create schema');
    }
    return response.json();
  },

  async deleteExtractionSchema(id: string): Promise<void> {
    const response = await fetch(`/api/extraction/schemas/${id}`, {
        method: 'DELETE',
        headers: await this._getHeaders()
    });
    if (!response.ok) throw new Error('Failed to delete schema');
  },

  async runExtraction(url: string, schemaId: string): Promise<any> {
    const response = await fetch('/api/extraction/run', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ url, schema_id: schemaId })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Extraction failed to start');
    }
    return response.json();
  },

  async getVisitLogs(userId?: string): Promise<any[]> {
    const query = userId ? `?user_id=${userId}` : '';
    const response = await fetch(`/api/visit-logs/${query}`, { headers: await this._getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch visit logs');
    return response.json();
  },

  async createVisitLog(formData: FormData): Promise<any> {
    const headers = await this._getHeaders();
    delete headers['Content-Type']; 
    
    const response = await fetch('/api/visit-logs/', {
        method: 'POST',
        headers: headers,
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create visit log');
    }
    return response.json();
  },

  // --- ATTENDANCE API (Mobile Ops) ---
  async getAttendanceStatus(): Promise<{ status: string; clock_in_time: string | null; location: string | null }> {
      const response = await fetch('/api/visit-logs/attendance/status', { headers: await this._getHeaders() });
      if (!response.ok) throw new Error('Failed to fetch attendance status');
      return response.json();
  },

  async clockIn(data: { latitude?: number; longitude?: number; location_name?: string; status: string }): Promise<void> {
      const response = await fetch('/api/visit-logs/attendance/clock-in', {
          method: 'POST',
          headers: await this._getHeaders(),
          body: JSON.stringify(data)
      });
      if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Clock In failed');
      }
  },

  async clockOut(): Promise<void> {
      const response = await fetch('/api/visit-logs/attendance/clock-out', {
          method: 'POST',
          headers: await this._getHeaders()
      });
      if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Clock Out failed');
      }
  },

  async getEthicsEvents(): Promise<any[]> {
    const response = await fetch('/api/ethics/events', { headers: await this._getHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch ethics events');
    }
    return response.json();
  },

  async getAlerts(): Promise<any[]> {
    const response = await fetch(`/api/marketing/manager/alerts`, { headers: await this._getHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch alerts');
    }
    return response.json();
  },

  async getManagerAlerts(): Promise<any[]> {
     return this.getAlerts();
  },

  async triggerSentinel(): Promise<any> {
    const response = await fetch('/api/marketing/manager/sentinel/run', {
        method: 'POST',
        headers: await this._getHeaders(),
    });
    return response.json();
  },

  async dispatchAlertTask(alertId: string): Promise<any> {
    const response = await fetch(`/api/marketing/manager/alerts/${alertId}/dispatch`, {
        method: 'POST',
        headers: await this._getHeaders(),
    });
    if (!response.ok) {
         const error = await response.json();
         throw new Error(error.detail || 'Dispatch failed');
    }
    return response.json();
  },

  async seedKnowledgeBase(): Promise<any> {
    const response = await fetch('/api/marketing/manager/knowledge/seed', {
        method: 'POST',
        headers: await this._getHeaders(),
    });
    if (!response.ok) {
         const error = await response.json();
         throw new Error(error.detail || 'Seeding failed');
    }
    return response.json();
  },

  async generateTaskFromAlert(alertId: string, assigneeId?: string): Promise<any> {
    const response = await fetch('/api/tasks/generate-from-alert', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ alert_id: alertId, assignee_id: assigneeId })
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to generate task from alert');
    }
    return response.json();
  },
};

// Export the API
export const api = supabaseApi;
