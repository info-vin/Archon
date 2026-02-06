import React, { useState, useEffect } from 'react';
import { api } from '../services/api.ts';
import { DocumentVersion, BlogPost } from '../types.ts';
import { CheckCircleIcon, PlusIcon, XIcon, RefreshCwIcon, SaveIcon, KeyIcon } from '../components/Icons.tsx';
import { useAuth } from '../hooks/useAuth.tsx';

import { IdentityMatrix } from '../features/admin/components/IdentityMatrix.tsx';
import { SystemHealthDashboard } from '../features/admin/components/SystemHealthDashboard.tsx';


const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('health'); // Default to System Health for Admin Persona

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 bg-background text-foreground">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">Admin Control Center</h1>
        <p className="text-muted-foreground">System-wide configuration and personnel management for L1 Administrators.</p>
      </header>

      <div className="border-b border-border mb-6">
        <nav className="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
          <TabButton title="System Health" isActive={activeTab === 'health'} onClick={() => setActiveTab('health')} />
          <TabButton title="User Management" isActive={activeTab === 'users'} onClick={() => setActiveTab('users')} />
          <TabButton title="System Prompts" isActive={activeTab === 'prompts'} onClick={() => setActiveTab('prompts')} />
          <TabButton title="Blog Management" isActive={activeTab === 'blog'} onClick={() => setActiveTab('blog')} />
          <TabButton title="Document Versions" isActive={activeTab === 'versions'} onClick={() => setActiveTab('versions')} />
        </nav>
      </div>

      <div className="flex-1 overflow-auto">
        {activeTab === 'health' && <SystemHealthDashboard />}
        {activeTab === 'users' && <IdentityMatrix />}
        {activeTab === 'prompts' && <PromptManagement />}
        {activeTab === 'blog' && <BlogManagement />}
        {activeTab === 'versions' && <DocumentVersionsLog />}
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
const PromptManagement: React.FC = () => {
    const [prompts, setPrompts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedPrompt, setSelectedEmployee] = useState<any>(null);
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
                setSelectedEmployee(data[0]);
                setEditValue(data[0].prompt);
            }
        } catch (err: any) {
            alert("Failed to load prompts: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = (p: any) => {
        setSelectedEmployee(p);
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
                             {/* Green Checkmark for "System Health" */}
                             <CheckCircleIcon className="w-4 h-4 text-green-500" />
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
                                <h3 className="font-bold text-lg">{selectedPrompt.prompt_name.replace(/_/g, ' ').toUpperCase()}</h3>
                                <p className="text-xs text-muted-foreground">Last updated: {new Date(selectedPrompt.updated_at).toLocaleString()}</p>
                            </div>
                            <button 
                                onClick={handleSave}
                                disabled={isSaving || editValue === selectedPrompt.prompt}
                                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-bold text-sm hover:bg-primary/90 disabled:opacity-50 disabled:grayscale transition-all"
                            >
                                {isSaving ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <SaveIcon className="w-4 h-4" />}
                                SAVE CHANGES
                            </button>
                        </div>
                        <div className="flex-1 p-4 flex flex-col space-y-4">
                            <div className="flex-1 relative">
                                <textarea 
                                    value={editValue}
                                    onChange={(e) => setEditValue(e.target.value)}
                                    className="w-full h-full p-4 bg-background border border-border rounded-xl font-mono text-sm focus:ring-2 focus:ring-primary outline-none resize-none leading-relaxed shadow-inner"
                                    placeholder="Enter system prompt here..."
                                />
                                <div className="absolute bottom-4 right-4 text-[10px] text-muted-foreground font-mono bg-background/80 px-2 py-1 rounded border border-border">
                                    {editValue.length} characters
                                </div>
                            </div>
                            <div className="bg-amber-50 dark:bg-amber-950/20 p-3 rounded-lg border border-amber-100 dark:border-amber-900/30 flex gap-3">
                                <KeyIcon className="w-5 h-5 text-amber-600 shrink-0" />
                                <div className="text-xs text-amber-800 dark:text-amber-400">
                                    <strong>Caution:</strong> Changes to system prompts directly affect AI behavior. The internal memory cache will be automatically reloaded upon saving.
                                </div>
                            </div>
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
    useEffect(() => {
        api.getDocumentVersions().then(setVersions).catch(err => alert(`Failed to load document versions: ${err.message}`));
    }, []);
    
    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
            <h2 className="text-xl font-bold mb-6">Document Version Audit Trail</h2>
             <div className="overflow-x-auto -mx-6">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Timestamp</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Changed By</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Type</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Field</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Summary</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-card">
                        {versions.map(log => (
                            <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap text-xs text-muted-foreground font-mono">{new Date(log.created_at).toLocaleString()}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{log.created_by}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-muted rounded border border-border">{log.change_type}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">{log.field_name} <span className="text-xs text-muted-foreground">v{log.version_number}</span></td>
                                <td className="px-6 py-4 text-xs text-muted-foreground italic max-w-xs truncate">{log.change_summary || 'N/A'}</td>
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

// End of AdminPage
export default AdminPage;