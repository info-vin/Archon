import React from 'react';
import { ChangeType } from '@/types';
import { 
  CheckCircleIcon, 
  CodeBracketIcon, 
  FileTextIcon as DocumentTextIcon, 
  CommandLineIcon,
  ClockIcon,
  ChevronRightIcon,
  UserIcon
} from '@/components/Icons';
import { UnifiedProposal } from '../hooks/useApprovalInbox';

// PERFORMANCE: Hoisted Intl.DateTimeFormat instance outside the component to prevent expensive re-instantiations during list rendering.
const timeFormatter = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: 'numeric', second: 'numeric' });
const safeFormatTime = (dateStr: string) => {
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? 'Invalid Date' : timeFormatter.format(d);
};

interface ApprovalSidebarListProps {
    proposals: UnifiedProposal[];
    loading: boolean;
    selectedId: string | null;
    onSelect: (id: string) => void;
}

export const ApprovalSidebarList: React.FC<ApprovalSidebarListProps> = ({ proposals, loading, selectedId, onSelect }) => {
    
    const getIcon = (type: ChangeType) => {
        switch (type) {
            case ChangeType.FILE: return <CodeBracketIcon className="w-5 h-5 text-blue-500" />;
            case ChangeType.SHELL: return <CommandLineIcon className="w-5 h-5 text-gray-700" />;
            case ChangeType.BLOG: return <DocumentTextIcon className="w-5 h-5 text-fuchsia-500" />;
            default: return <DocumentTextIcon className="w-5 h-5 text-indigo-500" />;
        }
    };

    if (loading && proposals.length === 0) {
        return <div className="p-8 text-center text-gray-400 italic text-sm">Loading proposals...</div>;
    }

    if (proposals.length === 0) {
        return (
            <div className="p-12 text-center">
                <div className="inline-block p-4 bg-green-50 dark:bg-green-900/20 rounded-full mb-4">
                    <CheckCircleIcon className="w-8 h-8 text-green-500" />
                </div>
                <h3 className="text-sm font-bold text-gray-800 dark:text-gray-200">Inbox Zero!</h3>
                <p className="text-xs text-gray-500 mt-1">All AI and Team changes have been reviewed.</p>
            </div>
        );
    }

    return (
        <div className="divide-y divide-gray-100 dark:divide-slate-800">
            {proposals.map((item) => (
                <div 
                    key={item.id}
                    onClick={() => onSelect(item.id)}
                    className={`p-4 cursor-pointer transition-all hover:bg-indigo-50/30 dark:hover:bg-indigo-900/10 ${
                    selectedId === item.id ? 'bg-indigo-50 dark:bg-indigo-900/20 border-l-4 border-indigo-600' : 'border-l-4 border-transparent'
                    }`}
                >
                    <div className="flex items-start gap-3">
                    <div className="mt-1">{getIcon(item.type)}</div>
                    <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-bold text-gray-900 dark:text-white truncate">
                        {item.change_summary || (item.request_payload?.file_path ? `Update ${item.request_payload.file_path.split('/').pop()}` : 'Proposed Change')}
                        </h4>
                        <p className="text-[10px] text-gray-500 mt-0.5 flex items-center gap-1">
                        <UserIcon className="w-3 h-3" /> {item.is_marketing ? item.marketing_author : 'DevBot'} • <ClockIcon className="w-3 h-3" /> {safeFormatTime(item.created_at)}
                        </p>
                    </div>
                    <ChevronRightIcon className="w-4 h-4 text-gray-300" />
                    </div>
                </div>
            ))}
        </div>
    );
};
