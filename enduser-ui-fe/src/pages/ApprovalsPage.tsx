import React, { useState, useEffect, useCallback } from 'react';
import Markdown from 'react-markdown';
import { api } from '../services/api';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { 
    ShieldCheckIcon, 
    CheckCircleIcon, 
    FileTextIcon, 
    DatabaseIcon, 
    RefreshCwIcon, 
    XIcon,
    TrendingUpIcon, 
    ClockIcon, 
    UserIcon, 
    EyeIcon,
    LayoutGridIcon,
    SparklesIcon,
    XCircleIcon
} from '../components/Icons';

const Badge = ({ children, className }: any) => (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-black uppercase tracking-tighter ${className}`}>
        {children}
    </span>
);

interface ChangeProposal {
  id: string;
  type: 'file' | 'git' | 'shell';
  status: string;
  created_at: string;
  request_payload: any;
}

interface BlogPost {
  id: string;
  title: string;
  status: string;
  content?: string;
  imageUrl?: string;
  hashtags?: string;
  authorName?: string;
  created_at?: string; 
  ai_score?: number;
}

interface AlertItem {
  id: string;
  level: 'ALERT' | 'INFO' | 'ERROR';
  message: string;
  created_at: string;
  details?: {
      type?: string;
      company?: string;
      days_stale?: number;
      enrichment_score?: number;
      [key: string]: any;
  };
}

const ApprovalsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'content' | 'code' | 'alerts'>('content');
  const [codeProposals, setCodeProposals] = useState<ChangeProposal[]>([]);
  const [contentApprovals, setContentApprovals] = useState<BlogPost[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Charlie's State Hooks
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [selectedPostId, setSelectedPostId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [contentRes, codeRes, alertsRes] = await Promise.all([
        api.getPendingApprovals().catch(e => { console.warn("Content fetch failed", e); return { blogs: [] }; }),
        api.getPendingChanges().catch(e => { console.warn("Code fetch failed", e); return []; }),
        api.getAlerts().catch(e => { console.warn("Alerts fetch failed", e); return []; })
      ]);

      setContentApprovals(contentRes.blogs || []);
      setCodeProposals(codeRes || []);
      setAlerts(alertsRes || []);

    } catch (err) {
      console.error("Critical error in Command Center fetch", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleContentAction = async (id: string, action: 'approve' | 'reject') => {
    if (action === 'reject') {
        setSelectedPostId(id);
        setRejectionReason("");
        setRejectModalOpen(true);
        return;
    }

    try {
      await api.processApproval('blog', id, action);
      alert('Content Published!');
      setPreviewId(null);
      fetchData();
    } catch (err) {
      alert("Action failed");
    }
  };

  const handleConfirmReject = async () => {
    if (!selectedPostId) return;
    try {
        await api.processApproval('blog', selectedPostId, 'reject', rejectionReason);
        alert('Returned to Bob with Feedback');
        setRejectModalOpen(false);
        setPreviewId(null);
        fetchData();
    } catch (err) {
        console.error(err);
        alert("Action failed");
    }
  };

  const handleGenerateReason = async () => {
      if (!selectedPostId) return;
      setIsGenerating(true);
      try {
          const res = await api.rejectSuggestion(selectedPostId);
          setRejectionReason(res.suggested_reason);
      } catch (e) {
          console.error(e);
          alert("AI Generation failed");
      } finally {
          setIsGenerating(false);
      }
  };

  const handleCodeAction = async (id: string, action: 'approve' | 'reject') => {
    try {
      if (action === 'approve') await api.approveChange(id);
      else await api.rejectChange(id);
      alert(action === 'approve' ? 'Change Applied' : 'Change Rejected');
      fetchData();
    } catch (err) {
      alert("Action failed");
    }
  };

  const handleDispatchTask = async (alertItem: AlertItem) => {
      try {
          setLoading(true);
          await api.generateTaskFromAlert(alertItem.id);
          alert(`Smart Task dispatched! Context enriched by AI.`);
          fetchData();
      } catch (err: any) {
          alert(`Failed to dispatch task: ${err.message}`);
      } finally {
          setLoading(false);
      }
  };

  return (
    <PermissionGuard permission="user:manage:team"> 
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6 md:space-y-8 min-h-screen bg-gray-50/50 dark:bg-slate-950 font-sans">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-gray-200 dark:border-slate-800 pb-6 bg-white dark:bg-slate-900 p-6 rounded-3xl shadow-sm gap-4">
          <div>
            <div className="flex items-center gap-2 text-indigo-600 mb-1">
                <LayoutGridIcon className="w-4 h-4" />
                <span className="text-[10px] font-black uppercase tracking-widest">Operations Workbench</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-gray-900 dark:text-white flex items-center gap-3">
                Operations Nexus
            </h1>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1 italic">Scan, Review, and Execute system-wide signals.</p>
          </div>
          
          <div className="flex w-full md:w-auto gap-2 overflow-x-auto pb-2 md:pb-0 scrollbar-hide">
             <button 
                onClick={() => setActiveTab('content')}
                className={`px-5 py-2.5 text-xs font-bold rounded-2xl transition-all flex items-center gap-2 shrink-0 ${activeTab === 'content' ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-200' : 'bg-white dark:bg-slate-800 text-gray-600 dark:text-slate-300 border border-gray-200 dark:border-slate-700 hover:bg-gray-50'}`}
             >
                <FileTextIcon className="w-4 h-4" />
                Content
                {contentApprovals.length > 0 && <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded-full text-[10px] font-black ml-1">{contentApprovals.length}</span>}
             </button>
             <button 
                onClick={() => setActiveTab('code')}
                className={`px-5 py-2.5 text-xs font-bold rounded-2xl transition-all flex items-center gap-2 shrink-0 ${activeTab === 'code' ? 'bg-amber-500 text-white shadow-xl shadow-amber-200' : 'bg-white dark:bg-slate-800 text-gray-600 dark:text-slate-300 border border-gray-200 dark:border-slate-700 hover:bg-gray-50'}`}
             >
                <DatabaseIcon className="w-4 h-4" />
                Dev Ops
                {codeProposals.length > 0 && <span className="bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded-full text-[10px] font-black ml-1">{codeProposals.length}</span>}
             </button>
             <button 
                onClick={() => setActiveTab('alerts')}
                className={`px-5 py-2.5 text-xs font-bold rounded-2xl transition-all flex items-center gap-2 shrink-0 ${activeTab === 'alerts' ? 'bg-red-600 text-white shadow-xl shadow-red-200' : 'bg-white dark:bg-slate-800 text-gray-600 dark:text-slate-300 border border-gray-200 dark:border-slate-700 hover:bg-gray-50'}`}
             >
                <TrendingUpIcon className="w-4 h-4" />
                Alerts
                {alerts.length > 0 && <span className="bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 px-2 py-0.5 rounded-full text-[10px] font-black ml-1">{alerts.length}</span>}
             </button>
             <button onClick={fetchData} className="p-2.5 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-2xl text-gray-500 hover:rotate-180 transition-transform duration-500">
                <RefreshCwIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
             </button>
          </div>
        </header>

        {loading && !contentApprovals.length && !codeProposals.length && !alerts.length ? (
            <div className="p-12 text-center text-gray-500 animate-pulse">Synchronizing with Nexus...</div>
        ) : (
            <div className="space-y-6">
                {/* --- CONTENT TAB --- */}
                {activeTab === 'content' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {contentApprovals.length === 0 ? (
                            <div className="col-span-full p-12 bg-white dark:bg-slate-900 rounded-3xl border border-dashed border-gray-300 dark:border-slate-800 text-center text-gray-500">
                                <div className="flex justify-center mb-4"><FileTextIcon className="w-12 h-12 text-gray-300 dark:text-slate-700" /></div>
                                No content pending review. Bob is quiet today.
                            </div>
                        ) : (
                            contentApprovals.map(post => (
                                <div key={post.id} className="bg-white dark:bg-slate-900 p-6 rounded-[2rem] border border-gray-200 dark:border-slate-800 shadow-sm hover:shadow-2xl transition-all flex flex-col gap-6 overflow-hidden group">
                                    <div className="flex flex-col gap-4">
                                        <div className="flex items-start justify-between gap-4">
                                            <h3 className="text-xl font-black text-gray-900 dark:text-white leading-tight line-clamp-2">{post.title}</h3>
                                            <Badge className="bg-amber-100 text-amber-800 shrink-0">Pending</Badge>
                                        </div>
                                        
                                        <div className="text-xs text-gray-500 flex flex-wrap items-center gap-x-4 gap-y-2 pb-4 border-b border-gray-100 dark:border-slate-800">
                                            <span className="flex items-center gap-1 font-bold"><UserIcon className="w-3 h-3 text-indigo-500" /> {post.authorName || 'Marketing'}</span>
                                            <span className="flex items-center gap-1 text-indigo-600 font-black uppercase tracking-tighter">
                                                <ShieldCheckIcon className="w-3 h-3" /> AI Integrity Score: {post.ai_score || 85}%
                                            </span>
                                        </div>

                                        {/* 所見即所得預覽 (WYSIWYG Preview) - Fully Unlocked for Review */}
                                        <div className={`relative bg-gray-50 dark:bg-slate-950 rounded-2xl p-5 border border-gray-100 dark:border-slate-800 transition-all duration-700 ease-in-out ${previewId === post.id ? 'h-auto opacity-100' : 'max-h-48 overflow-hidden'}`}>
                                            <div className={previewId === post.id ? 'opacity-100' : 'opacity-30 grayscale pointer-events-none'}>
                                                {(() => {
                                                    // Robust Markdown Image Scanning: Search for images anywhere in text, ignoring whitespace
                                                    const imgMatch = post.content?.match(/!\[.*?\]\(\s*(.*?)\s*\)/);
                                                    const displayImage = post.imageUrl || imgMatch?.[1];
                                                    
                                                    return displayImage && (
                                                        <div className="w-full aspect-video mb-6 overflow-hidden rounded-2xl border-2 border-white dark:border-slate-800 shadow-lg bg-slate-200 dark:bg-slate-800">
                                                            <img 
                                                                src={displayImage} 
                                                                alt="Article Cover" 
                                                                className="w-full h-full object-cover" 
                                                            />
                                                        </div>
                                                    );
                                                })()}
                                                <div className="prose prose-sm dark:prose-invert max-w-none text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
                                                    <Markdown>{post.content || ''}</Markdown>
                                                </div>
                                                {post.hashtags && (
                                                    <div className="flex flex-wrap gap-2 mt-8 pt-6 border-t dark:border-slate-800">
                                                        {post.hashtags.split(' ').map((tag, i) => (
                                                            <span key={i} className="text-[10px] font-black text-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 px-3 py-1 rounded-lg border border-indigo-100 dark:border-indigo-800/50">{tag}</span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                            
                                            {previewId !== post.id && (
                                                <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-t from-gray-50 dark:from-slate-950 via-gray-50/80 dark:via-slate-950/80 to-transparent pt-12">
                                                    <button 
                                                        onClick={() => setPreviewId(post.id)} 
                                                        className="px-6 py-3 bg-white dark:bg-slate-800 border dark:border-slate-700 rounded-full text-xs font-black shadow-xl flex items-center gap-2 hover:scale-110 active:scale-95 transition-all group-hover:bg-indigo-600 group-hover:text-white group-hover:border-indigo-600"
                                                    >
                                                        <EyeIcon className="w-4 h-4" /> Review Full Content
                                                    </button>
                                                </div>
                                            )}
                                            
                                            {previewId === post.id && (
                                                <button 
                                                    onClick={() => setPreviewId(null)} 
                                                    className="absolute top-4 right-4 p-2.5 bg-white/90 dark:bg-slate-800/90 backdrop-blur rounded-full shadow-lg border border-gray-100 dark:border-slate-700 active:scale-90 transition-transform"
                                                >
                                                    <XIcon className="w-5 h-5" />
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    {/* Tablet-Optimized Actions (Charlie) - Massive Targets */}
                                    <div className="grid grid-cols-2 gap-4 pt-2">
                                        <button 
                                            onClick={() => handleContentAction(post.id, 'reject')}
                                            className="py-5 text-sm text-red-600 border-2 border-red-100 dark:border-red-900/30 rounded-2xl hover:bg-red-50 dark:hover:bg-red-900/20 font-black flex items-center justify-center gap-2 active:scale-95 transition-all"
                                        >
                                            <XIcon className="w-5 h-5" /> Return
                                        </button>
                                        <button 
                                            onClick={() => handleContentAction(post.id, 'approve')}
                                            className="py-5 text-sm bg-indigo-600 text-white rounded-2xl hover:bg-indigo-700 font-black shadow-xl shadow-indigo-200 dark:shadow-indigo-900/20 flex items-center justify-center gap-2 active:scale-95 transition-all"
                                        >
                                            <CheckCircleIcon className="w-5 h-5" /> Publish
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}

                {/* --- CODE TAB --- */}
                {activeTab === 'code' && (
                    <div className="grid grid-cols-1 gap-4">
                        {codeProposals.length === 0 ? (
                            <div className="p-12 bg-white dark:bg-slate-900 rounded-3xl border border-dashed border-gray-300 dark:border-slate-800 text-center text-gray-500">
                                <div className="flex justify-center mb-4"><DatabaseIcon className="w-12 h-12 text-gray-300 dark:text-slate-700" /></div>
                                No pending code changes. System is stable.
                            </div>
                        ) : (
                            codeProposals.map(prop => (
                                <div key={prop.id} className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-gray-200 dark:border-slate-800 shadow-sm">
                                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                                        <div className="flex-1">
                                            <span className="text-[10px] font-black uppercase tracking-widest text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-3 py-1 rounded-full">
                                                {prop.type} Execution Proposal
                                            </span>
                                            <p className="mt-4 text-gray-900 dark:text-slate-200 font-medium font-mono text-sm bg-gray-50 dark:bg-slate-950 p-5 rounded-2xl border border-gray-100 dark:border-slate-800 leading-relaxed shadow-inner">
                                                {prop.request_payload?.description || 'No description provided.'}
                                            </p>
                                        </div>
                                        <div className="flex gap-3 w-full md:w-auto">
                                            <button 
                                                onClick={() => handleCodeAction(prop.id, 'reject')}
                                                className="flex-1 px-8 py-4 text-sm text-red-600 border border-red-200 dark:border-red-900/30 rounded-2xl font-black min-h-[52px] active:scale-95 transition-all"
                                            >
                                                Reject
                                            </button>
                                            <button 
                                                onClick={() => handleCodeAction(prop.id, 'approve')}
                                                className="flex-1 px-8 py-4 text-sm bg-amber-500 text-white rounded-2xl font-black shadow-lg shadow-amber-100 dark:shadow-amber-900/20 min-h-[52px] active:scale-95 transition-all"
                                            >
                                                Approve
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}

                {/* --- ALERTS TAB --- */}
                {activeTab === 'alerts' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {alerts.length === 0 ? (
                            <div className="col-span-full p-12 bg-white dark:bg-slate-900 rounded-3xl border border-dashed border-gray-300 dark:border-slate-800 text-center text-gray-500">
                                <div className="flex justify-center mb-4"><TrendingUpIcon className="w-12 h-12 text-gray-300 dark:text-slate-700" /></div>
                                No active business alerts.
                            </div>
                        ) : (
                            alerts.map(alert => (
                                <div key={alert.id} className={`p-6 rounded-[2rem] border-l-8 shadow-sm bg-white dark:bg-slate-900 flex flex-col justify-between gap-6 transition-all hover:shadow-md ${alert.level === 'ALERT' ? 'border-red-500' : 'border-blue-500'}`}>
                                    <div className="flex items-start gap-4">
                                        {alert.level === 'ALERT' ? <TrendingUpIcon className="w-6 h-6 text-red-500 mt-1" /> : <ShieldCheckIcon className="w-6 h-6 text-blue-500 mt-1" />}
                                        <div className="flex-1">
                                            <span className="text-lg text-gray-800 dark:text-white font-black block leading-tight">{alert.message}</span>
                                            
                                            {/* Alert Context Badges */}
                                            <div className="mt-4 flex flex-wrap gap-2">
                                                {alert.details?.enrichment_score && (
                                                    <span className="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-[10px] font-black px-2.5 py-1 rounded-lg border border-indigo-100 dark:border-indigo-800/50 uppercase tracking-tighter">
                                                        Quality: {alert.details.enrichment_score}%
                                                    </span>
                                                )}
                                                {alert.details?.days_stale && (
                                                    <span className="bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 text-[10px] font-black px-2.5 py-1 rounded-lg border border-orange-100 dark:border-orange-800/50 uppercase tracking-tighter">
                                                        {alert.details.days_stale} Days Idle
                                                    </span>
                                                )}
                                            </div>

                                            <span className="text-[10px] text-gray-400 font-mono mt-5 flex items-center gap-1 opacity-60">
                                                <ClockIcon className="w-3 h-3" />
                                                {new Date(alert.created_at).toLocaleString()}
                                            </span>
                                        </div>
                                    </div>
                                    {alert.level === 'ALERT' && (
                                        <button 
                                            onClick={() => handleDispatchTask(alert)}
                                            disabled={loading}
                                            className="w-full py-5 text-md bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-100 dark:border-red-900/30 rounded-2xl hover:bg-red-100 font-black transition-all active:scale-95 flex items-center justify-center gap-2 min-h-[56px] disabled:opacity-50 shadow-sm"
                                        >
                                            {loading ? <RefreshCwIcon className="animate-spin w-5 h-5" /> : <TrendingUpIcon className="w-5 h-5" />}
                                            ⚡ Dispatch Smart Task to Alice
                                        </button>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                )}
            </div>
        )}
        
        {/* REJECTION MODAL */}
        {rejectModalOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                <div className="bg-white dark:bg-slate-900 rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden border border-gray-200 dark:border-slate-800">
                    <div className="p-6 border-b border-gray-100 dark:border-slate-800 flex justify-between items-center bg-gray-50 dark:bg-slate-950">
                        <h3 className="text-lg font-black text-gray-900 dark:text-white flex items-center gap-2">
                            <XCircleIcon className="w-5 h-5 text-red-500" />
                            Return to Bob
                        </h3>
                        <button onClick={() => setRejectModalOpen(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                            <XIcon className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="p-6 space-y-4">
                        <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-xl border border-amber-100 dark:border-amber-900/30 text-xs text-amber-800 dark:text-amber-200 flex gap-2">
                             <SparklesIcon className="w-4 h-4 shrink-0 mt-0.5" />
                             <div>
                                <p className="font-bold mb-1">Coach, not Cop.</p>
                                Provide constructive feedback so Bob can improve the content.
                             </div>
                        </div>
                        
                        <div className="flex justify-end">
                            <button 
                                onClick={handleGenerateReason}
                                disabled={isGenerating}
                                className="text-xs font-black text-indigo-600 dark:text-indigo-400 flex items-center gap-1 hover:underline disabled:opacity-50"
                            >
                                <SparklesIcon className={`w-3 h-3 ${isGenerating ? 'animate-spin' : ''}`} />
                                {isGenerating ? 'Analyzing Draft...' : 'Generate with AI'}
                            </button>
                        </div>
                        
                        <textarea
                            className="w-full h-40 p-4 rounded-xl bg-gray-50 dark:bg-slate-950 border border-gray-200 dark:border-slate-800 focus:ring-2 focus:ring-red-500 focus:border-red-500 text-sm resize-none outline-none transition-all"
                            placeholder="Explain why this is being returned..."
                            value={rejectionReason}
                            onChange={(e) => setRejectionReason(e.target.value)}
                        />
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-slate-950 border-t border-gray-100 dark:border-slate-800 flex justify-end gap-3">
                        <button 
                            onClick={() => setRejectModalOpen(false)}
                            className="px-5 py-2.5 rounded-xl font-bold text-sm text-gray-600 hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-slate-800 transition-colors"
                        >
                            Cancel
                        </button>
                        <button 
                            onClick={handleConfirmReject}
                            disabled={!rejectionReason.trim()}
                            className="px-5 py-2.5 rounded-xl font-black text-sm bg-red-600 text-white hover:bg-red-700 shadow-lg shadow-red-200 dark:shadow-red-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            Confirm Return
                        </button>
                    </div>
                </div>
            </div>
        )}

      </div>
    </PermissionGuard>
  );
};

export default ApprovalsPage;