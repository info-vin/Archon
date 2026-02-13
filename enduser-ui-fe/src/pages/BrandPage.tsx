import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { BlogPost, EmployeeRole, TaskStatus } from '../types';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { TrendLineChart } from '../features/marketing/components/TrendLineChart';
import { SankeyDiagram } from '../features/marketing/components/SankeyDiagram';
import { VictoryFeedList, ContentSource } from '../features/marketing/components/VictoryFeedList';
import { ContentWorkbench } from '../features/marketing/components/ContentWorkbench';
import { useAuth } from '../hooks/useAuth';
import { 
    PlusIcon, 
    PaletteIcon, 
    LayoutIcon, 
    TrendingUpIcon, 
    DownloadIcon,
    RefreshCwIcon,
    CheckCircleIcon,
    FileEditIcon,
    EyeIcon,
    SparklesIcon
} from '../components/Icons';

const BrandPage: React.FC = () => {
    const { user } = useAuth();
    const [viewMode, setViewMode] = useState<'dashboard' | 'workbench'>('workbench');
    
    // Dashboard State
    const [posts, setPosts] = useState<BlogPost[]>([]);
    const [trendsData, setTrendsData] = useState<any>(null);
    const [logoSvg, setLogoSvg] = useState<string | null>(null);
    const [isGenerating, setIsLogoGenerating] = useState(false);
    const [loading, setLoading] = useState(true);

    // Workbench State
    const [sources, setSources] = useState<ContentSource[]>([]);
    const [activeSource, setActiveSource] = useState<ContentSource | null>(null);
    const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
    const [contextData, setContextData] = useState<any>(null);
    const [isLoadingSources, setIsLoadingSources] = useState(false);
    const [isLoadingContext, setIsLoadingContext] = useState(false);
    const [isDrafting, setIsDrafting] = useState(false);
    const [isGeneratingImage, setIsGeneratingImage] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    
    // Workbench Editor State (Lifted Up)
    const [workbenchTitle, setWorkbenchTitle] = useState('');
    const [workbenchContent, setWorkbenchContent] = useState('');
    const [workbenchImageUrl, setWorkbenchImageUrl] = useState('/placeholder-blog.jpg');
    const [lastPrompt, setLastPrompt] = useState<string | undefined>(undefined);

    // Persistence Logic (Restored from Child)
    useEffect(() => {
        if (activeSource?.id) {
            const savedTitle = localStorage.getItem(`draft_title_${activeSource.id}`);
            const savedContent = localStorage.getItem(`draft_content_${activeSource.id}`);
            const savedImage = localStorage.getItem(`draft_image_${activeSource.id}`);
            
            if (savedTitle) setWorkbenchTitle(savedTitle);
            else setWorkbenchTitle(''); 

            if (savedContent) setWorkbenchContent(savedContent);
            else setWorkbenchContent(''); 

            if (savedImage) setWorkbenchImageUrl(savedImage);
            else setWorkbenchImageUrl('/placeholder-blog.jpg');
        }
    }, [activeSource?.id]);

    useEffect(() => {
        if (activeSource?.id) {
            localStorage.setItem(`draft_title_${activeSource.id}`, workbenchTitle);
            localStorage.setItem(`draft_content_${activeSource.id}`, workbenchContent);
            localStorage.setItem(`draft_image_${activeSource.id}`, workbenchImageUrl);
        }
    }, [workbenchTitle, workbenchContent, workbenchImageUrl, activeSource?.id]);

    useEffect(() => {
        loadData();
        if (viewMode === 'workbench') {
            loadWorkbenchData();
        }
    }, [viewMode]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [postsData, trends] = await Promise.all([
                api.getBlogPosts(),
                api.getMarketingTrends().catch(err => {
                    console.error("Trends fetch failed, using fallback empty state", err);
                    return null;
                })
            ]);
            setPosts(postsData);
            setTrendsData(trends);
        } catch (err) {
            console.error("Failed to load brand data:", err);
        } finally {
            setLoading(false);
        }
    };

    const loadWorkbenchData = async () => {
        setIsLoadingSources(true);
        try {
            const sourcesData = await api.getContentSources();
            setSources(sourcesData);
        } catch (err) {
            console.error("Failed to load content sources:", err);
        } finally {
            setIsLoadingSources(false);
        }
    };

    const handleSelectSource = async (source: ContentSource) => {
        // Fix: Map API alias back to expected UI key for feedback visibility
        const sourceData = { ...source };
        if ((sourceData as any).reviewNotes && !(sourceData as any).review_notes) {
            (sourceData as any).review_notes = (sourceData as any).reviewNotes;
        }
        setActiveSource(sourceData);

        // Identify associated Task ID from metadata variants
        const taskId = (sourceData as any).metadata?.task_id || 
                       (sourceData as any).task_id || 
                       (sourceData as any).metadata?.taskId;
        setActiveTaskId(taskId || null);
        
        setIsLoadingContext(true);
        try {
            const context = await api.getContentContext(source.id, source.type);
            setContextData(context);
        } catch (err) {
            console.error("Failed to load context:", err);
        } finally {
            setIsLoadingContext(false);
        }
    };

    const handleMagicDraft = async (topic: string, config?: any) => {
        if (!activeSource) return;
        setIsDrafting(true);
        try {
            const result = await api.draftBlogPost({
                topic: topic,
                context_source_id: activeSource.id,
                context_type: activeSource.type,
                tone: 'professional',
                ...config
            });
            console.log("Magic Draft Result:", result);
            
            // FIX: Update Workbench State with Result
            setWorkbenchTitle(result.title);
            setWorkbenchContent(result.content);
            setLastPrompt(result.used_prompt);
            
            alert("Draft generated! Content has been updated in the Editor.");
        } catch (err: any) {
            alert(err.message || "Drafting failed");
        } finally {
            setIsDrafting(false);
        }
    };

    const cleanAIImageReference = (content: string, imageUrl: string) => {
        if (!imageUrl || imageUrl === '/placeholder-blog.jpg') return content;
        const escapedUrl = imageUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        // Match ![...](url) and surrounding minimal whitespace
        const regex = new RegExp(`\\s*!\\[.*?\\]\\(${escapedUrl}\\)\\s*`, 'g');
        return content.replace(regex, '\n\n').trim(); // Replace with standard spacing or empty
    };

    const handleSaveWorkbench = async () => {
        try {
            const finalContent = cleanAIImageReference(workbenchContent, workbenchImageUrl);

            // Persist to DB so it shows up in Kanban "Ideas & Drafts"
            await api.createBlogPost({
                title: workbenchTitle || "Untitled Draft",
                content: finalContent || "",
                excerpt: finalContent.slice(0, 100) + "...",
                imageUrl: workbenchImageUrl,
                status: 'draft',
                authorName: user?.name || "Bob",
                publishDate: new Date().toISOString()
            });

            // GAP-023: Sync Task Status to 'doing'
            if (activeTaskId) {
                await api.updateTask(activeTaskId, { status: TaskStatus.DOING });
            }

            alert("Draft saved to workspace!");
            setViewMode('dashboard');
            loadData(); // Refresh dashboard data
        } catch (err: any) {
            alert(`Failed to save draft: ${err.message}`);
        }
    };

    const handleGenerateImage = async (title: string) => {
        setIsGeneratingImage(true);
        try {
            const result = await api.nanaBananaProxy({ prompt: title });
            
            // FIX: Update Cover Image AND Append to Content
            setWorkbenchImageUrl(result.image_url);
            
            const imageMarkdown = `\n\n![Header Image](${result.image_url})\n\n`;
            setWorkbenchContent(prev => imageMarkdown + prev); 
            
            alert(`Asset generated and synced as cover image.`);
        } catch (err: any) {
            alert(err.message || "Image generation failed");
        } finally {
            setIsGeneratingImage(false);
        }
    };

    const handlePublishWorkbench = async (postData: { title: string, content: string }) => {
        const isManager = user?.role === EmployeeRole.MANAGER || user?.role === EmployeeRole.ADMIN;
        
        try {
            const finalContent = cleanAIImageReference(postData.content, workbenchImageUrl);

            // 1. Always Create/Update Draft First
            const draft = await api.createBlogPost({
                title: postData.title,
                content: finalContent,
                excerpt: finalContent.slice(0, 150) + '...',
                imageUrl: workbenchImageUrl,
                status: 'draft',
                authorName: user?.name || 'Unknown Author',
                publishDate: new Date().toISOString()
            });

            // 2. If Manager, Publish Directly. If Member, Submit for Review (AI Check)
            if (isManager) {
                await api.updateBlogPostStatus(draft.id, 'published');
                alert("Article published successfully!");
            } else {
                const result = await api.submitBlogPost(draft.id);
                if (result.status === 'changes_requested') {
                    alert(`Submission Returned by AI Reviewer:\n${result.review_notes || 'Quality check failed.'}`);
                } else {
                    // GAP-023: Sync Task Status to 'review'
                    if (activeTaskId) {
                        await api.updateTask(activeTaskId, { status: TaskStatus.REVIEW });
                    }
                    alert("Article submitted for review! (AI Check Passed)");
                }
            }
            loadData();
        } catch (err: any) {
            alert(`Operation failed: ${err.message}`);
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
            if (postId) {
                const updatedPost = await api.updateBlogPost(postId, postData);
                setPosts(prev => prev.map(p => p.id === postId ? updatedPost : p));
            } else {
                 const newPostData = {
                    ...postData,
                    authorName: user?.name || "Marketing Bot",
                    publishDate: new Date().toISOString(),
                };
                const newPost = await api.createBlogPost(newPostData);
                setPosts(prev => [newPost, ...prev]);
            }
            setIsPostModalOpen(false);
            setEditingPost(null);
            loadData();
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

    // UX-014: Smart Edit - Switch to Workbench for Drafts
    const handleEditSmart = (post: BlogPost) => {
        if (post.status === 'draft' || post.status === 'changes_requested') {
            setWorkbenchTitle(post.title || '');
            setWorkbenchContent(post.content || '');
            
            // Resolve source context association
            setActiveSource({ 
                id: post.id, 
                type: 'lead', 
                title: post.title || 'Untitled Draft',
                score: 100, 
                summary: post.excerpt || '', 
                date: post.publishDate || new Date().toISOString(),
                // Handle both snake_case and camelCase from API aliases
                review_notes: (post as any).reviewNotes || (post as any).review_notes 
            } as any);
            
            // Link Task ID for status sync
            const associatedTaskId = (post as any).generationMetadata?.task_id || (post as any).generation_metadata?.task_id || (post as any).task_id;
            setActiveTaskId(associatedTaskId || null);

            setViewMode('workbench');
        } else {
            openEditPostModal(post);
        }
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

    const KanbanColumn = ({ filter, title, icon: Icon, colorClass }: any) => {
        const columnPosts = posts.filter(filter);
        return (
        <div className="flex-1 min-w-[300px] bg-gray-50/50 rounded-xl p-4 flex flex-col gap-4">
            <div className={`flex items-center justify-between border-b pb-2 ${colorClass}`}>
                <h3 className="font-bold flex items-center gap-2">
                    <Icon className="w-5 h-5" />
                    {title}
                </h3>
                <span className="bg-white px-2 py-0.5 rounded-full text-xs shadow-sm font-bold">
                    {columnPosts.length}
                </span>
            </div>
            <div className="space-y-3 overflow-y-auto max-h-[500px] pr-1">
                {columnPosts.map(post => (
                    <div key={post.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-all group relative overflow-hidden">
                        {post.status === 'changes_requested' && (
                            <div className="absolute top-0 right-0 bg-red-100 text-red-600 text-[10px] font-bold px-2 py-1 rounded-bl-lg">
                                RETURNED
                            </div>
                        )}
                        <h4 className="font-semibold text-gray-800 line-clamp-2">{post.title}</h4>
                        {post.status === 'changes_requested' && (post as any).review_notes && (
                            <p className="mt-2 text-[10px] bg-red-50 text-red-700 p-2 rounded-lg border border-red-100 italic line-clamp-2">
                                💬 {(post as any).review_notes}
                            </p>
                        )}
                        <p className="text-xs text-gray-500 mt-2 italic">By {post.authorName}</p>
                        <div className="mt-4 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="flex gap-1">
                                {post.status !== 'draft' && post.status !== 'changes_requested' && (
                                    <button onClick={() => updatePostStatus(post.id, 'draft')} className="p-1 hover:bg-gray-100 rounded text-gray-400" title="Move to Draft">
                                        <FileEditIcon className="w-4 h-4" />
                                    </button>
                                )}
                                <button onClick={() => handleEditSmart(post)} className="p-1 hover:bg-gray-100 rounded text-blue-500" title="Edit Content">
                                    <FileEditIcon className="w-4 h-4" />
                                </button>
                                <button onClick={() => handleDeletePost(post.id)} className="p-1 hover:bg-red-50 rounded text-red-500" title="Delete">
                                    <TrendingUpIcon className="w-4 h-4 rotate-45" />
                                </button>
                                {post.status !== 'review' && (
                                    <button onClick={() => updatePostStatus(post.id, 'review')} className="p-1 hover:bg-amber-50 rounded text-amber-500" title="Move to Review">
                                        <EyeIcon className="w-4 h-4" />
                                    </button>
                                )}
                                {post.status !== 'published' && (
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
    )};

    return (
        <PermissionGuard permission="leads:view:marketing" fallback={<div className="p-12 text-center text-gray-500">Access Denied: Brand Hub is for Marketing roles only.</div>}>
            <div className="flex flex-col h-full">
                <header className="px-6 py-4 flex justify-between items-center bg-white dark:bg-slate-900 border-b shrink-0 font-sans">
                    <div className="flex items-center gap-4">
                        <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-3">
                            <PaletteIcon className="w-6 h-6 text-indigo-600" />
                            Brand Hub
                        </h1>
                        
                        <nav className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                            <button
                                onClick={() => setViewMode('dashboard')}
                                className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${
                                    viewMode === 'dashboard' ? 'bg-white dark:bg-slate-700 shadow-sm text-indigo-600' : 'text-slate-500'
                                }`}
                            >
                                <LayoutIcon className="w-3.5 h-3.5 inline mr-2" />
                                Insights
                            </button>
                            <button
                                onClick={() => setViewMode('workbench')}
                                className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${
                                    viewMode === 'workbench' ? 'bg-white dark:bg-slate-700 shadow-sm text-indigo-600' : 'text-slate-500'
                                }`}
                            >
                                <SparklesIcon className="w-3.5 h-3.5 inline mr-2" />
                                Workbench
                            </button>
                        </nav>
                    </div>
                    
                    <div className="flex items-center gap-3">
                        <button onClick={loadData} className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full transition-colors">
                            <RefreshCwIcon className={`w-5 h-5 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </header>

                <main className={`flex-1 ${viewMode === 'workbench' ? 'overflow-hidden' : 'overflow-auto'}`}>
                    {viewMode === 'dashboard' ? (
                        <div className="p-6 max-w-7xl mx-auto space-y-8 font-sans">
                            {/* ... Dashboard Content (stays same) ... */}
                            <div className="bg-purple-50 text-gray-900 p-6 rounded-2xl shadow-xl space-y-6 relative overflow-hidden w-full border border-purple-100">
                                <div className="relative z-10">
                                    <h2 className="text-xl font-bold flex items-center gap-2 text-purple-900">
                                        <TrendingUpIcon className="w-5 h-5 text-purple-600" />
                                        Market Intelligence 2.0
                                    </h2>
                                    <p className="text-purple-700 text-xs mt-1">Real-time keyword trends & demand flow</p>

                                    {trendsData ? (
                                        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                                            <div className="bg-white p-4 rounded-xl border border-purple-100 shadow-sm">
                                                <h3 className="text-sm font-bold text-purple-800 mb-4 uppercase tracking-wider">Rising Topics (Monthly)</h3>
                                                <div className="-ml-4">
                                                    <TrendLineChart data={trendsData.keyword_growth} />
                                                </div>
                                            </div>
                                            <div className="bg-white p-4 rounded-xl border border-purple-100 shadow-sm">
                                                <h3 className="text-sm font-bold text-purple-800 mb-4 uppercase tracking-wider">Demand Flow</h3>
                                                <SankeyDiagram data={trendsData.sankey_flow} />
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="animate-pulse grid grid-cols-2 gap-8 mt-8">
                                            <div className="h-40 bg-purple-100 rounded-xl"></div>
                                            <div className="h-40 bg-purple-100 rounded-xl"></div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Blog Content Kanban (Middle) */}
                            <section className="space-y-4">
                                <div className="flex justify-between items-end">
                                    <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                                        <PlusIcon className="w-5 h-5 text-indigo-500" />
                                        Content Pipeline
                                    </h2>
                                    <button onClick={openNewPostModal} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-indigo-700 flex items-center gap-2">
                                        <PlusIcon className="w-4 h-4" /> New Post
                                    </button>
                                </div>
                                <div className="flex flex-col md:flex-row gap-6 overflow-x-auto pb-4">
                                    <KanbanColumn 
                                        filter={(p: BlogPost) => p.status === 'draft' || p.status === 'changes_requested'} 
                                        title="Ideas, Drafts & Returns" 
                                        icon={FileEditIcon} 
                                        colorClass="text-gray-600 border-gray-200" 
                                    />
                                    <KanbanColumn 
                                        filter={(p: BlogPost) => p.status === 'review'} 
                                        title="In Review" 
                                        icon={EyeIcon} 
                                        colorClass="text-amber-600 border-amber-200" 
                                    />
                                    <KanbanColumn 
                                        filter={(p: BlogPost) => p.status === 'published'} 
                                        title="Published" 
                                        icon={CheckCircleIcon} 
                                        colorClass="text-green-600 border-green-200" 
                                    />
                                </div>
                            </section>

                            {/* Brand Identity Section (Moved Bottom for UX-010) */}
                            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 space-y-6">
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
                        </div>
                    ) : (
                        <div className="flex h-full relative">
                            {/* Collapsible Inbox Sidebar */}
                            <div 
                                className={`border-r bg-white dark:bg-slate-900 transition-all duration-300 ease-in-out overflow-hidden flex flex-col ${
                                    isSidebarOpen ? 'w-80 opacity-100 translate-x-0' : 'w-0 opacity-0 -translate-x-full border-r-0'
                                }`}
                            >
                                <VictoryFeedList 
                                    sources={sources}
                                    activeId={activeSource?.id}
                                    onSelect={handleSelectSource}
                                    isLoading={isLoadingSources}
                                />
                            </div>

                            {/* Floating Sidebar Toggle */}
                            <button
                                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                                className={`absolute bottom-10 z-40 p-2 bg-white dark:bg-slate-800 border dark:border-slate-700 rounded-r-lg shadow-md transition-all duration-300 hover:w-8 group ${
                                    isSidebarOpen ? 'left-80' : 'left-0'
                                }`}
                                title={isSidebarOpen ? "Collapse Feed" : "Expand Feed"}
                            >
                                <div className={`w-1 h-4 bg-slate-300 dark:bg-slate-600 rounded-full group-hover:bg-indigo-500 transition-colors ${!isSidebarOpen && 'bg-indigo-400'}`} />
                            </button>

                            <div className="flex-1 h-full min-w-0">
                                <ContentWorkbench 
                                    activeSource={activeSource}
                                    contextData={contextData}
                                    isLoadingContext={isLoadingContext}
                                    onDraft={handleMagicDraft}
                                    onGenerateImage={handleGenerateImage}
                                    onPublish={handlePublishWorkbench}
                                    onSave={handleSaveWorkbench}
                                    isDrafting={isDrafting}
                                    isGeneratingImage={isGeneratingImage}
                                    title={workbenchTitle}
                                    content={workbenchContent}
                                    onTitleChange={setWorkbenchTitle}
                                    onContentChange={setWorkbenchContent}
                                    usedPrompt={lastPrompt}
                                />
                            </div>
                        </div>
                    )}
                </main>
            </div>

            {/* Existing Modal for Dashboard Edits */}
            {isPostModalOpen && (
                <dialog open className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm w-full h-full">
                    <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-2xl p-6 relative font-sans border border-gray-100 dark:border-slate-800">
                        <div className="flex justify-between items-center mb-6 border-b dark:border-slate-800 pb-4">
                            <h3 className="text-2xl font-bold text-gray-800 dark:text-white">
                                {editingPost ? 'Edit Asset' : 'New Asset'}
                            </h3>
                            <button onClick={() => setIsPostModalOpen(false)} className="text-gray-400">✕</button>
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
    const imageUrl = post?.imageUrl || '';
    const excerpt = post?.excerpt || '';
    
    const [loading, setLoading] = useState(false);
    
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await onSubmit({ title, content, excerpt, imageUrl, status: post?.status || 'draft' }, post?.id);
            onSuccess();
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-5 font-sans">
            <input type="text" value={title} onChange={e => setTitle(e.target.value)} className="w-full p-3 border dark:border-slate-700 dark:bg-slate-800 dark:text-white rounded-xl outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Title" />
            <textarea value={content} onChange={e => setContent(e.target.value)} className="w-full p-3 border dark:border-slate-700 dark:bg-slate-800 dark:text-white rounded-xl min-h-[200px] outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Content" />
            <button type="submit" disabled={loading} className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl transition-colors disabled:opacity-50">
                {loading ? 'Saving...' : 'SAVE CHANGES'}
            </button>
        </form>
    );
};

export default BrandPage;