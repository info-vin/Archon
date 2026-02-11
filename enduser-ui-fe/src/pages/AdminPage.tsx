import React, { useState, useEffect } from 'react';
import { api } from '../services/api.ts';
import { DocumentVersion, BlogPost } from '../types.ts';
import { CheckCircleIcon, PlusIcon, XIcon, RefreshCwIcon, SaveIcon, KeyIcon, ShieldCheckIcon, SearchIcon } from '../components/Icons.tsx';
import { useAuth } from '../hooks/useAuth.tsx';

import { IdentityMatrix } from '../features/admin/components/IdentityMatrix.tsx';
import { SystemHealthDashboard } from '../features/admin/components/SystemHealthDashboard.tsx';


const AdminPage: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const role = user?.role?.toLowerCase();
  const isOnlyManager = !isAdmin && (role === 'manager');
  
  const [activeTab, setActiveTab] = useState(isOnlyManager ? 'settings' : 'health');

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 bg-background text-foreground">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">{isOnlyManager ? 'Manager Control Center' : 'Admin Control Center'}</h1>
        <p className="text-muted-foreground">
          {isOnlyManager 
            ? 'Configure extraction workflows and team-level parameters.' 
            : 'System-wide configuration and personnel management for L1 Administrators.'}
        </p>
      </header>

      <div className="border-b border-border mb-6">
        <nav className="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
          {!isOnlyManager && <TabButton title="System Health" isActive={activeTab === 'health'} onClick={() => setActiveTab('health')} />}
          {!isOnlyManager && <TabButton title="User Management" isActive={activeTab === 'users'} onClick={() => setActiveTab('users')} />}
          <TabButton title="System Settings" isActive={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
          <TabButton title="Data Extraction" isActive={activeTab === 'extraction'} onClick={() => setActiveTab('extraction')} />
          <TabButton title="System Prompts" isActive={activeTab === 'prompts'} onClick={() => setActiveTab('prompts')} />
          {!isOnlyManager && <TabButton title="Blog Management" isActive={activeTab === 'blog'} onClick={() => setActiveTab('blog')} />}
          {!isOnlyManager && <TabButton title="Document Versions" isActive={activeTab === 'versions'} onClick={() => setActiveTab('versions')} />}
        </nav>
      </div>

      <div className="flex-1 overflow-auto">
        {activeTab === 'health' && !isOnlyManager && <SystemHealthDashboard />}
        {activeTab === 'users' && !isOnlyManager && <IdentityMatrix />}
        {activeTab === 'settings' && <SystemSettings />}
        {activeTab === 'extraction' && <ExtractionManager />}
        {activeTab === 'prompts' && <PromptManagement isManagerMode={isOnlyManager} />}
        {activeTab === 'blog' && !isOnlyManager && <BlogManagement />}
        {activeTab === 'versions' && !isOnlyManager && <DocumentVersionsLog />}
      </div>
    </div>
  );
};

const TabButton: React.FC<{ title: string; isActive: boolean; onClick: () => void }> = ({ title, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={`${
      isActive
        ? 'border-indigo-500 text-indigo-500' // Updated to match Admin Brand (Violet/Indigo)
        : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-all`}
  >
    {title}
  </button>
);

// --- NEW COMPONENT: PROMPT MANAGEMENT ---
const PromptManagement: React.FC<{ isManagerMode: boolean }> = ({ isManagerMode }) => {
    const [prompts, setPrompts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedPrompt, setSelectedPrompt] = useState<any>(null);
    const [editValue, setEditValue] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        fetchPrompts();
    }, []);

    const fetchPrompts = async () => {
        setLoading(true);
        try {
            const data = await api.getSystemPrompts();
            setPrompts(data);
            if (data.length > 0 && !selectedPrompt) {
                handleSelect(data[0]);
            }
        } catch (err: any) {
            alert("Failed to load prompts: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = (p: any) => {
        setSelectedPrompt(p);
        setEditValue(p.prompt);
    };

    const handleSave = async () => {
        if (!selectedPrompt) return;
        setIsSaving(true);
        try {
            await api.updateSystemPrompt(selectedPrompt.prompt_name, { content: editValue });
            alert("Prompt updated and cache reloaded successfully!");
            fetchPrompts(); // Refresh list to get updated_at
        } catch (err: any) {
            alert("Save failed: " + err.message);
        } finally {
            setIsSaving(false);
        }
    };

    const isLocked = isManagerMode && selectedPrompt?.is_system_protected;

    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-primary" /></div>;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full min-h-[600px]">
            {/* List Sidebar */}
            <div className="lg:col-span-1 space-y-2 overflow-y-auto pr-2">
                <h3 className="text-xs font-bold uppercase text-muted-foreground tracking-wider mb-4">Available Prompts</h3>
                {prompts.map(p => (
                    <button 
                        key={p.prompt_name}
                        onClick={() => handleSelect(p)}
                        className={`w-full text-left p-4 rounded-xl border transition-all ${selectedPrompt?.prompt_name === p.prompt_name ? 'border-primary bg-primary/5 shadow-sm' : 'border-border bg-card hover:border-primary/50'}`}
                    >
                        <div className="flex justify-between items-start">
                             <div className="font-bold text-sm truncate">{p.prompt_name.replace(/_/g, ' ').toUpperCase()}</div>
                             {p.is_system_protected ? (
                                 <div className="flex items-center text-amber-500" title="System Protected">
                                     <KeyIcon className="w-3.5 h-3.5" />
                                 </div>
                             ) : (
                                 <div className="flex items-center text-green-500" title="Editable">
                                     <CheckCircleIcon className="w-4 h-4" />
                                 </div>
                             )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-1">{p.description || 'No description'}</div>
                    </button>
                ))}
            </div>

            {/* Editor Area */}
            <div className="lg:col-span-2 flex flex-col bg-card rounded-2xl border border-border overflow-hidden shadow-sm">
                {selectedPrompt ? (
                    <>
                        <div className="p-4 border-b border-border bg-muted/30 flex justify-between items-center">
                            <div>
                                <h3 className="font-bold text-lg flex items-center gap-2">
                                    {selectedPrompt.prompt_name.replace(/_/g, ' ').toUpperCase()}
                                    {isLocked && <span className="text-[10px] px-2 py-0.5 bg-amber-100 text-amber-700 rounded border border-amber-200">READ ONLY</span>}
                                </h3>
                                <p className="text-xs text-muted-foreground">Last updated: {new Date(selectedPrompt.updated_at).toLocaleString()}</p>
                            </div>
                            {!isLocked && (
                                <button 
                                    onClick={handleSave}
                                    disabled={isSaving || editValue === selectedPrompt.prompt}
                                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-bold text-sm hover:bg-primary/90 disabled:opacity-50 disabled:grayscale transition-all"
                                >
                                    {isSaving ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <SaveIcon className="w-4 h-4" />}
                                    SAVE CHANGES
                                </button>
                            )}
                        </div>
                        <div className="flex-1 p-4 flex flex-col space-y-4">
                            <div className="flex-1 relative">
                                <textarea 
                                    value={editValue}
                                    onChange={(e) => setEditValue(e.target.value)}
                                    readOnly={isLocked}
                                    className={`w-full h-full p-4 bg-background border border-border rounded-xl font-mono text-sm focus:ring-2 focus:ring-primary outline-none resize-none leading-relaxed shadow-inner ${isLocked ? 'opacity-70 cursor-not-allowed bg-muted/20' : ''}`}
                                    placeholder="Enter system prompt here..."
                                />
                                {!isLocked && (
                                    <div className="absolute bottom-4 right-4 text-[10px] text-muted-foreground font-mono bg-background/80 px-2 py-1 rounded border border-border">
                                        {editValue.length} characters
                                    </div>
                                )}
                            </div>
                            {isLocked ? (
                                <div className="bg-amber-50 dark:bg-amber-950/20 p-3 rounded-lg border border-amber-100 dark:border-amber-900/30 flex gap-3">
                                    <KeyIcon className="w-5 h-5 text-amber-600 shrink-0" />
                                    <div className="text-xs text-amber-800 dark:text-amber-400">
                                        <strong>System Protected:</strong> This prompt defines core compliance or security rules. Only Administrators can modify it.
                                    </div>
                                </div>
                            ) : (
                                <div className="bg-blue-50 dark:bg-blue-950/20 p-3 rounded-lg border border-blue-100 dark:border-blue-900/30 flex gap-3">
                                    <ShieldCheckIcon className="w-5 h-5 text-blue-600 shrink-0" />
                                    <div className="text-xs text-blue-800 dark:text-blue-400">
                                        <strong>Business Logic:</strong> You can edit this prompt to adjust tone, style, or output format. Changes apply immediately.
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-muted-foreground italic">Select a prompt from the list to start editing.</div>
                )}
            </div>
        </div>
    );
};



const DocumentVersionsLog: React.FC = () => {
    const [versions, setVersions] = useState<DocumentVersion[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        api.getDocumentVersions()
            .then(setVersions)
            .catch(err => alert(`Failed to load document versions: ${err.message}`))
            .finally(() => setLoading(false));
    }, []);

    // GAP 3: Robust Multi-dimensional Filtering Logic
    const filteredVersions = React.useMemo(() => {
        const query = searchTerm.toLowerCase().trim();
        if (!query) return versions;
        
        return versions.filter(v => 
            v.created_by?.toLowerCase().includes(query) ||
            v.field_name?.toLowerCase().includes(query) ||
            v.change_summary?.toLowerCase().includes(query) ||
            v.change_type?.toLowerCase().includes(query)
        );
    }, [versions, searchTerm]);
    
    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm flex flex-col h-full max-h-[calc(100vh-250px)]">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <div>
                    <h2 className="text-xl font-bold">Document Version Audit Trail</h2>
                    <p className="text-xs text-muted-foreground italic">Track every configuration change across the system.</p>
                </div>
                
                {/* GAP 3: Search Interface */}
                <div className="relative w-full md:w-64">
                    <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input 
                        type="text"
                        placeholder="Search logs..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 bg-muted/50 border border-border rounded-xl text-sm focus:ring-2 ring-primary/30 outline-none transition-all"
                    />
                </div>
            </div>

             <div className="overflow-x-auto overflow-y-auto -mx-6 flex-1 min-h-0">
                <table className="min-w-full divide-y divide-border relative">
                    <thead className="bg-muted/50 sticky top-0 z-10">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Timestamp</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Changed By</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Type</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Field / Version</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Summary</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-card">
                        {loading ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center italic text-muted-foreground">
                                    <RefreshCwIcon className="animate-spin w-6 h-6 mx-auto mb-2 opacity-20" />
                                    Loading audit logs...
                                </td>
                            </tr>
                        ) : filteredVersions.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground italic">
                                    {searchTerm ? `No logs matching "${searchTerm}"` : 'No version history found.'}
                                </td>
                            </tr>
                        ) : (
                            filteredVersions.map(log => (
                                <tr key={log.id} className="hover:bg-muted/30 transition-colors group">
                                    <td className="px-6 py-4 whitespace-nowrap text-[10px] text-muted-foreground font-mono">
                                        {new Date(log.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-bold flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
                                            {log.created_by}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-0.5 text-[9px] font-black uppercase rounded border ${
                                            log.change_type === 'CREATE' ? 'bg-green-50 text-green-700 border-green-200' : 
                                            log.change_type === 'DELETE' ? 'bg-red-50 text-red-700 border-red-200' :
                                            'bg-indigo-50 text-indigo-700 border-indigo-200'
                                        }`}>{log.change_type}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-xs">
                                        <span className="font-mono bg-muted px-1 rounded">{log.field_name}</span>
                                        <span className="ml-2 text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">REV-{log.version_number}</span>
                                    </td>
                                    <td className="px-6 py-4 text-xs text-slate-600 dark:text-slate-400 max-w-xs truncate font-medium" title={log.change_summary || ''}>
                                        {log.change_summary || 'N/A'}
                                    </td>
                                </tr>
                            ))
                        )}
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
    const [editingPost, setEditingPost] = useState<BlogPost | null>(null);

    useEffect(() => {
        api.getBlogPosts().then(setPosts).catch(err => alert(`Failed to load blog posts: ${err.message}`));
    }, []);

    const handleSavePost = async (postData: Omit<BlogPost, 'id' | 'authorName' | 'publishDate'>, postId?: string) => {
        try {
            if (!user) throw new Error("User not found");
            if (postId) { // Editing existing post
                const updatedPost = await api.updateBlogPost(postId, postData);
                setPosts(prev => prev.map(p => p.id === postId ? updatedPost : p));
                alert('Blog post updated successfully!');
            } else { // Creating new post
                const newPostData = {
                    ...postData,
                    authorName: user.name,
                    publishDate: new Date().toISOString(),
                };
                const newPost = await api.createBlogPost(newPostData);
                setPosts(prev => [newPost, ...prev]);
                alert('Blog post created successfully!');
            }
            setIsModalOpen(false);
            setEditingPost(null);
        } catch(error: any) {
             alert(`Failed to save post: ${error.message}`);
        }
    };

    const handleDeletePost = async (postId: string) => {
        if (window.confirm('Are you sure you want to delete this post?')) {
            try {
                await api.deleteBlogPost(postId);
                setPosts(prev => prev.filter(p => p.id !== postId));
                alert('Post deleted successfully!');
            } catch (error: any) {
                alert(`Failed to delete post: ${error.message}`);
            }
        }
    };

    const openNewPostModal = () => {
        setEditingPost(null);
        setIsModalOpen(true);
    };

    const openEditPostModal = (post: BlogPost) => {
        setEditingPost(post);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setEditingPost(null);
    }

    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">Content Assets</h2>
                <button onClick={openNewPostModal} className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 font-bold transition-all shadow-sm">
                    <PlusIcon className="w-5 h-5 mr-2" />
                    NEW POST
                </button>
            </div>
             <div className="overflow-x-auto -mx-6">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Title</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Author</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Date</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-card">
                        {posts.map(post => (
                            <tr key={post.id} className="hover:bg-muted/30 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap font-bold text-sm">{post.title}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">{post.authorName}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded border ${post.status === 'published' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-amber-50 text-amber-700 border-amber-200'}`}>{post.status}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-xs text-muted-foreground">{new Date(post.publishDate).toLocaleDateString()}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button onClick={() => openEditPostModal(post)} className="text-primary hover:text-primary/90 font-bold transition-colors">Edit</button>
                                    <button onClick={() => handleDeletePost(post.id)} className="text-destructive hover:text-destructive/90 font-bold ml-4 transition-colors">Delete</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {isModalOpen && <PostEditorModal post={editingPost} onClose={closeModal} onSubmit={handleSavePost} />}
        </div>
    );
};

const PostEditorModal: React.FC<{post: BlogPost | null, onClose: () => void, onSubmit: (data: any, postId?: string) => Promise<void>}> = ({ post, onClose, onSubmit }) => {
    const [title, setTitle] = useState(post?.title || '');
    const [excerpt, setExcerpt] = useState(post?.excerpt || '');
    const [content, setContent] = useState(post?.content || ''); 
    const [imageUrl, setImageUrl] = useState(post?.imageUrl || '');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({ title, excerpt, content, imageUrl }, post?.id);
    };
    const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-card rounded-2xl shadow-xl w-full max-w-2xl p-6 relative animate-in fade-in zoom-in-95 duration-200">
                <h2 className="text-2xl font-bold mb-4">{post ? 'Edit' : 'Create'} Blog Post</h2>
                <button onClick={onClose} className="absolute top-4 right-4 p-2 rounded-full hover:bg-muted transition-colors"><XIcon className="w-6 h-6" /></button>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input type="text" placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} className={inputClass} required/>
                    <textarea placeholder="Excerpt" value={excerpt} onChange={e => setExcerpt(e.target.value)} className={inputClass} rows={3} required></textarea>
                    <textarea placeholder="Main Content (Markdown)" value={content} onChange={e => setContent(e.target.value)} className={inputClass} rows={10} required></textarea>
                    <input type="url" placeholder="Image URL" value={imageUrl} onChange={e => setImageUrl(e.target.value)} className={inputClass} required/>
                    <div className="flex justify-end space-x-2 pt-4 border-t border-border mt-4">
                        <button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors">Cancel</button>
                        <button type="submit" className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 font-bold transition-all">
                            {post ? 'SAVE CHANGES' : 'CREATE ASSET'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// --- NEW COMPONENT: SYSTEM SETTINGS ---
const SystemSettings: React.FC = () => {
    const [settings, setSettings] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState<string | null>(null);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        setLoading(true);
        try {
            // Fetch crawler, config, diagnostics, and lead scoring settings
            const crawlerData = await api.getSystemSettings('crawler_rbac');
            const crawlerConfig = await api.getSystemSettings('crawler_config');
            const diagnosticsData = await api.getSystemSettings('diagnostics');
            const scoringData = await api.getSystemSettings('lead_scoring');
            setSettings([...crawlerData, ...crawlerConfig, ...diagnosticsData, ...scoringData]);
        } catch (err: any) {
            alert("Failed to load settings: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdate = async (key: string, newValue: string) => {
        setIsSaving(key);
        try {
            await api.updateSystemSetting(key, { value: newValue });
            setSettings(prev => prev.map(s => s.key === key ? { ...s, value: newValue } : s));
        } catch (err: any) {
            alert("Update failed: " + err.message);
        } finally {
            setIsSaving(null);
        }
    };

    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-primary" /></div>;

    const roles = ['SALES', 'MARKETING', 'MANAGER', 'ADMIN'];
    const logLevelSetting = settings.find(s => s.key === 'system.log_level');
    const scoringSettings = settings.filter(s => s.category === 'lead_scoring');
    const crawlerConfigSettings = settings.filter(s => s.category === 'crawler_config');

    return (
        <div className="space-y-6 pb-20">
            {/* NEW: Crawler Endpoint Configuration (GAP-024) */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-blue-500">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-blue-600">
                    <SearchIcon className="w-5 h-5" />
                    Crawler Endpoint Configuration (104.com.tw)
                </h3>
                <div className="space-y-4">
                    {crawlerConfigSettings.map(setting => (
                        <div key={setting.key} className="p-4 bg-muted/20 rounded-xl border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex-1">
                                <div className="font-bold text-xs uppercase tracking-widest text-blue-600/70">{setting.key.replace(/CRAWLER_104_/g, '').replace(/_/g, ' ')}</div>
                                <p className="text-[10px] text-muted-foreground mt-0.5">{setting.description}</p>
                            </div>
                            <div className="flex items-center gap-3 w-full md:w-2/3">
                                <input 
                                    type="text" 
                                    defaultValue={setting.value}
                                    onBlur={(e) => handleUpdate(setting.key, e.target.value)}
                                    className="flex-1 p-2 bg-background border border-border rounded-lg text-xs font-mono outline-none focus:ring-2 ring-blue-500/50 transition-all"
                                />
                                {isSaving === setting.key && <RefreshCwIcon className="animate-spin w-4 h-4 text-blue-600" />}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* NEW: Lead Scoring Weights (GAP-024 Optimization) */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-indigo-600">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h3 className="text-lg font-bold flex items-center gap-2 text-indigo-600">
                            <ShieldCheckIcon className="w-5 h-5" />
                            Lead Scoring Weights
                        </h3>
                        <p className="text-xs text-muted-foreground">Adjust Alice's Lead Enrichment scoring logic in real-time. Changes apply to the next enrichment loop.</p>
                    </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {scoringSettings.map(setting => (
                        <div key={setting.key} className="p-4 bg-muted/20 rounded-xl border border-border flex items-center justify-between gap-4 group hover:border-indigo-500/30 transition-all">
                            <div className="flex-1">
                                <div className="font-bold text-[10px] uppercase tracking-widest text-indigo-600/70">{setting.key.replace(/SCORING_/g, '').replace(/_/g, ' ')}</div>
                                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 leading-tight mt-1">{setting.description}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="relative">
                                    <input 
                                        type="number" 
                                        defaultValue={setting.value}
                                        onBlur={(e) => handleUpdate(setting.key, e.target.value)}
                                        className="w-16 p-2 bg-background border border-border rounded-lg text-sm font-bold text-center outline-none focus:ring-2 ring-indigo-500/50 transition-all"
                                    />
                                    {isSaving === setting.key && (
                                        <div className="absolute -top-1 -right-1">
                                            <RefreshCwIcon className="animate-spin w-3 h-3 text-indigo-600" />
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                    {scoringSettings.length === 0 && (
                        <div className="col-span-2 p-8 text-center border-2 border-dashed border-border rounded-xl text-muted-foreground italic text-sm">
                            No scoring rules found in database. Execute migration 038 to seed defaults.
                        </div>
                    )}
                </div>
            </div>

            {/* NEW: Diagnostics & Log Level Control */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-amber-500">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-amber-600">
                    <RefreshCwIcon className="w-5 h-5" />
                    Server Diagnostics
                </h3>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 bg-muted/20 rounded-xl border border-border">
                    <div className="flex-1">
                        <div className="font-bold text-sm">Backend Access Log Level</div>
                        <p className="text-xs text-muted-foreground">{logLevelSetting?.description || '控制 API 存取日誌的詳細程度'}</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <select 
                            value={logLevelSetting?.value || 'WARNING'}
                            onChange={(e) => handleUpdate('system.log_level', e.target.value)}
                            className="bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono outline-none focus:ring-2 ring-primary/50"
                        >
                            <option value="DEBUG">DEBUG (Detailed)</option>
                            <option value="INFO">INFO (Normal)</option>
                            <option value="WARNING">WARNING (Recommended)</option>
                            <option value="ERROR">ERROR (Critical Only)</option>
                        </select>
                        {isSaving === 'system.log_level' && <RefreshCwIcon className="animate-spin w-4 h-4 text-primary" />}
                    </div>
                </div>
            </div>

            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <RefreshCwIcon className="w-5 h-5 text-indigo-500" />
                    Crawler RBAC Limits
                </h3>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-border">
                        <thead>
                            <tr className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                                <th className="px-4 py-2 text-left">Role</th>
                                <th className="px-4 py-2 text-left">Max Depth</th>
                                <th className="px-4 py-2 text-left">Concurrency</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {roles.map(role => {
                                const depthKey = `CRAWL_MAX_DEPTH_${role}`;
                                const concurrentKey = `CRAWL_CONCURRENT_MAX_${role}`;
                                const depthSetting = settings.find(s => s.key === depthKey);
                                const concurrentSetting = settings.find(s => s.key === concurrentKey);

                                return (
                                    <tr key={role} className="text-sm">
                                        <td className="px-4 py-3 font-medium">{role}</td>
                                        <td className="px-4 py-3">
                                            <input 
                                                type="number" 
                                                defaultValue={depthSetting?.value || 0}
                                                onBlur={(e) => handleUpdate(depthKey, e.target.value)}
                                                className="w-20 p-1 bg-background border border-border rounded focus:ring-1 ring-primary outline-none"
                                            />
                                            {isSaving === depthKey && <RefreshCwIcon className="inline animate-spin w-3 h-3 ml-2 text-primary" />}
                                        </td>
                                        <td className="px-4 py-3">
                                            <input 
                                                type="number" 
                                                defaultValue={concurrentSetting?.value || 0}
                                                onBlur={(e) => handleUpdate(concurrentKey, e.target.value)}
                                                className="w-20 p-1 bg-background border border-border rounded focus:ring-1 ring-primary outline-none"
                                            />
                                            {isSaving === concurrentKey && <RefreshCwIcon className="inline animate-spin w-3 h-3 ml-2 text-primary" />}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <ShieldCheckIcon className="w-5 h-5 text-indigo-500" />
                    Global Whitelist Domains
                </h3>
                {settings.find(s => s.key === 'CRAWL_ALLOWED_DOMAINS_RESTRICTED') && (
                    <div className="space-y-2">
                        <textarea 
                            defaultValue={settings.find(s => s.key === 'CRAWL_ALLOWED_DOMAINS_RESTRICTED')?.value}
                            onBlur={(e) => handleUpdate('CRAWL_ALLOWED_DOMAINS_RESTRICTED', e.target.value)}
                            className="w-full p-3 bg-background border border-border rounded-xl font-mono text-xs focus:ring-2 ring-primary outline-none h-24"
                            placeholder="comma, separated, domains.com"
                        />
                        <p className="text-[10px] text-muted-foreground italic">Changes are saved automatically on blur. These domains apply to all non-admin users.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

// --- NEW COMPONENT: EXTRACTION MANAGER (GAP-018) ---
const ExtractionManager: React.FC = () => {
    const [schemas, setSchemas] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [analyzeUrl, setAnalyzeUrl] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [suggestions, setSuggestions] = useState<any>(null);
    const [newSchemaName, setNewSchemaName] = useState('');
    const [newDomainPattern, setNewDomainPattern] = useState('');

    useEffect(() => {
        fetchSchemas();
    }, []);

    const fetchSchemas = async () => {
        setLoading(true);
        try {
            const data = await api.getExtractionSchemas();
            setSchemas(data);
        } catch (err: any) {
            alert("Failed to load schemas: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAnalyze = async () => {
        if (!analyzeUrl) return;
        setIsAnalyzing(true);
        setSuggestions(null);
        try {
            const result = await api.analyzeExtractionUrl(analyzeUrl);
            setSuggestions(result);
            
            // Auto-fill some defaults based on URL
            const url = new URL(analyzeUrl);
            setNewDomainPattern(`${url.hostname}${url.pathname.split('/').slice(0, 3).join('/')}/*`);
        } catch (err: any) {
            alert("Analysis failed: " + err.message);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleSaveSchema = async () => {
        if (!newSchemaName || !newDomainPattern || !suggestions) return;
        
        try {
            await api.createExtractionSchema({
                name: newSchemaName,
                domain_pattern: newDomainPattern,
                schema_definition: suggestions,
                description: `Auto-generated for ${newDomainPattern}`
            });
            alert("Schema saved successfully!");
            fetchSchemas();
            setSuggestions(null);
            setAnalyzeUrl('');
        } catch (err: any) {
            alert("Save failed: " + err.message);
        }
    };

    const handleDeleteSchema = async (id: string) => {
        if (!window.confirm("Delete this extraction template?")) return;
        try {
            await api.deleteExtractionSchema(id);
            fetchSchemas();
        } catch (err: any) {
            alert("Delete failed: " + err.message);
        }
    };

    const handleRunNow = async (schemaId: string) => {
        const url = prompt("Enter target URL to extract data from:");
        if (!url) return;
        try {
            const res = await api.runExtraction(url, schemaId);
            alert(res.message);
        } catch (err: any) {
            alert("Execution failed: " + err.message);
        }
    };

    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-primary" /></div>;

    return (
        <div className="space-y-8">
            {/* New Schema / Analyze Tool */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <RefreshCwIcon className="w-5 h-5 text-indigo-500" />
                    New Extraction Discovery (Powered by DevBot)
                </h3>
                <p className="text-sm text-muted-foreground mb-4">Paste a sample URL to let DevBot discover its structure and suggest data fields.</p>
                <div className="flex gap-2 mb-6">
                    <input 
                        type="url" 
                        value={analyzeUrl}
                        onChange={(e) => setAnalyzeUrl(e.target.value)}
                        placeholder="https://www.104.com.tw/job/..."
                        className="flex-1 p-2 bg-background border border-border rounded-lg outline-none focus:ring-2 ring-primary/50 transition-all"
                    />
                    <button 
                        onClick={handleAnalyze}
                        disabled={isAnalyzing || !analyzeUrl}
                        className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 transition-all"
                    >
                        {isAnalyzing ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <ShieldCheckIcon className="w-4 h-4" />}
                        ANALYZE STRUCTURE
                    </button>
                </div>

                {suggestions && (
                    <div className="mt-6 p-4 bg-muted/30 rounded-xl border border-dashed border-border animate-in slide-in-from-top-2 duration-300">
                        <div className="flex justify-between items-start mb-4">
                            <h4 className="font-bold text-indigo-500">Suggested Fields Found</h4>
                            <div className="flex gap-2">
                                <input 
                                    placeholder="Template Name (e.g. 104 Job Detail)" 
                                    value={newSchemaName}
                                    onChange={(e) => setNewSchemaName(e.target.value)}
                                    className="p-1 text-sm bg-background border border-border rounded"
                                />
                                <input 
                                    placeholder="Domain Pattern" 
                                    value={newDomainPattern}
                                    onChange={(e) => setNewDomainPattern(e.target.value)}
                                    className="p-1 text-sm bg-background border border-border rounded w-48"
                                />
                                <button 
                                    onClick={handleSaveSchema}
                                    className="px-3 py-1 bg-green-600 text-white text-xs font-bold rounded hover:bg-green-700"
                                >
                                    SAVE TEMPLATE
                                </button>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {suggestions.fields?.map((field: any, idx: number) => (
                                <div key={idx} className="p-3 bg-card border border-border rounded-lg shadow-sm">
                                    <div className="flex justify-between">
                                        <span className="font-bold text-xs uppercase tracking-wider">{field.name}</span>
                                        <span className="text-[10px] bg-muted px-1 rounded">{field.type}</span>
                                    </div>
                                    <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">{field.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Existing Schemas List */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4">Saved Extraction Templates</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {schemas.map(s => (
                        <div key={s.id} className="p-4 border border-border rounded-xl bg-muted/10 hover:bg-muted/20 transition-all group relative">
                            <button 
                                onClick={() => handleDeleteSchema(s.id)}
                                className="absolute top-2 right-2 p-1 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-all"
                            >
                                <XIcon className="w-4 h-4" />
                            </button>
                            <div className="font-bold text-sm mb-1">{s.name}</div>
                            <code className="text-[10px] bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 px-1 rounded">{s.domain_pattern}</code>
                            <div className="mt-3 flex flex-wrap gap-1">
                                {s.schema_definition?.fields?.slice(0, 5).map((f: any, idx: number) => (
                                    <span key={idx} className="text-[9px] bg-background border border-border px-1.5 py-0.5 rounded-full">{f.name}</span>
                                ))}
                                {s.schema_definition?.fields?.length > 5 && <span className="text-[9px] text-muted-foreground italic">+{s.schema_definition.fields.length - 5} more</span>}
                            </div>
                            <div className="mt-4 pt-3 border-t border-border flex justify-end">
                                <button 
                                    onClick={() => handleRunNow(s.id)}
                                    className="text-[10px] font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                                >
                                    <RefreshCwIcon className="w-3 h-3" />
                                    RUN EXTRACTION NOW
                                </button>
                            </div>
                        </div>
                    ))}
                    {schemas.length === 0 && <div className="col-span-2 text-center py-12 text-muted-foreground italic">No templates defined yet. Use the tool above to discover and save your first extraction schema.</div>}
                </div>
            </div>
        </div>
    );
};

// End of AdminPage
export default AdminPage;