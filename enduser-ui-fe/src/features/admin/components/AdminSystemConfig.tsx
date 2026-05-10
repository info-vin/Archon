import React, { useMemo } from 'react';
import { RefreshCwIcon, ShieldCheckIcon } from '../../../components/Icons';
import { ConfigDrivenInput } from './ConfigDrivenInput';
import { useSystemSettings } from '../hooks/useAdminDashboard';

export const AdminSystemConfig: React.FC = () => {
    // Dynamic loading of all settings across categories
    const { settings, loading, isSaving, updateSetting } = useSystemSettings(['features', 'monitoring', 'api_keys', 'rag_strategy']);

    // Group settings by category dynamically
    const groupedSettings = useMemo(() => {
        console.log("AdminSystemConfig settings loaded:", settings);
        return settings.reduce((acc, curr) => {
            const cat = curr.category || 'general';
            if (!acc[cat]) acc[cat] = [];
            acc[cat].push(curr);
            return acc;
        }, {} as Record<string, any[]>);
    }, [settings]);

    const getIconForCategory = (category: string) => {
        if (category === 'system' || category.includes('diagnostic')) return <RefreshCwIcon className="w-5 h-5" />;
        return <ShieldCheckIcon className="w-5 h-5" />;
    };

    const getColorsForCategory = (category: string) => {
        switch (category) {
            case 'system': return 'border-orange-500 text-orange-600';
            case 'lead_scoring': return 'border-indigo-600 text-indigo-600';
            case 'crawler_rbac': return 'border-emerald-500 text-emerald-600';
            default: return 'border-blue-500 text-blue-600';
        }
    };

    const inferFieldType = (key: string, value: string) => {
        if (key.includes('JSON') || key.includes('RESTRICTED') || value?.includes('{') || value?.includes(',')) return 'textarea';
        if (!isNaN(Number(value))) return 'number';
        return 'text';
    };

    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-indigo-600" /></div>;

    if (!loading && settings.length === 0) {
        return (
            <div className="space-y-6 pb-20 font-sans">
                <div className="mb-4">
                    <h2 className="text-2xl font-bold text-gray-800">Dynamic System Configuration</h2>
                </div>
                <div className="bg-red-50 text-red-600 p-6 rounded-xl border border-red-200">
                    <h3 className="font-bold">Settings failed to load</h3>
                    <p>No settings were returned from the API. Please check your browser console (F12) for network errors.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 pb-20 font-sans">
            <div className="mb-4">
                <h2 className="text-2xl font-bold text-gray-800">Dynamic System Configuration</h2>
                <p className="text-sm text-gray-500">Settings are dynamically loaded from the `archon_settings` table. No hardcoded fields.</p>
            </div>

            {Object.entries(groupedSettings).map(([category, _catSettings]) => {
                const catSettings = _catSettings as any[];
                const colors = getColorsForCategory(category);
                
                return (
                    <div key={category} className={`bg-card p-6 rounded-2xl border border-border shadow-sm border-l-4 ${colors.split(' ')[0]}`}>
                        <h3 className={`text-lg font-bold mb-4 flex items-center gap-2 ${colors.split(' ')[1]}`}>
                            {getIconForCategory(category)}
                            {category.toUpperCase().replace('_', ' ')}
                        </h3>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {catSettings.map((setting: any) => {
                                const type = inferFieldType(setting.key, setting.value);
                                const fieldDef = { key: setting.key, type, label: setting.key };
                                
                                return (
                                    <div key={setting.key} className="p-4 bg-muted/20 rounded-xl border border-border flex flex-col justify-between gap-3 group transition-all hover:border-gray-400">
                                        <div>
                                            <div className={`font-bold text-[10px] uppercase tracking-widest ${colors.split(' ')[1]}/70 break-all`}>
                                                {setting.key}
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-1 leading-tight">{setting.description || 'No description provided.'}</p>
                                        </div>
                                        <div className="mt-2">
                                            <ConfigDrivenInput 
                                                field={fieldDef}
                                                value={setting.value || ''}
                                                onBlur={(v) => updateSetting(setting.key, v.toString())}
                                                isSaving={isSaving === setting.key}
                                                className={`w-full p-2 bg-background border border-border rounded-lg text-sm outline-none focus:ring-2 transition-all ${type === 'textarea' ? 'h-32 font-mono text-xs' : 'font-bold'}`}
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                );
            })}

            {Object.keys(groupedSettings).length === 0 && (
                <div className="text-center p-12 text-gray-500">
                    No settings found in the database.
                </div>
            )}
        </div>
    );
};
