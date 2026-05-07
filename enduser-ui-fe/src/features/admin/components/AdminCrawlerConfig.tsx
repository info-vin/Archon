import React from 'react';
import { ShieldCheckIcon, RefreshCwIcon, PlusIcon, XIcon } from '../../../components/Icons';
import { ConfigDrivenInput } from './ConfigDrivenInput';
import { useCrawlerTargets } from '../hooks/useAdminDashboard';

const crawlerFieldsConfig = [
    { key: 'url', type: 'url', label: 'Target URL', placeholder: 'e.g. https://wlb.mol.gov.tw/Page/index.aspx' },
    { key: 'desc', type: 'text', label: 'Description', placeholder: 'Description (Optional)' },
    { key: 'depth', type: 'number', label: 'Depth', min: 1, max: 5 }
];

export const AdminCrawlerConfig: React.FC = () => {
    const { 
        targets, loading, newUrl, setNewUrl, newDepth, setNewDepth, newDesc, setNewDesc, 
        isSaving: isTargetsSaving, saveTarget, deleteTarget 
    } = useCrawlerTargets();

    if (loading) return <div className="flex justify-center p-6"><RefreshCwIcon className="animate-spin w-6 h-6 text-indigo-600" /></div>;

    return (
        <div className="space-y-8 font-sans">
            {/* Target Manager */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-green-500">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-green-600">
                    <ShieldCheckIcon className="w-5 h-5" />
                    Knowledge Base Targets (Crawler)
                </h3>
                <p className="text-sm text-muted-foreground mb-6">Define the allowed root URLs that Librarian is permitted to crawl.</p>

                <div className="flex flex-col md:flex-row gap-4 mb-8">
                    {crawlerFieldsConfig.map(field => {
                        const valueMap: any = { url: newUrl, desc: newDesc, depth: newDepth };
                        const setterMap: any = { url: setNewUrl, desc: setNewDesc, depth: setNewDepth };
                        
                        return (
                            <ConfigDrivenInput 
                                key={field.key}
                                field={field}
                                value={valueMap[field.key]}
                                onChange={setterMap[field.key]}
                                className={`p-2 bg-background border border-border rounded-lg outline-none focus:ring-2 ring-green-500/50 transition-all ${field.key === 'url' ? 'flex-[2] font-mono text-sm' : field.key === 'depth' ? 'w-full text-center' : 'flex-1 text-sm'}`}
                            />
                        );
                    })}
                    <button 
                        onClick={saveTarget}
                        disabled={isTargetsSaving || !newUrl}
                        className="px-6 py-2 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 disabled:opacity-50 flex items-center gap-2 transition-all whitespace-nowrap"
                    >
                        {isTargetsSaving ? <RefreshCwIcon className="animate-spin w-4 h-4" /> : <PlusIcon className="w-4 h-4" />}
                        ADD TARGET
                    </button>
                </div>

                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-border">
                        <thead>
                            <tr className="text-xs font-bold text-muted-foreground uppercase tracking-wider bg-muted/30">
                                <th className="px-4 py-3 text-left w-12">Status</th>
                                <th className="px-4 py-3 text-left">Target URL</th>
                                <th className="px-4 py-3 text-left">Description</th>
                                <th className="px-4 py-3 text-center">Depth</th>
                                <th className="px-4 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border text-sm">
                            {targets.map(t => (
                                <tr key={t.id} className="hover:bg-muted/10 transition-colors">
                                    <td className="px-4 py-3 text-center"><div className="w-2 h-2 rounded-full bg-green-500 mx-auto"></div></td>
                                    <td className="px-4 py-3 font-mono text-xs text-blue-600 dark:text-blue-400 break-all">{t.target_url}</td>
                                    <td className="px-4 py-3 text-muted-foreground">{t.description || '-'}</td>
                                    <td className="px-4 py-3 text-center font-bold">{t.max_depth}</td>
                                    <td className="px-4 py-3 text-right"><button onClick={() => deleteTarget(t.id)} className="p-1.5 text-red-500 hover:bg-red-500/10 rounded-lg transition-all" aria-label="Delete target" title="Delete target"><XIcon className="w-4 h-4" /></button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
