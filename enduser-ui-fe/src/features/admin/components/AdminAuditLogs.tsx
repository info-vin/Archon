import React from 'react';
import { SearchIcon, RefreshCwIcon } from '../../../components/Icons';
import { ConfigDrivenInput } from './ConfigDrivenInput';
import { useDocumentVersions } from '../hooks/useAdminDashboard';

const dateFormatter = new Intl.DateTimeFormat(undefined, {
    year: 'numeric', month: 'numeric', day: 'numeric',
    hour: 'numeric', minute: 'numeric', second: 'numeric'
});

const formatDateTime = (dateStr: string) => {
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? 'Invalid Date' : dateFormatter.format(d);
};

export const AdminAuditLogs: React.FC = () => {
    const { filteredVersions, searchTerm, setSearchTerm, loading } = useDocumentVersions();
    
    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm flex flex-col h-full max-h-[calc(100vh-250px)] font-sans">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <div>
                    <h2 className="text-xl font-bold">Document Version Audit Trail</h2>
                    <p className="text-xs text-muted-foreground italic">Track every configuration change across the system.</p>
                </div>
                
                <div className="relative w-full md:w-64">
                    <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <ConfigDrivenInput 
                        field={{ key: 'search', type: 'text', placeholder: 'Search logs...' }}
                        value={searchTerm}
                        onChange={setSearchTerm}
                        className="w-full pl-9 pr-4 py-2 bg-muted/50 border border-border rounded-xl text-sm focus:ring-2 ring-primary/30 outline-none transition-all"
                    />
                </div>
            </div>

            <div className="overflow-x-auto overflow-y-auto -mx-6 flex-1 min-h-0">
                <table className="min-w-full divide-y divide-border relative">
                    <thead className="bg-muted/50 sticky top-0 z-10">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Timestamp</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Changed By</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Type</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Field / Version</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Summary</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-card">
                        {loading ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center italic text-muted-foreground">
                                    <RefreshCwIcon className="animate-spin w-6 h-6 mx-auto mb-2 opacity-20" />
                                    Loading audit logs...
                                </td>
                            </tr>
                        ) : filteredVersions.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground italic">
                                    {searchTerm ? `No logs matching "${searchTerm}"` : 'No version history found.'}
                                </td>
                            </tr>
                        ) : (
                            filteredVersions.map(log => (
                                <tr key={log.id} className="hover:bg-muted/30 transition-colors group text-sm">
                                    <td className="px-6 py-4 whitespace-nowrap text-[10px] text-muted-foreground font-mono">
                                        {formatDateTime(log.created_at)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-bold flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-indigo-500"></div>
                                            {log.created_by}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-0.5 text-[9px] font-black uppercase rounded border ${
                                            log.change_type === 'CREATE' ? 'bg-green-50 text-green-700 border-green-200' : 
                                            log.change_type === 'DELETE' ? 'bg-red-50 text-red-700 border-red-200' :
                                            'bg-indigo-50 text-indigo-700 border-indigo-200'
                                        }`}>{log.change_type}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-xs">
                                        <span className="font-mono bg-muted px-1 rounded">{log.field_name}</span>
                                        <span className="ml-2 text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">REV-{log.version_number}</span>
                                    </td>
                                    <td className="px-6 py-4 text-xs text-slate-600 dark:text-slate-400 max-w-xs truncate font-medium" title={log.change_summary || ''}>
                                        {log.change_summary || 'N/A'}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
