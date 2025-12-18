import { Employee, EmployeeRole, Task, TaskStatus, TaskPriority, DocumentVersion, Project, BlogPost, AssignableUser } from '../types.ts';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

// --- SUPABASE CLIENT SETUP ---
const getSupabaseConfig = () => {
    const url = localStorage.getItem('supabaseUrl');
    const key = localStorage.getItem('supabaseAnonKey');
    // A robust implementation would handle missing keys more gracefully,
    // but for this step, we assume they are present as we are removing the mock fallback.
    if (!url || !key) {
        console.error("Supabase credentials are not set in localStorage. Please configure them in the Admin Panel -> Settings.");
        // throw new Error("Supabase credentials are not set.");
    }
    return { url, key };
};

const { url: supabaseUrl, key: supabaseAnonKey } = getSupabaseConfig();

export let supabase: SupabaseClient | null = null;

// Unconditionally initialize Supabase client
try {
    supabase = createClient(supabaseUrl!, supabaseAnonKey!); 
} catch (error) {
    console.error("Failed to initialize Supabase client. Check credentials in localStorage.", error);
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
};

export type NewProjectData = {
  title: string;
  description?: string;
};

export type UpdateTaskData = Partial<Omit<NewTaskData, 'project_id'> & { assignee_id: string | null }>;

export type NewBlogPostData = Omit<BlogPost, 'id' | 'authorName' | 'publishDate'>;

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
  async createTask(taskData: NewTaskData): Promise<Task> {
    let assigneeName = 'Unassigned';
    if (taskData.assigneeId) {
        const { data: employee, error } = await supabase!.from('profiles').select('name').eq('id', taskData.assigneeId).single();
        if (employee) { assigneeName = employee.name; } 
        else if (error) { console.warn('Error fetching assignee name:', error.message); }
    }
    const taskToInsert = { 
        project_id: taskData.project_id, 
        title: taskData.title, 
        description: taskData.description, 
        priority: taskData.priority, // Use passed priority
        due_date: taskData.due_date, 
        assignee: assigneeName, 
        assignee_id: taskData.assigneeId || null,
        status: TaskStatus.TODO 
    };
    const { data, error } = await supabase!.from('archon_tasks').insert(taskToInsert).select().single();
    if (error) throw new Error(error.message);
    return data as Task;
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
  }
};

// Export the Supabase API implementation unconditionally
export const api = supabaseApi;
