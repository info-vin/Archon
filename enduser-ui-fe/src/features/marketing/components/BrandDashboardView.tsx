import React from 'react';
import { BlogPost } from '../../../types';
import { TrendLineChart } from './TrendLineChart';
import { SankeyDiagram } from './SankeyDiagram';
import { VictoryFeedList, ContentSource } from './VictoryFeedList';
import { IntelligenceHud } from './IntelligenceHud';
import { 
    PlusIcon, TrendingUpIcon, FileEditIcon, EyeIcon, CheckCircleIcon, SparklesIcon, LayoutIcon, DownloadIcon, RefreshCwIcon, PaletteIcon
} from '../../../components/Icons';

interface BrandDashboardViewProps {
    posts: BlogPost[];
    trendsData: any;
    logoSvg: string | null;
    isGeneratingLogo: boolean;
    onNewPost: () => void;
    onEditSmart: (post: BlogPost) => void;
    onUpdateStatus: (id: string, status: BlogPost['status']) => void;
    onDeletePost: (id: string) => void;
    onNavigateAdvanced: (id: string) => void;
    onGenerateLogo: () => void;
}

// PERFORMANCE: Hoisted inline components out of the render loop to prevent full sub-tree remounts
// on every parent state change (e.g., when the parent re-renders, React will now correctly reconcile).
const KanbanColumn: React.FC<{
    title: string;
    columnPosts: BlogPost[];
    icon: any;
    colorClass: string;
    onUpdateStatus: (id: string, status: BlogPost['status']) => void;
    onEditSmart: (post: BlogPost) => void;
    onNavigateAdvanced: (id: string) => void;
    onDeletePost: (id: string) => void;
}> = ({ title, columnPosts, icon: Icon, colorClass, onUpdateStatus, onEditSmart, onNavigateAdvanced, onDeletePost }) => {
    return (
        <div className="flex-1 min-w-[300px] bg-white rounded-2xl border border-gray-100 p-4 shadow-sm flex flex-col max-h-[600px]">
            <h3 className={`text-sm font-black uppercase tracking-widest mb-4 flex items-center justify-between border-b pb-2 ${colorClass}`}>
                <span className="flex items-center gap-2"><Icon className="w-4 h-4" /> {title}</span>
                <span className="bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full text-[10px]">{columnPosts.length}</span>
            </h3>
            <div className="space-y-3 overflow-y-auto flex-1 pr-1 custom-scrollbar">
                {columnPosts.map((post: BlogPost) => {
                    return (
                        <div key={post.id} className="group bg-white border border-gray-100 p-4 rounded-xl shadow-sm hover:shadow-md transition-all hover:border-indigo-100">
                            <h4 className="font-bold text-gray-800 text-sm mb-1 leading-snug">{post.title || 'Untitled'}</h4>
                            <p className="text-xs text-gray-500 line-clamp-2 mb-3 h-8">{post.excerpt}</p>
                            <div className="flex items-center justify-between mt-4">
                                <span className="text-[10px] text-gray-400 font-mono">
                                    {new Date(post.publishDate).toLocaleDateString()}
                                </span>
                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
                                    <button onClick={() => onEditSmart(post)} className="p-1 hover:bg-gray-100 rounded text-blue-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2" title="Edit Content" aria-label="Edit Content"><FileEditIcon className="w-4 h-4" /></button>
                                    <button onClick={() => onNavigateAdvanced(post.id)} className="p-1 hover:bg-indigo-50 rounded text-indigo-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2" title="Advanced Editor (Pro)" aria-label="Advanced Editor (Pro)"><SparklesIcon className="w-4 h-4" /></button>
                                    {post.status !== 'review' && (
                                        <button onClick={() => onUpdateStatus(post.id, 'review')} className="p-1 hover:bg-amber-50 rounded text-amber-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2" title="Move to Review" aria-label="Move to Review"><EyeIcon className="w-4 h-4" /></button>
                                    )}
                                    {post.status !== 'published' && (
                                        <button onClick={() => onUpdateStatus(post.id, 'published')} className="p-1 hover:bg-green-50 rounded text-green-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2" title="Publish Now" aria-label="Publish Now"><CheckCircleIcon className="w-4 h-4" /></button>
                                    )}
                                    <button onClick={() => onDeletePost(post.id)} className="p-1 hover:bg-red-50 rounded text-red-500 ml-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2" title="Delete" aria-label="Delete"><PlusIcon className="w-4 h-4 rotate-45" /></button>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    )
};

export const BrandDashboardView: React.FC<BrandDashboardViewProps> = ({
    posts, trendsData, logoSvg, isGeneratingLogo, onNewPost, onEditSmart, onUpdateStatus, onDeletePost, onNavigateAdvanced, onGenerateLogo
}) => {
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

    // PERFORMANCE: Wrapped feedSources in useMemo to prevent redundant array allocations and mapping operations on every render cycle
    const feedSources: ContentSource[] = React.useMemo(() => {
        return posts.map(p => ({
            id: p.id,
            type: 'blog',
            title: p.title,
            score: p.ai_score || 0,
            summary: p.excerpt || '',
            date: p.publishDate,
            status: p.status
        }));
    }, [posts]);

    // PERFORMANCE: Precalculate map for posts to avoid O(N) Array.find calls
    const postMap = React.useMemo(() => {
        const map = new Map<string, BlogPost>();
        posts.forEach(p => map.set(p.id, p));
        return map;
    }, [posts]);

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8 font-sans">
            <div className="bg-purple-50 text-gray-900 p-6 rounded-2xl shadow-xl space-y-6 relative overflow-hidden w-full border border-purple-100">
                <div className="relative z-10">
                    <h2 className="text-xl font-bold flex items-center gap-2 text-purple-900 mb-6">
                        <TrendingUpIcon className="w-5 h-5 text-purple-600" />
                        Market Intelligence 2.0
                    </h2>
                    
                    <IntelligenceHud />

                    {trendsData ? (
                        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="bg-white p-4 rounded-xl border border-purple-100 shadow-sm">
                                <h3 className="text-sm font-bold text-purple-800 mb-4 uppercase tracking-wider">Rising Topics (Monthly)</h3>
                                <div className="-ml-4"><TrendLineChart data={trendsData.keyword_growth} /></div>
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

            <section className="space-y-4">
                <div className="flex justify-between items-end">
                    <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                        <PlusIcon className="w-5 h-5 text-indigo-500" />
                        Content Pipeline
                    </h2>
                    <button onClick={onNewPost} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-indigo-700 flex items-center gap-2">
                        <PlusIcon className="w-4 h-4" /> New Post
                    </button>
                </div>
                <div className="flex flex-wrap gap-6">
                    <KanbanColumn
                        title="Drafts & Returned"
                        columnPosts={posts.filter((p: BlogPost) => p.status === 'draft' || p.status === 'changes_requested')}
                        icon={FileEditIcon}
                        colorClass="text-gray-600 border-gray-200"
                        onUpdateStatus={onUpdateStatus}
                        onEditSmart={onEditSmart}
                        onNavigateAdvanced={onNavigateAdvanced}
                        onDeletePost={onDeletePost}
                    />
                    <KanbanColumn
                        title="In Review"
                        columnPosts={posts.filter((p: BlogPost) => p.status === 'review')}
                        icon={EyeIcon}
                        colorClass="text-amber-600 border-amber-200"
                        onUpdateStatus={onUpdateStatus}
                        onEditSmart={onEditSmart}
                        onNavigateAdvanced={onNavigateAdvanced}
                        onDeletePost={onDeletePost}
                    />
                    <KanbanColumn
                        title="Published"
                        columnPosts={posts.filter((p: BlogPost) => p.status === 'published')}
                        icon={CheckCircleIcon}
                        colorClass="text-green-600 border-green-200"
                        onUpdateStatus={onUpdateStatus}
                        onEditSmart={onEditSmart}
                        onNavigateAdvanced={onNavigateAdvanced}
                        onDeletePost={onDeletePost}
                    />
                </div>
            </section>

            <section className="space-y-4">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <TrendingUpIcon className="w-5 h-5 text-indigo-500" />
                    Victory Feed
                </h2>
                <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
                    <VictoryFeedList sources={feedSources} onSelect={(s) => {
                        const post = postMap.get(s.id);
                        if (post) onEditSmart(post);
                    }} />
                </div>
            </section>

            {/* Brand Identity Section (Restored) */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 space-y-6">
                <div className="flex justify-between items-center">
                    <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                        <LayoutIcon className="w-5 h-5 text-indigo-500" />
                        Visual Identity
                    </h2>
                    <button
                        onClick={onGenerateLogo}
                        disabled={isGeneratingLogo}
                        className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-indigo-700 disabled:opacity-50 transition-all flex items-center gap-2 shadow-lg shadow-indigo-200"
                    >
                        <RefreshCwIcon className={`w-4 h-4 ${isGeneratingLogo ? 'animate-spin' : ''}`} />
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
                            aria-label="Download SVG"
                            className="absolute bottom-4 right-4 bg-white/10 backdrop-blur-md text-white p-2 rounded-lg hover:bg-white/20 transition-all opacity-0 group-hover:opacity-100 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
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
    );
};
