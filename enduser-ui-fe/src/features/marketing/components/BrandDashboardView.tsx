import React from 'react';
import { BlogPost } from '../../../types';
import { TrendLineChart } from './TrendLineChart';
import { SankeyDiagram } from './SankeyDiagram';
import { VictoryFeedList } from './VictoryFeedList';
import { 
    PlusIcon, TrendingUpIcon, FileEditIcon, EyeIcon, CheckCircleIcon, SparklesIcon
} from '../../../components/Icons';

interface BrandDashboardViewProps {
    posts: BlogPost[];
    trendsData: any;
    onNewPost: () => void;
    onEditSmart: (post: BlogPost) => void;
    onUpdateStatus: (id: string, status: string) => void;
    onDeletePost: (id: string) => void;
    onNavigateAdvanced: (id: string) => void;
}

export const BrandDashboardView: React.FC<BrandDashboardViewProps> = ({
    posts, trendsData, onNewPost, onEditSmart, onUpdateStatus, onDeletePost, onNavigateAdvanced
}) => {
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
                <div className="space-y-3 overflow-y-auto max-h-[500px] pr-1 font-sans">
                    {columnPosts.map(post => {
                        const feedback = post.review_notes || (post as any).reviewNotes;
                        const isReturned = post.status === 'changes_requested' || (feedback && post.status !== 'published' && post.status !== 'review');
                        
                        return (
                            <div key={post.id} className={`bg-white p-4 rounded-lg shadow-sm border transition-all group relative overflow-hidden ${isReturned ? 'border-red-200 ring-1 ring-red-50' : 'border-gray-100 hover:shadow-md'}`}>
                                {isReturned && (
                                    <div className="absolute top-0 right-0 bg-red-600 text-white text-[9px] font-black px-2 py-0.5 rounded-bl-lg tracking-tighter shadow-sm z-20">
                                        RETURNED
                                    </div>
                                )}
                                <h4 className="font-semibold text-gray-800 line-clamp-2 pr-12">{post.title}</h4>
                                {isReturned && feedback && (
                                    <div className="mt-3 p-2 bg-red-50/80 rounded-lg border border-red-100 relative">
                                        <p className="text-[11px] text-red-900 italic line-clamp-4 leading-snug">"{feedback}"</p>
                                    </div>
                                )}
                                <p className="text-[10px] text-gray-500 mt-2 font-medium">By {post.authorName}</p>
                                <div className="mt-4 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    <div className="flex gap-1">
                                        <button onClick={() => onEditSmart(post)} className="p-1 hover:bg-gray-100 rounded text-blue-500"><FileEditIcon className="w-4 h-4" /></button>
                                        <button onClick={() => onNavigateAdvanced(post.id)} className="p-1 hover:bg-indigo-50 rounded text-indigo-500"><SparklesIcon className="w-4 h-4" /></button>
                                        {post.status !== 'review' && (
                                            <button onClick={() => onUpdateStatus(post.id, 'review')} className="p-1 hover:bg-amber-50 rounded text-amber-500"><EyeIcon className="w-4 h-4" /></button>
                                        )}
                                        {post.status !== 'published' && (
                                            <button onClick={() => onUpdateStatus(post.id, 'published')} className="p-1 hover:bg-green-50 rounded text-green-600"><CheckCircleIcon className="w-4 h-4" /></button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        )
    };

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8 font-sans">
            {/* Market Intelligence */}
            <div className="bg-purple-50 text-gray-900 p-6 rounded-2xl shadow-xl space-y-6 relative overflow-hidden w-full border border-purple-100">
                <div className="relative z-10">
                    <h2 className="text-xl font-bold flex items-center gap-2 text-purple-900">
                        <TrendingUpIcon className="w-5 h-5 text-purple-600" />
                        Market Intelligence 2.0
                    </h2>
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

            {/* Pipeline */}
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
                        filter={(p: BlogPost) => p.status === 'draft' || p.status === 'changes_requested'}
                        icon={FileEditIcon} 
                        colorClass="text-gray-600 border-gray-200" 
                    />
                    <KanbanColumn 
                        title="In Review" 
                        filter={(p: BlogPost) => p.status === 'review'}
                        icon={EyeIcon} 
                        colorClass="text-amber-600 border-amber-200" 
                    />
                    <KanbanColumn 
                        title="Published" 
                        filter={(p: BlogPost) => p.status === 'published'}
                        icon={CheckCircleIcon} 
                        colorClass="text-green-600 border-green-200" 
                    />
                </div>
            </section>

            {/* Victory Feed */}
            <section className="space-y-4">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <TrendingUpIcon className="w-5 h-5 text-indigo-500" />
                    Victory Feed
                </h2>
                <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
                    <VictoryFeedList posts={posts} onPostClick={onEditSmart} />
                </div>
            </section>
        </div>
    );
};
