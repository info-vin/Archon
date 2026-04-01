import React, { useState } from 'react';
import { api } from '@/services/api';
import { SearchIcon, DatabaseIcon, FileTextIcon, ShieldCheckIcon } from '@/components/Icons';

export const RAGPlayground: React.FC = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setSearching(true);
        setError(null);
        try {
            // Physically calling the search API hardened in 4.6.25/26
            // Note: We're assuming api.searchKnowledgeItems exists or we use a raw call
            const response = await api.searchKnowledgeItems(query, 3);
            setResults(response || []);
        } catch (err: any) {
            setError(err.message || "RAG Search Failed");
        } finally {
            setSearching(false);
        }
    };

    return (
        <div className="bg-card rounded-2xl border border-border shadow-sm overflow-hidden">
            <div className="p-6 border-b border-border bg-muted/30">
                <h3 className="text-lg font-bold flex items-center gap-2">
                    <DatabaseIcon className="w-5 h-5 text-indigo-500" />
                    Industrial RAG Playground
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                    Phase 4.6.26: Verify Contextual Fingerprints & Retrieval Accuracy.
                </p>
            </div>

            <div className="p-6">
                <form onSubmit={handleSearch} className="flex gap-2 mb-6">
                    <div className="relative flex-1">
                        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <input 
                            type="text" 
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Ask the knowledge base... (e.g. 156 backend integration)"
                            className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                        />
                    </div>
                    <button 
                        disabled={searching}
                        className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl font-bold transition-all active:scale-95"
                    >
                        {searching ? "Searching..." : "Execute"}
                    </button>
                </form>

                {error && (
                    <div className="p-4 mb-6 bg-red-50 text-red-600 rounded-xl border border-red-100 text-sm">
                        {error}
                    </div>
                )}

                <div className="space-y-4">
                    {results.length > 0 ? (
                        results.map((res, i) => (
                            <div key={i} className="p-4 border border-border rounded-xl bg-muted/10 hover:bg-muted/20 transition-colors">
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center gap-2">
                                        <FileTextIcon className="w-4 h-4 text-slate-400" />
                                        <span className="text-xs font-bold font-mono text-slate-600">{res.source_id}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-[10px] px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full font-black">
                                            SIM: {(res.similarity * 100).toFixed(1)}%
                                        </span>
                                        {res.rerank_score !== undefined && (
                                            <span className="text-[10px] px-2 py-0.5 bg-emerald-100 text-green-700 rounded-full font-black">
                                                RANK: {res.rerank_score.toFixed(2)}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <div className="text-sm text-foreground leading-relaxed font-mono whitespace-pre-wrap bg-background p-3 rounded-lg border border-border/50">
                                    {/* The content now includes physical fingerprints from Phase 4.6.26 */}
                                    {res.content}
                                </div>
                            </div>
                        ))
                    ) : query && !searching ? (
                        <div className="text-center py-12 text-muted-foreground italic border-2 border-dashed border-border rounded-xl">
                            No matching knowledge chunks found for this query.
                        </div>
                    ) : (
                        <div className="text-center py-12 text-slate-300 flex flex-col items-center gap-2">
                            <ShieldCheckIcon className="w-8 h-8 opacity-20" />
                            <p className="text-sm">Ready for Industrial Retrieval Verification</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
