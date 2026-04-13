import React from 'react';
import { ShieldCheckIcon, ZapIcon, FileTextIcon, CheckCircleIcon } from '../../../../components/Icons';

export interface EthicsAuditPanelProps {
    ethicsAudit: any;
    handleDispatch: (id: string) => void;
    handleApprovePrompt: (id: string) => void;
    processingId: string | null;
}

export const EthicsAuditPanel: React.FC<EthicsAuditPanelProps> = ({
    ethicsAudit,
    handleDispatch,
    handleApprovePrompt,
    processingId
}) => {
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
            <div className="bg-indigo-50/30 border border-indigo-100 rounded-3xl p-6">
                <h4 className="text-xs font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <ZapIcon className="w-3 h-3" /> Actionable Safety Queue ({ethicsAudit?.total_pending || 0})
                </h4>

                <div className="space-y-4">
                    {/* 1. Ethics Violations (Sentinel) */}
                    {ethicsAudit?.violations.map((v: any) => (
                        <div key={v.id} className="bg-white border border-red-100 p-4 rounded-2xl flex items-center justify-between shadow-sm hover:shadow-md transition-all">
                            <div className="flex items-center gap-4">
                                <div className="bg-red-50 p-3 rounded-xl text-red-600">
                                    <ShieldCheckIcon className="w-5 h-5" />
                                </div>
                                <div>
                                    <span className="text-[10px] font-black px-2 py-0.5 bg-red-100 text-red-700 rounded uppercase">Safety Intercept</span>
                                    <h5 className="font-bold text-gray-800 text-sm mt-1">{v.event_type}: {v.description}</h5>
                                    <p className="text-[10px] text-gray-400 font-mono mt-0.5">Attempted Input: {v.raw_input?.slice(0, 50)}...</p>
                                </div>
                            </div>
                            <button
                                onClick={() => handleDispatch(v.id)}
                                className="px-4 py-2 bg-red-600 text-white rounded-xl text-[10px] font-black hover:bg-red-700 transition-all"
                                aria-label={`Dispatch investigation for ${v.event_type}`}
                            >
                                DISPATCH INVESTIGATION
                            </button>
                        </div>
                    ))}

                    {/* 2. Prompt Changes (Librarian) */}
                    {ethicsAudit?.pending_versions.map((p: any) => (
                        <div key={p.id} className="bg-white border border-amber-100 p-4 rounded-2xl flex items-center justify-between shadow-sm hover:shadow-md transition-all">
                            <div className="flex items-center gap-4">
                                <div className="bg-amber-50 p-3 rounded-xl text-amber-600">
                                    <FileTextIcon className="w-5 h-5" />
                                </div>
                                <div>
                                    <span className="text-[10px] font-black px-2 py-0.5 bg-amber-100 text-amber-700 rounded uppercase">Prompt Change</span>
                                    <h5 className="font-bold text-gray-800 text-sm mt-1">{p.document_id} (v{p.version_number})</h5>
                                    <p className="text-[10px] text-gray-400 font-mono mt-0.5">Changed by {p.created_by} | {p.change_summary}</p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleViewDiff(p)}
                                    className="px-4 py-2 bg-slate-100 text-slate-600 rounded-xl text-[10px] font-black hover:bg-slate-200"
                                    aria-label={`View diff for prompt change on ${p.document_id}`}
                                >
                                    VIEW DIFF
                                </button>
                                <button
                                    onClick={() => handleApprovePrompt(p.id)}
                                    disabled={processingId === p.id}
                                    className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-[10px] font-black hover:bg-indigo-700"
                                    aria-label={processingId === p.id ? `Approving prompt change for ${p.document_id}...` : `Approve prompt change for ${p.document_id}`}
                                >
                                    {processingId === p.id ? '...' : 'APPROVE'}
                                </button>
                            </div>
                        </div>
                    ))}

                    {ethicsAudit?.total_pending === 0 && (
                        <div className="py-12 flex flex-col items-center justify-center text-center text-green-600 opacity-60">
                            <CheckCircleIcon className="w-12 h-12 mb-2" />
                            <p className="text-sm font-black uppercase tracking-widest">Compliance Nominal</p>
                            <p className="text-[10px]">No unauthorized prompt changes or safety leaks detected.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
