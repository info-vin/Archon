import { useState, useEffect, useCallback } from 'react';
import { api } from '../../../services/api';
import { BlogPost, TaskStatus, EmployeeRole } from '../../../types';
import { useAuth } from '@/hooks/useAuth';
import { ContentSource } from '../components/VictoryFeedList';

export const useBrandLogic = () => {
    const { user } = useAuth();
    const [viewMode, setViewMode] = useState<'dashboard' | 'workbench'>('workbench');
    
    // Dashboard State
    const [posts, setPosts] = useState<BlogPost[]>([]);
    const [trendsData, setTrendsData] = useState<any>(null);
    const [logoSvg, setLogoSvg] = useState<string | null>(null);
    const [isGeneratingLogo, setIsGeneratingLogo] = useState(false);
    const [loading, setLoading] = useState(true);

    // Workbench State
    const [sources, setSources] = useState<ContentSource[]>([]);
    const [activeSource, setActiveSource] = useState<ContentSource | null>(null);
    const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
    const [activePostId, setActivePostId] = useState<string | null>(null);
    const [contextData, setContextData] = useState<any>(null);
    const [isLoadingSources, setIsLoadingSources] = useState(false);
    const [isLoadingContext, setIsLoadingContext] = useState(false);
    const [isDrafting, setIsDrafting] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    
    // Workbench Editor State
    const [workbenchTitle, setWorkbenchTitle] = useState('');
    const [workbenchContent, setWorkbenchContent] = useState('');
    const [workbenchImageUrl, setWorkbenchImageUrl] = useState('/placeholder-blog.jpg');

    // Persistence Logic
    useEffect(() => {
        if (activeSource?.id && activeSource.type !== 'blog') {
            const savedTitle = localStorage.getItem(`draft_title_${activeSource.id}`);
            const savedContent = localStorage.getItem(`draft_content_${activeSource.id}`);
            const savedImage = localStorage.getItem(`draft_image_${activeSource.id}`);
            
            setWorkbenchTitle(savedTitle || '');
            setWorkbenchContent(savedContent || '');
            setWorkbenchImageUrl(savedImage || '/placeholder-blog.jpg');
        }
    }, [activeSource?.id, activeSource?.type]);

    useEffect(() => {
        if (activeSource?.id) {
            localStorage.setItem(`draft_title_${activeSource.id}`, workbenchTitle);
            localStorage.setItem(`draft_content_${activeSource.id}`, workbenchContent);
            localStorage.setItem(`draft_image_${activeSource.id}`, workbenchImageUrl);
        }
    }, [workbenchTitle, workbenchContent, workbenchImageUrl, activeSource?.id]);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            // Using Settled pattern for Bob's dashboard resilience
            const results = await Promise.allSettled([
                api.getBlogPosts(),
                api.getMarketingTrends()
            ]);
            
            if (results[0].status === 'fulfilled') setPosts(results[0].value);
            if (results[1].status === 'fulfilled') setTrendsData(results[1].value);
            
        } catch (err) {
            console.error("Failed to load brand data:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadWorkbenchData = useCallback(async () => {
        setIsLoadingSources(true);
        try {
            const sourcesData = await api.getContentSources();
            setSources(sourcesData as ContentSource[]);
        } catch (err) {
            console.error("Failed to load content sources:", err);
        } finally {
            setIsLoadingSources(false);
        }
    }, []);

    useEffect(() => {
        loadData();
        if (viewMode === 'workbench') loadWorkbenchData();
    }, [viewMode, loadData, loadWorkbenchData]);

    const handleSelectSource = async (source: ContentSource) => {
        setWorkbenchTitle('');
        setWorkbenchContent('');
        setWorkbenchImageUrl('/placeholder-blog.jpg');
        setContextData(null);
        
        const sourceData = { ...source };
        
        if (source.type === 'blog' && source.id && !source.id.startsWith('blank-')) {
            setIsLoadingContext(true);
            try {
                const blogRes = await api.getBlogPost(source.id);
                const finalImage = blogRes.imageUrl || '/placeholder-blog.jpg';
                setWorkbenchTitle(blogRes.title);
                setWorkbenchContent(blogRes.content || '');
                setWorkbenchImageUrl(finalImage);
                setActivePostId(blogRes.id); 
                
                localStorage.setItem(`draft_title_${source.id}`, blogRes.title);
                localStorage.setItem(`draft_content_${source.id}`, blogRes.content || '');
                localStorage.setItem(`draft_image_${source.id}`, finalImage);
                
                const taskId = (blogRes as any).generationMetadata?.task_id || (blogRes as any).task_id;
                setActiveTaskId(taskId || null);
                sourceData.review_notes = blogRes.review_notes;
                sourceData.ai_score = blogRes.ai_score;
            } catch (err) {
                console.error("Failed to load blog context", err);
            } finally {
                setIsLoadingContext(false);
            }
        } else {
            setActivePostId(null);
            const taskId = sourceData.metadata?.task_id || (sourceData as any).task_id;
            setActiveTaskId(taskId || null);
        }
        
        setActiveSource(sourceData);
        if (!source.id.startsWith('blank-')) {
            setIsLoadingContext(true);
            try {
                const context = await api.getContentContext(source.id, source.type);
                setContextData(context);
            } catch (err) {
                console.error("Failed to load context:", err);
            } finally {
                setIsLoadingContext(false);
            }
        }
    };

    const handleNewPost = () => {
        setWorkbenchTitle('');
        setWorkbenchContent('');
        setWorkbenchImageUrl('/placeholder-blog.jpg');
        setActivePostId(null);
        setActiveTaskId(null);
        setContextData(null);
        setActiveSource({
            id: `blank-${Date.now()}`,
            type: 'blog',
            title: 'Blank Canvas',
            summary: 'Start creating from scratch.',
        } as any);
        setViewMode('workbench');
    };

    const handleMagicDraft = async (topic: string, config?: any) => {
        if (!activeSource) return;
        setIsDrafting(true);
        try {
            const result = await api.draftBlogPost({
                topic,
                context_source_id: activeSource.id,
                context_type: activeSource.type,
                tone: 'professional',
                ...config
            });
            setWorkbenchTitle(result.title);
            setWorkbenchContent(result.content);
        } catch (err: any) {
            alert(err.message || "Drafting failed");
        } finally {
            setIsDrafting(false);
        }
    };

    const handleSaveWorkbench = async () => {
        try {
            const postPayload = {
                title: workbenchTitle || "Untitled Draft",
                content: workbenchContent || "",
                excerpt: workbenchContent.slice(0, 100) + "...",
                imageUrl: workbenchImageUrl,
                status: 'draft',
                authorName: user?.name || "Bob",
                publishDate: new Date().toISOString(),
                generationMetadata: {
                    task_id: activeTaskId,
                    context_source_id: activeSource?.id,
                    context_type: activeSource?.type
                }
            };

            if (activePostId) {
                await api.updateBlogPost(activePostId, postPayload as any);
            } else {
                const newPost = await api.createBlogPost(postPayload as any);
                setActivePostId(newPost.id);
            }

            if (activeTaskId) {
                await api.updateTask(activeTaskId, { status: TaskStatus.DOING });
            }
            setViewMode('dashboard');
            loadData();
        } catch (err: any) {
            alert(`Failed to save draft: ${err.message}`);
        }
    };

    const handlePublishWorkbench = async (postData: { title: string, content: string }) => {
        const isManager = user?.role === EmployeeRole.MANAGER || user?.role === EmployeeRole.ADMIN;
        try {
            const payload = {
                ...postData,
                excerpt: postData.content.slice(0, 150) + '...',
                imageUrl: workbenchImageUrl,
                status: 'draft',
                authorName: user?.name || 'Unknown Author',
                publishDate: new Date().toISOString(),
                generationMetadata: {
                    task_id: activeTaskId,
                    context_source_id: activeSource?.id,
                    context_type: activeSource?.type
                }
            };

            const targetPost = activePostId 
                ? await api.updateBlogPost(activePostId, payload as any)
                : await api.createBlogPost(payload as any);

            if (isManager) {
                await api.updateBlogPostStatus(targetPost.id, 'published');
            } else {
                const result = await api.submitBlogPost(targetPost.id);
                if (result.status !== 'changes_requested' && activeTaskId) {
                    await api.updateTask(activeTaskId, { status: TaskStatus.REVIEW });
                }
            }
            loadData();
        } catch (err: any) {
            alert(`Operation failed: ${err.message}`);
        }
    };

    const handleDeletePost = async (id: string) => {
        if (!window.confirm("Are you sure you want to delete this post?")) return;
        try {
            await api.deleteBlogPost(id);
            setPosts(prev => prev.filter(p => p.id !== id));
        } catch (err: any) {
            alert(`Delete failed: ${err.message}`);
        }
    };

    const updatePostStatus = async (id: string, newStatus: BlogPost['status']) => {
        try {
            await api.updateBlogPostStatus(id, newStatus);
            setPosts(prev => prev.map(p => p.id === id ? { ...p, status: newStatus } : p));
        } catch (err) {
            alert("Status update failed");
        }
    };

    const handleSavePost = async (postData: any, postId?: string) => {
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
            loadData();
        } catch(error: any) {
             alert(`Failed to save post: ${error.message}`);
        }
    };

    const handleGenerateImage = async (style: string) => {
        setIsGeneratingLogo(true);
        try {
            const result = await api.generateLogo(style);
            if (result.image_url) {
                setWorkbenchImageUrl(result.image_url);
                // Also inject into content for P6 Smart Polish
                setWorkbenchContent(prev => `![AI Image](${result.image_url})\n\n${prev}`);
            }
        } catch (err) {
            alert("Failed to generate image");
        } finally {
            setIsGeneratingLogo(false);
        }
    };

    return {
        viewMode, setViewMode, user,
        posts, trendsData, loading,
        logoSvg, setLogoSvg, isGeneratingLogo,
        sources, activeSource, activeTaskId, contextData,
        isLoadingSources, isLoadingContext, isDrafting,
        isSidebarOpen, setIsSidebarOpen,
        workbenchTitle, setWorkbenchTitle,
        workbenchContent, setWorkbenchContent,
        workbenchImageUrl, setWorkbenchImageUrl,
        handleSelectSource, handleMagicDraft, handleSaveWorkbench, handlePublishWorkbench,
        handleDeletePost, handleNewPost, updatePostStatus, handleSavePost, 
        handleGenerateImage,
        loadData, loadWorkbenchData
    };
};
