import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api.ts';
import { DocumentVersion, BlogPost } from '../types.ts';
import { PlusIcon, XIcon, RefreshCwIcon, ShieldCheckIcon, SearchIcon, SparklesIcon } from '../components/Icons.tsx';
import { useAuth } from '../hooks/useAuth.tsx';

import { IdentityMatrix } from '../features/admin/components/IdentityMatrix.tsx';
import { SystemHealthDashboard } from '../features/admin/components/SystemHealthDashboard.tsx';
import { PromptManagement } from '../features/admin/components/PromptManagement.tsx';


const AdminPage: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const role = user?.role?.toLowerCase();
  const isOnlyManager = !isAdmin && (role === 'manager');
  const canManageUsers = isAdmin || role === 'manager'; // Allow Managers to see RBAC
  
  // Default tab logic: If manager, default to 'users' if available, or 'settings'
  const [activeTab, setActiveTab] = useState(isOnlyManager ? 'users' : 'health');

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 bg-background text-foreground">
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-3">{isOnlyManager ? 'Manager Control Center' : 'Admin Control Center'}</h1>
        <p className="text-muted-foreground">
          {isOnlyManager 
            ? 'Configure team permissions, workflows, and operational parameters.'
            : 'System-wide configuration and personnel management for L1 Administrators.'}
        </p>
      </header>

      <div className="border-b border-border mb-6">
        <nav className="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
          <TabButton title="System Health" isActive={activeTab === 'health'} onClick={() => setActiveTab('health')} />
          {canManageUsers && <TabButton title="User Management" isActive={activeTab === 'users'} onClick={() => setActiveTab('users')} />}
          <TabButton title="System Settings" isActive={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
          <TabButton title="Data Extraction" isActive={activeTab === 'extraction'} onClick={() => setActiveTab('extraction')} />
          <TabButton title="System Prompts" isActive={activeTab === 'prompts'} onClick={() => setActiveTab('prompts')} />
          {!isOnlyManager && <TabButton title="Blog Management" isActive={activeTab === 'blog'} onClick={() => setActiveTab('blog')} />}
          {!isOnlyManager && <TabButton title="Document Versions" isActive={activeTab === 'versions'} onClick={() => setActiveTab('versions')} />}
        </nav>
      </div>

      <div className="flex-1 overflow-auto">
        {activeTab === 'health' && <SystemHealthDashboard />}
        {activeTab === 'users' && canManageUsers && <IdentityMatrix />}
        {activeTab === 'settings' && <SystemSettings />}
        {activeTab === 'extraction' && (
          <div className="space-y-8">
            <CrawlerEndpointConfig />
            <CrawlerTargetManager />
            <ExtractionManager />
          </div>
        )}
        {activeTab === 'prompts' && <PromptManagement isManagerMode={isOnlyManager} />}
        {activeTab === 'blog' && !isOnlyManager && <BlogManagement />}
        {activeTab === 'versions' && !isOnlyManager && <DocumentVersionsLog />}
      </div>
    </div>
  );
};

const TabButton: React.FC<{ title: string; isActive: boolean; onClick: () => void }> = ({ title, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={`${
      isActive
        ? 'border-indigo-500 text-indigo-500' // Updated to match Admin Brand (Violet/Indigo)
        : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-all`}
  >
    {title}
  </button>
);

// PromptManagement extracted to src/features/admin/components/PromptManagement.tsx


const DocumentVersionsLog: React.FC = () => {
    const [versions, setVersions] = useState<DocumentVersion[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        api.getDocumentVersions()
            .then(setVersions)
            .catch(err => alert(`Failed to load document versions: ${err.message}`))
            .finally(() => setLoading(false));
    }, []);

    // GAP 3: Robust Multi-dimensional Filtering Logic
    const filteredVersions = React.useMemo(() => {
        const query = searchTerm.toLowerCase().trim();
        if (!query) return versions;
        
        return versions.filter(v => 
            v.created_by?.toLowerCase().includes(query) ||
            v.field_name?.toLowerCase().includes(query) ||
            v.change_summary?.toLowerCase().includes(query) ||
            v.change_type?.toLowerCase().includes(query)
        );
    }, [versions, searchTerm]);
    
    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm flex flex-col h-full max-h-[calc(100vh-250px)]">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <div>
                    <h2 className="text-xl font-bold">Document Version Audit Trail</h2>
                    <p className="text-xs text-muted-foreground italic">Track every configuration change across the system.</p>
                </div>
                
                {/* GAP 3: Search Interface */}
                <div className="relative w-full md:w-64">
                    <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input 
                        type="text"
                        placeholder="Search logs..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 bg-muted/50 border border-border rounded-xl text-sm focus:ring-2 ring-primary/30 outline-none transition-all"
                    />
                </div>
            </div>

             <div className="overflow-x-auto overflow-y-auto -mx-6 flex-1 min-h-0">
                <table className="min-w-full divide-y divide-border relative">
                    <thead className="bg-muted/50 sticky top-0 z-10">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Timestamp</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Changed By</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Type</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Field / Version</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Summary</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-card">
                        {loading ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center italic text-muted-foreground">
                                    <RefreshCwIcon className="animate-spin w-6 h-6 mx-auto mb-2 opacity-20" />
                                    Loading audit logs...
                                </td>
                            </tr>
                        ) : filteredVersions.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground italic">
                                    {searchTerm ? `No logs matching "${searchTerm}"` : 'No version history found.'}
                                </td>
                            </tr>
                        ) : (
                            filteredVersions.map(log => (
                                <tr key={log.id} className="hover:bg-muted/30 transition-colors group">
                                    <td className="px-6 py-4 whitespace-nowrap text-[10px] text-muted-foreground font-mono">
                                        {new Date(log.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-bold flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
                                            {log.created_by}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-0.5 text-[9px] font-black uppercase rounded border ${
                                            log.change_type === 'CREATE' ? 'bg-green-50 text-green-700 border-green-200' : 
                                            log.change_type === 'DELETE' ? 'bg-red-50 text-red-700 border-red-200' :
                                            'bg-indigo-50 text-indigo-700 border-indigo-200'
                                        }`}>{log.change_type}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-xs">
                                        <span className="font-mono bg-muted px-1 rounded">{log.field_name}</span>
                                        <span className="ml-2 text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">REV-{log.version_number}</span>
                                    </td>
                                    <td className="px-6 py-4 text-xs text-slate-600 dark:text-slate-400 max-w-xs truncate font-medium" title={log.change_summary || ''}>
                                        {log.change_summary || 'N/A'}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const BlogManagement: React.FC = () => {
    const [posts, setPosts] = useState<BlogPost[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        api.getBlogPosts().then(setPosts).catch(err => alert(`Failed to load blog posts: ${err.message}`));
    }, []);

    const handleDeletePost = async (postId: string) => {
        if (window.confirm('Are you sure you want to delete this post?')) {
            try {
                await api.deleteBlogPost(postId);
                setPosts(prev => prev.filter(p => p.id !== postId));
                alert('Post deleted successfully!');
            } catch (error: any) {
                alert(`Failed to delete post: ${error.message}`);
            }
        }
    };

    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">Content Assets</h2>
                <button onClick={() => navigate('/admin/editor/new')} className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 font-bold transition-all shadow-sm">
                    <PlusIcon className="w-5 h-5 mr-2" />
                    NEW POST
                </button>
            </div>
             <div className="overflow-x-auto -mx-6">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Title</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Author</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Date</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-card">
                        {posts.map(post => (
                            <tr key={post.id} className="hover:bg-muted/30 transition-colors cursor-pointer" onClick={() => navigate(`/admin/editor/${post.id}`)}>
                                <td className="px-6 py-4 whitespace-nowrap font-bold text-sm">{post.title}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm">{post.authorName}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded border ${post.status === 'published' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-amber-50 text-amber-700 border-amber-200'}`}>{post.status}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-xs text-muted-foreground">{new Date(post.publishDate).toLocaleDateString()}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button onClick={(e) => { e.stopPropagation(); navigate(`/admin/editor/${post.id}`); }} className="text-primary hover:text-primary/90 font-bold transition-colors">Edit</button>
                                    <button onClick={(e) => { e.stopPropagation(); handleDeletePost(post.id); }} className="text-destructive hover:text-destructive/90 font-bold ml-4 transition-colors">Delete</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};



// --- NEW COMPONENT: SYSTEM SETTINGS ---
const SystemSettings: React.FC = () => {
    const [settings, setSettings] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState<string | null>(null);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        setLoading(true);
        try {
            // Fetch all necessary configuration categories
            const crawlerData = await api.getSystemSettings('crawler_rbac');
            const diagnosticsData = await api.getSystemSettings('diagnostics');
            const scoringData = await api.getSystemSettings('lead_scoring');
            const systemData = await api.getSystemSettings('system'); // SCHEDULER frequency settings
            setSettings([...crawlerData, ...diagnosticsData, ...scoringData, ...systemData]);
        } catch (err: any) {
            alert("Failed to load settings: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdate = async (key: string, newValue: string) => {
        setIsSaving(key);
        try {
            await api.updateSystemSetting(key, { value: newValue });
            setSettings(prev => prev.map(s => s.key === key ? { ...s, value: newValue } : s));
        } catch (err: any) {
            alert("Update failed: " + err.message);
        } finally {
            setIsSaving(null);
        }
    };

    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-primary" /></div>;

    const roles = ['SALES', 'MARKETING', 'MANAGER', 'ADMIN'];
    const logLevelSetting = settings.find(s => s.key === 'system.log_level');
    const scoringSettings = settings.filter(s => s.category === 'lead_scoring');
    const schedulerSettings = settings.filter(s => s.category === 'system' && s.key.startsWith('SCHEDULER_'));

    return (
        <div className="space-y-6 pb-20">
            {/* NEW: Scheduler Frequency Configuration (Clockwork) */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-orange-500">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-orange-600">
                    <RefreshCwIcon className="w-5 h-5" />
                    Clockwork: Agent Biological Frequencies (Heartbeat)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {schedulerSettings.map(setting => {
                        // Clear mapping to persona-aligned titles
                        const displayTitle = setting.key === 'SCHEDULER_PROBE_INTERVAL_MINS' ? 'System Heartbeat (Probe)' :
                                           setting.key === 'SCHEDULER_PATROL_INTERVAL_MINS' ? 'Log Patrol (Auto-Repair)' :
                                           setting.key === 'SCHEDULER_SENTINEL_INTERVAL_HOURS' ? 'Sentinel (Business Risks)' :
                                           setting.key.replace(/SCHEDULER_|_MINS|_HOURS/g, '').replace(/_/g, ' ');

                        return (
                            <div key={setting.key} className="p-4 bg-muted/20 rounded-xl border border-border flex flex-col justify-between gap-3 group hover:border-orange-500/30 transition-all">
                                <div>
                                    <div className="font-bold text-[10px] uppercase tracking-widest text-orange-600/70">{displayTitle}</div>
                                    <p className="text-[10px] text-muted-foreground mt-1 leading-tight">{setting.description}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="relative flex-1">
                                        <input 
                                            type="number" 
                                            defaultValue={setting.value}
                                            onBlur={(e) => handleUpdate(setting.key, e.target.value)}
                                            className="w-full p-2 bg-background border border-border rounded-lg text-sm font-bold text-center outline-none focus:ring-2 ring-orange-500/50 transition-all"
                                        />
                                        {isSaving === setting.key && (
                                            <div className="absolute -top-1 -right-1">
                                                <RefreshCwIcon className="animate-spin w-3 h-3 text-orange-600" />
                                            </div>
                                        )}
                                    </div>
                                    <span className="text-[10px] font-bold text-muted-foreground uppercase">{setting.key.includes('MINS') ? 'Mins' : 'Hrs'}</span>
                                </div>
                            </div>
                        );
                    })}
                    {schedulerSettings.length === 0 && (
                        <div className="col-span-3 p-4 text-center text-muted-foreground italic text-xs">
                            No scheduler settings found in database.
                        </div>
                    )}
                </div>
            </div>

            {/* NEW: RAG Strategy Configuration (Google Gemini) - Redirect to SSOT */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-purple-500">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-purple-600">
                    <SparklesIcon className="w-5 h-5" />
                    RAG Strategy Configuration
                </h3>
                <div className="p-6 bg-purple-50/50 dark:bg-purple-900/10 rounded-xl border border-purple-100 dark:border-purple-900 text-center">
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-4">
                        Advanced RAG parameters (Chunking, Embedding Models, Retrieval Hooks) have been migrated to the dedicated Operational Control Center.
                    </p>
                    <a 
                        href="http://localhost:3737" 
                        target="_blank" 
                        rel="noreferrer"
                        className="inline-flex items-center px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg transition-colors shadow-sm"
                    >
                        Open RAG Control Center (Port 3737)
                    </a>
                    <p className="text-xs text-muted-foreground mt-4 italic">
                        This ensures a Single Source of Truth (SSOT) for all deep system configurations.
                    </p>
                </div>
            </div>

            {/* NEW: Lead Scoring Weights (GAP-024 Optimization) */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-indigo-600">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h3 className="text-lg font-bold flex items-center gap-2 text-indigo-600">
                            <ShieldCheckIcon className="w-5 h-5" />
                            Lead Scoring Weights
                        </h3>
                        <p className="text-xs text-muted-foreground">Adjust Alice's Lead Enrichment scoring logic in real-time. Changes apply to the next enrichment loop.</p>
                    </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {scoringSettings.map(setting => (
                        <div key={setting.key} className="p-4 bg-muted/20 rounded-xl border border-border flex items-center justify-between gap-4 group hover:border-indigo-500/30 transition-all">
                            <div className="flex-1">
                                <div className="font-bold text-[10px] uppercase tracking-widest text-indigo-600/70">{setting.key.replace(/SCORING_/g, '').replace(/_/g, ' ')}</div>
                                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 leading-tight mt-1">{setting.description}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="relative">
                                    <input 
                                        type="number" 
                                        defaultValue={setting.value}
                                        onBlur={(e) => handleUpdate(setting.key, e.target.value)}
                                        className="w-16 p-2 bg-background border border-border rounded-lg text-sm font-bold text-center outline-none focus:ring-2 ring-indigo-500/50 transition-all"
                                    />
                                    {isSaving === setting.key && (
                                        <div className="absolute -top-1 -right-1">
                                            <RefreshCwIcon className="animate-spin w-3 h-3 text-indigo-600" />
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                    {scoringSettings.length === 0 && (
                        <div className="col-span-2 p-8 text-center border-2 border-dashed border-border rounded-xl text-muted-foreground italic text-sm">
                            No scoring rules found in database. Execute migration 038 to seed defaults.
                        </div>
                    )}
                </div>
            </div>

            {/* NEW: Diagnostics & Log Level Control */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-amber-500">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-amber-600">
                    <RefreshCwIcon className="w-5 h-5" />
                    Server Diagnostics
                </h3>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 bg-muted/20 rounded-xl border border-border">
                    <div className="flex-1">
                        <div className="font-bold text-sm">Backend Access Log Level</div>
                        <p className="text-xs text-muted-foreground">{logLevelSetting?.description || '控制 API 存取日誌的詳細程度'}</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <select 
                            value={logLevelSetting?.value || 'WARNING'}
                            onChange={(e) => handleUpdate('system.log_level', e.target.value)}
                            className="bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono outline-none focus:ring-2 ring-primary/50"
                        >
                            <option value="DEBUG">DEBUG (Detailed)</option>
                            <option value="INFO">INFO (Normal)</option>
                            <option value="WARNING">WARNING (Recommended)</option>
                            <option value="ERROR">ERROR (Critical Only)</option>
                        </select>
                        {isSaving === 'system.log_level' && <RefreshCwIcon className="animate-spin w-4 h-4 text-primary" />}
                    </div>
                </div>
            </div>

            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <RefreshCwIcon className="w-5 h-5 text-indigo-500" />
                    Crawler RBAC Limits
                </h3>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-border">
                        <thead>
                            <tr className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                                <th className="px-4 py-2 text-left">Role</th>
                                <th className="px-4 py-2 text-left">Max Depth</th>
                                <th className="px-4 py-2 text-left">Concurrency</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {roles.map(role => {
                                const depthKey = `CRAWL_MAX_DEPTH_${role}`;
                                const concurrentKey = `CRAWL_CONCURRENT_MAX_${role}`;
                                const depthSetting = settings.find(s => s.key === depthKey);
                                const concurrentSetting = settings.find(s => s.key === concurrentKey);

                                return (
                                    <tr key={role} className="text-sm">
                                        <td className="px-4 py-3 font-medium">{role}</td>
                                        <td className="px-4 py-3">
                                            <input 
                                                type="number" 
                                                defaultValue={depthSetting?.value || 0}
                                                onBlur={(e) => handleUpdate(depthKey, e.target.value)}
                                                className="w-20 p-1 bg-background border border-border rounded focus:ring-1 ring-primary outline-none"
                                            />
                                            {isSaving === depthKey && <RefreshCwIcon className="inline animate-spin w-3 h-3 ml-2 text-primary" />}
                                        </td>
                                        <td className="px-4 py-3">
                                            <input 
                                                type="number" 
                                                defaultValue={concurrentSetting?.value || 0}
                                                onBlur={(e) => handleUpdate(concurrentKey, e.target.value)}
                                                className="w-20 p-1 bg-background border border-border rounded focus:ring-1 ring-primary outline-none"
                                            />
                                            {isSaving === concurrentKey && <RefreshCwIcon className="inline animate-spin w-3 h-3 ml-2 text-primary" />}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <ShieldCheckIcon className="w-5 h-5 text-indigo-500" />
                    Global Whitelist Domains
                </h3>
                {settings.find(s => s.key === 'CRAWL_ALLOWED_DOMAINS_RESTRICTED') && (
                    <div className="space-y-2">
                        <textarea 
                            defaultValue={settings.find(s => s.key === 'CRAWL_ALLOWED_DOMAINS_RESTRICTED')?.value}
                            onBlur={(e) => handleUpdate('CRAWL_ALLOWED_DOMAINS_RESTRICTED', e.target.value)}
                            className="w-full p-3 bg-background border border-border rounded-xl font-mono text-xs focus:ring-2 ring-primary outline-none h-24"
                            placeholder="comma, separated, domains.com"
                        />
                        <p className="text-[10px] text-muted-foreground italic">Changes are saved automatically on blur. These domains apply to all non-admin users.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

// --- NEW COMPONENT: EXTRACTION MANAGER (GAP-018) ---
const ExtractionManager: React.FC = () => {
    const [schemas, setSchemas] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [analyzeUrl, setAnalyzeUrl] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [suggestions, setSuggestions] = useState<any>(null);
    const [newSchemaName, setNewSchemaName] = useState('');
    const [newDomainPattern, setNewDomainPattern] = useState('');

    useEffect(() => {
        fetchSchemas();
    }, []);

    const fetchSchemas = async () => {
        setLoading(true);
        try {
            const data = await api.getExtractionSchemas();
            setSchemas(data);
        } catch (err: any) {
            alert("Failed to load schemas: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAnalyze = async () => {
        if (!analyzeUrl) return;
        setIsAnalyzing(true);
        setSuggestions(null);
        try {
            const result = await api.analyzeExtractionUrl(analyzeUrl);
            setSuggestions(result);
            
            // Auto-fill some defaults based on URL
            const url = new URL(analyzeUrl);
            setNewDomainPattern(`${url.hostname}${url.pathname.split('/').slice(0, 3).join('/')}/*`);
        } catch (err: any) {
            alert("Analysis failed: " + err.message);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleSaveSchema = async () => {
        if (!newSchemaName || !newDomainPattern || !suggestions) return;
        
        try {
            await api.createExtractionSchema({
                name: newSchemaName,
                domain_pattern: newDomainPattern,
                schema_definition: suggestions,
                description: `Auto-generated for ${newDomainPattern}`
            });
            alert("Schema saved successfully!");
            fetchSchemas();
            setSuggestions(null);
            setAnalyzeUrl('');
        } catch (err: any) {
            alert("Save failed: " + err.message);
        }
    };

    const handleDeleteSchema = async (id: string) => {
        if (!window.confirm("Delete this extraction template?")) return;
        try {
            await api.deleteExtractionSchema(id);
            fetchSchemas();
        } catch (err: any) {
            alert("Delete failed: " + err.message);
        }
    };

    const handleRunNow = async (schemaId: string) => {
        const url = prompt("Enter target URL to extract data from:");
        if (!url) return;
        try {
            const res = await api.runExtraction(url, schemaId);
            alert(res.message);
        } catch (err: any) {
            alert("Execution failed: " + err.message);
        }
    };

    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-primary" /></div>;

    return (
        <div className="space-y-8">
            {/* New Schema / Analyze Tool */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <RefreshCwIcon className="w-5 h-5 text-indigo-500" />
                    New Extraction Discovery (Powered by DevBot)
                </h3>
                <p className="text-sm text-muted-foreground mb-4">Paste a sample URL to let DevBot discover its structure and suggest data fields.</p>
                <div className="flex gap-2 mb-6">
                    <input 
                        type="url" 
                        value={analyzeUrl}
                        onChange={(e) => setAnalyzeUrl(e.target.value)}
                        placeholder="https://www.104.com.tw/job/..."
                        className="flex-1 p-2 bg-background border border-border rounded-lg outline-none focus:ring-2 ring-primary/50 transition-all"
                    />
                    <button 
                        onClick={handleAnalyze}
                        disabled={isAnalyzing || !analyzeUrl}
                        className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 transition-all"
                    >
                        {isAnalyzing ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <ShieldCheckIcon className="w-4 h-4" />}
                        ANALYZE STRUCTURE
                    </button>
                </div>

                {suggestions && (
                    <div className="mt-6 p-4 bg-muted/30 rounded-xl border border-dashed border-border animate-in slide-in-from-top-2 duration-300">
                        <div className="flex justify-between items-start mb-4">
                            <h4 className="font-bold text-indigo-500">Suggested Fields Found</h4>
                            <div className="flex gap-2">
                                <input 
                                    placeholder="Template Name (e.g. 104 Job Detail)" 
                                    value={newSchemaName}
                                    onChange={(e) => setNewSchemaName(e.target.value)}
                                    className="p-1 text-sm bg-background border border-border rounded"
                                />
                                <input 
                                    placeholder="Domain Pattern" 
                                    value={newDomainPattern}
                                    onChange={(e) => setNewDomainPattern(e.target.value)}
                                    className="p-1 text-sm bg-background border border-border rounded w-48"
                                />
                                <button 
                                    onClick={handleSaveSchema}
                                    className="px-3 py-1 bg-green-600 text-white text-xs font-bold rounded hover:bg-green-700"
                                >
                                    SAVE TEMPLATE
                                </button>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {suggestions.fields?.map((field: any, idx: number) => (
                                <div key={idx} className="p-3 bg-card border border-border rounded-lg shadow-sm">
                                    <div className="flex justify-between">
                                        <span className="font-bold text-xs uppercase tracking-wider">{field.name}</span>
                                        <span className="text-[10px] bg-muted px-1 rounded">{field.type}</span>
                                    </div>
                                    <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">{field.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Existing Schemas List */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4">Saved Extraction Templates</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {schemas.map(s => (
                        <div key={s.id} className="p-4 border border-border rounded-xl bg-muted/10 hover:bg-muted/20 transition-all group relative">
                            <button 
                                onClick={() => handleDeleteSchema(s.id)}
                                className="absolute top-2 right-2 p-1 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-all"
                            >
                                <XIcon className="w-4 h-4" />
                            </button>
                            <div className="font-bold text-sm mb-1">{s.name}</div>
                            <code className="text-[10px] bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 px-1 rounded">{s.domain_pattern}</code>
                            <div className="mt-3 flex flex-wrap gap-1">
                                {s.schema_definition?.fields?.slice(0, 5).map((f: any, idx: number) => (
                                    <span key={idx} className="text-[9px] bg-background border border-border px-1.5 py-0.5 rounded-full">{f.name}</span>
                                ))}
                                {s.schema_definition?.fields?.length > 5 && <span className="text-[9px] text-muted-foreground italic">+{s.schema_definition.fields.length - 5} more</span>}
                            </div>
                            <div className="mt-4 pt-3 border-t border-border flex justify-end">
                                <button 
                                    onClick={() => handleRunNow(s.id)}
                                    className="text-[10px] font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                                >
                                    <RefreshCwIcon className="w-3 h-3" />
                                    RUN EXTRACTION NOW
                                </button>
                            </div>
                        </div>
                    ))}
                    {schemas.length === 0 && <div className="col-span-2 text-center py-12 text-muted-foreground italic">No templates defined yet. Use the tool above to discover and save your first extraction schema.</div>}
                </div>
            </div>
        </div>
    );
};

// --- NEW COMPONENT: CRAWLER ENDPOINT CONFIGURATION ---
const CrawlerEndpointConfig: React.FC = () => {
    const [settings, setSettings] = useState<any[]>([]);
    const [isSaving, setIsSaving] = useState<string | null>(null);

    useEffect(() => {
        api.getSystemSettings('crawler_config').then(setSettings).catch(console.error);
    }, []);

    const handleUpdate = async (key: string, newValue: string) => {
        setIsSaving(key);
        try {
            await api.updateSystemSetting(key, { value: newValue });
            setSettings(prev => prev.map(s => s.key === key ? { ...s, value: newValue } : s));
        } catch (err: any) {
            alert("Update failed: " + err.message);
        } finally {
            setIsSaving(null);
        }
    };

    if (settings.length === 0) return null;

    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-blue-500">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-blue-600">
                <SearchIcon className="w-5 h-5" />
                Crawler Endpoint Configuration (104.com.tw)
            </h3>
            <div className="space-y-4">
                {settings.map(setting => (
                    <div key={setting.key} className="p-4 bg-muted/20 rounded-xl border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="flex-1">
                            <div className="font-bold text-xs uppercase tracking-widest text-blue-600/70">{setting.key.replace(/CRAWLER_104_/g, '').replace(/_/g, ' ')}</div>
                            <p className="text-[10px] text-muted-foreground mt-0.5">{setting.description}</p>
                        </div>
                        <div className="flex items-center gap-3 w-full md:w-2/3">
                            <input 
                                type="text" 
                                defaultValue={setting.value}
                                onBlur={(e) => handleUpdate(setting.key, e.target.value)}
                                className="flex-1 p-2 bg-background border border-border rounded-lg text-xs font-mono outline-none focus:ring-2 ring-blue-500/50 transition-all"
                            />
                            {isSaving === setting.key && <RefreshCwIcon className="animate-spin w-4 h-4 text-blue-600" />}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

// --- NEW COMPONENT: CRAWLER TARGET MANAGER (GAP-024) ---
const CrawlerTargetManager: React.FC = () => {
    const [targets, setTargets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [newUrl, setNewUrl] = useState('');
    const [newDepth, setNewDepth] = useState(2);
    const [newDesc, setNewDesc] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        fetchTargets();
    }, []);

    const fetchTargets = async () => {
        setLoading(true);
        try {
            const data = await api.getCrawlerTargets();
            setTargets(data);
        } catch (err: any) {
            console.error("Failed to load targets:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!newUrl) return;
        setIsSaving(true);
        try {
            await api.createCrawlerTarget({
                target_url: newUrl,
                max_depth: newDepth,
                description: newDesc
            });
            setNewUrl('');
            setNewDesc('');
            setNewDepth(2);
            fetchTargets();
        } catch (err: any) {
            alert("Save failed: " + err.message);
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm("Delete this crawler target? Tasks relying on it may fail.")) return;
        try {
            await api.deleteCrawlerTarget(id);
            fetchTargets();
        } catch (err: any) {
            alert("Delete failed: " + err.message);
        }
    };

    if (loading) return <div className="flex justify-center p-6"><RefreshCwIcon className="animate-spin w-6 h-6 text-primary" /></div>;

    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-green-500">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-green-600">
                <ShieldCheckIcon className="w-5 h-5" />
                Knowledge Base Targets (Crawler)
            </h3>
            <p className="text-sm text-muted-foreground mb-6">
                Define the allowed root URLs that Librarian is permitted to crawl during periodic scheduled tasks.
                These act as dynamic whitelists and starting points.
            </p>

            <div className="flex flex-col md:flex-row gap-4 mb-8">
                <input 
                    type="url" 
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                    placeholder="e.g. https://wlb.mol.gov.tw/Page/index.aspx"
                    className="flex-[2] p-2 bg-background border border-border rounded-lg outline-none focus:ring-2 ring-green-500/50 transition-all font-mono text-sm"
                />
                <input 
                    type="text" 
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    placeholder="Description (Optional)"
                    className="flex-1 p-2 bg-background border border-border rounded-lg outline-none focus:ring-2 ring-green-500/50 transition-all text-sm"
                />
                <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-muted-foreground">Depth:</span>
                    <input 
                        type="number" 
                        min="1" max="5"
                        value={newDepth}
                        onChange={(e) => setNewDepth(parseInt(e.target.value) || 2)}
                        className="w-16 p-2 bg-background border border-border rounded-lg text-sm text-center outline-none focus:ring-2 ring-green-500/50 transition-all"
                    />
                </div>
                <button 
                    onClick={handleSave}
                    disabled={isSaving || !newUrl}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 disabled:opacity-50 flex items-center gap-2 transition-all whitespace-nowrap"
                >
                    {isSaving ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <PlusIcon className="w-4 h-4" />}
                    ADD TARGET
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border">
                    <thead>
                        <tr className="text-xs font-bold text-muted-foreground uppercase tracking-wider bg-muted/30">
                            <th className="px-4 py-3 text-left w-12">Status</th>
                            <th className="px-4 py-3 text-left">Target URL</th>
                            <th className="px-4 py-3 text-left">Description</th>
                            <th className="px-4 py-3 text-center">Depth</th>
                            <th className="px-4 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {targets.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="py-8 text-center text-muted-foreground italic text-sm">
                                    No crawler targets defined. Tasks will only be able to use ad-hoc URLs.
                                </td>
                            </tr>
                        ) : targets.map(t => (
                            <tr key={t.id} className="text-sm hover:bg-muted/10 transition-colors">
                                <td className="px-4 py-3 text-center">
                                    <div className="w-2 h-2 rounded-full bg-green-500 mx-auto" title="Active"></div>
                                </td>
                                <td className="px-4 py-3 font-mono text-xs text-blue-600 dark:text-blue-400 break-all">{t.target_url}</td>
                                <td className="px-4 py-3 text-muted-foreground">{t.description || '-'}</td>
                                <td className="px-4 py-3 text-center font-bold">{t.max_depth}</td>
                                <td className="px-4 py-3 text-right">
                                    <button 
                                        onClick={() => handleDelete(t.id)}
                                        className="p-1.5 text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                                        title="Delete Target"
                                    >
                                        <XIcon className="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// End of AdminPage
export default AdminPage;