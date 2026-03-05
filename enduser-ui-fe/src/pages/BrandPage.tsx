import React, { useState } from 'react';
import { BlogPost } from '../types';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { useBrandLogic } from '../features/marketing/hooks/useBrandLogic';
import { BrandDashboardView } from '../features/marketing/components/BrandDashboardView';
import { BrandWorkbenchView } from '../features/marketing/components/BrandWorkbenchView';
import { useNavigate } from 'react-router-dom';
import { 
    PaletteIcon, LayoutIcon, RefreshCwIcon, SparklesIcon
} from '../components/Icons';

const BrandPage: React.FC = () => {
    const navigate = useNavigate();
    const {
        viewMode, setViewMode,
        posts, trendsData, loading,
        sources, activeSource, contextData,
        isLoadingSources, isLoadingContext, isDrafting, isGeneratingImage,
        isSidebarOpen, setIsSidebarOpen,
        workbenchTitle, setWorkbenchTitle,
        workbenchContent, setWorkbenchContent,
        workbenchImageUrl, setWorkbenchImageUrl,
        handleSelectSource, handleMagicDraft, handleSaveWorkbench, handlePublishWorkbench,
        loadData
    } = useBrandLogic();

    const [editingPost, setEditingPost] = useState<BlogPost | null>(null);
    const [_isPostModalOpen, setIsPostModalOpen] = useState(false);

    const handleEditSmart = (post: BlogPost) => {
        if (post.status === 'draft' || post.status === 'changes_requested') {
            setWorkbenchTitle(post.title || '');
            setWorkbenchContent(post.content || '');
            setWorkbenchImageUrl(post.imageUrl || '/placeholder-blog.jpg');
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
            permission="leads:view:marketing" 
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
                        <button onClick={loadData} className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full transition-colors">
                            <RefreshCwIcon className={`w-5 h-5 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </header>

                <main className={`flex-1 ${viewMode === 'workbench' ? 'overflow-hidden' : 'overflow-auto'}`}>
                    {viewMode === 'dashboard' ? (
                        <BrandDashboardView 
                            posts={posts}
                            trendsData={trendsData}
                            onNewPost={() => setViewMode('workbench')}
                            onEditSmart={handleEditSmart}
                            onUpdateStatus={() => alert("Quick status update pending implementation")}
                            onDeletePost={() => alert("Delete pending implementation")}
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
                            isGeneratingImage={isGeneratingImage}
                            isSidebarOpen={isSidebarOpen}
                            setIsSidebarOpen={setIsSidebarOpen}
                            workbenchTitle={workbenchTitle}
                            setWorkbenchTitle={setWorkbenchTitle}
                            workbenchContent={workbenchContent}
                            setWorkbenchContent={setWorkbenchContent}
                            workbenchImageUrl={workbenchImageUrl}
                            setWorkbenchImageUrl={setWorkbenchImageUrl}
                            handleSelectSource={handleSelectSource}
                            handleMagicDraft={handleMagicDraft}
                            handleSaveWorkbench={handleSaveWorkbench}
                            handlePublishWorkbench={handlePublishWorkbench}
                        />
                    )}
                </main>
            </div>
            {/* Minimal support for editingPost modal placeholder */}
            {editingPost && (
                <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl p-6 max-w-md w-full">
                        <h3 className="text-lg font-bold mb-4">Edit Post: {editingPost.title}</h3>
                        <p className="text-sm text-gray-500 mb-6">Advanced metadata editing is currently disabled in this simplified view. Please use Workbench for content edits.</p>
                        <button onClick={() => setEditingPost(null)} className="w-full py-2 bg-gray-100 rounded-lg font-bold">Close</button>
                    </div>
                </div>
            )}
        </PermissionGuard>
    );
};

export default BrandPage;
