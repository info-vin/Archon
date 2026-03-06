import { Employee, EmployeeRole, Task, TaskStatus, TaskPriority, DocumentVersion, Project, BlogPost, AssignableUser, TaskStats, MemberPerformance, JobData, CrawlerTarget } from '../types.ts';
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

// --- SUPABASE API IMPLEMENTATION ---
const supabaseApi = {
  _userCache: null as Employee | null,

  /**
   * Internal helper to build headers with user role for RBAC
   */
  async _getHeaders(extraHeaders: Record<string, string> = {}): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...extraHeaders,
    };

    try {
      // Use cached user to avoid DB round-trip on every header generation
      const user = await this.getCurrentUser();
      if (user?.role) {
        headers['X-User-Role'] = user.role;
      }
      
      // Attach Session Token for Backend Auth (SDK call is fast as it hits local memory)
      if (supabase) {
          const sessionResult: any = await Promise.race([
            supabase.auth.getSession(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Auth timeout')), 5000))
          ]);
          const { data: { session }, error: sessionError } = sessionResult;
          
          if (!sessionError && session?.access_token) {
              headers['Authorization'] = `Bearer ${session.access_token}`;
          }
      }
    } catch (e) {
      console.warn("Could not attach auth headers", e);
    }
    return headers;
  },

  /**
   * Safe response handler to prevent SyntaxErrors from non-JSON (HTML) error pages.
   * Now includes 429 Retry logic to handle AI quota limits gracefully.
   */
  async _handleResponse(response: Response, errorContext: string, retryCount = 0): Promise<any> {
    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');

    // 1. Handle 429 Too Many Requests (Retry Logic)
    if (response.status === 429 && retryCount < 2) {
        const delay = 2000 * (retryCount + 1);
        console.warn(`⏳ [API 429][${errorContext}]: Retrying in ${delay}ms... (Attempt ${retryCount + 1}/2)`);
        await new Promise(r => setTimeout(r, delay));
        
        // Re-execute the request (Note: this is a simple retry, doesn't re-run headers logic for simplicity here)
        // For full retry, the caller should handle it, but for 429 we inject it here.
        const newResponse = await fetch(response.url, {
            method: 'GET', // Default, might need enhancement for POST
            headers: response.headers
        });
        return this._handleResponse(newResponse, errorContext, retryCount + 1);
    }

    if (!response.ok) {
        let errorMessage = errorContext;
        if (isJson) {
            const errorData = await response.json().catch(() => ({}));
            errorMessage = errorData.detail || errorData.message || errorContext;
        } else {
            // Log for developers to see what happened in the console
            const text = await response.text().catch(() => '');
            console.error(`🚨 [API ERROR][${errorContext}]: Server returned non-JSON response (${response.status}). Body snippet: ${text.slice(0, 300)}`);
            errorMessage = `Backend error (${response.status}): Unexpected response format (Expected JSON, got ${contentType || 'unknown'}).`;
        }
        throw new Error(errorMessage);
    }

    if (isJson) {
        return response.json();
    }
    return response.text();
  },

  async login(credentials: LoginCredentials): Promise<Employee | null> {
    this._userCache = null; // Clear cache before login
    const { data, error } = await supabase!.auth.signInWithPassword({
      email: credentials.email,
      password: credentials.password!,
    });
    if (error) throw new Error(error.message);
    if (data.user) return this.getCurrentUser();
    throw new Error("Login failed. Please check your credentials.");
  },
  async register(credentials: RegistrationData): Promise<Employee | null> {
    this._userCache = null; 
    const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
    });

    await this._handleResponse(response, 'Registration failed');
    return this.login({ email: credentials.email, password: credentials.password });
  },
  async adminCreateUser(userData: AdminNewUserData): Promise<Employee> {
    const response = await fetch('/api/admin/users', {
        method: 'POST',
        headers: await this._getHeaders(), 
        body: JSON.stringify(userData)
    });

    const data = await this._handleResponse(response, 'Failed to create user');
    return data.profile;
  },
  async logout(): Promise<void> {
    this._userCache = null; // Purge cache on logout
    const { error } = await supabase!.auth.signOut();
    if (error) throw new Error(error.message);
  },
  async getCurrentUser(): Promise<Employee | null> {
    if (!supabase) return null;
    if (this._userCache) return this._userCache; // Return cached result immediately

    let sessionUser: any = null;

    try {
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

    try {
      const { data: profile, error } = await supabase.from('profiles').select('*').eq('id', sessionUser.id).maybeSingle();
      
      if (error) throw error;
      if (!profile) throw new Error("Profile missing in public.profiles");
      
      this._userCache = profile as Employee;
      return this._userCache;
    } catch (e: any) {
      const metadataRole = sessionUser.user_metadata?.role || EmployeeRole.MEMBER;
      console.warn(`[api.ts] Profile fetch failed (${e?.message}), falling back to metadata role: ${metadataRole}`);
      
      this._userCache = { 
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
      
      return this._userCache;
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
    const data = await this._handleResponse(response, 'Failed to fetch tasks');
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
    await this._handleResponse(response, 'Failed to archive task');
  },
  async getProjects(): Promise<Project[]> {
    const response = await fetch('/api/projects?include_computed_status=true', { headers: await this._getHeaders() });
    const data = await this._handleResponse(response, 'Failed to fetch projects');
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
    return this._handleResponse(response, 'Failed to create project');
  },
  async createTask(task_data: NewTaskData): Promise<Task> {
    // Map frontend camelCase to backend snake_case
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
    const response = await fetch('/api/knowledge-items?per_page=1000', {
      headers: await this._getHeaders()
    });
    const data = await this._handleResponse(response, 'Failed to fetch knowledge items');
    return data.items || [];
  },
  async getCrawlerTargets(): Promise<CrawlerTarget[]> {
    const response = await fetch(`/api/admin/crawler-targets`, {
      headers: await this._getHeaders()
    });
    return this._handleResponse(response, 'Failed to fetch crawler targets');
  },
  async createCrawlerTarget(data: { target_url: string; max_depth?: number; description?: string }): Promise<any> {
    const response = await fetch('/api/admin/crawler-targets', {
      method: 'POST',
      headers: await this._getHeaders(),
      body: JSON.stringify(data)
    });
    return this._handleResponse(response, 'Failed to create crawler target');
  },
  async deleteCrawlerTarget(targetId: string): Promise<void> {
    const response = await fetch(`/api/admin/crawler-targets/${targetId}`, {
      method: 'DELETE',
      headers: await this._getHeaders()
    });
    await this._handleResponse(response, 'Failed to delete crawler target');
  },
  async updateTask(taskId: string, updates: UpdateTaskData): Promise<Task> {
    const { assigneeId, ...rest } = updates;
    const payload = {
        ...rest,
        ...(assigneeId !== undefined ? { assignee_id: assigneeId } : {}),
        is_recurring: updates.is_recurring,
        crawler_target_id: updates.crawler_target_id,
        schedule_config: updates.schedule_config
    };

    const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: await this._getHeaders(),
        body: JSON.stringify(payload)
    });

    const data = await this._handleResponse(response, 'Failed to update task');
    return data.task;
  },
  async refineTaskDescription(title: string, description: string): Promise<string> {
    const response = await fetch('/api/tasks/refine-description', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ title, description })
    });
    const data = await this._handleResponse(response, 'Failed to refine task description');
    return data.refined_description;
  },
  async getEmployees(): Promise<Employee[]> {
    const response = await fetch('/api/admin/users', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch employees');
  },
  async getAssignableUsers(): Promise<AssignableUser[]> {
    const response = await fetch('/api/assignable-users', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch assignable users');
  },
  async getAssignableAgents(): Promise<AssignableUser[]> {
    const response = await fetch('/api/agents/assignable', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch assignable AI agents');
  },
  async getDocumentVersions(): Promise<DocumentVersion[]> {
    const response = await fetch('/api/version/documents', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch document versions');
  },
  async getBlogPosts(): Promise<BlogPost[]> {
    const response = await fetch('/api/blogs', { headers: await this._getHeaders() });
    const data = await this._handleResponse(response, 'Failed to fetch blog posts');
    
    // Defensive mapping to ensure camelCase and status inclusion
    return data.map((post: any) => ({
        ...post,
        id: post.id,
        authorName: post.authorName || post.author_name,
        publishDate: post.publishDate || post.publish_date,
        imageUrl: post.imageUrl || post.image_url,
        status: post.status || 'published'
    }));
  },

  async updateBlogPostStatus(postId: string, status: string): Promise<void> {
    const response = await fetch(`/api/marketing/blog/${postId}/status?status=${status}`, {
        method: 'PATCH',
        headers: await this._getHeaders()
    });
    await this._handleResponse(response, 'Failed to update post status');
  },

  async generateLogo(style: string): Promise<{ svg_content: string }> {
    const response = await fetch('/api/marketing/logo', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ style })
    });
    return this._handleResponse(response, "API Request failed");
  },

  async getMarketStats(): Promise<any> {
    const response = await fetch('/api/marketing/market-stats', {
        headers: await this._getHeaders()
    });
    return this._handleResponse(response, "API Request failed");
  },

  async getMarketingTrends(): Promise<any> {
    const response = await fetch('/api/marketing/trends', {
        headers: await this._getHeaders()
    });
    return this._handleResponse(response, "API Request failed");
  },

  async getLeads(): Promise<any[]> {
    const response = await fetch('/api/marketing/leads', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch leads');
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
    return this._handleResponse(response, "API Request failed");
  },

  async promoteLead(leadId: string, data: { vendor_name: string; contact_email?: string; notes?: string }): Promise<void> {
    const response = await fetch(`/api/marketing/leads/${leadId}/promote`, {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(data)
    });
    await this._handleResponse(response, 'Failed to promote lead');
  },

  async updateLead(leadId: string, updates: { status?: string; enrichment_status?: string }): Promise<void> {
    const response = await fetch(`/api/marketing/leads/${leadId}`, {
        method: 'PATCH',
        headers: await this._getHeaders(),
        body: JSON.stringify(updates)
    });
    await this._handleResponse(response, 'Failed to update lead');
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
    return this._handleResponse(response, "API Request failed");
  },

  async rejectSuggestion(blogPostId: string): Promise<{ suggested_reason: string }> {
      const response = await fetch('/api/marketing/approvals/reject-suggestion', {
          method: 'POST',
          headers: await this._getHeaders(),
          body: JSON.stringify({ blog_post_id: blogPostId })
      });
      return this._handleResponse(response, "API Request failed");
  },

  async processApproval(type: 'blog' | 'lead', id: string, action: 'approve' | 'reject', reviewNotes?: string): Promise<void> {
    const payload: any = {};
    if (reviewNotes) payload.review_notes = reviewNotes;

    const response = await fetch(`/api/marketing/approvals/${type}/${id}/${action}`, {
        method: 'POST',
        headers: await this._getHeaders(),
        body: Object.keys(payload).length > 0 ? JSON.stringify(payload) : undefined
    });
    await this._handleResponse(response, `Failed to ${action} ${type}`);
  },

  async getBlogPost(id: string): Promise<BlogPost> {
    const response = await fetch(`/api/blogs/${id}`, { headers: await this._getHeaders() });
    const post = await this._handleResponse(response, 'Failed to fetch blog post');
    return {
        ...post,
        authorName: post.authorName || post.author_name,
        publishDate: post.publishDate || post.publish_date,
        imageUrl: post.imageUrl || post.image_url,
        ai_score: post.ai_score,
        review_notes: post.review_notes
    };
  },
  async createBlogPost(postData: NewBlogPostData): Promise<BlogPost> {
    const response = await fetch('/api/blogs', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(postData)
    });
    return this._handleResponse(response, 'Failed to create blog post');
  },
  async draftBlogPost(data: any): Promise<{ title: string; content: string; excerpt: string; references: string[]; used_prompt?: string }> {
      const response = await fetch('/api/marketing/blog/draft', {
          method: 'POST',
          headers: await this._getHeaders(),
          body: JSON.stringify(data)
      });
      return this._handleResponse(response, 'Failed to generate draft');
  },

  async submitBlogPost(postId: string): Promise<any> {
      const response = await fetch(`/api/marketing/blog/${postId}/submit`, {
          method: 'POST',
          headers: await this._getHeaders()
      });
      return this._handleResponse(response, 'Failed to submit blog post');
  },

  async uploadFile(file: File): Promise<{ url: string; key: string }> {
      const formData = new FormData();
      formData.append('file', file);

      // Create headers but explicitly remove Content-Type so browser sets it with boundary
      const headers = await this._getHeaders();
      delete headers['Content-Type'];

      const response = await fetch('/api/files/upload', {
          method: 'POST',
          headers,
          body: formData
      });
      return this._handleResponse(response, 'Failed to upload file');
  },

  async getContentSources(): Promise<any[]> {
    const response = await fetch('/api/marketing/sources', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch sources');
  },

  async getContentContext(sourceId: string, sourceType: string = 'lead'): Promise<any> {
    const response = await fetch(`/api/marketing/context/${sourceId}?source_type=${sourceType}`, { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch context');
  },

  async nanaBananaProxy(payload: any): Promise<{ image_url: string }> {
    const response = await fetch('/api/marketing/nana-banana', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify(payload)
    });
    return this._handleResponse(response, 'Image generation proxy failed');
  },
  async updateBlogPost(postId: string, postData: Partial<NewBlogPostData>): Promise<BlogPost> {
    const response = await fetch(`/api/blogs/${postId}`, {
        method: 'PUT',
        headers: await this._getHeaders(),
        body: JSON.stringify(postData)
    });
    return this._handleResponse(response, 'Failed to update blog post');
  },
  async deleteBlogPost(postId: string): Promise<void> {
    const response = await fetch(`/api/blogs/${postId}`, {
        method: 'DELETE',
        headers: await this._getHeaders()
    });
    await this._handleResponse(response, 'Failed to delete blog post');
  },
  async updateEmployee(employeeId: string, updates: Partial<Employee>): Promise<Employee> {
    const response = await fetch(`/api/admin/users/${employeeId}`, {
        method: 'PATCH',
        headers: await this._getHeaders(),
        body: JSON.stringify(updates)
    });
    const data = await this._handleResponse(response, 'Failed to update employee');
    return data.profile;
  },

  async diagnoseFile(filePath: string): Promise<any> {
    const response = await fetch('/api/admin/diagnose', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ file_path: filePath })
    });
    return this._handleResponse(response, 'Diagnostic failed');
  },

  async getSystemPermissions(): Promise<string[]> {
    const response = await fetch('/api/auth/permissions', {
        headers: await this._getHeaders()
    });
    const data = await this._handleResponse(response, 'Failed to fetch permissions');
    return data.permissions;
  },
  async updateUserEmail(newEmail: string): Promise<void> {
    const response = await fetch('/api/auth/email', {
        method: 'PUT',
        headers: await this._getHeaders(),
        body: JSON.stringify({ new_email: newEmail })
    });
    await this._handleResponse(response, 'Failed to update email');
  },
  async updateUserPassword(newPassword: string): Promise<void> {
    const { error } = await supabase!.auth.updateUser({ password: newPassword });
    if (error) throw new Error(error.message);
  },

  // --- CHANGE PROPOSAL API ---
  async getPendingChanges(): Promise<any[]> {
    const response = await fetch('/api/changes', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch pending changes');
  },

  async approveChange(changeId: string): Promise<any> {
    const response = await fetch(`/api/changes/${changeId}/approve`, {
        method: 'POST',
        headers: await this._getHeaders(),
    });
    return this._handleResponse(response, 'Failed to approve change');
  },

  async rejectChange(changeId: string): Promise<any> {
    const response = await fetch(`/api/changes/${changeId}/reject`, {
        method: 'POST',
        headers: await this._getHeaders(),
    });
    return this._handleResponse(response, 'Failed to reject change');
  },

  // --- STATS & MARKETING API ---
  async getAgentXPStats(): Promise<any[]> {
    const response = await fetch('/api/stats/agent-xp', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch XP stats');
  },

  async getTaskDistribution(): Promise<TaskStats[]> {
    const response = await fetch('/api/stats/tasks-by-status', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch task distribution');
  },

  async getAiUsage(): Promise<import('../types.ts').AiUsageStats> {
    const response = await fetch('/api/stats/ai-usage', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch AI usage');
  },

  async getSystemOverview(): Promise<import('../types.ts').SystemOverview> {
      const response = await fetch('/api/stats/system-overview', { headers: await this._getHeaders() });
      return this._handleResponse(response, 'Failed to fetch system overview');
  },

  async getMemberPerformance(): Promise<MemberPerformance[]> {
    const response = await fetch('/api/stats/member-performance', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch performance stats');
  },

  async getTokenUsageDetails(days: number = 7): Promise<any[]> {
    const response = await fetch(`/api/stats/token-usage/details?days=${days}`, {
        headers: await this._getHeaders()
    });
    return this._handleResponse(response, 'Failed to fetch usage details');
  },

  async searchJobs(keyword: string): Promise<JobData[]> {
    const response = await fetch(`/api/marketing/jobs?keyword=${encodeURIComponent(keyword)}`, { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to search jobs');
  },

  async generatePitch(jobTitle: string, company: string, description: string): Promise<{ content: string; references: string[] }> {
    const response = await fetch('/api/marketing/generate-pitch', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ job_title: jobTitle, company, description })
    });
    return this._handleResponse(response, 'Failed to generate pitch');
  },

  // --- SYSTEM PROMPT MANAGEMENT ---
  async getSystemPrompts(): Promise<any[]> {
    const response = await fetch('/api/system/prompts', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch prompts');
  },

  async updateSystemPrompt(promptName: string, data: { content: string; description?: string }): Promise<any> {
    const response = await fetch(`/api/system/prompts/${promptName}`, {
        method: 'POST', // Backend uses POST for update to match legacy behavior
        headers: await this._getHeaders(),
        body: JSON.stringify({ prompt: data.content, description: data.description })
    });
    return this._handleResponse(response, 'Failed to update system prompt');
  },

  // --- SYSTEM SETTINGS MANAGEMENT ---
  async getSystemSettings(category?: string): Promise<any[]> {
    const query = category ? `?category=${category}` : '';
    const response = await fetch(`/api/system/settings${query}`, { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch settings');
  },

  async updateSystemSetting(key: string, data: { value: string; description?: string }): Promise<any> {
    const response = await fetch(`/api/system/settings/${key}`, {
        method: 'PATCH',
        headers: await this._getHeaders(),
        body: JSON.stringify(data)
    });
    return this._handleResponse(response, 'Failed to update setting');
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
    return this._handleResponse(response, "API Request failed");
  },

  async getExtractionSchemas(): Promise<any[]> {
    const response = await fetch('/api/extraction/schemas', {
        headers: await this._getHeaders()
    });
    return this._handleResponse(response, "API Request failed");
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
    return this._handleResponse(response, "API Request failed");
  },

  async getConnectivityLogs(): Promise<any[]> {
    const response = await fetch('/api/system/logs/connectivity', {
        headers: await this._getHeaders()
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch connectivity logs');
    }
    return this._handleResponse(response, "API Request failed");
  },

  async getAiHealth(): Promise<import('../types.ts').AiHealthStatus> {
      const response = await fetch('/api/system/health/ai', { headers: await this._getHeaders() });
      return this._handleResponse(response, "API Request failed");
  },

  async getHealthTrend(): Promise<{ trend: any[]; audit: any[] }> {
    const response = await fetch('/api/stats/health-trend', {
        headers: await this._getHeaders()
    });
    return this._handleResponse(response, "API Request failed");
  },

  async getManagerAlerts(): Promise<import('../types.ts').AlertItem[]> {
      const response = await fetch('/api/logs/alerts', { headers: await this._getHeaders() });
      return this._handleResponse(response, "API Request failed");
  },

  async dispatchAlertTask(alertId: string, assigneeId?: string): Promise<any> {
      const response = await fetch('/api/tasks/generate-from-alert', {
          method: 'POST',
          headers: await this._getHeaders(),
          body: JSON.stringify({ alert_id: alertId, assignee_id: assigneeId })
      });
      if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to dispatch task');
      }
      return this._handleResponse(response, "API Request failed");
  },

  async seedKnowledgeBase(): Promise<{ indexed_count: number; total_files: number }> {
      // Placeholder for verify/rebuild index functionality
      console.log("Mocking seedKnowledgeBase/Rebuild Index...");
      await new Promise(resolve => setTimeout(resolve, 1000));
      return { indexed_count: 0, total_files: 0 };
  },

  async deleteExtractionSchema(id: string): Promise<void> {
    const response = await fetch(`/api/extraction/schemas/${id}`, {
        method: 'DELETE',
        headers: await this._getHeaders()
    });
    await this._handleResponse(response, 'Failed to delete schema');
  },

  async runExtraction(url: string, schemaId: string): Promise<any> {
    const response = await fetch('/api/extraction/run', {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ url, schema_id: schemaId })
    });
    return this._handleResponse(response, 'Extraction failed to start');
  },

  async getVisitLogs(userId?: string): Promise<any[]> {
    const query = userId ? `?user_id=${userId}` : '';
    const response = await fetch(`/api/visit-logs/${query}`, { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch visit logs');
  },

  async createVisitLog(formData: FormData): Promise<any> {
    const headers = await this._getHeaders();
    delete headers['Content-Type']; 
    
    const response = await fetch('/api/visit-logs/', {
        method: 'POST',
        headers: headers,
        body: formData
    });
    return this._handleResponse(response, 'Failed to create visit log');
  },

  // --- ATTENDANCE API (Mobile Ops) ---
  async getAttendanceStatus(): Promise<{ status: string; clock_in_time: string | null; location: string | null }> {
      const response = await fetch('/api/visit-logs/attendance/status', { headers: await this._getHeaders() });
      return this._handleResponse(response, 'Failed to fetch attendance status');
  },

  async clockIn(data: { latitude?: number; longitude?: number; location_name?: string; status: string }): Promise<void> {
      const response = await fetch('/api/visit-logs/attendance/clock-in', {
          method: 'POST',
          headers: await this._getHeaders(),
          body: JSON.stringify(data)
      });
      await this._handleResponse(response, 'Clock In failed');
  },

  async clockOut(): Promise<void> {
      const response = await fetch('/api/visit-logs/attendance/clock-out', {
          method: 'POST',
          headers: await this._getHeaders()
      });
      await this._handleResponse(response, 'Clock Out failed');
  },

  async getEthicsEvents(): Promise<any[]> {
    const response = await fetch('/api/ethics/events', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch ethics events');
  },

  async getAlerts(): Promise<any[]> {
    const response = await fetch(`/api/marketing/manager/alerts`, { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch alerts');
  },

  async triggerSentinel(): Promise<any> {
    const response = await fetch('/api/marketing/manager/sentinel/run', {
        method: 'POST',
        headers: await this._getHeaders(),
    });
    return this._handleResponse(response, 'Sentinel trigger failed');
  },

  async getCommanderTrends(): Promise<any[]> {
    const response = await fetch('/api/stats/commander-trends', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch commander trends');
  },

  async getForceReadiness(): Promise<any> {
    const response = await fetch('/api/stats/force-readiness', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch force readiness');
  },

  async getCollabSynergy(): Promise<any> {
    const response = await fetch('/api/stats/collab-synergy', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch collaboration synergy');
  },

  async getSlaReliability(): Promise<any> {
    const response = await fetch('/api/stats/sla-reliability', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch SLA reliability');
  },

  async getEthicsAuditQueue(): Promise<any> {
    const response = await fetch('/api/stats/ethics-audit-queue', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch ethics audit queue');
  },

  async getKnowledgeRoi(): Promise<any> {
    const response = await fetch('/api/stats/knowledge-roi', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch knowledge ROI');
  },

  async approvePromptChange(versionId: string): Promise<any> {
    const response = await fetch(`/api/stats/approve-prompt-change/${versionId}`, {
        method: 'POST',
        headers: await this._getHeaders()
    });
    return this._handleResponse(response, 'Failed to approve prompt change');
  },

  async getBusinessRisks(): Promise<any[]> {
    const response = await fetch('/api/stats/business-risks', { headers: await this._getHeaders() });
    return this._handleResponse(response, 'Failed to fetch business risks');
  },

  async generateTaskFromAlert(alertId: string, assigneeId?: string): Promise<any> {
    const response = await fetch(`/api/marketing/manager/alerts/${alertId}/dispatch`, {
        method: 'POST',
        headers: await this._getHeaders(),
        body: JSON.stringify({ assignee_id: assigneeId })
    });
    return this._handleResponse(response, 'Failed to generate task from alert');
  },

};

// Export the API
export const api = supabaseApi;
