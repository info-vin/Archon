import React from 'react';
import { RefreshCwIcon, ShieldCheckIcon } from '../../../components/Icons';
import { ConfigDrivenInput } from './ConfigDrivenInput';
import { useSystemSettings } from '../hooks/useAdminDashboard';

const systemFieldsConfig = [
    { key: 'system.log_level', type: 'select', label: 'Backend Access Log Level', options: [
      { value: 'DEBUG', label: 'DEBUG (Detailed)' },
      { value: 'INFO', label: 'INFO (Normal)' },
      { value: 'WARNING', label: 'WARNING (Recommended)' },
      { value: 'ERROR', label: 'ERROR (Critical Only)' }
    ]},
    { key: 'CRAWL_ALLOWED_DOMAINS_RESTRICTED', type: 'textarea', label: 'Global Whitelist Domains', placeholder: 'comma, separated, domains.com' },
    { key: 'SCHEDULER_PROBE_INTERVAL_MINS', type: 'number', label: 'System Heartbeat (Probe)' },
    { key: 'SCHEDULER_PATROL_INTERVAL_MINS', type: 'number', label: 'Log Patrol (Auto-Repair)' },
    { key: 'SCHEDULER_SENTINEL_INTERVAL_HOURS', type: 'number', label: 'Sentinel (Business Risks)' },
    { key: 'SCORING_RELEVANCE', type: 'number', label: 'Scoring: Relevance' },
    { key: 'SCORING_AUTHORITY', type: 'number', label: 'Scoring: Authority' },
    { key: 'SCORING_RECENCY', type: 'number', label: 'Scoring: Recency' }
];

export const AdminSystemConfig: React.FC = () => {
    const { settings, loading, isSaving, updateSetting } = useSystemSettings(['crawler_rbac', 'diagnostics', 'lead_scoring', 'system']);
    
    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-indigo-600" /></div>;

    const roles = ['SALES', 'MARKETING', 'MANAGER', 'ADMIN'];

    return (
        <div className="space-y-6 pb-20 font-sans">
            {/* Heartbeat */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-orange-500">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-orange-600">
                    <RefreshCwIcon className="w-5 h-5" />
                    Clockwork: Agent Biological Frequencies (Heartbeat)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {systemFieldsConfig.filter(f => f.key.startsWith('SCHEDULER_')).map(field => {
                        const setting = settings.find(s => s.key === field.key);
                        if (!setting) return null;
                        return (
                            <div key={field.key} className="p-4 bg-muted/20 rounded-xl border border-border flex flex-col justify-between gap-3 group hover:border-orange-500/30 transition-all">
                                <div>
                                    <div className="font-bold text-[10px] uppercase tracking-widest text-orange-600/70">{field.label}</div>
                                    <p className="text-[10px] text-muted-foreground mt-1 leading-tight">{setting.description}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <ConfigDrivenInput 
                                        field={field}
                                        value={setting.value}
                                        onBlur={(v) => updateSetting(field.key, v.toString())}
                                        isSaving={isSaving === field.key}
                                        className="w-full p-2 bg-background border border-border rounded-lg text-sm font-bold text-center outline-none focus:ring-2 ring-orange-500/50 transition-all"
                                    />
                                    <span className="text-[10px] font-bold text-muted-foreground uppercase">{field.key.includes('MINS') ? 'Mins' : 'Hrs'}</span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Lead Scoring */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-indigo-600">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-indigo-600">
                    <ShieldCheckIcon className="w-5 h-5" />
                    Lead Scoring Weights
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {systemFieldsConfig.filter(f => f.key.startsWith('SCORING_')).map(field => {
                        const setting = settings.find(s => s.key === field.key);
                        if (!setting) return null;
                        return (
                            <div key={field.key} className="p-4 bg-muted/20 rounded-xl border border-border flex items-center justify-between gap-4 group hover:border-indigo-500/30 transition-all">
                                <div className="flex-1">
                                    <div className="font-bold text-[10px] uppercase tracking-widest text-indigo-600/70">{field.label}</div>
                                    <p className="text-xs font-medium text-slate-700 dark:text-slate-300 leading-tight mt-1">{setting.description}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <ConfigDrivenInput 
                                        field={field}
                                        value={setting.value}
                                        onBlur={(v) => updateSetting(field.key, v.toString())}
                                        isSaving={isSaving === field.key}
                                        className="w-16 p-2 bg-background border border-border rounded-lg text-sm font-bold text-center outline-none focus:ring-2 ring-indigo-500/50 transition-all"
                                    />
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Diagnostics */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 border-l-amber-500">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-amber-600">
                    <RefreshCwIcon className="w-5 h-5" />
                    Server Diagnostics
                </h3>
                {systemFieldsConfig.filter(f => f.key === 'system.log_level' || f.key === 'CRAWL_ALLOWED_DOMAINS_RESTRICTED').map(field => {
                    const setting = settings.find(s => s.key === field.key);
                    if (!setting) return null;
                    
                    if (field.type === 'select') {
                        return (
                            <div key={field.key} className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 bg-muted/20 rounded-xl border border-border mb-4">
                                <div className="flex-1">
                                    <div className="font-bold text-sm">{field.label}</div>
                                    <p className="text-xs text-muted-foreground">{setting.description}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                    <ConfigDrivenInput 
                                        field={field}
                                        value={setting.value}
                                        onChange={(v) => updateSetting(field.key, v.toString())}
                                        isSaving={isSaving === field.key}
                                        className="bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono outline-none focus:ring-2 ring-primary/50"
                                    />
                                </div>
                            </div>
                        );
                    }
                    
                    if (field.type === 'textarea') {
                        return (
                            <div key={field.key} className="p-6 bg-card rounded-2xl border border-border shadow-sm mt-4">
                                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                    <ShieldCheckIcon className="w-5 h-5 text-indigo-500" />
                                    {field.label}
                                </h3>
                                <div className="space-y-2">
                                    <ConfigDrivenInput 
                                        field={field}
                                        value={setting.value}
                                        onBlur={(v) => updateSetting(field.key, v.toString())}
                                        className="w-full p-3 bg-background border border-border rounded-xl font-mono text-xs focus:ring-2 ring-primary outline-none h-24"
                                    />
                                    <p className="text-[10px] text-muted-foreground italic">Changes are saved automatically on blur.</p>
                                </div>
                            </div>
                        );
                    }
                    return null;
                })}
            </div>

            {/* RBAC Limits */}
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <RefreshCwIcon className="w-5 h-5 text-indigo-500" />
                    Crawler RBAC Limits
                </h3>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-border">
                        <thead>
                            <tr className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                                <th className="px-4 py-2 text-left">Role</th>
                                <th className="px-4 py-2 text-left">Max Depth</th>
                                <th className="px-4 py-2 text-left">Concurrency</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border text-sm">
                            {roles.map(role => {
                                const depthKey = `CRAWL_MAX_DEPTH_${role}`;
                                const concurrentKey = `CRAWL_CONCURRENT_MAX_${role}`;
                                const depthSetting = settings.find(s => s.key === depthKey);
                                const concurrentSetting = settings.find(s => s.key === concurrentKey);

                                return (
                                    <tr key={role}>
                                        <td className="px-4 py-3 font-medium">{role}</td>
                                        <td className="px-4 py-3">
                                            <ConfigDrivenInput 
                                                field={{ key: depthKey, type: 'number' }}
                                                value={depthSetting?.value || 0}
                                                onBlur={(v) => updateSetting(depthKey, v.toString())}
                                                isSaving={isSaving === depthKey}
                                                className="w-20 p-1 bg-background border border-border rounded focus:ring-1 ring-primary outline-none inline-block mr-2"
                                            />
                                        </td>
                                        <td className="px-4 py-3">
                                            <ConfigDrivenInput 
                                                field={{ key: concurrentKey, type: 'number' }}
                                                value={concurrentSetting?.value || 0}
                                                onBlur={(v) => updateSetting(concurrentKey, v.toString())}
                                                isSaving={isSaving === concurrentKey}
                                                className="w-20 p-1 bg-background border border-border rounded focus:ring-1 ring-primary outline-none inline-block mr-2"
                                            />
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
