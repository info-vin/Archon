import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { BlogPost } from '../types';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { 
    PlusIcon, 
    PaletteIcon, 
    LayoutIcon, 
    TrendingUpIcon, 
    DownloadIcon,
    RefreshCwIcon,
    CheckCircleIcon,
    FileEditIcon,
    EyeIcon
} from '../components/Icons';

const BrandPage: React.FC = () => {
    const [posts, setPosts] = useState<BlogPost[]>([]);
    const [marketStats, setMarketStats] = useState<any>(null);
    const [logoSvg, setLogoSvg] = useState<string | null>(null);
    const [isGenerating, setIsLogoGenerating] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [postsData, stats] = await Promise.all([
                api.getBlogPosts(),
                api.getMarketStats()
            ]);
            setPosts(postsData);
            setMarketStats(stats);
        } catch (err) {
            console.error("Failed to load brand data:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateLogo = async () => {
        setIsLogoGenerating(true);
        try {
            const result = await api.generateLogo("eciton");
            setLogoSvg(result.svg_content);
        } catch (err) {
            alert("Failed to generate logo");
        } finally {
            setIsLogoGenerating(false);
        }
    };

    const [editingPost, setEditingPost] = useState<BlogPost | null>(null);
    const [isPostModalOpen, setIsPostModalOpen] = useState(false);

    const updatePostStatus = async (id: string, newStatus: any) => {
        try {
            await api.updateBlogPostStatus(id, newStatus);
            setPosts(prev => prev.map(p => p.id === id ? { ...p, status: newStatus } : p));
        } catch (err) {
            alert("Status update failed");
        }
    };

    const handleSavePost = async (postData: Omit<BlogPost, 'id' | 'authorName' | 'publishDate'>, postId?: string) => {
        try {
            if (postId) { // Editing existing post
                const updatedPost = await api.updateBlogPost(postId, postData);
                setPosts(prev => prev.map(p => p.id === postId ? updatedPost : p));
            } else { // Creating new post
                // For new posts, we can let the backend handle author/date or pass defaults
                 const newPostData = {
                    ...postData,
                    authorName: "Marketing Bot", // Or fetch current user name via API/Context if available
                    publishDate: new Date().toISOString(),
                };
                const newPost = await api.createBlogPost(newPostData);
                setPosts(prev => [newPost, ...prev]);
            }
            setIsPostModalOpen(false);
            setEditingPost(null);
            loadData(); // Refresh to be sure
        } catch(error: any) {
             alert(`Failed to save post: ${error.message}`);
        }
    };

    const handleDeletePost = async (postId: string) => {
        if (window.confirm('Are you sure you want to delete this post?')) {
            try {
                await api.deleteBlogPost(postId);
                setPosts(prev => prev.filter(p => p.id !== postId));
            } catch (error: any) {
                alert(`Failed to delete post: ${error.message}`);
            }
        }
    };

    const openNewPostModal = () => {
        setEditingPost(null);
        setIsPostModalOpen(true);
    };

    const openEditPostModal = (post: BlogPost) => {
        setEditingPost(post);
        setIsPostModalOpen(true);
    };

    const downloadLogo = () => {
        if (!logoSvg) return;
        const blob = new Blob([logoSvg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'logo-eciton.svg';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const KanbanColumn = ({ status, title, icon: Icon, colorClass }: any) => (
        <div className="flex-1 min-w-[300px] bg-gray-50/50 rounded-xl p-4 flex flex-col gap-4">
            <div className={`flex items-center justify-between border-b pb-2 ${colorClass}`}>
                <h3 className="font-bold flex items-center gap-2">
                    <Icon className="w-5 h-5" />
                    {title}
                </h3>
                <span className="bg-white px-2 py-0.5 rounded-full text-xs shadow-sm font-bold">
                    {posts.filter(p => p.status === status).length}
                </span>
            </div>
            <div className="space-y-3 overflow-y-auto max-h-[500px] pr-1">
                {posts.filter(p => p.status === status).map(post => (
                    <div key={post.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-all group">
                        <h4 className="font-semibold text-gray-800 line-clamp-2">{post.title}</h4>
                        <p className="text-xs text-gray-500 mt-2 italic">By {post.authorName}</p>
                        <div className="mt-4 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="flex gap-1">
                                {status !== 'draft' && (
                                    <button onClick={() => updatePostStatus(post.id, 'draft')} className="p-1 hover:bg-gray-100 rounded text-gray-400" title="Move to Draft">
                                        <FileEditIcon className="w-4 h-4" />
                                    </button>
                                )}
                                <button onClick={() => openEditPostModal(post)} className="p-1 hover:bg-gray-100 rounded text-blue-500" title="Edit Content">
                                    <FileEditIcon className="w-4 h-4" />
                                </button>
                                <button onClick={() => handleDeletePost(post.id)} className="p-1 hover:bg-red-50 rounded text-red-500" title="Delete">
                                    <TrendingUpIcon className="w-4 h-4 rotate-45" /> {/* Using generic icon as XCircle is not imported, can fix later */}
                                </button>
                                {status !== 'review' && (
                                    <button onClick={() => updatePostStatus(post.id, 'review')} className="p-1 hover:bg-amber-50 rounded text-amber-500" title="Move to Review">
                                        <EyeIcon className="w-4 h-4" />
                                    </button>
                                )}
                                {status !== 'published' && (
                                    <button onClick={() => updatePostStatus(post.id, 'published')} className="p-1 hover:bg-green-50 rounded text-green-600" title="Publish Now">
                                        <CheckCircleIcon className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                            <span className="text-[10px] uppercase font-bold text-gray-300">#{post.id.slice(0,4)}</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    return (
        <PermissionGuard permission="leads:view:marketing" fallback={<div className="p-12 text-center text-gray-500">Access Denied: Brand Hub is for Marketing roles only.</div>}>
            <div className="p-6 max-w-7xl mx-auto space-y-8">
                <header className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                            <PaletteIcon className="w-8 h-8 text-indigo-600" />
                            Brand Hub
                        </h1>
                        <p className="text-gray-500 mt-2">Manage brand identity, content planning, and market trends.</p>
                    </div>
                    <button onClick={loadData} className="p-2 hover:bg-gray-100 rounded-full transition-colors" title="Refresh data">
                        <RefreshCwIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Brand Identity Section */}
                    <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100 space-y-6">
                        <div className="flex justify-between items-center">
                            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                                <LayoutIcon className="w-5 h-5 text-indigo-500" />
                                Visual Identity
                            </h2>
                            <button 
                                onClick={handleGenerateLogo}
                                disabled={isGenerating}
                                className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-indigo-700 disabled:opacity-50 transition-all flex items-center gap-2 shadow-lg shadow-indigo-200"
                            >
                                {isGenerating ? <RefreshCwIcon className="w-4 h-4 animate-spin" /> : <RefreshCwIcon className="w-4 h-4" />}
                                Generate with DevBot
                            </button>
                        </div>

                        <div className="h-64 bg-slate-900 rounded-xl flex items-center justify-center relative overflow-hidden group border-4 border-slate-800">
                            {logoSvg ? (
                                <div className="w-48 h-48 drop-shadow-[0_0_15px_rgba(0,242,255,0.5)]" dangerouslySetInnerHTML={{ __html: logoSvg }} />
                            ) : (
                                <div className="text-slate-500 flex flex-col items-center gap-2">
                                    <PaletteIcon className="w-12 h-12 opacity-20" />
                                    <p className="text-sm">Click generate to preview living brand assets</p>
                                </div>
                            )}
                            
                            {logoSvg && (
                                <button 
                                    onClick={downloadLogo}
                                    className="absolute bottom-4 right-4 bg-white/10 backdrop-blur-md text-white p-2 rounded-lg hover:bg-white/20 transition-all opacity-0 group-hover:opacity-100"
                                    title="Download SVG"
                                >
                                    <DownloadIcon className="w-5 h-5" />
                                </button>
                            )}
                        </div>
                        <p className="text-xs text-gray-400 italic text-center">
                            Powered by **Project ECITON** Engine. Dynamic SVG generation based on collective intelligence math.
                        </p>
                    </div>

                    {/* Market Insight Section */}
                    <div className="bg-indigo-900 text-white p-6 rounded-2xl shadow-xl space-y-6 relative overflow-hidden">
                        <div className="relative z-10">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                <TrendingUpIcon className="w-5 h-5 text-indigo-300" />
                                Market Specs
                            </h2>
                            <p className="text-indigo-200 text-xs mt-1">AI-driven market trend analysis</p>
                            
                            {marketStats ? (
                                <div className="mt-8 space-y-6">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-white/10 p-4 rounded-xl border border-white/5">
                                            <p className="text-[10px] uppercase font-bold text-indigo-300">AI Trends</p>
                                            <p className="text-2xl font-mono font-bold mt-1">{Math.round((marketStats["AI/LLM"] / marketStats["Total Leads"]) * 100)}%</p>
                                        </div>
                                        <div className="bg-white/10 p-4 rounded-xl border border-white/5">
                                            <p className="text-[10px] uppercase font-bold text-indigo-300">Growth</p>
                                            <p className="text-2xl font-mono font-bold mt-1">+{marketStats["Total Leads"]}</p>
                                        </div>
                                    </div>
                                    
                                    <div className="space-y-4">
                                        <div className="bg-white/5 p-3 rounded-lg flex justify-between items-center">
                                            <span className="text-sm">LLM/Agent Frame</span>
                                            <span className="text-indigo-400 font-mono font-bold">{marketStats["AI/LLM"]}</span>
                                        </div>
                                        <div className="bg-white/5 p-3 rounded-lg flex justify-between items-center">
                                            <span className="text-sm">Data Analytics</span>
                                            <span className="text-indigo-400 font-mono font-bold">{marketStats["Data/BI"]}</span>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="animate-pulse space-y-4 mt-8">
                                    <div className="h-20 bg-white/5 rounded-xl"></div>
                                    <div className="h-32 bg-white/5 rounded-xl"></div>
                                </div>
                            )}
                        </div>
                        {/* Decorative circle */}
                        <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-indigo-500 rounded-full blur-3xl opacity-20"></div>
                    </div>
                </div>

                {/* Blog Content Kanban */}
                <section className="space-y-4">
                    <div className="flex justify-between items-end">
                        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                            <PlusIcon className="w-5 h-5 text-indigo-500" />
                            Content Pipeline
                        </h2>
                        <div className="flex gap-3 items-center">
                            <span className="text-xs text-gray-400">Drag-and-drop coming soon</span>
                            <button 
                                onClick={() => {
                                    openNewPostModal();
                                }}
                                className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-indigo-700 flex items-center gap-2 shadow-sm transition-transform active:scale-95"
                            >
                                <PlusIcon className="w-4 h-4" />
                                New Post
                            </button>
                        </div>
                    </div>
                    
                    <div className="flex flex-col md:flex-row gap-6 overflow-x-auto pb-4">
                        <KanbanColumn status="draft" title="Ideas & Drafts" icon={FileEditIcon} colorClass="text-gray-600 border-gray-200" />
                        <KanbanColumn status="review" title="In Review" icon={EyeIcon} colorClass="text-amber-600 border-amber-200" />
                        <KanbanColumn status="published" title="Published" icon={CheckCircleIcon} colorClass="text-green-600 border-green-200" />
                    </div>
                </section>
            </div>

            {/* Create/Edit Post Modal - Reusing the same modal structure but controlled by state */}
            {isPostModalOpen && (
                <dialog open className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm w-full h-full">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-6 relative animate-in fade-in zoom-in-95 duration-200 border border-gray-100">
                        <div className="flex justify-between items-center mb-6 border-b pb-4">
                            <h3 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                                <PaletteIcon className="w-6 h-6 text-indigo-600" />
                                {editingPost ? 'Edit Brand Asset' : 'New Content Asset'}
                            </h3>
                            <button onClick={() => setIsPostModalOpen(false)} className="text-gray-400 hover:text-gray-600 p-2 hover:bg-gray-100 rounded-full transition-colors">
                                ✕
                            </button>
                        </div>
                        
                        <CreatePostForm 
                            post={editingPost} 
                            onSuccess={() => setIsPostModalOpen(false)} 
                            onSubmit={handleSavePost}
                        />
                    </div>
                </dialog>
            )}
        </PermissionGuard>
    );
};

const CreatePostForm: React.FC<{ post?: BlogPost | null, onSuccess: () => void, onSubmit: (data: any, id?: string) => Promise<void> }> = ({ post, onSuccess, onSubmit }) => {
    const [title, setTitle] = useState(post?.title || '');
    const [content, setContent] = useState(post?.content || '');
    const [imageUrl, setImageUrl] = useState(post?.imageUrl || '');
    const [excerpt, setExcerpt] = useState(post?.excerpt || '');
    
    const [loading, setLoading] = useState(false);
    const [isDrafting, setIsDrafting] = useState(false);
    
    const handleDraft = async () => {
        if (!title) {
            alert("Please enter a title or topic first.");
            return;
        }
        setIsDrafting(true);
        try {
            const result = await api.draftBlogPost({
                topic: title, 
                tone: 'professional'
            });
            setTitle(result.title);
            setContent(result.content);
            setExcerpt(result.excerpt);
        } catch (err: any) {
            alert(err.message || "Failed to generate draft");
        } finally {
            setIsDrafting(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await onSubmit({
                title,
                content,
                excerpt: excerpt || content.slice(0, 100) + '...',
                imageUrl: imageUrl || '/placeholder-blog.jpg',
                status: post?.status || 'draft'
            }, post?.id);
            onSuccess(); // Ensure modal closes
        } catch (err) {
            // Error handling is done in parent
        } finally {
            setLoading(false);
        }
    };

    const inputClass = "w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none text-gray-900 shadow-sm transition-all";

    return (
        <form onSubmit={handleSubmit} className="space-y-5">
            <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Title / Topic</label>
                <div className="flex gap-2">
                    <input 
                        type="text" 
                        required
                        value={title} 
                        onChange={e => setTitle(e.target.value)} 
                        className={inputClass}
                        placeholder="e.g. 5 Ways AI Transforms Manufacturing" 
                    />
                    <button 
                        type="button"
                        onClick={handleDraft}
                        disabled={isDrafting}
                        className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-lg text-sm font-bold flex items-center gap-2 disabled:opacity-50 transition-all hover:scale-105 active:scale-95"
                        title="Generate draft with AI"
                    >
                        {isDrafting ? <RefreshCwIcon className="w-4 h-4 animate-spin" /> : <TrendingUpIcon className="w-4 h-4" />}
                        Magic Draft
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Cover Image URL</label>
                    <input 
                        type="url" 
                        value={imageUrl} 
                        onChange={e => setImageUrl(e.target.value)} 
                        className={inputClass}
                        placeholder="https://..." 
                    />
                </div>
                 <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Excerpt (SEO)</label>
                    <input 
                        type="text" 
                        value={excerpt} 
                        onChange={e => setExcerpt(e.target.value)} 
                        className={inputClass}
                        placeholder="Short summary..." 
                    />
                </div>
            </div>

            <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Content (Markdown Supported)</label>
                <textarea 
                    required
                    value={content} 
                    onChange={e => setContent(e.target.value)} 
                    className={`${inputClass} min-h-[300px] font-mono text-sm leading-relaxed`}
                    placeholder="Write your content here or use Magic Draft..."
                />
            </div>

            <div className="flex justify-end pt-4 border-t border-gray-100">
                <button 
                    type="submit" 
                    disabled={loading || isDrafting}
                    className="px-8 py-3 bg-gray-900 text-white font-bold rounded-xl hover:bg-black disabled:opacity-50 flex items-center gap-2 shadow-xl hover:shadow-2xl transition-all"
                >
                    {loading ? <RefreshCwIcon className="w-5 h-5 animate-spin" /> : <CheckCircleIcon className="w-5 h-5" />}
                    {post ? 'SAVE CHANGES' : 'CREATE ASSET'}
                </button>
            </div>
        </form>
    );
};

export default BrandPage;
