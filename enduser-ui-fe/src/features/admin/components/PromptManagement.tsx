import React, { useEffect } from 'react';
import { useMachine } from '@xstate/react';
import { promptMachine } from '../machines/promptMachine.ts';
import { api } from '../../../services/api.ts';
import { CheckCircleIcon, KeyIcon, RefreshCwIcon, SaveIcon, ShieldCheckIcon, EyeIcon, Edit2Icon, UndoIcon } from '../../../components/Icons.tsx';
import DiffViewer from '../../../components/DiffViewer';

export const PromptManagement: React.FC<{ isManagerMode: boolean }> = ({ isManagerMode }) => {
    const [state, send] = useMachine(promptMachine);
    const { prompts, selectedPrompt, editValue, viewMode, error } = state.context;
    const isLoading = state.matches('loading');
    const isSaving = state.matches({ ready: 'saving' });

    useEffect(() => {
        fetchPrompts();
    }, []);

    const fetchPrompts = async () => {
        try {
            const data = await api.getSystemPrompts();
            send({ type: 'FETCH_SUCCESS', prompts: data });
            if (data.length > 0 && !state.context.selectedPrompt) {
                send({ type: 'SELECT_PROMPT', prompt: data[0] });
            }
        } catch (err: any) {
            send({ type: 'FETCH_ERROR', error: err.message });
            alert("Failed to load prompts: " + err.message);
        }
    };

    const handleSelect = (p: any) => {
        send({ type: 'SELECT_PROMPT', prompt: p });
    };

    const handleRevert = () => {
        send({ type: 'REVERT' });
    };

    const handleSave = async () => {
        if (!selectedPrompt) return;
        send({ type: 'SAVE' });
        try {
            await api.updateSystemPrompt(selectedPrompt.prompt_name, { content: editValue });
            send({ type: 'SAVE_SUCCESS' });
            alert("Prompt updated and cache reloaded successfully!");
            
            // Reload from API
            const data = await api.getSystemPrompts();
            send({ type: 'FETCH_SUCCESS', prompts: data });
            
            // Re-select the updated prompt to refresh original value
            const updatedPrompt = data.find(p => p.prompt_name === selectedPrompt.prompt_name);
            if(updatedPrompt) {
                send({ type: 'SELECT_PROMPT', prompt: updatedPrompt });
            }
        } catch (err: any) {
            send({ type: 'SAVE_ERROR', error: err.message });
            alert("Save failed: " + err.message);
        }
    };

    const isLocked = isManagerMode && selectedPrompt?.is_system_protected;
    const hasChanges = selectedPrompt && editValue !== (selectedPrompt.prompt || selectedPrompt.content);

    if (isLoading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-primary" /></div>;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-250px)] min-h-[600px] font-sans">
            {/* List Sidebar */}
            <div className="lg:col-span-1 space-y-2 overflow-y-auto pr-2 pb-4">
                <h3 className="text-xs font-bold uppercase text-muted-foreground tracking-wider mb-4">Available Prompts</h3>
                {prompts.length === 0 ? (
                    <div className="p-4 text-center text-muted-foreground italic text-[11px] border-2 border-dashed border-border rounded-xl">
                        No system prompts initialized yet.
                    </div>
                ) : (
                    prompts.map(p => (
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
                    ))
                )}
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
                            <div className="flex items-center gap-3">
                                {!isLocked && hasChanges && (
                                    <>
                                        <button 
                                            onClick={handleRevert}
                                            className="flex items-center gap-1.5 px-3 py-1.5 text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-lg font-bold text-xs transition-colors"
                                        >
                                            <UndoIcon className="w-3.5 h-3.5" />
                                            REVERT
                                        </button>
                                        <div className="bg-muted p-1 rounded-lg flex gap-1">
                                            <button 
                                                onClick={() => send({ type: 'TOGGLE_VIEW', mode: 'edit' })}
                                                className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all flex items-center gap-1 ${viewMode === 'edit' ? 'bg-background shadow text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                                            >
                                                <Edit2Icon className="w-3.5 h-3.5" /> EDIT
                                            </button>
                                            <button 
                                                onClick={() => send({ type: 'TOGGLE_VIEW', mode: 'diff' })}
                                                className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all flex items-center gap-1 ${viewMode === 'diff' ? 'bg-background shadow text-indigo-600' : 'text-muted-foreground hover:text-foreground'}`}
                                            >
                                                <EyeIcon className="w-3.5 h-3.5" /> DIFF
                                            </button>
                                        </div>
                                    </>
                                )}
                                {!isLocked && (
                                    <button 
                                        onClick={handleSave}
                                        disabled={isSaving || !hasChanges}
                                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg font-bold text-sm hover:bg-primary/90 disabled:opacity-50 disabled:grayscale transition-all shadow-sm"
                                    >
                                        {isSaving ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <SaveIcon className="w-4 h-4" />}
                                        SAVE CHANGES
                                    </button>
                                )}
                            </div>
                        </div>
                        
                        <div className="flex-1 p-4 flex flex-col space-y-4 overflow-hidden">
                            {viewMode === 'edit' ? (
                                <div className="flex-1 relative">
                                    <textarea 
                                        value={editValue}
                                        onChange={(e) => send({ type: 'UPDATE_VALUE', value: e.target.value })}
                                        readOnly={isLocked}
                                        className={`w-full h-full p-4 bg-background border border-border rounded-xl font-mono text-sm focus:ring-2 focus:ring-primary outline-none resize-none leading-relaxed shadow-inner ${isLocked ? 'opacity-70 cursor-not-allowed bg-muted/20' : ''}`}
                                        placeholder="Enter system prompt here..."
                                    />
                                    {!isLocked && (
                                        <div className="absolute bottom-4 right-4 text-[10px] text-muted-foreground font-mono bg-background/80 px-2 py-1 rounded border border-border">
                                            {editValue.length} chars
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="flex-1 overflow-auto bg-background border border-border rounded-xl shadow-inner relative">
                                     <div className="absolute top-0 left-0 right-0 p-2 bg-muted/80 backdrop-blur-sm border-b flex justify-between text-xs font-bold text-muted-foreground z-10">
                                         <span className="text-rose-600">Original (Database)</span>
                                         <span className="text-emerald-600">Your Edits</span>
                                     </div>
                                     <div className="pt-10 h-full overflow-auto">
                                        <DiffViewer 
                                            oldCode={selectedPrompt.prompt || selectedPrompt.content || ''} 
                                            newCode={editValue} 
                                            splitView={true} 
                                        />
                                     </div>
                                </div>
                            )}

                            {isLocked ? (
                                <div className="bg-amber-50 dark:bg-amber-950/20 p-3 rounded-lg border border-amber-100 dark:border-amber-900/30 flex gap-3 shrink-0">
                                    <KeyIcon className="w-5 h-5 text-amber-600 shrink-0" />
                                    <div className="text-xs text-amber-800 dark:text-amber-400">
                                        <strong>System Protected:</strong> This prompt defines core compliance or security rules. Only Administrators can modify it.
                                    </div>
                                </div>
                            ) : (
                                <div className="bg-blue-50 dark:bg-blue-950/20 p-3 rounded-lg border border-blue-100 dark:border-blue-900/30 flex gap-3 shrink-0">
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
