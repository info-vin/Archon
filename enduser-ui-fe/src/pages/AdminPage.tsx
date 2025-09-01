import React, { useState, useEffect } from 'react';
import { api, AdminNewUserData } from '../services/api.ts';
import { Employee, DocumentVersion, BlogPost, EmployeeRole } from '../types.ts';
import { CheckCircleIcon, XCircleIcon, ClockIcon, PlusIcon, XIcon } from '../components/Icons.tsx';
import { useAuth } from '../hooks/useAuth.tsx';
import UserAvatar from '../components/UserAvatar.tsx';


const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('users');

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 bg-background">
      <h1 className="text-3xl font-bold mb-6">Admin Panel</h1>
      <div className="border-b border-border mb-6">
        <nav className="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
          <TabButton title="User Management" isActive={activeTab === 'users'} onClick={() => setActiveTab('users')} />
          <TabButton title="Document Versions" isActive={activeTab === 'versions'} onClick={() => setActiveTab('versions')} />
          <TabButton title="Blog Management" isActive={activeTab === 'blog'} onClick={() => setActiveTab('blog')} />
          <TabButton title="Admin Transfer" isActive={activeTab === 'transfer'} onClick={() => setActiveTab('transfer')} />
          <TabButton title="Settings" isActive={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
        </nav>
      </div>
      <div className="flex-1 overflow-auto">
        {activeTab === 'users' && <UserManagement />}
        {activeTab === 'versions' && <DocumentVersionsLog />}
        {activeTab === 'blog' && <BlogManagement />}
        {activeTab === 'transfer' && <AdminTransfer />}
        {activeTab === 'settings' && <SettingsComponent />}
      </div>
    </div>
  );
};

const TabButton: React.FC<{ title: string; isActive: boolean; onClick: () => void }> = ({ title, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={`${
      isActive
        ? 'border-primary text-primary'
        : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
  >
    {title}
  </button>
);

const EditUserModal: React.FC<{ user: Employee; onClose: () => void; onSave: (updatedUser: Employee) => void; }> = ({ user, onClose, onSave }) => {
    const [role, setRole] = useState(user.role);
    const [status, setStatus] = useState(user.status);
    const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

    const handleSave = async () => {
        try {
            const updatedUser = await api.updateEmployee(user.id, { role, status });
            onSave(updatedUser);
            alert('User updated successfully!');
            onClose();
        } catch(error: any) {
            alert(`Error updating user: ${error.message}`);
        }
    };

    return (
         <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
            <div className="bg-card rounded-lg shadow-xl w-full max-w-lg p-6 relative">
                <h2 className="text-2xl font-bold mb-4">Edit User: {user.name}</h2>
                <button onClick={onClose} className="absolute top-4 right-4 p-1 rounded-full hover:bg-secondary"><XIcon className="w-6 h-6" /></button>
                <div className="space-y-4">
                    <div>
                        <label htmlFor="role" className="block text-sm font-medium mb-1">Role</label>
                        <select id="role" value={role} onChange={e => setRole(e.target.value as EmployeeRole)} className={inputClass}>
                            {Object.values(EmployeeRole).map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                    </div>
                     <div>
                        <label htmlFor="status" className="block text-sm font-medium mb-1">Status</label>
                        <select id="status" value={status} onChange={e => setStatus(e.target.value as 'active' | 'inactive' | 'suspended')} className={inputClass}>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="suspended">Suspended</option>
                        </select>
                    </div>
                    <div className="flex justify-end space-x-2 pt-2">
                        <button onClick={onClose} className="px-4 py-2 rounded-md bg-secondary text-secondary-foreground">Cancel</button>
                        <button onClick={handleSave} className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90">Save Changes</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const NewUserModal: React.FC<{ onClose: () => void; onSave: (newUser: Employee) => void; }> = ({ onClose, onSave }) => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState<EmployeeRole>(EmployeeRole.MEMBER);
    const [status, setStatus] = useState<'active' | 'inactive' | 'suspended'>('active');
    const [isLoading, setIsLoading] = useState(false);

    const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";
    
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            const newUser = await api.adminCreateUser({ name, email, password, role, status });
            onSave(newUser);
            alert('User created successfully!');
            onClose();
        } catch (error: any) {
            alert(`Error creating user: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
            <div className="bg-card rounded-lg shadow-xl w-full max-w-lg p-6 relative">
                <h2 className="text-2xl font-bold mb-4">Create New User</h2>
                <button onClick={onClose} className="absolute top-4 right-4 p-1 rounded-full hover:bg-secondary"><XIcon className="w-6 h-6" /></button>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input type="text" placeholder="Full Name" value={name} onChange={e => setName(e.target.value)} className={inputClass} required />
                    <input type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} className={inputClass} required />
                    <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className={inputClass} required />
                    <div>
                        <label htmlFor="role-new" className="block text-sm font-medium mb-1">Role</label>
                        <select id="role-new" value={role} onChange={e => setRole(e.target.value as EmployeeRole)} className={inputClass}>
                            {Object.values(EmployeeRole).map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                    </div>
                     <div>
                        <label htmlFor="status-new" className="block text-sm font-medium mb-1">Status</label>
                        <select id="status-new" value={status} onChange={e => setStatus(e.target.value as 'active' | 'inactive' | 'suspended')} className={inputClass}>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="suspended">Suspended</option>
                        </select>
                    </div>
                    <div className="flex justify-end space-x-2 pt-2">
                        <button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-secondary text-secondary-foreground">Cancel</button>
                        <button type="submit" disabled={isLoading} className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{isLoading ? 'Creating...' : 'Create User'}</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

const UserManagement: React.FC = () => {
    const [employees, setEmployees] = useState<Employee[]>([]);
    const [editingUser, setEditingUser] = useState<Employee | null>(null);
    const [isNewUserModalOpen, setIsNewUserModalOpen] = useState(false);

    useEffect(() => {
        api.getEmployees().then(setEmployees).catch(err => alert(`Failed to load employees: ${err.message}`));
    }, []);
    
    const handleUpdateUserInList = (updatedUser: Employee) => {
        setEmployees(employees.map(e => e.id === updatedUser.id ? updatedUser : e));
    };

    const handleAddNewUserToList = (newUser: Employee) => {
        setEmployees(prev => [...prev, newUser]);
    };

    return (
        <>
            <div className="bg-card p-4 rounded-lg">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold">Employees</h2>
                     <button onClick={() => setIsNewUserModalOpen(true)} className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                        <PlusIcon className="w-5 h-5 mr-2" />
                        New User
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-border">
                        <thead className="bg-secondary">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium uppercase">Name</th>
                                <th className="px-6 py-3 text-left text-xs font-medium uppercase">Role</th>
                                <th className="px-6 py-3 text-left text-xs font-medium uppercase">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium uppercase">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {employees.map(emp => (
                                <tr key={emp.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <UserAvatar name={emp.name || ''} className="h-10 w-10" />
                                            <div className="ml-4">
                                                <div className="text-sm font-medium">{emp.name}</div>
                                                <div className="text-sm text-muted-foreground">{emp.email}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">{emp.role}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${emp.status === 'active' ? 'bg-green-500' : 'bg-red-500'} text-white`}>
                                            {emp.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <button onClick={() => setEditingUser(emp)} className="text-primary hover:text-primary/90 disabled:opacity-50 disabled:cursor-not-allowed" disabled={emp.role === EmployeeRole.SYSTEM_ADMIN}>Edit</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            {editingUser && <EditUserModal user={editingUser} onClose={() => setEditingUser(null)} onSave={handleUpdateUserInList} />}
            {isNewUserModalOpen && <NewUserModal onClose={() => setIsNewUserModalOpen(false)} onSave={handleAddNewUserToList} />}
        </>
    );
};

const DocumentVersionsLog: React.FC = () => {
    const [versions, setVersions] = useState<DocumentVersion[]>([]);
    useEffect(() => {
        api.getDocumentVersions().then(setVersions).catch(err => alert(`Failed to load document versions: ${err.message}`));
    }, []);
    
    return (
        <div className="bg-card p-4 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Document Version History</h2>
             <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-secondary">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase">Timestamp</th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase">Changed By</th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase">Change Type</th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase">Field</th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase">Summary</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {versions.map(log => (
                            <tr key={log.id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">{new Date(log.created_at).toLocaleString()}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">{log.created_by}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm capitalize">{log.change_type}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">{log.field_name} (v{log.version_number})</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">{log.change_summary || 'N/A'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const BlogManagement: React.FC = () => {
    const { user } = useAuth();
    const [posts, setPosts] = useState<BlogPost[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        api.getBlogPosts().then(setPosts).catch(err => alert(`Failed to load blog posts: ${err.message}`));
    }, []);

    const handleCreatePost = async (postData: Omit<BlogPost, 'id' | 'authorName' | 'publishDate'>) => {
        try {
            if (!user) throw new Error("User not found");
            const newPostData = {
                ...postData,
                authorName: user.name,
                publishDate: new Date().toISOString(),
            };
            const newPost = await api.createBlogPost(newPostData);
            setPosts(prev => [newPost, ...prev]);
            setIsModalOpen(false);
            alert('Blog post created successfully!');
        } catch(error: any) {
             alert(`Failed to create post: ${error.message}`);
        }
    };

    return (
        <div className="bg-card p-4 rounded-lg">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Blog Posts</h2>
                <button onClick={() => setIsModalOpen(true)} className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                    <PlusIcon className="w-5 h-5 mr-2" />
                    New Post
                </button>
            </div>
             <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-secondary">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase">Title</th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase">Author</th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase">Published Date</th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {posts.map(post => (
                            <tr key={post.id}>
                                <td className="px-6 py-4 whitespace-nowrap font-medium">{post.title}</td>
                                <td className="px-6 py-4 whitespace-nowrap">{post.authorName}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">{new Date(post.publishDate).toLocaleDateString()}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                    <button className="text-primary hover:text-primary/90">Edit</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {isModalOpen && <NewPostModal onClose={() => setIsModalOpen(false)} onSubmit={handleCreatePost} />}
        </div>
    );
};

const NewPostModal: React.FC<{onClose: () => void, onSubmit: (data: any) => Promise<void>}> = ({ onClose, onSubmit }) => {
    const [title, setTitle] = useState('');
    const [excerpt, setExcerpt] = useState('');
    const [imageUrl, setImageUrl] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({ title, excerpt, imageUrl });
    };
    const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
            <div className="bg-card rounded-lg shadow-xl w-full max-w-lg p-6 relative">
                <h2 className="text-2xl font-bold mb-4">Create New Blog Post</h2>
                <button onClick={onClose} className="absolute top-4 right-4 p-1 rounded-full hover:bg-secondary"><XIcon className="w-6 h-6" /></button>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input type="text" placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} className={inputClass} required/>
                    <textarea placeholder="Excerpt" value={excerpt} onChange={e => setExcerpt(e.target.value)} className={inputClass} rows={3} required></textarea>
                    <input type="url" placeholder="Image URL" value={imageUrl} onChange={e => setImageUrl(e.target.value)} className={inputClass} required/>
                    <div className="flex justify-end space-x-2"><button type="submit" className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90">Create</button></div>
                </form>
            </div>
        </div>
    );
};

const AdminTransfer: React.FC = () => {
    const [employees, setEmployees] = useState<Employee[]>([]);
    const [selectedEmployee, setSelectedEmployee] = useState('');
    
    useEffect(() => {
        api.getEmployees().then(setEmployees).catch(err => alert(`Failed to load employees: ${err.message}`));
    }, []);

    const handleTransfer = () => {
        if(selectedEmployee) {
            alert(`Admin rights transfer to ${employees.find(e=>e.id === selectedEmployee)?.name} initiated. This is a mock action.`);
        } else {
            alert('Please select an employee to transfer admin rights to.');
        }
    };

    return (
        <div className="bg-card p-6 rounded-lg max-w-lg mx-auto">
            <h2 className="text-xl font-semibold mb-4">Transfer System Administrator Privileges</h2>
            <p className="text-muted-foreground mb-6">Select an employee to become the new system administrator. This action is irreversible through the UI.</p>
            <div className="space-y-4">
                 <div>
                    <label htmlFor="employee" className="block text-sm font-medium mb-1">New Administrator</label>
                    <select
                        id="employee"
                        value={selectedEmployee}
                        onChange={(e) => setSelectedEmployee(e.target.value)}
                        className="block w-full pl-3 pr-10 py-2 text-base border-border bg-input rounded-md focus:outline-none focus:ring-ring focus:border-ring sm:text-sm"
                    >
                        <option value="">Select an employee</option>
                        {employees.filter(e => e.role !== 'system_admin').map(emp => (
                            <option key={emp.id} value={emp.id}>{emp.name} ({emp.email})</option>
                        ))}
                    </select>
                </div>
                <button
                    onClick={handleTransfer}
                    className="w-full py-2 px-4 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90"
                >
                    Transfer Admin Rights
                </button>
            </div>
        </div>
    );
};

const SettingsComponent: React.FC = () => {
    const [supabaseUrl, setSupabaseUrl] = useState(localStorage.getItem('supabaseUrl') || '');
    const [supabaseAnonKey, setSupabaseAnonKey] = useState(localStorage.getItem('supabaseAnonKey') || '');

    const handleSave = () => {
        try {
            if(!supabaseUrl || !supabaseAnonKey) {
                alert("Both Supabase URL and Anon Key are required.");
                return;
            }
            localStorage.setItem('supabaseUrl', supabaseUrl);
            localStorage.setItem('supabaseAnonKey', supabaseAnonKey);
            alert('Settings saved successfully! The page will now reload to apply changes.');
            window.location.reload();
        } catch (error) {
            alert(`Failed to save settings: ${error}`);
        }
    };
    
    const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

    return (
        <div className="bg-card p-6 rounded-lg max-w-lg mx-auto">
            <h2 className="text-xl font-semibold mb-4">Supabase Settings</h2>
            <p className="text-muted-foreground mb-6">Enter your Supabase project URL and anonymous key. The application will use these to connect to your database.</p>
            <div className="space-y-4">
                <div>
                    <label htmlFor="supabaseUrl" className="block text-sm font-medium mb-1">Supabase URL</label>
                    <input id="supabaseUrl" type="url" value={supabaseUrl} onChange={e => setSupabaseUrl(e.target.value)} className={inputClass} placeholder="https://your-project-ref.supabase.co" />
                </div>
                <div>
                    <label htmlFor="supabaseAnonKey" className="block text-sm font-medium mb-1">Supabase Anon Key</label>
                    <input id="supabaseAnonKey" type="text" value={supabaseAnonKey} onChange={e => setSupabaseAnonKey(e.target.value)} className={inputClass} placeholder="ey..." />
                </div>
                <button
                    onClick={handleSave}
                    className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                    Save and Reload
                </button>
            </div>
        </div>
    );
};

export default AdminPage;