import React, { useState } from 'react';
import { BlogPost } from '../types';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { useBrandLogic } from '../features/marketing/hooks/useBrandLogic';
import { BrandDashboardView } from '../features/marketing/components/BrandDashboardView';
import { BrandWorkbenchView } from '../features/marketing/components/BrandWorkbenchView';
import { useNavigate } from 'react-router-dom';
import { 
    PaletteIcon, LayoutIcon, RefreshCwIcon, SparklesIcon, XIcon
} from '../components/Icons';

const BrandPage: React.FC = () => {
    const navigate = useNavigate();
    const {
        viewMode, setViewMode,
        posts, trendsData, loading,
        logoSvg, 
        sources, activeSource, contextData,
        isLoadingSources, isLoadingContext, isDrafting,
        isSidebarOpen, setIsSidebarOpen,
        workbenchTitle, setWorkbenchTitle,
        workbenchContent, setWorkbenchContent,
        handleSelectSource, handleMagicDraft, handleSaveWorkbench, handlePublishWorkbench,
        handleDeletePost, handleNewPost, updatePostStatus, handleSavePost, 
        handleGenerateImage, isGeneratingLogo,
        loadData
    } = useBrandLogic();

    const [editingPost, setEditingPost] = useState<BlogPost | null>(null);
    const [isPostModalOpen, setIsPostModalOpen] = useState(false);

    const handleEditSmart = (post: BlogPost) => {
        if (post.status === 'draft' || post.status === 'changes_requested') {
            setWorkbenchTitle(post.title || '');
            setWorkbenchContent(post.content || '');
            handleSelectSource({ 
                id: post.id, 
                type: 'blog', 
                title: post.title || 'Untitled Draft',
                summary: post.excerpt || '',
                date: post.publishDate || new Date().toISOString()
            } as any);
            setViewMode('workbench');
        } else {
            setEditingPost(post);
            setIsPostModalOpen(true);
        }
    };

    return (
        <PermissionGuard 
            permission="brand:manage" 
            fallback={<div className="p-12 text-center text-gray-500">Access Denied: Brand Hub is for Marketing roles only.</div>}
        >
            <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-900">
                <header className="px-6 py-8 md:px-10 flex justify-between items-center bg-white dark:bg-slate-900 border-b shrink-0 font-sans">
                    <div className="flex items-center gap-4">
                        <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-3">
                            <PaletteIcon className="w-8 h-8 text-indigo-600" />
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
                        <button onClick={loadData} aria-label="Refresh brand data" className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full transition-colors">
                            <RefreshCwIcon className={`w-5 h-5 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-auto">
                    {viewMode === 'dashboard' ? (
                        <BrandDashboardView 
                            posts={posts}
                            trendsData={trendsData}
                            logoSvg={logoSvg}
                            isGeneratingLogo={isGeneratingLogo}
                            onGenerateLogo={() => handleGenerateImage('minimal')}
                            onNewPost={handleNewPost}
                            onEditSmart={handleEditSmart}
                            onUpdateStatus={updatePostStatus}
                            onDeletePost={handleDeletePost}
                            onNavigateAdvanced={(id) => navigate(`/brand/editor/${id}`)}
                        />
                    ) : (
                        <BrandWorkbenchView 
                            sources={sources}
                            activeSource={activeSource}
                            contextData={contextData}
                            isLoadingSources={isLoadingSources}
                            isLoadingContext={isLoadingContext}
                            isDrafting={isDrafting}
                            isSidebarOpen={isSidebarOpen}
                            setIsSidebarOpen={setIsSidebarOpen}
                            workbenchTitle={workbenchTitle}
                            setWorkbenchTitle={setWorkbenchTitle}
                            workbenchContent={workbenchContent}
                            setWorkbenchContent={setWorkbenchContent}
                            handleSelectSource={handleSelectSource}
                            handleMagicDraft={handleMagicDraft}
                            handleSaveWorkbench={handleSaveWorkbench}
                            handlePublishWorkbench={handlePublishWorkbench}
                            handleGenerateImage={handleGenerateImage}
                            isGeneratingLogo={isGeneratingLogo}
                        />
                    )}
                </main>
            </div>
            
            {/* Restored Modal for Dashboard Edits */}
            {isPostModalOpen && (
                <dialog open className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm w-full h-full">
                    <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-2xl p-6 relative font-sans border border-gray-100 dark:border-slate-800">
                        <div className="flex justify-between items-center mb-6 border-b dark:border-slate-800 pb-4">
                            <h3 className="text-2xl font-bold text-gray-800 dark:text-white">
                                {editingPost ? 'Edit Asset' : 'New Asset'}
                            </h3>
                            <button onClick={() => setIsPostModalOpen(false)} aria-label="Close modal" className="text-gray-400 hover:text-gray-600 transition-colors"><XIcon className="w-5 h-5" /></button>
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
            <input type="text" value={title} onChange={e => setTitle(e.target.value)} className="w-full p-3 border border-gray-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white rounded-xl outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Title" />
            <textarea value={content} onChange={e => setContent(e.target.value)} className="w-full p-3 border border-gray-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white rounded-xl min-h-[200px] outline-none focus:ring-2 focus:ring-indigo-500 custom-scrollbar resize-none" placeholder="Content" />
            <button type="submit" disabled={loading} className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl transition-colors disabled:opacity-50 shadow-lg shadow-indigo-200 dark:shadow-none">
                {loading ? 'Saving...' : 'SAVE CHANGES'}
            </button>
        </form>
    );
};

export default BrandPage;
