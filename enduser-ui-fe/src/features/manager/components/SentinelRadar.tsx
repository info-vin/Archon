import React from 'react';
import { ZapIcon, CheckCircleIcon, RefreshCwIcon } from '../../../components/Icons';

interface SentinelRadarProps {
    businessRisks: any[];
    processingId: string | null;
    handleDispatch: (alertId: string) => Promise<void>;
    rules: any[];
    rulesMeta: { version: string };
    isSavingRules?: boolean;
    totalRuleWeight: number;
    handleRuleChange: (key: string, weight: number) => void;
    handleSaveRules: () => Promise<void>;
}

// PERFORMANCE: Hoist Intl.DateTimeFormat instance outside the component to avoid expensive repeated instantiations (implicitly called by toLocaleDateString) inside the render loop.
const dateFormatter = new Intl.DateTimeFormat(undefined);
const safeFormatSentinelDate = (dateVal: any) => {
    const d = new Date(dateVal);
    return isNaN(d.getTime()) ? 'Invalid Date' : dateFormatter.format(d);
};

export const SentinelRadar: React.FC<SentinelRadarProps> = ({
    businessRisks, processingId, handleDispatch,
    rules, rulesMeta, isSavingRules, totalRuleWeight, handleRuleChange, handleSaveRules
}) => {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
                <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4">Actionable Threats ({businessRisks.length})</h4>
                <div className="space-y-3">
                    {businessRisks.map(alert => (
                        <div key={alert.id} className="bg-white border-l-4 border-l-red-500 border-y border-r border-gray-100 p-4 rounded-r-xl flex items-center justify-between group hover:shadow-md transition-all">
                            <div className="flex items-center gap-4">
                                <div className="bg-red-50 p-3 rounded-xl text-red-600">
                                    <ZapIcon className="w-5 h-5" />
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-[10px] font-black px-2 py-0.5 bg-red-100 text-red-700 rounded uppercase tracking-tighter">{alert.details?.type?.replace('_', ' ') || 'RISK'}</span>
                                        <span className="text-[10px] text-gray-400 font-mono">{safeFormatSentinelDate(alert.created_at)}</span>
                                    </div>
                                    <h5 className="font-bold text-gray-800 text-sm mt-1">{alert.message}</h5>
                                    <p className="text-[10px] text-gray-500 italic mt-0.5">{alert.details?.company || alert.details?.title || 'System context attached'}</p>
                                </div>
                            </div>
                            <button 
                                onClick={() => handleDispatch(alert.id)}
                                disabled={processingId === alert.id}
                                className="px-5 py-2.5 bg-red-600 text-white rounded-xl text-xs font-black hover:bg-red-700 shadow-lg shadow-red-100 transition-all active:scale-95 disabled:opacity-50"
                            >
                                {processingId === alert.id ? '...' : 'DISPATCH'}
                            </button>
                        </div>
                    ))}
                    {businessRisks.length === 0 && (
                        <div className="py-16 bg-green-50/30 border-2 border-dashed border-green-100 rounded-3xl flex flex-col items-center justify-center text-center">
                            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-4">
                                <CheckCircleIcon className="w-8 h-8" />
                            </div>
                            <h4 className="text-lg font-black text-green-800">ALL SYSTEMS NOMINAL</h4>
                            <p className="text-xs text-green-600 mt-1 max-w-[240px]">Sentinel Radar reports zero business logic anomalies in the last 30 days.</p>
                        </div>
                    )}
                </div>
            </div>
            
            <div className="bg-gray-50 p-6 rounded-2xl border border-gray-100">
                <div className="flex justify-between items-center mb-4">
                    <h4 className="text-xs font-black text-gray-500 uppercase tracking-widest">Scoring Config</h4>
                    <span className="text-[10px] font-mono text-gray-400">{rulesMeta.version}</span>
                </div>
                <div className="space-y-4 mb-6">
                    {rules.map(rule => (
                        <div key={rule.key}>
                            <div className="flex justify-between text-xs mb-1">
                                <span className="font-bold text-gray-700">{rule.label}</span>
                                <span className="font-mono text-gray-500">{rule.weight}%</span>
                            </div>
                            <input 
                                type="range" 
                                min="0" max="100" 
                                value={rule.weight}
                                aria-label={`Adjust weight for ${rule.label}`}
                                onChange={e => handleRuleChange(rule.key, parseInt(e.target.value))}
                                className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                            />
                        </div>
                    ))}
                </div>
                <div className="flex justify-between items-center pt-4 border-t border-gray-200">
                    <span className={`text-xs font-bold ${totalRuleWeight === 100 ? 'text-green-500' : 'text-red-500'}`}>
                        Total: {totalRuleWeight}%
                    </span>
                    <button
                        onClick={handleSaveRules}
                        disabled={isSavingRules}
                        className="text-xs font-bold text-indigo-600 hover:underline disabled:opacity-50 flex items-center gap-1"
                    >
                        {isSavingRules ? (
                            <>
                                <RefreshCwIcon className="w-3 h-3 animate-spin" />
                                Saving...
                            </>
                        ) : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    );
};
