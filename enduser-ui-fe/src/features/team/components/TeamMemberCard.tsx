import React from 'react';
import { Employee } from '@/types';
import UserAvatar from '@/components/UserAvatar';
import { ShieldCheckIcon, MailIcon, BadgeCheckIcon, FileTextIcon } from '@/components/Icons';

// PERFORMANCE: Hoisted Intl.NumberFormat to avoid expensive re-instantiations during render
const numberFormatter = new Intl.NumberFormat();

interface TeamMemberCardProps {
    member: Employee;
    aiUsage: any;
    onEditRole: (member: Employee) => void;
    onViewActivity: (member: Employee) => void;
    onViewSop: () => void;
}

export const TeamMemberCard: React.FC<TeamMemberCardProps> = ({
    member,
    aiUsage,
    onEditRole,
    onViewActivity,
    onViewSop
}) => {
    const isAgent = member.role === 'ai_agent' || member.email?.endsWith('.bot@archon.ai');
    
    const roleClasses = isAgent 
        ? 'text-purple-600 bg-purple-50' 
        : 'text-gray-600 bg-gray-100';
    
    const bannerClasses = isAgent 
        ? 'bg-gradient-to-r from-indigo-400 to-purple-500' 
        : 'bg-gray-800';

    return (
        <div className={`bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow relative ${isAgent ? 'ring-2 ring-indigo-50' : ''}`}>
            <div className={`h-2 ${bannerClasses}`}></div>
            <div className="p-6">
                <div className="flex items-start gap-4">
                    <UserAvatar name={member.name || ''} role={member.role} isAI={isAgent} className="w-16 h-16 text-xl shadow-sm border border-gray-200 shrink-0" />
                    
                    <div className="flex-1 min-w-0">
                        <h3 className="font-bold text-lg text-gray-900 flex items-center gap-2">
                            <span className="truncate">{member.name}</span>
                            {isAgent && <span className="text-[10px] bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full uppercase tracking-wider shrink-0">Bot</span>}
                        </h3>
                        <p className="text-sm text-gray-500 truncate">{member.position}</p>
                        <div className={`mt-1 flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full w-fit ${roleClasses}`}>
                            <BadgeCheckIcon className="w-3 h-3" />
                            <span className="truncate">{member.role.toUpperCase().replace('_', ' ')}</span>
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
                            <div className="mt-2 flex justify-between items-center text-[10px]">
                                <div className="flex items-center gap-1 font-bold text-gray-400">
                                    <span className="bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded uppercase tracking-tighter">Cost</span>
                                    <span className="text-gray-600 font-mono">${aiUsage?.total_monthly_usd?.toFixed(4) || "0.0000"} USD</span>
                                </div>
                                <div className="text-gray-400">
                                    {aiUsage?.total_used != null ? numberFormatter.format(aiUsage.total_used) : undefined} / {aiUsage?.total_budget != null ? numberFormatter.format(aiUsage.total_budget) : undefined} Credits
                                </div>
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
                        onClick={() => onEditRole(member)}
                        disabled={isAgent}
                        className={`flex-1 min-w-0 text-sm font-medium py-3 rounded-xl transition-colors min-h-[44px] flex items-center justify-center ${isAgent ? 'bg-gray-50 text-gray-300 cursor-not-allowed' : 'bg-gray-50 text-gray-700 hover:bg-gray-100 active:bg-gray-200'}`}
                        aria-label={`Manage role for ${member.name}`}
                        title="Manage Role"
                    >
                        <span className="truncate">Manage Role</span>
                    </button>
                    <button 
                        onClick={() => onViewActivity(member)}
                        className="flex-1 min-w-0 text-sm font-medium py-3 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 active:bg-gray-100 transition-colors min-h-[44px] flex items-center justify-center"
                        aria-label={`View activity for ${member.name}`}
                        title="View Activity"
                    >
                        <span className="truncate">View Activity</span>
                    </button>
                    {/* Inject SOP Viewer specifically for Alice's workflow context */}
                    {member.name === 'Alice Johnson' && (
                        <button 
                            onClick={onViewSop}
                            className="flex-1 min-w-0 text-sm font-bold bg-indigo-50 text-indigo-700 py-3 rounded-xl border border-indigo-100 hover:bg-indigo-100 active:bg-indigo-200 transition-colors min-h-[44px] flex items-center justify-center gap-1 shadow-sm"
                            aria-label="View SOP Documentation"
                            title="View SOP"
                        >
                            <FileTextIcon className="w-4 h-4 shrink-0" /> <span className="truncate">SOP</span>
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};
