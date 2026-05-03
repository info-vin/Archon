import React, { useState } from 'react';
import { PerformancePulseChart } from './PerformancePulseChart';
import { ContentReviewPanel } from './ContentReviewPanel';
import { DevOpsProposalList } from './DevOpsProposalList';

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
            <PerformancePulseChart data={commanderTrends} />

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
                <ContentReviewPanel 
                    blogs={approvals.blogs}
                    processingId={processingId}
                    setProcessingId={setProcessingId}
                    handleApproveContent={handleApproveContent}
                    fetchData={fetchData}
                />
            )}

            {opLoadTab === 'devops' && (
                <DevOpsProposalList 
                    proposals={codeProposals}
                    processingId={processingId}
                    handleCodeAction={handleCodeAction}
                    handleViewDiff={handleViewDiff}
                />
            )}
        </div>
    );
};
