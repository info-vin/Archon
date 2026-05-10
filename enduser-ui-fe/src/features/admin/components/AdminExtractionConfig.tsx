import React from 'react';
import { RefreshCwIcon, ShieldCheckIcon } from '../../../components/Icons';
import { ConfigDrivenInput } from './ConfigDrivenInput';
import { useExtractionSchemas } from '../hooks/useAdminDashboard';

const extractionFieldsConfig = [
    { key: 'analyzeUrl', type: 'url', label: 'Analyze URL', placeholder: 'https://www.104.com.tw/job/...' },
    { key: 'newSchemaName', type: 'text', label: 'Template Name', placeholder: 'e.g. 104 Job Detail' },
    { key: 'newDomainPattern', type: 'text', label: 'Domain Pattern', placeholder: 'Domain Pattern' }
];

export const AdminExtractionConfig: React.FC = () => {
    const { 
        schemas, loading, analyzeUrl, setAnalyzeUrl, isAnalyzing, suggestions, 
        newSchemaName, setNewSchemaName, newDomainPattern, setNewDomainPattern,
        analyzeStructure, saveSchema, runExtraction 
    } = useExtractionSchemas();

    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-indigo-600" /></div>;

    return (
        <div className="space-y-8 font-sans">
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-indigo-600">
                    <RefreshCwIcon className="w-5 h-5" />
                    New Extraction Discovery (Powered by DevBot)
                </h3>
                <p className="text-sm text-muted-foreground mb-4">Paste a sample URL to let DevBot discover its structure and suggest data fields.</p>
                <div className="flex gap-2 mb-6">
                    {extractionFieldsConfig.filter(f => f.key === 'analyzeUrl').map(field => (
                        <ConfigDrivenInput 
                            key={field.key}
                            field={field}
                            value={analyzeUrl}
                            onChange={setAnalyzeUrl}
                            className="flex-1 p-2 bg-background border border-border rounded-lg outline-none focus:ring-2 ring-primary/50 transition-all"
                        />
                    ))}
                    <button 
                        onClick={analyzeStructure}
                        disabled={isAnalyzing || !analyzeUrl}
                        className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 transition-all"
                    >
                        {isAnalyzing ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <ShieldCheckIcon className="w-4 h-4" />}
                        ANALYZE STRUCTURE
                    </button>
                </div>

                {suggestions && (
                    <div className="mt-6 p-4 bg-muted/30 rounded-xl border border-dashed border-border animate-in slide-in-from-top-2 duration-300">
                        <div className="flex justify-between items-start mb-4">
                            <h4 className="font-bold text-indigo-500">LLM Semantic Analysis & Suggested Fields</h4>
                            <div className="flex gap-2">
                                {extractionFieldsConfig.filter(f => f.key !== 'analyzeUrl').map(field => {
                                    const valueMap: any = { newSchemaName: newSchemaName, newDomainPattern: newDomainPattern };
                                    const setterMap: any = { newSchemaName: setNewSchemaName, newDomainPattern: setNewDomainPattern };
                                    
                                    return (
                                        <ConfigDrivenInput 
                                            key={field.key}
                                            field={field}
                                            value={valueMap[field.key]}
                                            onChange={setterMap[field.key]}
                                            className={`p-1 text-sm bg-background border border-border rounded ${field.key === 'newDomainPattern' ? 'w-48' : ''}`}
                                        />
                                    );
                                })}
                                <button onClick={saveSchema} className="px-3 py-1 bg-green-600 text-white text-xs font-bold rounded hover:bg-green-700">SAVE TEMPLATE</button>
                            </div>
                        </div>

                        {suggestions.summary && (
                            <div className="mb-6 p-4 bg-indigo-50 dark:bg-indigo-900/20 border-l-4 border-indigo-500 rounded-r-lg">
                                <h5 className="text-xs font-bold text-indigo-700 dark:text-indigo-400 uppercase tracking-wider mb-1">Semantic Understanding</h5>
                                <p className="text-sm text-indigo-900 dark:text-indigo-200">{suggestions.summary}</p>
                            </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {suggestions.fields?.map((field: any, idx: number) => (
                                <div key={idx} className="p-3 bg-card border border-border rounded-lg shadow-sm">
                                    <div className="flex justify-between font-bold text-xs uppercase tracking-wider">
                                        <span>{field.name}</span>
                                        <span className="text-[10px] bg-muted px-1 rounded">{field.type}</span>
                                    </div>
                                    <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">{field.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4">Saved Extraction Templates</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {schemas.map(s => (
                        <div key={s.id} className="p-4 border border-border rounded-xl bg-muted/10 hover:bg-muted/20 transition-all group relative">
                            <div className="font-bold text-sm mb-1 text-gray-900 dark:text-white">{s.name}</div>
                            <code className="text-[10px] bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 px-1 rounded">{s.domain_pattern}</code>
                            <div className="mt-3 flex flex-wrap gap-1">
                                {s.schema_definition?.fields?.slice(0, 5).map((f: any, idx: number) => (
                                    <span key={idx} className="text-[9px] bg-background border border-border px-1.5 py-0.5 rounded-full">{f.name}</span>
                                ))}
                            </div>
                            <div className="mt-4 pt-3 border-t border-border flex justify-end">
                                <button onClick={() => runExtraction(s.id)} className="text-[10px] font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"><RefreshCwIcon className="w-3 h-3" />RUN EXTRACTION</button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
