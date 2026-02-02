
import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { Project } from '../types.ts';
import { 
    ShieldCheckIcon, 
    CheckCircleIcon, 
    FileTextIcon, 
    DatabaseIcon, 
    RefreshCwIcon, 
    XIcon,
    TrendingUpIcon, // For Alert
    ClockIcon, // For History
    UserIcon, // Added missing
} from '../components/Icons';

const Badge = ({ children, className }: any) => (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${className}`}>
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
  authorName?: string;
  created_at?: string; 
  ai_score?: number;
}

interface AlertItem {
  id: string;
  type: 'ALERT' | 'INFO';
  content: string;
  created_at: string;
}

const ApprovalsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'content' | 'code' | 'alerts'>('content');
  const [codeProposals, setCodeProposals] = useState<ChangeProposal[]>([]);
  const [contentApprovals, setContentApprovals] = useState<BlogPost[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Execute all requests but handle them with care for robustness
      const [contentRes, codeRes, projectsRes] = await Promise.all([
        api.getPendingApprovals().catch(e => { console.warn("Content fetch failed", e); return { blogs: [] }; }),
        api.getPendingChanges().catch(e => { console.warn("Code fetch failed", e); return []; }),
        api.getProjects().catch(e => { console.warn("Projects fetch failed", e); return []; })
      ]);

      setContentApprovals(contentRes.blogs || []);
      setCodeProposals(codeRes || []);
      setProjects(projectsRes || []);

      // Fetch Alerts (Mock)
      setAlerts([
          { id: '1', type: 'ALERT', content: 'Sentinel: Alice (Field) has 3 high-value leads at risk.', created_at: new Date().toISOString() },
          { id: '2', type: 'INFO', content: 'Librarian: Weekly knowledge indexing complete.', created_at: new Date().toISOString() }
      ]);

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
    try {
      await api.processApproval('blog', id, action);
      alert(action === 'approve' ? 'Content Published!' : 'Returned to Draft');
      fetchData();
    } catch (err) {
      alert("Action failed");
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

  // Dispatch Task Logic
  const handleDispatchTask = async (alertItem: AlertItem) => {
      try {
          const targetProjectId = projects.length > 0 ? projects[0].id : 'default-project';
          
          await api.createTask({
              title: `Follow-up: ${alertItem.content}`,
              description: `Automated task generated from Sentinel Alert. Source: ${alertItem.id}`,
              status: 'todo' as any, 
              priority: 'high' as any,
              project_id: targetProjectId, 
              due_date: new Date(Date.now() + 86400000 * 3).toISOString()
          });
          
          alert(`Task dispatched to Field Team under project: ${projects[0]?.title || 'Default'}!`);
          setAlerts(prev => prev.filter(a => a.id !== alertItem.id));
      } catch (err) {
          alert("Failed to dispatch task");
          console.error(err);
      }
  };

  return (
    <PermissionGuard permission="user:manage:team"> 
      <div className="p-6 max-w-7xl mx-auto space-y-8 min-h-screen bg-gray-50">
        <header className="flex justify-between items-end border-b border-gray-200 pb-6 bg-white p-6 rounded-xl shadow-sm">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Command Center</h1>
            <p className="text-gray-500 mt-2">Oversee operations, approve content, and manage system changes.</p>
          </div>
          
          <div className="flex gap-2">
             <button 
                onClick={() => setActiveTab('content')}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-2 ${activeTab === 'content' ? 'bg-indigo-600 text-white shadow-md' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
             >
                <FileTextIcon className="w-4 h-4" />
                Content
                {contentApprovals.length > 0 && <span className="bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded text-xs font-bold ml-2">{contentApprovals.length}</span>}
             </button>
             <button 
                onClick={() => setActiveTab('code')}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-2 ${activeTab === 'code' ? 'bg-indigo-600 text-white shadow-md' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
             >
                <DatabaseIcon className="w-4 h-4" />
                Dev Ops
                {codeProposals.length > 0 && <span className="bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded text-xs font-bold ml-2">{codeProposals.length}</span>}
             </button>
             <button 
                onClick={() => setActiveTab('alerts')}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all flex items-center gap-2 ${activeTab === 'alerts' ? 'bg-indigo-600 text-white shadow-md' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
             >
                <TrendingUpIcon className="w-4 h-4" />
                Alerts
                {alerts.length > 0 && <span className="bg-red-100 text-red-700 px-1.5 py-0.5 rounded text-xs font-bold ml-2">{alerts.length}</span>}
             </button>
             <button onClick={fetchData} className="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-500">
                <RefreshCwIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
             </button>
          </div>
        </header>

        {loading && !contentApprovals.length && !codeProposals.length ? (
            <div className="p-12 text-center text-gray-500">Loading Command Center...</div>
        ) : (
            <div className="space-y-6">
                {/* --- CONTENT TAB --- */}
                {activeTab === 'content' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {contentApprovals.length === 0 ? (
                            <div className="col-span-full p-12 bg-white rounded-xl border border-dashed border-gray-300 text-center text-gray-500">
                                <div className="flex justify-center mb-4"><FileTextIcon className="w-12 h-12 text-gray-300" /></div>
                                No content pending review.
                            </div>
                        ) : (
                            contentApprovals.map(post => (
                                <div key={post.id} className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between gap-6">
                                    <div>
                                        <div className="flex items-center gap-3 mb-3">
                                            <h3 className="text-xl font-bold text-gray-900 leading-tight">{post.title}</h3>
                                            <Badge className="bg-amber-100 text-amber-800 shrink-0">Pending</Badge>
                                        </div>
                                        <div className="text-sm text-gray-500 flex flex-wrap items-center gap-x-4 gap-y-2">
                                            <span className="flex items-center gap-1"><UserIcon className="w-4 h-4" /> {post.authorName || 'Marketing'}</span>
                                            <span className="flex items-center gap-1 text-indigo-600 font-bold">
                                                <ShieldCheckIcon className="w-4 h-4" /> AI Score: 85/100
                                            </span>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4 pt-2">
                                        <button 
                                            onClick={() => handleContentAction(post.id, 'reject')}
                                            className="px-4 py-4 text-red-600 border border-red-200 rounded-xl hover:bg-red-50 font-bold flex items-center justify-center gap-2 min-h-[48px] active:scale-95 transition-transform"
                                        >
                                            <XIcon className="w-5 h-5" /> Return
                                        </button>
                                        <button 
                                            onClick={() => handleContentAction(post.id, 'approve')}
                                            className="px-4 py-4 bg-green-600 text-white rounded-xl hover:bg-green-700 font-bold shadow-lg shadow-green-100 flex items-center justify-center gap-2 min-h-[48px] active:scale-95 transition-transform"
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
                            <div className="p-12 bg-white rounded-xl border border-dashed border-gray-300 text-center text-gray-500">
                                <div className="flex justify-center mb-4"><DatabaseIcon className="w-12 h-12 text-gray-300" /></div>
                                No pending code changes.
                            </div>
                        ) : (
                            codeProposals.map(prop => (
                                <div key={prop.id} className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
                                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                                        <div className="flex-1">
                                            <span className="text-xs font-bold uppercase tracking-widest text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
                                                {prop.type}
                                            </span>
                                            <p className="mt-3 text-gray-900 font-medium font-mono text-sm bg-gray-50 p-4 rounded-xl border border-gray-100 leading-relaxed">
                                                {prop.request_payload.description}
                                            </p>
                                        </div>
                                        <div className="flex gap-3 w-full md:w-auto">
                                            <button 
                                                onClick={() => handleCodeAction(prop.id, 'reject')}
                                                className="flex-1 px-6 py-3 text-sm text-red-600 border border-red-200 rounded-xl font-bold min-h-[44px]"
                                            >
                                                Reject
                                            </button>
                                            <button 
                                                onClick={() => handleCodeAction(prop.id, 'approve')}
                                                className="flex-1 px-6 py-3 text-sm bg-indigo-600 text-white rounded-xl font-bold shadow-md min-h-[44px]"
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
                        {alerts.map(alert => (
                            <div key={alert.id} className={`p-6 rounded-2xl border-l-8 shadow-sm bg-white flex flex-col justify-between gap-6 ${alert.type === 'ALERT' ? 'border-red-500' : 'border-blue-500'}`}>
                                <div className="flex items-start gap-4">
                                    {alert.type === 'ALERT' ? <TrendingUpIcon className="w-6 h-6 text-red-500 mt-1" /> : <ShieldCheckIcon className="w-6 h-6 text-blue-500 mt-1" />}
                                    <div>
                                        <span className="text-lg text-gray-800 font-bold block leading-tight">{alert.content}</span>
                                        <span className="text-xs text-gray-400 font-mono mt-2 flex items-center gap-1">
                                            <ClockIcon className="w-3 h-3" />
                                            {new Date(alert.created_at).toLocaleTimeString()}
                                        </span>
                                    </div>
                                </div>
                                {alert.type === 'ALERT' && (
                                    <button 
                                        onClick={() => handleDispatchTask(alert)}
                                        className="w-full py-4 text-md bg-red-50 text-red-700 border border-red-200 rounded-xl hover:bg-red-100 font-black transition-all active:scale-95 flex items-center justify-center gap-2 min-h-[52px]"
                                    >
                                        ⚡ Dispatch Task to Alice
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        )}
      </div>
    </PermissionGuard>
  );
};

export default ApprovalsPage;
