import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Employee } from '../types';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { AiCollaborationWidget } from '../features/team/components/AiCollaborationWidget';
import { ManageMemberModal } from '../features/team/components/ManageMemberModal';
import { ActivityLogModal } from '../features/team/components/ActivityLogModal';
import { TeamMemberCard } from '../features/team/components/TeamMemberCard';
import TokenUsageTable from '../components/TokenUsageTable';
import { XIcon, BarChartIcon, FileTextIcon } from '../components/Icons';
import ReactMarkdown from 'react-markdown';

// Removed direct file import from outside the project root (../../PRPs/...) 
// because it breaks Vite production builds.
const aliceSopMarkdown = "SOP documentation is currently unavailable. Please check the central knowledge base.";

const TeamManagementPage: React.FC = () => {
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
        <PermissionGuard permission="user:manage:team" fallback={<div className="p-8 text-center text-gray-500">Access Denied: Team Management is for Managers and Admins only.</div>}>
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
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-pulse min-h-[250px]">
                                <div className="h-2 bg-gray-200"></div>
                                <div className="p-6">
                                    <div className="flex items-start gap-4">
                                        <div className="w-16 h-16 bg-gray-200 rounded-xl shrink-0"></div>
                                        <div className="flex-1 space-y-3 py-1">
                                            <div className="h-5 bg-gray-200 rounded w-3/4"></div>
                                            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                                            <div className="h-4 bg-gray-200 rounded-full w-16 mt-2"></div>
                                        </div>
                                    </div>
                                    <div className="mt-8 space-y-4">
                                        <div className="flex gap-3 items-center"><div className="w-4 h-4 rounded-full bg-gray-200"></div><div className="h-3 bg-gray-200 rounded w-full"></div></div>
                                        <div className="flex gap-3 items-center"><div className="w-4 h-4 rounded-full bg-gray-200"></div><div className="h-3 bg-gray-200 rounded w-2/3"></div></div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {team.map((member: any) => (
                            <TeamMemberCard
                                key={member.id}
                                member={member}
                                aiUsage={aiUsage}
                                onEditRole={setEditingMember}
                                onViewActivity={setActivityMember}
                                onViewSop={() => setShowSopModal(true)}
                            />
                        ))}
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
                                <button onClick={() => setShowTokenDetails(false)} className="p-2 hover:bg-gray-200 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2" aria-label="Close token details"><XIcon className="w-5 h-5" /></button>
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
                                <button onClick={() => setShowSopModal(false)} className="p-2 hover:bg-gray-200 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2" aria-label="Close SOP modal"><XIcon className="w-5 h-5" /></button>
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

export default TeamManagementPage;