import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { XIcon, SparklesIcon, CheckCircleIcon, RefreshCwIcon } from '../../../components/Icons';
import { api } from '../../../services/api';

// PERFORMANCE: Hoist Intl.DateTimeFormat instance outside the component to avoid expensive repeated instantiations (implicitly called by toLocaleDateString) inside the render loop.
const dateFormatter = new Intl.DateTimeFormat(undefined);

interface ContentReviewPanelProps {
    blogs: any[];
    processingId: string | null;
    setProcessingId: (id: string | null) => void;
    handleApproveContent: (id: string, type: 'blog' | 'lead') => Promise<void>;
    fetchData: () => Promise<void>;
}

export const ContentReviewPanel: React.FC<ContentReviewPanelProps> = ({
    blogs, processingId, setProcessingId, handleApproveContent, fetchData
}) => {
    const [selectedContent, setSelectedContent] = useState<any | null>(null);
    const [isRejecting, setIsRejecting] = useState(false);
    const [rejectReason, setRejectReason] = useState('');
    const [isGeneratingReason, setIsGeneratingReason] = useState(false);

    const handleGenerateReason = async () => {
        if (!selectedContent) return;
        setIsGeneratingReason(true);
        try {
            const res = await api.rejectSuggestion(selectedContent.id);
            setRejectReason(res.suggested_reason);
        } catch (e: any) {
            alert("AI suggestion failed: " + e.message);
        } finally {
            setIsGeneratingReason(false);
        }
    };

    const handleRejectContent = async () => {
        if (!selectedContent) return;
        setProcessingId(selectedContent.id);
        try {
            await api.processApproval('blog', selectedContent.id, 'reject', rejectReason); 
            alert("Content Returned. Bob has been notified.");
            await fetchData();
            setSelectedContent(null);
            setIsRejecting(false);
            setRejectReason('');
        } catch (e: any) {
            alert("Rejection failed: " + e.message);
        } finally {
            setProcessingId(null);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 space-y-2">
                {blogs.map((blog: any) => (
                    <div 
                        key={blog.id}
                        onClick={() => setSelectedContent(blog)}
                        className={`p-4 rounded-xl border cursor-pointer transition-all ${
                            selectedContent?.id === blog.id 
                            ? 'bg-indigo-50 border-indigo-200 shadow-sm' 
                            : 'bg-white border-gray-100 hover:border-indigo-100'
                        }`}
                    >
                        <h4 className="font-bold text-gray-800 text-sm line-clamp-1">{blog.title}</h4>
                        <p className="text-xs text-gray-500 mt-1 flex justify-between">
                            <span>{blog.author_name || 'Bob'}</span>
                            <span className="font-mono text-[10px]">{dateFormatter.format(new Date(blog.created_at || Date.now()))}</span>
                        </p>
                    </div>
                ))}
                {blogs.length === 0 && <div className="text-center py-8 text-gray-400 text-sm italic">No content pending review.</div>}
            </div>
            <div className="lg:col-span-2">
                {selectedContent ? (
                    <div className="bg-gray-50 dark:bg-slate-900 rounded-2xl p-6 border border-gray-100 dark:border-slate-800 h-full overflow-y-auto max-h-[600px] shadow-inner">
                        <div className="flex justify-between items-start mb-6">
                            <div className="flex-1">
                                <h3 className="text-xl font-black text-gray-900 dark:text-white leading-tight">{selectedContent.title}</h3>
                                <div className="flex items-center gap-3 mt-2">
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest ${ (selectedContent.ai_score || selectedContent.aiScore) < 80 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
                                        AI SCORE: {selectedContent.ai_score || selectedContent.aiScore || 0}%
                                    </span>
                                    <span className="text-[10px] text-gray-400 font-bold uppercase">{selectedContent.author_name || selectedContent.authorName}</span>
                                </div>
                            </div>
                            <button onClick={() => setSelectedContent(null)} className="p-2 hover:bg-gray-200 rounded-full transition-colors" aria-label="Close content preview" title="Close content preview"><XIcon className="w-4 h-4" /></button>
                        </div>

                        <div className="prose prose-sm dark:prose-invert max-w-none mb-8 bg-white dark:bg-slate-950 p-6 rounded-xl border border-gray-100 dark:border-slate-800 shadow-sm overflow-hidden">
                            {(selectedContent.imageUrl || selectedContent.image_url) && (
                                <img 
                                    src={selectedContent.imageUrl || selectedContent.image_url} 
                                    alt="Cover" 
                                    className="w-full h-48 object-cover rounded-lg mb-6 shadow-md" 
                                />
                            )}
                            <ReactMarkdown>{selectedContent.content || ''}</ReactMarkdown>
                        </div>

                        {isRejecting ? (
                            <div className="bg-white dark:bg-slate-950 p-4 rounded-xl border border-red-100 dark:border-red-900/30 mb-4 animate-in fade-in slide-in-from-top-2">
                                <div className="flex justify-between items-center mb-2">
                                    <h5 className="text-xs font-black text-red-500 uppercase">Instructions for Bob</h5>
                                    <button 
                                        onClick={handleGenerateReason}
                                        disabled={isGeneratingReason}
                                        className="text-[10px] font-black text-indigo-600 flex items-center gap-1 hover:underline"
                                    >
                                        <SparklesIcon className={`w-3 h-3 ${isGeneratingReason ? 'animate-spin' : ''}`} />
                                        {isGeneratingReason ? 'Generating...' : 'Suggest with AI'}
                                    </button>
                                </div>
                                <textarea 
                                    className="w-full text-sm p-3 bg-gray-50 dark:bg-slate-900 rounded-lg border border-gray-100 dark:border-slate-800 focus:ring-2 focus:ring-red-500/20 mb-3 outline-none"
                                    rows={3}
                                    placeholder="What should be improved?"
                                    value={rejectReason}
                                    onChange={e => setRejectReason(e.target.value)}
                                />
                                <div className="flex gap-2 justify-end">
                                    <button onClick={() => setIsRejecting(false)} className="px-3 py-1.5 text-xs font-bold text-gray-500">Cancel</button>
                                    <button 
                                        disabled={!rejectReason.trim() || !!processingId}
                                        onClick={handleRejectContent} 
                                        className="px-4 py-1.5 bg-red-600 text-white text-xs font-black rounded-lg hover:bg-red-700 shadow-lg shadow-red-100 dark:shadow-none transition-all active:scale-95 flex items-center justify-center gap-2"
                                    >
                                        {!!processingId ? <RefreshCwIcon className="animate-spin w-3 h-3" /> : null}
                                        {!!processingId ? 'RETURNING...' : 'CONFIRM RETURN'}
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="flex gap-3">
                                <button 
                                    disabled={!!processingId}
                                    onClick={() => { setIsRejecting(true); }}
                                    className="flex-1 py-4 text-sm font-bold text-red-600 border border-red-200 rounded-xl hover:bg-red-50 transition-all active:scale-95"
                                >
                                    RETURN
                                </button>
                                <button 
                                    disabled={!!processingId}
                                    onClick={() => handleApproveContent(selectedContent.id, 'blog')}
                                    className="flex-[2] py-4 text-sm font-black bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 shadow-lg shadow-indigo-100 dark:shadow-none transition-all active:scale-95 flex items-center justify-center gap-2"
                                >
                                    {processingId === selectedContent.id ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <CheckCircleIcon className="w-4 h-4" />}
                                    PUBLISH ASSET
                                </button>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="h-full flex items-center justify-center border-2 border-dashed border-gray-200 rounded-2xl text-gray-400 italic text-sm">
                        Select a content draft to begin strategic review
                    </div>
                )}
            </div>
        </div>
    );
};
