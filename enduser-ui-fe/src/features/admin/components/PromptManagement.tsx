import React, { useState, useEffect } from 'react';
import { api } from '../../../services/api.ts';
import { CheckCircleIcon, KeyIcon, RefreshCwIcon, SaveIcon, ShieldCheckIcon } from '../../../components/Icons.tsx';

export const PromptManagement: React.FC<{ isManagerMode: boolean }> = ({ isManagerMode }) => {
    const [prompts, setPrompts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedPrompt, setSelectedPrompt] = useState<any>(null);
    const [editValue, setEditValue] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        fetchPrompts();
    }, []);

    const fetchPrompts = async () => {
        setLoading(true);
        try {
            const data = await api.getSystemPrompts();
            setPrompts(data);
            if (data.length > 0 && !selectedPrompt) {
                handleSelect(data[0]);
            }
        } catch (err: any) {
            alert("Failed to load prompts: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = (p: any) => {
        setSelectedPrompt(p);
        setEditValue(p.prompt || p.content || '');
    };

    const handleSave = async () => {
        if (!selectedPrompt) return;
        setIsSaving(true);
        try {
            await api.updateSystemPrompt(selectedPrompt.prompt_name, { content: editValue });
            alert("Prompt updated and cache reloaded successfully!");
            fetchPrompts(); // Refresh list to get updated_at
        } catch (err: any) {
            alert("Save failed: " + err.message);
        } finally {
            setIsSaving(false);
        }
    };

    const isLocked = isManagerMode && selectedPrompt?.is_system_protected;

    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-primary" /></div>;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-250px)] min-h-[600px]">
            {/* List Sidebar */}
            <div className="lg:col-span-1 space-y-2 overflow-y-auto pr-2 pb-4">
                <h3 className="text-xs font-bold uppercase text-muted-foreground tracking-wider mb-4">Available Prompts</h3>
                {prompts.map(p => (
                    <button 
                        key={p.prompt_name}
                        onClick={() => handleSelect(p)}
                        className={`w-full text-left p-4 rounded-xl border transition-all ${selectedPrompt?.prompt_name === p.prompt_name ? 'border-primary bg-primary/5 shadow-sm' : 'border-border bg-card hover:border-primary/50'}`}
                    >
                        <div className="flex justify-between items-start">
                             <div className="font-bold text-sm truncate">{p.prompt_name.replace(/_/g, ' ').toUpperCase()}</div>
                             {p.is_system_protected ? (
                                 <div className="flex items-center text-amber-500" title="System Protected">
                                     <KeyIcon className="w-3.5 h-3.5" />
                                 </div>
                             ) : (
                                 <div className="flex items-center text-green-500" title="Editable">
                                     <CheckCircleIcon className="w-4 h-4" />
                                 </div>
                             )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-1">{p.description || 'No description'}</div>
                    </button>
                ))}
            </div>

            {/* Editor Area */}
            <div className="lg:col-span-2 flex flex-col bg-card rounded-2xl border border-border overflow-hidden shadow-sm">
                {selectedPrompt ? (
                    <>
                        <div className="p-4 border-b border-border bg-muted/30 flex justify-between items-center">
                            <div>
                                <h3 className="font-bold text-lg flex items-center gap-2">
                                    {selectedPrompt.prompt_name.replace(/_/g, ' ').toUpperCase()}
                                    {isLocked && <span className="text-[10px] px-2 py-0.5 bg-amber-100 text-amber-700 rounded border border-amber-200">READ ONLY</span>}
                                </h3>
                                <p className="text-xs text-muted-foreground">Last updated: {new Date(selectedPrompt.updated_at).toLocaleString()}</p>
                            </div>
                            {!isLocked && (
                                <button 
                                    onClick={handleSave}
                                    disabled={isSaving || editValue === (selectedPrompt.prompt || selectedPrompt.content)}
                                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-bold text-sm hover:bg-primary/90 disabled:opacity-50 disabled:grayscale transition-all"
                                >
                                    {isSaving ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <SaveIcon className="w-4 h-4" />}
                                    SAVE CHANGES
                                </button>
                            )}
                        </div>
                        <div className="flex-1 p-4 flex flex-col space-y-4">
                            <div className="flex-1 relative">
                                <textarea 
                                    value={editValue}
                                    onChange={(e) => setEditValue(e.target.value)}
                                    readOnly={isLocked}
                                    className={`w-full h-full p-4 bg-background border border-border rounded-xl font-mono text-sm focus:ring-2 focus:ring-primary outline-none resize-none leading-relaxed shadow-inner ${isLocked ? 'opacity-70 cursor-not-allowed bg-muted/20' : ''}`}
                                    placeholder="Enter system prompt here..."
                                />
                                {!isLocked && (
                                    <div className="absolute bottom-4 right-4 text-[10px] text-muted-foreground font-mono bg-background/80 px-2 py-1 rounded border border-border">
                                        {editValue.length} characters
                                    </div>
                                )}
                            </div>
                            {isLocked ? (
                                <div className="bg-amber-50 dark:bg-amber-950/20 p-3 rounded-lg border border-amber-100 dark:border-amber-900/30 flex gap-3">
                                    <KeyIcon className="w-5 h-5 text-amber-600 shrink-0" />
                                    <div className="text-xs text-amber-800 dark:text-amber-400">
                                        <strong>System Protected:</strong> This prompt defines core compliance or security rules. Only Administrators can modify it.
                                    </div>
                                </div>
                            ) : (
                                <div className="bg-blue-50 dark:bg-blue-950/20 p-3 rounded-lg border border-blue-100 dark:border-blue-900/30 flex gap-3">
                                    <ShieldCheckIcon className="w-5 h-5 text-blue-600 shrink-0" />
                                    <div className="text-xs text-blue-800 dark:text-blue-400">
                                        <strong>Business Logic:</strong> You can edit this prompt to adjust tone, style, or output format. Changes apply immediately.
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-muted-foreground italic">Select a prompt from the list to start editing.</div>
                )}
            </div>
        </div>
    );
};
