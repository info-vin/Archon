import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SparklesIcon, TrashIcon } from '../components/Icons';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { EmptyState } from '../components/common/EmptyState';

const SalesCartPage: React.FC = () => {
    const [leads, setLeads] = useState<any[]>([]);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    const [generatingPitch, setGeneratingPitch] = useState<string | null>(null);
    const [pitchResult, setPitchResult] = useState<{ content: string; company: string } | null>(null);

    useEffect(() => {
        fetchCart();
    }, []);

    const fetchCart = async () => {
        setLoading(true);
        try {
            const allLeads = await api.getLeads();
            // Filter for shortlisted items
            setLeads(allLeads.filter((l: any) => l.status === 'shortlisted'));
        } catch (err) {
            console.error("Failed to load cart", err);
        } finally {
            setLoading(false);
        }
    };

    const toggleSelection = (id: string) => {
        const newSet = new Set(selectedIds);
        if (newSet.has(id)) {
            newSet.delete(id);
        } else {
            newSet.add(id);
        }
        setSelectedIds(newSet);
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === leads.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(leads.map(l => l.id)));
        }
    };

    const handleBatchAction = async (action: 'export' | 'content' | 'remove') => {
        if (selectedIds.size === 0) return;
        setProcessing(true);
        try {
            const ids = Array.from(selectedIds);
            
            if (action === 'remove') {
                await Promise.all(ids.map(id => api.updateLead(id, { status: 'new' })));
                setLeads(leads.filter(l => !selectedIds.has(l.id)));
                setSelectedIds(new Set());
            } else if (action === 'export') {
                // Simulate CRM Export
                await new Promise(resolve => setTimeout(resolve, 1500));
                alert(`Exported ${ids.length} leads to Salesforce/HubSpot successfully.`);
            } else if (action === 'content') {
                 // Simulate triggering Magic Draft
                 await new Promise(resolve => setTimeout(resolve, 1500));
                 alert(`Requested Magic Draft content for ${ids.length} leads. Bob has been notified.`);
            }
        } catch (err) {
            alert(`Batch ${action} failed`);
        } finally {
            setProcessing(false);
        }
    };

    const handleRemove = async (id: string) => {
        try {
            await api.updateLead(id, { status: 'new' });
            setLeads(leads.filter(l => l.id !== id));
            if (selectedIds.has(id)) {
                const newSet = new Set(selectedIds);
                newSet.delete(id);
                setSelectedIds(newSet);
            }
        } catch (err) {
            alert("Failed to remove item");
        }
    };

    const handlePromote = async (lead: any) => {
        if (confirm(`Promote ${lead.company_name} to Vendor?`)) {
            try {
                await api.promoteLead(lead.id, { vendor_name: lead.company_name });
                setLeads(leads.filter(l => l.id !== lead.id));
            } catch (err) {
                alert("Failed to promote");
            }
        }
    };

    const handleGeneratePitch = async (lead: any) => {
        setGeneratingPitch(lead.id);
        try {
             const res = await api.generatePitch(lead.job_title, lead.company_name, lead.identified_need);
             // alert(`Pitch Generated:\n\n${res.content.substring(0, 100)}...`);
             setPitchResult({ content: res.content, company: lead.company_name });
        } catch(err) {
            alert("Failed to generate pitch");
        } finally {
            setGeneratingPitch(null);
        }
    };

    return (
        <PermissionGuard permission="leads:view:sales">
            <div className="p-4 pb-32 max-w-lg mx-auto min-h-screen relative">
                <header className="mb-6 flex justify-between items-center sticky top-0 bg-background/95 backdrop-blur z-10 py-2 border-b border-transparent">
                    <div className="flex items-center gap-3">
                         <h1 className="text-2xl font-bold">Sales Cart ({leads.length})</h1>
                         {leads.length > 0 && (
                            <button 
                                onClick={toggleSelectAll}
                                className="text-xs font-medium text-primary bg-primary/10 px-2 py-1 rounded hover:bg-primary/20 transition-colors"
                            >
                                {selectedIds.size === leads.length ? 'Deselect All' : 'Select All'}
                            </button>
                         )}
                    </div>
                    <button onClick={fetchCart} className="text-sm text-primary hover:underline">Refresh</button>
                </header>

                {loading ? (
                    <div className="flex justify-center p-12">
                         <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                ) : leads.length === 0 ? (
                    <EmptyState 
                        title="Cart Empty" 
                        description="Swipe right on leads in the Marketing tab to shortlist them here."
                        actionLabel="Find Leads"
                        onAction={() => window.location.href = '/marketing'} 
                    />
                ) : (
                    <div className="space-y-4">
                        {leads.map(lead => (
                            <div 
                                key={lead.id} 
                                className={`bg-card p-4 rounded-xl shadow-sm border transition-all ${selectedIds.has(lead.id) ? 'border-primary ring-1 ring-primary bg-primary/5' : 'border-border'}`}
                                onClick={() => toggleSelection(lead.id)}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${selectedIds.has(lead.id) ? 'bg-primary border-primary' : 'border-gray-300 bg-white'}`}>
                                            {selectedIds.has(lead.id) && <SparklesIcon className="w-3 h-3 text-white" />}
                                        </div>
                                        <h3 className="font-bold text-lg leading-none">{lead.company_name}</h3>
                                    </div>
                                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-mono">
                                        {lead.match_score ? `${lead.match_score}%` : 'NEW'}
                                    </span>
                                </div>
                                <div className="pl-8">
                                    <p className="text-sm text-muted-foreground mb-3">{lead.job_title}</p>
                                    
                                    <div className="bg-secondary/50 p-2 rounded text-xs text-secondary-foreground mb-4">
                                        <span className="font-semibold">Need:</span> {lead.identified_need}
                                    </div>

                                    <div className="grid grid-cols-2 gap-2" onClick={e => e.stopPropagation()}>
                                        <button 
                                            onClick={() => handleGeneratePitch(lead)}
                                            disabled={generatingPitch === lead.id}
                                            className="col-span-2 flex items-center justify-center gap-2 bg-indigo-50 text-indigo-700 py-2 rounded-lg text-sm font-medium hover:bg-indigo-100"
                                        >
                                            <SparklesIcon className="w-4 h-4" />
                                            {generatingPitch === lead.id ? "Generating..." : "Generate AI Pitch"}
                                        </button>
                                        <button 
                                            onClick={() => handleRemove(lead.id)}
                                            className="py-2 rounded-lg text-sm font-medium border border-border text-muted-foreground hover:bg-secondary flex items-center justify-center gap-2"
                                        >
                                            <TrashIcon className="w-4 h-4" />
                                            Remove
                                        </button>
                                        <button 
                                            onClick={() => handlePromote(lead)}
                                            className="py-2 rounded-lg text-sm font-medium bg-secondary text-secondary-foreground hover:bg-secondary/80"
                                        >
                                            Promote
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Batch Action Bar */}
                {selectedIds.size > 0 && (
                    <div className="fixed bottom-[4.5rem] left-4 right-4 md:left-1/2 md:-translate-x-1/2 md:max-w-lg bg-gray-900/90 backdrop-blur text-white p-3 rounded-2xl shadow-2xl flex items-center justify-between gap-4 animate-in slide-in-from-bottom-5 duration-300 z-50">
                        <div className="pl-2 font-bold text-sm whitespace-nowrap">
                            {selectedIds.size} Selected
                        </div>
                        <div className="flex gap-2 w-full overflow-x-auto">
                             <button 
                                onClick={() => handleBatchAction('remove')}
                                disabled={processing}
                                className="flex-1 bg-red-500/20 hover:bg-red-500/40 text-red-200 py-2 px-3 rounded-xl text-xs font-bold transition-colors"
                             >
                                Remove
                             </button>
                             <button 
                                onClick={() => handleBatchAction('export')}
                                disabled={processing}
                                className="flex-1 bg-white/10 hover:bg-white/20 py-2 px-3 rounded-xl text-xs font-bold transition-colors whitespace-nowrap"
                             >
                                Export CRM
                             </button>
                             <button 
                                onClick={() => handleBatchAction('content')}
                                disabled={processing}
                                className="flex-1 bg-indigo-500 hover:bg-indigo-600 text-white py-2 px-3 rounded-xl text-xs font-bold transition-colors whitespace-nowrap flex items-center justify-center gap-1 shadow-lg shadow-indigo-500/20"
                             >
                                <SparklesIcon className="w-3 h-3" />
                                Magic Draft
                             </button>
                        </div>
                    </div>
                )}
                {/* Result Modal */}
                {pitchResult && (
                    <PitchModal 
                        isOpen={!!pitchResult} 
                        onClose={() => setPitchResult(null)} 
                        content={pitchResult.content} 
                        company={pitchResult.company} 
                    />
                )}
            </div>
        </PermissionGuard>
    );
};

// Simple Modal Component for Pitch Result
const PitchModal: React.FC<{ isOpen: boolean; onClose: () => void; content: string; company: string }> = ({ isOpen, onClose, content, company }) => {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                    <h3 className="font-bold text-gray-800 flex items-center gap-2">
                        <SparklesIcon className="w-5 h-5 text-indigo-600" />
                        AI Pitch: {company}
                    </h3>
                    <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded-full text-gray-500 transition-colors">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-6 text-gray-700 leading-relaxed space-y-4">
                    <div className="prose prose-sm max-w-none">
                         <div className="whitespace-pre-wrap">{content}</div>
                    </div>
                </div>
                <div className="p-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
                    <button 
                        onClick={() => {
                            navigator.clipboard.writeText(content);
                            alert("Copied to clipboard!");
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors text-gray-700 shadow-sm"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
                        Copy
                    </button>
                    <button 
                        onClick={onClose}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 shadow-md shadow-indigo-200"
                    >
                        Done
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SalesCartPage;
