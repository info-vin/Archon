import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
    AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip as ReTooltip 
} from 'recharts';
import { 
    SparklesIcon, XIcon, CheckCircleIcon, RefreshCwIcon, SearchIcon 
} from '../../../components/Icons';
import { api } from '../../../services/api';

interface OpLoadPanelProps {
    commanderTrends: any[];
    approvals: { blogs: any[]; leads: any[] };
    codeProposals: any[];
    processingId: string | null;
    setProcessingId: (id: string | null) => void;
    handleApproveContent: (id: string, type: 'blog' | 'lead') => Promise<void>;
    handleCodeAction: (id: string, action: 'approve' | 'reject') => Promise<void>;
    fetchData: () => Promise<void>;
}

export const OpLoadPanel: React.FC<OpLoadPanelProps> = ({
    commanderTrends, approvals, codeProposals, processingId, setProcessingId,
    handleApproveContent, handleCodeAction, fetchData
}) => {
    const [opLoadTab, setOpLoadTab] = useState<'content' | 'devops'>('content');
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

    const handleViewDiff = (item: any) => {
        try {
            if (!item) return;
            let contentData = item.content;
            if (typeof item.content === 'string') {
                try {
                    contentData = JSON.parse(item.content);
                } catch (e) {
                    contentData = { raw: item.content };
                }
            }
            const summary = item.change_summary || "Strategic Prompt Update";
            const field = item.field_name || "Prompt Config";
            const author = item.created_by || "System";
            const displayStr = typeof contentData === 'string' ? contentData : JSON.stringify(contentData, null, 2);

            alert(
                `[ AUDIT VIEW: PROMPT CHANGE ]\n` +
                `----------------------------------\n` +
                `Target: ${item.document_id}\n` +
                `Author: ${author}\n` +
                `Field:  ${field}\n` +
                `Summary: ${summary}\n\n` +
                `NEW CONTENT PREVIEW:\n` +
                `${displayStr.slice(0, 400)}${displayStr.length > 400 ? '...' : ''}`
            );
        } catch (err) {
            console.error("ViewDiff Failed:", err);
            alert("Unable to preview this change. The data format might be incompatible.");
        }
    };

    return (
        <div className="space-y-6">
            {/* 30-Day Trend Insight */}
            <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 mb-8 min-h-[300px] flex flex-col">
                <h4 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                    <SparklesIcon className="w-3 h-3" /> 30-Day Performance Pulse (Daily)
                </h4>
                <div className="flex-1 min-h-[220px]">
                    {commanderTrends && commanderTrends.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%" minHeight={220}>
                            <AreaChart data={commanderTrends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <XAxis 
                                    dataKey="date" 
                                    axisLine={false} 
                                    tickLine={false} 
                                    fontSize={10} 
                                    interval={Math.max(0, Math.floor(commanderTrends.length / 3))} 
                                    tick={{fill: '#94a3b8'}}
                                />
                                <YAxis yAxisId="left" hide />
                                <YAxis yAxisId="right" hide domain={[0, 24]} />
                                <ReTooltip 
                                    contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}}
                                />
                                <Area yAxisId="left" type="monotone" dataKey="bob_tokens" stroke="#6366f1" fillOpacity={1} fill="url(#colorTokens)" strokeWidth={2} name="Bob's Tokens" isAnimationActive={false} />
                                <Area yAxisId="right" type="monotone" dataKey="decision_hours" stroke="#f59e0b" fill="transparent" strokeWidth={2} strokeDasharray="5 5" name="Decision Gap (Hrs)" isAnimationActive={false} />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-full flex items-center justify-center text-muted-foreground italic text-xs">
                            No performance data recorded in the last 30 days.
                        </div>
                    )}
                </div>
                {commanderTrends && commanderTrends.length > 0 && (
                    <div className="flex justify-center gap-6 mt-4">
                        <span className="flex items-center gap-2 text-[10px] font-bold text-indigo-600"><div className="w-2 h-2 rounded-full bg-indigo-600"/> Cumulative Tokens</span>
                        <span className="flex items-center gap-2 text-[10px] font-bold text-amber-600"><div className="w-2 h-2 border-t-2 border-amber-600 border-dashed w-4"/> Wait Time (Max 24h)</span>
                    </div>
                )}
            </div>

            <div className="flex gap-4 mb-6 border-b border-gray-100 pb-2">
                <button 
                    onClick={() => setOpLoadTab('content')}
                    className={`pb-2 text-sm font-bold transition-colors ${opLoadTab === 'content' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
                >
                    Context / Content ({approvals.blogs.length})
                </button>
                <button 
                    onClick={() => setOpLoadTab('devops')}
                    className={`pb-2 text-sm font-bold transition-colors ${opLoadTab === 'devops' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
                >
                    Dev Ops / Code ({codeProposals.length})
                </button>
            </div>

            {opLoadTab === 'content' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-1 space-y-2">
                        {approvals.blogs.map((blog: any) => (
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
                                    <span className="font-mono text-[10px]">{new Date(blog.created_at || Date.now()).toLocaleDateString()}</span>
                                </p>
                            </div>
                        ))}
                        {approvals.blogs.length === 0 && <div className="text-center py-8 text-gray-400 text-sm italic">No content pending review.</div>}
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
                                    <button onClick={() => setSelectedContent(null)} className="p-2 hover:bg-gray-200 rounded-full transition-colors" aria-label="Close content preview"><XIcon className="w-4 h-4" /></button>
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
                                                className="px-4 py-1.5 bg-red-600 text-white text-xs font-black rounded-lg hover:bg-red-700 shadow-lg shadow-red-100 dark:shadow-none transition-all active:scale-95"
                                            >
                                                CONFIRM RETURN
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
            )}

            {opLoadTab === 'devops' && (
                <div className="space-y-4">
                    {codeProposals.map((prop: any) => (
                        <div key={prop.id} className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-gray-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all">
                            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-3">
                                        <span className="text-[10px] font-black uppercase tracking-widest text-indigo-600 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded-full border border-indigo-100 dark:border-indigo-800/50">
                                            {prop.type} proposal
                                        </span>
                                        <span className="text-[10px] text-gray-400 font-mono">{new Date(prop.created_at).toLocaleString()}</span>
                                    </div>
                                    <p className="text-gray-800 dark:text-slate-200 font-mono text-sm bg-gray-50 dark:bg-slate-950 p-4 rounded-xl border border-gray-100 dark:border-slate-800 shadow-inner">
                                        {prop.request_payload?.description || 'Infrastructure change request detected.'}
                                    </p>
                                </div>
                                <div className="flex gap-3 w-full md:w-auto">
                                    <button 
                                        onClick={() => handleViewDiff(prop)}
                                        className="p-4 bg-gray-50 dark:bg-slate-800 text-gray-600 dark:text-slate-400 rounded-2xl hover:bg-gray-100 dark:hover:bg-slate-700 transition-all border border-gray-100 dark:border-slate-700"
                                        title="Inspect Code Difference"
                                        aria-label="Inspect Code Difference"
                                    >
                                        <SearchIcon className="w-5 h-5" />
                                    </button>
                                    <button 
                                        onClick={() => handleCodeAction(prop.id, 'reject')}
                                        disabled={!!processingId}
                                        className="flex-1 px-6 py-4 text-xs font-bold text-red-600 border border-red-100 rounded-2xl hover:bg-red-50 transition-all active:scale-95 min-w-[80px]"
                                    >
                                        REJECT
                                    </button>
                                    <button 
                                        onClick={() => handleCodeAction(prop.id, 'approve')}
                                        disabled={!!processingId}
                                        className="flex-1 px-6 py-4 text-xs font-black bg-amber-500 text-white rounded-2xl shadow-lg shadow-amber-100 dark:shadow-none transition-all active:scale-95 min-w-[80px]"
                                    >
                                        {processingId === prop.id ? '...' : 'APPROVE'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                    {codeProposals.length === 0 && (
                        <div className="p-12 text-center border-2 border-dashed border-gray-200 rounded-3xl text-gray-400 italic text-sm">
                            No pending code proposals. Infrastructure is stable and verified.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
