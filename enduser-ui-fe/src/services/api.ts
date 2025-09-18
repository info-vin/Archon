import { Employee, EmployeeRole, Task, TaskStatus, TaskPriority, DocumentVersion, Project, BlogPost, AssignableUser } from '../types.ts';
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
    { id: '4', employeeId: 'E1004', name: 'Design AI Agent', email: 'ai-designer@archon.com', department: 'AI', position: 'AI Agent', status: 'active', role: EmployeeRole.AI_AGENT, avatar: `https://i.pravatar.cc/150?u=ai-designer@archon.com` },
];

const MOCK_PROJECTS: Project[] = [
    { id: 'proj-1', title: 'Archon Core Platform', description: 'Development of the main Archon task management system.', status: 'active', projectManagerId: '1' },
    { id: 'proj-2', title: 'Website Redesign', description: 'Complete overhaul of the public-facing marketing website.', status: 'planning', projectManagerId: '2' },
];

const MOCK_TASKS: Task[] = [
    { id: 'task-1', project_id: 'proj-1', title: 'Implement Supabase Integration', description: '', status: TaskStatus.DONE, assignee: 'Alice Johnson', task_order: 1, priority: TaskPriority.CRITICAL, due_date: '2025-08-30T23:59:59Z', created_at: '2025-06-01T10:00:00Z', updated_at: '2025-08-28T10:00:00Z' },
    { id: 'task-2', project_id: 'proj-1', title: 'Develop Kanban View', description: '', status: TaskStatus.DOING, assignee: 'Bob Williams', task_order: 2, priority: TaskPriority.HIGH, due_date: '2025-08-15T23:59:59Z', created_at: '2025-06-15T10:00:00Z', updated_at: '2025-07-20T10:00:00Z' },
    { id: 'task-3', project_id: 'proj-2', title: 'Design new landing page mockups', description: '', status: TaskStatus.TODO, assignee: 'Unassigned', task_order: 1, priority: TaskPriority.MEDIUM, due_date: '2025-08-01T23:59:59Z', created_at: '2025-07-01T10:00:00Z', updated_at: '2025-07-01T10:00:00Z' },
    { id: 'task-4', project_id: 'proj-1', title: 'Fix authentication bug', description: 'Users are reporting intermittent login failures.', status: TaskStatus.REVIEW, assignee: 'Alice Johnson', task_order: 3, priority: TaskPriority.HIGH, due_date: '2025-09-10T23:59:59Z', created_at: '2025-07-10T10:00:00Z', updated_at: '2025-07-15T10:00:00Z', attachments: [{ file_name: 'debug-log.txt', url: 'data:text/plain;charset=utf-8,This%20is%20a%20mock%20debug%20log%20file.'},{ file_name: 'screenshot-error.png', url: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=' }] },
];

const MOCK_DOCUMENT_VERSIONS: DocumentVersion[] = [
    { id: 'dv-1', project_id: 'proj-1', task_id: null, field_name: 'docs', version_number: 1, content: { 'initial_spec': '...' }, change_summary: 'Initial project documentation created.', change_type: 'create', created_by: 'Admin User', created_at: '2024-09-01T09:00:00Z' },
    { id: 'dv-2', project_id: 'proj-2', task_id: null, field_name: 'features', version_number: 1, content: { 'feature_list': '...' }, change_summary: 'Added feature list for website redesign.', change_type: 'update', created_by: 'Alice Johnson', created_at: '2024-09-02T11:00:00Z' },
];

const MOCK_BLOG_POSTS: BlogPost[] = [
    {
        id: 'post-1',
        title: '案例一：AI 助您輕鬆完成行銷素材',
        excerpt: "**角色**: 一位行銷專員 (User)。\n\n**目標**: 產出一份新產品的行銷 DM。\n\n**流程拆解**:\n\n1.  **任務啟動 (前端)**\n    *   行銷專員登入系統，點擊「新增任務」。\n    *   他上傳了 `product_spec.pdf` 和 `copy_draft.txt` 兩個檔案。\n    *   他點擊「指派給」下拉選單，選擇了「設計師 AI Agent」。\n\n2.  **後端處理與 Agent 觸發**\n    *   後端 API 收到請求，進行權限驗證。\n    *   在資料庫建立任務，狀態為 `處理中`。\n    *   後端非同步地觸發「設計師 AI Agent」。\n\n3.  **AI Agent 執行**\n    *   AI Agent 被喚醒，下載並分析任務文件。\n    *   基於內容，它生成了一張圖片檔案 `dm_draft_v1.png`。\n\n4.  **產出交付與任務更新**\n    *   Agent 呼叫工具，將 `dm_draft_v1.png` 上傳到 Supabase Storage。\n    *   後端更新資料庫任務：狀態改為 `待審核`，並附加檔案 URL。\n\n5.  **使用者審核 (前端)**\n    *   行銷專員的介面收到即時更新，看到狀態變更和新的附件連結，點擊審核。",
        authorName: 'Archon 團隊',
        publishDate: '2025-08-29T10:00:00Z',
        imageUrl: `https://picsum.photos/seed/usecase-1/600/400`
    },
    {
        id: 'post-2',
        title: '案例二：從技術支援到知識庫建立的自動化流程',
        excerpt: "**角色**: 初階客服、資深後端工程師、知識庫 AI Agent。\n\n**目標**: 解決一個複雜的技術問題，並將解決方案歸檔至內部知識庫。\n\n**流程拆解**:\n\n1.  **問題升級 (客服 -> 工程師)**\n    *   初階客服遇到無法解決的 Bug，建立任務並附上日誌，指派給資深後端工程師「陳大哥」。\n\n2.  **人工處理 (工程師)**\n    *   陳大哥調查並解決問題，在任務評論區詳細記錄了排查過程和解決方案。\n\n3.  **知識庫歸檔 (工程師 -> AI Agent)**\n    *   陳大哥認為此方案有價值，將任務重新指派給「知識庫 AI Agent」，並指示它整理成 Q&A 文件。\n\n4.  **AI Agent 整理與歸檔**\n    *   AI Agent 讀取任務歷史，提煉核心內容，生成一份標準化的 Markdown 文件。\n    *   它呼叫工具將文件上傳至 Supabase Storage 中名為「internal_knowledge_base」的特定位置。\n\n5.  **任務完成與知識沉澱**\n    *   任務狀態變為 `已歸檔`，並附上知識庫文章連結，供團隊未來搜尋參考。",
        authorName: 'Archon 團隊',
        publishDate: '2025-08-28T14:30:00Z',
        imageUrl: `https://picsum.photos/seed/usecase-2/600/400`
    },
    {
        id: 'post-3',
        title: '案例三：業務開發與客戶拜訪的智能規劃',
        excerpt: "**角色**: 業務人員「小王」。\n\n**目標**: 蒐集潛在大客戶「ABC 科技」的完整情報，並規劃一次成功的初次拜訪。\n\n**流程拆解**:\n\n1.  **情資蒐集 (智能查詢)**\n    *   小王在系統中使用自然語言查詢關於「ABC 科技」的所有資訊。\n    *   RAG Agent 在後端搜尋所有關聯資料庫與文件，並生成一份摘要總結，連同原始資料連結一併呈現。\n\n2.  **行動規劃 (任務建立與指派)**\n    *   小王根據情資建立父任務「規劃拜訪 ABC 科技」，並設定截止日期。\n    *   他建立多個子任務：\n        *   指派「行銷 AI Agent」製作客製化簡報。\n        *   指派「自己」去和客戶預約時間。\n        *   指派「資深工程師」作為技術顧問，準備一同出席。\n\n3.  **協同工作與進度追蹤**\n    *   所有相關人員與 AI 都在同一個任務下更新各自的進度與產出（例如，AI 附加簡報草稿、工程師回覆時間）。\n\n4.  **行程確定與完成**\n    *   小王在所有準備工作就緒後，敲定會議時間，並在父任務中記錄，完成整個規劃的閉環。",
        authorName: 'Archon 團隊',
        publishDate: '2025-08-27T09:00:00Z',
        imageUrl: `https://picsum.photos/seed/usecase-3/600/400`
    }
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
    async getAssignableUsers(): Promise<AssignableUser[]> { 
        // In mock mode, return a subset of employees to simulate RBAC filtering
        return MOCK_EMPLOYEES.filter(e => e.role !== EmployeeRole.SYSTEM_ADMIN).map(e => ({ id: e.id, name: e.name, role: e.role }));
    },
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