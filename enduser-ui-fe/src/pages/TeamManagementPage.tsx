import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Employee, Task } from '../types';
import { useAuth } from '../hooks/useAuth';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { AiCollaborationWidget } from '../features/team/components/AiCollaborationWidget';
import { ManageMemberModal } from '../features/team/components/ManageMemberModal';
import UserAvatar from '../components/UserAvatar';
import TokenUsageTable from '../components/TokenUsageTable';
import { ShieldCheckIcon, MailIcon, BadgeCheckIcon, XIcon, BarChartIcon, FileTextIcon } from '../components/Icons';
import ReactMarkdown from 'react-markdown';

// Import raw markdown as a string for static in-app SOP rendering
import aliceSopMarkdown from '../../../PRPs/Phase_4.6.1_Alice_Persona_Workflows.md?raw';

const TeamManagementPage: React.FC = () => {
    const { user } = useAuth();
    const [team, setTeam] = useState<Employee[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [editingMember, setEditingMember] = useState<Employee | null>(null);
    const [activityMember, setActivityMember] = useState<Employee | null>(null);
    const [showSopModal, setShowSopModal] = useState<boolean>(false);
    const [showTokenDetails, setShowTokenDetails] = useState(false);
    const [aiUsage, setAiUsage] = useState<any>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [teamData, usageData] = await Promise.all([
                api.getEmployees(),
                api.getAiUsage()
            ]);
            setTeam(teamData);
            setAiUsage(usageData);
        } catch (err: any) {
            setError(err.message || "Failed to fetch team data.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <PermissionGuard permission="user:manage:team" userRole={user?.role} fallback={<div className="p-8 text-center text-gray-500">Access Denied: Team Management is for Managers and Admins only.</div>}>
            <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6 md:space-y-8">
                <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-3">Team Management</h1>
                        <p className="text-gray-500 mt-2">Manage your team members and oversee AI resource allocation.</p>
                    </div>
                </header>

                {/* AI COLLABORATION WIDGET (Strategic View integrated from Nexus metrics) */}
                <AiCollaborationWidget 
                    data={aiUsage} 
                    onClick={() => setShowTokenDetails(true)} 
                />

                {error && (
                    <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-100">
                        {error}
                    </div>
                )}

                {loading ? (
                    <div className="flex justify-center p-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {/* Combine Team + Mock Agents for Unified View */}
                        {/* FB-06: Using only Verified DB Data - removed hardcoded Mock Agents */}
                        {team.map((member: any) => {
                            // FB-06: Infer Agent status from role instead of hardcoded flag
                            const isAgent = member.role === 'ai_agent' || member.email?.endsWith('.bot@archon.ai');
                            
                            return (
                            <div key={member.id} className={`bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow relative ${isAgent ? 'ring-2 ring-indigo-50' : ''}`}>
                                <div className={`h-2 ${isAgent ? 'bg-gradient-to-r from-indigo-400 to-purple-500' : 'bg-gray-800'}`}></div>
                                <div className="p-6">
                                    <div className="flex items-start gap-4">
                                        {/* Unified Avatar Style (Square + Role Color/Hash Color) */}
                                        <UserAvatar name={member.name} role={member.role} isAI={isAgent} className="w-16 h-16 text-xl shadow-sm border border-gray-200" />
                                        
                                        <div className="flex-1">
                                            <h3 className="font-bold text-lg text-gray-900 flex items-center gap-2">
                                                {member.name}
                                                {isAgent && <span className="text-[10px] bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full uppercase tracking-wider">Bot</span>}
                                            </h3>
                                            <p className="text-sm text-gray-500">{member.position}</p>
                                            <div className={`mt-1 flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full w-fit ${isAgent ? 'text-purple-600 bg-purple-50' : 'text-gray-600 bg-gray-100'}`}>
                                                <BadgeCheckIcon className="w-3 h-3" />
                                                {member.role.toUpperCase().replace('_', ' ')}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-6 space-y-3">
                                        {isAgent ? (
                                            // Agent Specific Stats (Shared Budget)
                                            <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                                                <div className="flex justify-between items-center text-xs mb-1">
                                                    <span className="text-gray-500 font-bold uppercase">Shared Budget</span>
                                                    <span className="text-indigo-600 font-mono">{aiUsage?.usage_percentage || 0}%</span>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                                    <div 
                                                        className="bg-indigo-500 h-full rounded-full transition-all duration-500" 
                                                        style={{ width: `${aiUsage?.usage_percentage || 0}%` }}
                                                    ></div>
                                                </div>
                                                <div className="mt-1 text-right text-[10px] text-gray-400">
                                                    {aiUsage?.total_used?.toLocaleString()} / {aiUsage?.total_budget?.toLocaleString()} Credits
                                                </div>
                                            </div>
                                        ) : (
                                            // Human Stats
                                            <>
                                                <div className="flex items-center text-sm text-gray-600 gap-3">
                                                    <MailIcon className="w-4 h-4 text-gray-400" />
                                                    <span className="truncate">{member.email}</span>
                                                </div>
                                                <div className="flex items-center text-sm text-gray-600 gap-3">
                                                    <ShieldCheckIcon className="w-4 h-4 text-gray-400" />
                                                    Dept: {member.department || 'General'}
                                                </div>
                                            </>
                                        )}
                                    </div>

                                    <div className="mt-6 pt-6 border-t border-gray-50 flex gap-3">
                                        <button 
                                            onClick={() => setEditingMember(member)}
                                            disabled={isAgent}
                                            className={`flex-1 text-sm font-medium py-3 rounded-xl transition-colors min-h-[44px] flex items-center justify-center ${isAgent ? 'bg-gray-50 text-gray-300 cursor-not-allowed' : 'bg-gray-50 text-gray-700 hover:bg-gray-100 active:bg-gray-200'}`}
                                        >
                                            Manage Role
                                        </button>
                                        <button 
                                            onClick={() => setActivityMember(member)}
                                            className="flex-1 text-sm font-medium py-3 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 active:bg-gray-100 transition-colors min-h-[44px] flex items-center justify-center"
                                        >
                                            View Activity
                                        </button>
                                        {/* Inject SOP Viewer specifically for Alice's workflow context */}
                                        {member.name === 'Alice Johnson' && (
                                            <button 
                                                onClick={() => setShowSopModal(true)}
                                                className="flex-1 text-sm font-bold bg-indigo-50 text-indigo-700 py-3 rounded-xl border border-indigo-100 hover:bg-indigo-100 active:bg-indigo-200 transition-colors min-h-[44px] flex items-center justify-center gap-1 shadow-sm"
                                            >
                                                <FileTextIcon className="w-4 h-4" /> SOP
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                            );
                        })}
                    </div>
                )}

                {/* MODAL */}
                {editingMember && (
                    <ManageMemberModal 
                        member={editingMember} 
                        onClose={() => setEditingMember(null)} 
                        onSuccess={() => { setEditingMember(null); fetchData(); }}
                    />
                )}
                
                {/* ACTIVITY MODAL */}
                {activityMember && (
                    <ActivityLogModal 
                        member={activityMember} 
                        onClose={() => setActivityMember(null)} 
                    />
                )}

                {/* TOKEN USAGE DETAILS MODAL */}
                {showTokenDetails && (
                    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                        <div className="bg-white rounded-2xl shadow-xl w-full max-w-4xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
                            <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-indigo-50/50">
                                <div className="flex items-center gap-3">
                                    <div className="bg-indigo-600 p-2 rounded-lg text-white">
                                        <BarChartIcon className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-gray-900">Token Consumption Details</h3>
                                        <p className="text-xs text-gray-500">Real-time Human vs Machine Resource Audit (Last 7 Days)</p>
                                    </div>
                                </div>
                                <button onClick={() => setShowTokenDetails(false)} className="p-2 hover:bg-gray-200 rounded-full transition-colors"><XIcon className="w-5 h-5" /></button>
                            </div>
                            
                            <div className="flex-1 overflow-y-auto p-0">
                                {aiUsage?.details ? (
                                    <TokenUsageTable details={aiUsage.details} />
                                ) : (
                                    <div className="p-12 text-center text-gray-400">No usage details available.</div>
                                )}
                            </div>
                            
                            <div className="p-4 border-t border-gray-100 bg-gray-50 text-right">
                                <button 
                                    onClick={() => setShowTokenDetails(false)}
                                    className="px-6 py-2 bg-white border border-gray-200 rounded-xl text-sm font-bold text-gray-600 hover:bg-gray-100 transition-colors"
                                >
                                    Close Audit
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* ALICE 4.6.1 SOP MODAL */}
                {showSopModal && (
                    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                        <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col h-[85vh]">
                            <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-indigo-50/50 shrink-0">
                                <div className="flex items-center gap-3">
                                    <div className="bg-indigo-600 p-2 rounded-lg text-white">
                                        <FileTextIcon className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-gray-900 leading-tight">Alice Workflow Guidelines</h3>
                                        <p className="text-[10px] text-gray-500">Phase 4.6.1 Standard Operating Procedure</p>
                                    </div>
                                </div>
                                <button onClick={() => setShowSopModal(false)} className="p-2 hover:bg-gray-200 rounded-full transition-colors"><XIcon className="w-5 h-5" /></button>
                            </div>
                            
                            <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-gray-50">
                                <article className="prose prose-sm md:prose-base prose-indigo max-w-none prose-headings:font-bold prose-h1:text-2xl prose-a:text-indigo-600 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                                    <ReactMarkdown>{aliceSopMarkdown}</ReactMarkdown>
                                </article>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </PermissionGuard>
    );
};



const ActivityLogModal: React.FC<{ member: Employee; onClose: () => void }> = ({ member, onClose }) => {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadTasks = async () => {
            try {
                // Fetch tasks for specific member + unassigned, with higher limit
                // Passing member.id to backend allows efficient filtering and avoids pagination issues (BUG-027)
                const tasks = await api.getTasks(true, true, member.id, 100);

                // Client-side fallback filter for legacy name-based assignment consistency
                const memberTasks = tasks.filter(t =>
                    t.assignee_id === member.id || 
                    t.assignee === member.name ||
                    (t.assignee === 'User' && member.role === 'marketing')
                ).sort((a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime());

                setTasks(memberTasks);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        loadTasks();
    }, [member]);

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
             <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[80vh]">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <div className="flex items-center gap-3">
                        <UserAvatar name={member.name} role={member.role} className="w-10 h-10 shadow-sm" />
                        <div>
                            <h3 className="font-bold text-gray-900">{member.name}'s Activity</h3>
                            <p className="text-xs text-gray-500">Recent Assignments & Tasks</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full transition-colors"><XIcon className="w-5 h-5" /></button>
                </div>
                
                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="flex justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>
                    ) : tasks.length === 0 ? (
                        <div className="text-center py-8 text-gray-400">No recent activity found.</div>
                    ) : (
                        <div className="space-y-3">
                            {tasks.map(task => (
                                <div key={task.id} className="p-4 bg-white border border-gray-100 rounded-xl shadow-sm hover:border-indigo-100 transition-colors">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h4 className="font-bold text-gray-800 text-sm flex items-center flex-wrap gap-1">
                                                {task.title}
                                                {task.is_recurring && <span className="text-[10px] font-normal text-blue-500 bg-blue-50 px-1 py-0.5 rounded border border-blue-100">(🔁 定期)</span>}
                                            </h4>
                                            <p className="text-xs text-gray-500 mt-1 line-clamp-1">{task.description}</p>
                                        </div>
                                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                            task.status === 'done' ? 'bg-green-100 text-green-700' :
                                            task.status === 'doing' ? 'bg-blue-100 text-blue-700' :
                                            'bg-gray-100 text-gray-600'
                                        }`}>
                                            {task.status}
                                        </span>
                                    </div>
                                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
                                        <span>Updated: {new Date(task.updated_at || Date.now()).toLocaleDateString()}</span>
                                        <span>Priority: {task.priority}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
             </div>
        </div>
    );
};

export default TeamManagementPage;