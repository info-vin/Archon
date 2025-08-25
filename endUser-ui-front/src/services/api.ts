import { Employee, EmployeeRole, Task, TaskStatus, TaskPriority, DocumentVersion, Project, BlogPost } from '../types.ts';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// --- SUPABASE CLIENT SETUP ---
const getSupabaseConfig = () => {
    const url = localStorage.getItem('supabaseUrl');
    const key = localStorage.getItem('supabaseAnonKey');
    return { url, key };
};

const { url: supabaseUrl, key: supabaseAnonKey } = getSupabaseConfig();

const useMockData = !supabaseUrl || !supabaseAnonKey || supabaseUrl.startsWith('YOUR_SUPABASE_URL');

export let supabase: SupabaseClient | null = null;

if (useMockData) {
    console.warn("Supabase credentials are not set in localStorage. Using mock data. Please update them in the Admin Panel -> Settings.");
} else {
    try {
        supabase = createClient(supabaseUrl!, supabaseAnonKey!);
    } catch (error) {
        console.error("Failed to initialize Supabase client. Check credentials in localStorage.", error);
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
};

export type NewBlogPostData = Omit<BlogPost, 'id' | 'authorName' | 'publishDate'>;

// --- MOCK DATA (used if Supabase is not configured) ---
const MOCK_EMPLOYEES: Employee[] = [
    { id: '1', employeeId: 'E1001', name: 'Admin User', email: 'admin@archon.com', department: 'IT', position: 'System Administrator', status: 'active', role: EmployeeRole.SYSTEM_ADMIN, avatar: `https://i.pravatar.cc/150?u=admin@archon.com` },
    { id: '2', employeeId: 'E1002', name: 'Alice Johnson', email: 'alice@archon.com', department: 'Engineering', position: 'Senior Developer', status: 'active', role: EmployeeRole.SENIOR_MEMBER, avatar: `https://i.pravatar.cc/150?u=alice@archon.com` },
    { id: '3', employeeId: 'E1003', name: 'Bob Williams', email: 'bob@archon.com', department: 'Engineering', position: 'Frontend Developer', status: 'active', role: EmployeeRole.MEMBER, avatar: `https://i.pravatar.cc/150?u=bob@archon.com` },
];

const MOCK_PROJECTS: Project[] = [
    { id: 'proj-1', title: 'Archon Core Platform', description: 'Development of the main Archon task management system.', status: 'active', projectManagerId: '1' },
    { id: 'proj-2', title: 'Website Redesign', description: 'Complete overhaul of the public-facing marketing website.', status: 'planning', projectManagerId: '2' },
];

const MOCK_TASKS: Task[] = [
    { id: 'task-1', project_id: 'proj-1', title: 'Implement Supabase Integration', description: '', status: TaskStatus.DONE, assignee: 'Alice Johnson', task_order: 1, priority: TaskPriority.CRITICAL, due_date: '2024-09-10T23:59:59Z', created_at: '2024-09-01T10:00:00Z', updated_at: '2024-09-05T10:00:00Z' },
    { id: 'task-2', project_id: 'proj-1', title: 'Develop Kanban View', description: '', status: TaskStatus.DOING, assignee: 'Bob Williams', task_order: 2, priority: TaskPriority.HIGH, due_date: '2024-09-15T23:59:59Z', created_at: '2024-09-02T10:00:00Z', updated_at: '2024-09-06T10:00:00Z' },
    { id: 'task-3', project_id: 'proj-2', title: 'Design new landing page mockups', description: '', status: TaskStatus.TODO, assignee: 'Unassigned', task_order: 1, priority: TaskPriority.MEDIUM, due_date: '2024-09-20T23:59:59Z', created_at: '2024-09-03T10:00:00Z', updated_at: '2024-09-03T10:00:00Z' },
    { id: 'task-4', project_id: 'proj-1', title: 'Fix authentication bug', description: 'Users are reporting intermittent login failures.', status: TaskStatus.REVIEW, assignee: 'Alice Johnson', task_order: 3, priority: TaskPriority.HIGH, due_date: '2024-09-12T23:59:59Z', created_at: '2024-09-04T10:00:00Z', updated_at: '2024-09-08T10:00:00Z' },
];

const MOCK_DOCUMENT_VERSIONS: DocumentVersion[] = [
    { id: 'dv-1', project_id: 'proj-1', task_id: null, field_name: 'docs', version_number: 1, content: { 'initial_spec': '...' }, change_summary: 'Initial project documentation created.', change_type: 'create', created_by: 'Admin User', created_at: '2024-09-01T09:00:00Z' },
    { id: 'dv-2', project_id: 'proj-2', task_id: null, field_name: 'features', version_number: 1, content: { 'feature_list': '...' }, change_summary: 'Added feature list for website redesign.', change_type: 'update', created_by: 'Alice Johnson', created_at: '2024-09-02T11:00:00Z' },
];

const MOCK_BLOG_POSTS: BlogPost[] = [
    { id: 'post-1', title: 'Q3 Engineering Roadmap', excerpt: 'An overview of our key initiatives and project timelines for the upcoming quarter.', authorName: 'Alice Johnson', publishDate: '2024-08-20T10:00:00Z', imageUrl: `https://picsum.photos/seed/post-1/600/400` },
    { id: 'post-2', title: 'A Guide to Our New Design System', excerpt: 'Learn about the components, patterns, and principles behind our updated UI/UX framework.', authorName: 'Charlie Brown', publishDate: '2024-08-18T14:30:00Z', imageUrl: `https://picsum.photos/seed/post-2/600/400` },
    { id: 'post-3', title: 'Welcome to the Archon Platform', excerpt: 'Discover how Archon can help your team manage tasks and projects with greater efficiency.', authorName: 'Admin User', publishDate: '2024-08-15T09:00:00Z', imageUrl: `https://picsum.photos/seed/post-3/600/400` }
];

// --- MOCK API IMPLEMENTATION ---
const mockApi = {
    async login(credentials: LoginCredentials): Promise<Employee | null> {
        const user = MOCK_EMPLOYEES.find(e => e.email === credentials.email);
        if (user) {
            sessionStorage.setItem('mock_user_id', user.id);
            return user;
        }
        throw new Error("Invalid credentials.");
    },
    async register(credentials: RegistrationData): Promise<Employee | null> {
        if (MOCK_EMPLOYEES.some(e => e.email === credentials.email)) {
            throw new Error("Email already in use.");
        }
        const newUser: Employee = {
            id: String(MOCK_EMPLOYEES.length + 1),
            employeeId: `E${1001 + MOCK_EMPLOYEES.length}`,
            name: credentials.name,
            email: credentials.email,
            department: 'Unassigned',
            position: 'New Member',
            status: 'active',
            role: EmployeeRole.MEMBER,
            avatar: `https://i.pravatar.cc/150?u=${credentials.email}`
        };
        MOCK_EMPLOYEES.push(newUser);
        sessionStorage.setItem('mock_user_id', newUser.id);
        return newUser;
    },
    async adminCreateUser(userData: AdminNewUserData): Promise<Employee> {
        if (MOCK_EMPLOYEES.some(e => e.email === userData.email)) {
            throw new Error("Email already in use.");
        }
        const newUser: Employee = {
            id: String(MOCK_EMPLOYEES.length + 1),
            employeeId: `E${1001 + MOCK_EMPLOYEES.length}`,
            name: userData.name,
            email: userData.email,
            department: 'Unassigned',
            position: 'New Member',
            status: userData.status,
            role: userData.role,
            avatar: `https://i.pravatar.cc/150?u=${userData.email}`
        };
        MOCK_EMPLOYEES.push(newUser);
        return newUser;
    },
    async logout(): Promise<void> {
        sessionStorage.removeItem('mock_user_id');
    },
    async getCurrentUser(): Promise<Employee | null> {
        const userId = sessionStorage.getItem('mock_user_id');
        if (!userId) return null;
        return MOCK_EMPLOYEES.find(e => e.id === userId) || null;
    },
    async getTasks(): Promise<Task[]> { return [...MOCK_TASKS]; },
    async getProjects(): Promise<Project[]> { return [...MOCK_PROJECTS]; },
    async createTask(taskData: NewTaskData): Promise<Task> {
        const assignee = MOCK_EMPLOYEES.find(e => e.id === taskData.assigneeId);
        const newTask: Task = {
            id: `task-${Date.now()}`,
            project_id: taskData.project_id,
            title: taskData.title,
            description: taskData.description,
            status: TaskStatus.TODO,
            assignee: assignee ? assignee.name : 'Unassigned',
            task_order: MOCK_TASKS.filter(t => t.project_id === taskData.project_id).length + 1,
            priority: TaskPriority.HIGH,
            due_date: taskData.due_date,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
        MOCK_TASKS.push(newTask);
        return newTask;
    },
    async getEmployees(): Promise<Employee[]> { return [...MOCK_EMPLOYEES]; },
    async getDocumentVersions(): Promise<DocumentVersion[]> { return [...MOCK_DOCUMENT_VERSIONS]; },
    async getBlogPosts(): Promise<BlogPost[]> {
        await new Promise(res => setTimeout(res, 250));
        return MOCK_BLOG_POSTS;
    },
    async createBlogPost(postData: any): Promise<BlogPost> {
        const newPost: BlogPost = {
            id: `post-${Date.now()}`,
            ...postData,
        };
        MOCK_BLOG_POSTS.unshift(newPost);
        return newPost;
    },
    async updateEmployee(employeeId: string, updates: Partial<Employee>): Promise<Employee> {
        const index = MOCK_EMPLOYEES.findIndex(e => e.id === employeeId);
        if (index > -1) {
            MOCK_EMPLOYEES[index] = { ...MOCK_EMPLOYEES[index], ...updates };
            return MOCK_EMPLOYEES[index];
        }
        throw new Error("Employee not found.");
    },
    async updateUserEmail(newEmail: string): Promise<void> {
        console.log(`Mock: Updating email to ${newEmail}`);
        const user = await this.getCurrentUser();
        if (user) {
            user.email = newEmail;
        } else {
            throw new Error("User not found");
        }
    },
    async updateUserPassword(newPassword: string): Promise<void> {
        console.log("Mock: Password updated for current user.");
        return;
    }
};

// --- SUPABASE API IMPLEMENTATION ---
const supabaseApi = {
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
    const { data: profile, error } = await supabase!.from('profiles').select('*').eq('id', session.user.id).single();
    if (error) {
      console.error('Error fetching user profile:', error.message);
      // Fallback to auth data if profile is not ready
      return { id: session.user.id, email: session.user.email!, name: session.user.user_metadata.name || 'New User', role: EmployeeRole.VIEWER, avatar: session.user.user_metadata.avatar_url || '', employeeId: '', department: '', position: '', status: 'active' };
    }
    return profile as Employee;
  },
  async getTasks(): Promise<Task[]> {
    const { data, error } = await supabase!.from('archon_tasks').select('*');
    if (error) throw new Error(error.message);
    return data as Task[];
  },
  async getProjects(): Promise<Project[]> {
    const { data, error } = await supabase!.from('archon_projects').select('*');
    if (error) throw new Error(error.message);
    return data as Project[];
  },
  async createTask(taskData: NewTaskData): Promise<Task> {
    let assigneeName = 'Unassigned';
    if (taskData.assigneeId) {
        const { data: employee, error } = await supabase!.from('profiles').select('name').eq('id', taskData.assigneeId).single();
        if (employee) { assigneeName = employee.name; } 
        else if (error) { console.warn('Error fetching assignee name:', error.message); }
    }
    const taskToInsert = { project_id: taskData.project_id, title: taskData.title, description: taskData.description, priority: TaskPriority.HIGH, due_date: taskData.due_date, assignee: assigneeName, status: TaskStatus.TODO };
    const { data, error } = await supabase!.from('archon_tasks').insert(taskToInsert).select().single();
    if (error) throw new Error(error.message);
    return data as Task;
  },
  async getEmployees(): Promise<Employee[]> {
    const { data, error } = await supabase!.from('profiles').select('*');
    if (error) throw new Error(error.message);
    return data as Employee[];
  },
  async getDocumentVersions(): Promise<DocumentVersion[]> {
    const { data, error } = await supabase!.from('archon_document_versions').select('*');
    if (error) throw new Error(error.message);
    return data as DocumentVersion[];
  },
  async getBlogPosts(): Promise<BlogPost[]> {
    await new Promise(res => setTimeout(res, 250)); // Simulating network latency
    return MOCK_BLOG_POSTS;
  },
  async createBlogPost(postData: any): Promise<BlogPost> {
    console.warn("createBlogPost is not implemented for Supabase API yet.");
    // For demonstration, let's just return a mock response.
    const newPost: BlogPost = { id: `post-${Date.now()}`, ...postData };
    return newPost;
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
  }
};

// Export the correct API implementation based on whether Supabase is configured
export const api = useMockData ? mockApi : supabaseApi;