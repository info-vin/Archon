import React, { useMemo } from 'react';
import { RefreshCwIcon, ShieldCheckIcon } from '../../../components/Icons';
import { ConfigDrivenInput } from './ConfigDrivenInput';
import { useSystemSettings } from '../hooks/useAdminDashboard';

export const AdminSystemConfig: React.FC = () => {
    // Dynamic loading of all settings across categories
    const { settings, loading, updateSetting } = useSystemSettings(['features', 'monitoring', 'api_keys', 'rag_strategy']);

    const groupedSettings = useMemo(() => {
        return settings
            .filter((curr: any) => curr.key !== 'HF_TOKEN' && curr.key !== 'forced_fallback_tier')
            .reduce((acc: Record<string, any[]>, curr: any) => {
                const cat = curr.category || 'general';
                // Pre-calculate formatted strings to avoid O(N) regex evaluation on every render cycle
                const formattedCategory = cat.replace(/_/g, ' ');
                const formattedKey = curr.key.replace(/_/g, ' ');

                if (!acc[formattedCategory]) acc[formattedCategory] = [];
                acc[formattedCategory].push({
                    ...curr,
                    formatted_key: formattedKey
                });
                return acc;
            }, {} as Record<string, any[]>);
    }, [settings]);

    if (loading) return <div className="flex justify-center p-12"><RefreshCwIcon className="animate-spin w-8 h-8 text-indigo-600" /></div>;

    return (
        <div className="space-y-6 pb-20 font-sans">
            <div className="mb-4">
                <h2 className="text-2xl font-bold text-gray-800">Dynamic System Configuration</h2>
                <p className="text-sm text-gray-500">Settings are dynamically loaded from the `archon_settings` table. No hardcoded fields.</p>
            </div>
            
            {Object.keys(groupedSettings).length === 0 ? (
                <div className="bg-amber-50 text-amber-700 p-6 rounded-xl border border-amber-200">
                    <h3 className="font-bold">No settings loaded</h3>
                    <p>The system settings table is empty. Please ensure the seed script has been executed.</p>
                </div>
            ) : (
                Object.entries(groupedSettings).map(([category, catSettings]) => (
                    <div key={category} className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                        <h3 className="text-lg font-bold mb-6 capitalize flex items-center gap-2">
                            <ShieldCheckIcon className="w-5 h-5 text-indigo-500" />
                            {category}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {catSettings
                                .map((s: any) => {
                                let fieldConfig: any = { 
                                    key: s.key, 
                                    label: s.formatted_key,
                                    type: !isNaN(Number(s.value)) ? 'number' : 'text' 
                                };

                                return (
                                    <ConfigDrivenInput 
                                        key={s.key}
                                        field={fieldConfig}
                                        value={s.value}
                                        onChange={(v: string) => updateSetting(s.key, v)}
                                    />
                                );
                            })}
                        </div>
                    </div>
                ))
            )}
        </div>
    );
};
