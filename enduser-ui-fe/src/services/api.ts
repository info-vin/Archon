import { Employee, EmployeeRole, Task, TaskStatus, TaskPriority, DocumentVersion, Project, BlogPost, AssignableUser } from '../types.ts';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// --- SUPABASE CLIENT SETUP ---
const getSupabaseConfig = () => {
    // 1. Try Environment Variables first (Docker/Vite injection)
    let url = import.meta.env.VITE_SUPABASE_URL;
    let key = import.meta.env.VITE_SUPABASE_ANON_KEY;
    
    // 2. Fallback to localStorage (User override)
    if (!url || !key) {
        url = localStorage.getItem('supabaseUrl');
        key = localStorage.getItem('supabaseAnonKey');
    }

    return { url: url || null, key: key || null };
};

const { url: supabaseUrl, key: supabaseAnonKey } = getSupabaseConfig();

// Detect if we explicitly LACK credentials
// If credentials exist but are invalid (e.g. internal docker URL), we detect that at runtime via Smart Fallback.
const forceMockMode = !supabaseUrl || !supabaseAnonKey || supabaseUrl === 'YOUR_SUPABASE_URL';

export let supabase: SupabaseClient | null = null;

if (forceMockMode) {
    console.warn("Supabase credentials are not set. Application is running in MOCK mode.");
} else {
    try {
        // Set a shorter timeout for the client if possible, but standard fetch doesn't support global timeout easily in createClient
        // without a custom fetch wrapper. We handle the fast-fail in the Smart API wrapper.
        supabase = createClient(supabaseUrl!, supabaseAnonKey!); 
    } catch (error) {
        console.error("Failed to initialize Supabase client:", error);
    }
}

// --- MOCK DATA ---
const MOCK_USER: Employee = {
    id: 'mock-admin-uuid',
    employeeId: 'E1001',
    name: 'Admin User (Mock)',
    email: 'admin@archon.com',
    department: 'IT',
    position: 'System Administrator',
    status: 'active',
    role: EmployeeRole.SYSTEM_ADMIN,
    avatar: 'https://i.pravatar.cc/150?u=admin@archon.com'
};

const MOCK_TASKS: Task[] = [
    {
        id: 'mock-task-1',
        title: 'Initial Setup (Mock)',
        description: 'This is a mock task because the backend is unreachable.',
        status: TaskStatus.TODO,
        priority: TaskPriority.HIGH,
        project_id: 'mock-project-1',
        assignee: 'Admin User',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        task_order: 1
    }
];

const MOCK_PROJECTS: Project[] = [
    {
        id: 'mock-project-1',
        title: 'Mock Project',
        description: 'Project for mock mode',
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    }
];

// --- MOCK API IMPLEMENTATION ---
// Enhanced to include all methods from supabaseApi to prevent crashes
const mockApi: any = {
    async login() { return MOCK_USER; },
    async logout() { return; },
    async getCurrentUser() { return MOCK_USER; },
    async getTasks() { return MOCK_TASKS; },
    async getProjects() { return MOCK_PROJECTS; },
    async getAssignableAgents() { return []; },
    async getKnowledgeItems() { return []; },
    async getPendingChanges() { return []; },

    // Stubs for missing methods to prevent crashes
    async register() { throw new Error("Registration not supported in Mock Mode"); },
    async adminCreateUser() { throw new Error("Admin Create User not supported in Mock Mode"); },
    async createProject(data: any) {
        console.log("Mock createProject", data);
        return { project: { ...MOCK_PROJECTS[0], ...data, id: 'mock-new-' + Date.now() } };
    },
    async createTask(data: any) {
        console.log("Mock createTask", data);
        return { ...MOCK_TASKS[0], ...data, id: 'mock-task-' + Date.now() };
    },
    async updateTask(id: string, data: any) { return { ...MOCK_TASKS[0], id, ...data }; },
    async getEmployees() { return [MOCK_USER]; },
    async getAssignableUsers() { return [{ id: MOCK_USER.id, name: MOCK_USER.name, role: MOCK_USER.role }]; },
    async getDocumentVersions() { return []; },
    async getBlogPosts() { return []; },
    async createBlogPost() { throw new Error("Blog creation not supported in Mock Mode"); },
    async updateBlogPost() { throw new Error("Blog update not supported in Mock Mode"); },
    async deleteBlogPost() { return; },
    async updateEmployee() { return MOCK_USER; },
    async updateUserEmail() { return; },
    async updateUserPassword() { return; },
    async approveChange() { return { success: true }; },
    async rejectChange() { return { success: true }; }
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
    } catch (e) {
      console.warn("Could not attach X-User-Role to headers", e);
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
    const { data, error } = await supabase!.auth.signUp({
      email: credentials.email,
      password: credentials.password!,
      options: { data: { name: credentials.name, avatar_url: `https://i.pravatar.cc/150?u=${credentials.email}` } }
    });
    if (error) throw new Error(error.message);
    if (data.user) {
      const { error: profileError } = await supabase!.from('profiles').insert({ id: data.user.id, name: credentials.name, email: credentials.email, avatar: `https://i.pravatar.cc/150?u=${data.user.id}`, role: EmployeeRole.MEMBER, status: 'active' });
      if (profileError) throw new Error(profileError.message);
      return this.getCurrentUser();
    }
    throw new Error("Registration failed.");
  },
  async adminCreateUser(userData: AdminNewUserData): Promise<Employee> {
    const { data: authData, error: signUpError } = await supabase!.auth.signUp({
        email: userData.email,
        password: userData.password,
        options: { data: { name: userData.name } }
    });

    if (signUpError) throw new Error(signUpError.message);
    if (!authData.user) throw new Error("User creation failed in auth.");

    const profileData = {
        id: authData.user.id,
        name: userData.name,
        email: userData.email,
        role: userData.role,
        status: userData.status,
        avatar: `https://i.pravatar.cc/150?u=${authData.user.id}`
    };

    const { data: newProfile, error: profileError } = await supabase! 
        .from('profiles')
        .insert(profileData)
        .select()
        .single();

    if (profileError) {
        console.error("Failed to insert profile, trying to update as a fallback...", profileError);
        const { data: updatedProfile, error: updateError } = await supabase! 
            .from('profiles')
            .update(profileData)
            .eq('id', authData.user.id)
            .select()
            .single();
        if (updateError) throw new Error(`Failed to create or update profile: ${updateError.message}`);
        return updatedProfile as Employee;
    }

    return newProfile as Employee;
  },
  async logout(): Promise<void> {
    const { error } = await supabase!.auth.signOut();
    if (error) throw new Error(error.message);
  },
  async getCurrentUser(): Promise<Employee | null> {
    const { data: { session }, error: sessionError } = await supabase!.auth.getSession();
    if (sessionError) throw new Error(sessionError.message);
    if (!session?.user) return null;
    
    try {
      const { data: profile, error } = await supabase!.from('profiles').select('*').eq('id', session.user.id).single();
      
      if (error || !profile) {
        console.warn('Profile not found in public.profiles, using auth metadata fallback:', error?.message);
        // Robust fallback: Return basic info from session so UI doesn't crash/hang
        return { 
          id: session.user.id, 
          email: session.user.email!, 
          name: session.user.user_metadata.name || session.user.email?.split('@')[0] || 'Authenticated User', 
          role: EmployeeRole.MEMBER, // Default role
          avatar: session.user.user_metadata.avatar_url || `https://i.pravatar.cc/150?u=${session.user.id}`,
          employeeId: 'TEMP-' + session.user.id.substring(0, 5),
          department: 'Unknown',
          position: 'User',
          status: 'active' 
        } as Employee;
      }
      return profile as Employee;
    } catch (e) {
      console.error("Critical error in getCurrentUser:", e);
      return null;
    }
  },
  async getTasks(): Promise<Task[]> {
    const response = await fetch('/api/tasks');
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch tasks.');
    }
    return response.json();
  },
  async getProjects(): Promise<Project[]> {
    const response = await fetch('/api/projects?include_computed_status=true');
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch projects.');
    }
    const data = await response.json();
    return data.projects as Project[];
  },
  async createProject(projectData: NewProjectData): Promise<{ project: Project }> {
    const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(projectData)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create project.');
    }
    return response.json();
  },
  async createTask(task_data: NewTaskData): Promise<Task> {
    // Map frontend field 'assigneeId' to backend expected 'assignee' if needed, 
    // but the backend CreateTaskRequest expects 'assignee' as a string (name or id).
    // Based on projects_api.py, it takes 'assignee' string.
    const payload = {
      ...task_data,
      assignee: task_data.assigneeId // Backend expects 'assignee'
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
    let processedUpdates: any = { ...updates };

    // If assignee_id is being updated, we also need to update the assignee name string.
    if (updates.assignee_id) {
        const { data: employee, error } = await supabase!.from('profiles').select('name').eq('id', updates.assignee_id).single();
        if (employee) { 
            processedUpdates.assignee = employee.name; 
        } else if (error) { 
            console.warn('Error fetching assignee name for update:', error.message); 
            processedUpdates.assignee = 'Unassigned';
        }
    } else if (updates.assignee_id === null) {
        processedUpdates.assignee = 'Unassigned';
    }

    const { data, error } = await supabase!.from('archon_tasks').update(processedUpdates).eq('id', taskId).select().single();
    if (error) throw new Error(error.message);
    return data as Task;
  },
  async getEmployees(): Promise<Employee[]> {
    const { data, error } = await supabase!.from('profiles').select('*');
    if (error) throw new Error(error.message);
    return data as Employee[];
  },
  async getAssignableUsers(): Promise<AssignableUser[]> {
    // This function calls our own backend API, which has the RBAC logic.
    const response = await fetch('/api/assignable-users');
    if (!response.ok) {
      throw new Error('Failed to fetch assignable users.');
    }
    return response.json();
  },
  async getAssignableAgents(): Promise<AssignableUser[]> {
    const response = await fetch('/api/agents/assignable');
    if (!response.ok) {
      throw new Error('Failed to fetch assignable AI agents.');
    }
    return response.json();
  },
  async getDocumentVersions(): Promise<DocumentVersion[]> {
    const { data, error } = await supabase!.from('archon_document_versions').select('*');
    if (error) throw new Error(error.message);
    return data as DocumentVersion[];
  },
  async getBlogPosts(): Promise<BlogPost[]> {
    const response = await fetch('/api/blogs');
    if (!response.ok) {
      throw new Error('Failed to fetch blog posts.');
    }
    const data = await response.json();
    return data;
  },
  async createBlogPost(postData: NewBlogPostData): Promise<BlogPost> {
    const response = await fetch('/api/blogs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Assuming a mechanism to get the user role for the header
            'X-User-Role': 'SYSTEM_ADMIN' // Placeholder
        },
        body: JSON.stringify(postData)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create blog post.');
    }
    return response.json();
  },
  async updateBlogPost(postId: string, postData: Partial<NewBlogPostData>): Promise<BlogPost> {
    const response = await fetch(`/api/blogs/${postId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-User-Role': 'SYSTEM_ADMIN' // Placeholder
        },
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
        headers: {
            'X-User-Role': 'SYSTEM_ADMIN' // Placeholder
        }
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete blog post.');
    }
  },
  async updateEmployee(employeeId: string, updates: Partial<Employee>): Promise<Employee> {
    const { data, error } = await supabase!.from('profiles').update(updates).eq('id', employeeId).select().single();
    if (error) throw new Error(error.message);
    return data as Employee;
  },
  async updateUserEmail(newEmail: string): Promise<void> {
    const { data, error } = await supabase!.auth.updateUser({ email: newEmail });
    if (error) throw new Error(error.message);
    if (data.user) {
        const { error: profileError } = await supabase!.from('profiles').update({ email: newEmail }).eq('id', data.user.id);
        if (profileError) console.warn('Auth email updated, but profile email failed to update:', profileError.message);
    }
  },
  async updateUserPassword(newPassword: string): Promise<void> {
    const { error } = await supabase!.auth.updateUser({ password: newPassword });
    if (error) throw new Error(error.message);
  },

  // --- CHANGE PROPOSAL API ---
  async getPendingChanges(): Promise<any[]> {
    const response = await fetch('/api/changes');
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch pending changes.');
    }
    return response.json();
  },

  async approveChange(changeId: string): Promise<any> {
    const response = await fetch(`/api/changes/${changeId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
        headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reject change.');
    }
    return response.json();
  },
};

// --- SMART FALLBACK API IMPLEMENTATION ---

// Check connection helper
// We use a simple fetch to the Supabase health check or just the base URL
// If it fails or times out, we know we are in trouble.
let isFallbackMode = forceMockMode;
let connectionChecked = false;

// Create a wrapper that dynamically falls back to mockApi on network failures
const createSmartApi = () => {
    // Collect all unique method names from both APIs
    const allMethods = new Set([...Object.keys(supabaseApi), ...Object.keys(mockApi)]);
    const smartApi: any = {};

    allMethods.forEach(key => {
        smartApi[key] = async (...args: any[]) => {
            // 1. If we already know we are in fallback/mock mode, go straight to mock
            if (isFallbackMode) {
                // Check if mock implementation exists
                if (typeof mockApi[key] === 'function') {
                    return mockApi[key](...args);
                }
                console.warn(`[SmartAPI] Method ${key} called in Mock Mode but not implemented.`);
                throw new Error(`Method ${key} not supported in Mock Mode.`);
            }

            // 2. Initial Connection Check (Fast-Fail)
            // Perform this only once to avoid overhead, but do it before the first real call.
            if (!connectionChecked && supabaseUrl) {
                connectionChecked = true;
                try {
                    // Try to fetch the root URL (Kong) with a short timeout (2s)
                    // If supabaseUrl is internal (e.g. http://supabase_kong:8000), this will fail fast in browser.
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout

                    // We just fetch the URL. It might return 404 or 200, but as long as it connects, we are good.
                    // If it's a network error (dns, refused), fetch throws.
                    await fetch(supabaseUrl, { method: 'HEAD', signal: controller.signal }).catch(e => {
                        // If HEAD fails (e.g. CORS), try GET. Or just ignore specific http errors.
                        // We strictly care about Network/Connection errors.
                        if (e.name === 'AbortError' || e.message.includes('Failed to fetch') || e.message.includes('Network request failed')) {
                            throw e;
                        }
                    });
                    clearTimeout(timeoutId);
                } catch (e: any) {
                    console.warn(`[SmartAPI] Initial connection check to ${supabaseUrl} failed: ${e.message}. Switching to Mock Mode.`);
                    isFallbackMode = true;
                    // Retry current call in mock mode
                    if (typeof mockApi[key] === 'function') {
                        return mockApi[key](...args);
                    }
                }
            }

            // 3. Try Real API
            try {
                // Double check isFallbackMode in case the check above flipped it
                if (isFallbackMode && typeof mockApi[key] === 'function') {
                    return mockApi[key](...args);
                }

                const method = (supabaseApi as any)[key];
                if (typeof method !== 'function') throw new Error(`Method ${key} not found in Supabase API`);

                return await method.apply(supabaseApi, args);
            } catch (error: any) {
                // 4. Runtime Fallback on Network Error
                // If the initial check passed (or was skipped), but this specific call fails with network error.
                const isNetworkError =
                    error.message && (
                        error.message.includes('Failed to fetch') ||
                        error.message.includes('Network request failed') ||
                        error.message.includes('connection refused') ||
                        error.message.includes('upstream connect error')
                    );

                if (isNetworkError) {
                    console.warn(`[SmartAPI] Network error detected during ${key}: ${error.message}. Switching to Mock Mode.`);
                    isFallbackMode = true;
                    if (typeof mockApi[key] === 'function') {
                        return mockApi[key](...args);
                    }
                }

                // If it's a business logic error (e.g. 401 Unauthorized, 404 Not Found), rethrow.
                throw error;
            }
        };
    });

    return smartApi;
};

// Export the Smart API
export const api = createSmartApi();
