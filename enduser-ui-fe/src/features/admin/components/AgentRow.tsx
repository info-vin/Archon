import React from 'react';

interface AgentRowProps {
    name: string;
    role: string;
    status: 'active' | 'standby' | 'offline';
    xpData: any;
    cost: number;
    roi: string;
    isActive: boolean;
}

export const AgentRow: React.FC<AgentRowProps> = ({ name, role, status, xpData, cost, roi, isActive }) => {
    // Dynamic Token Cost Color Scaling (Phase 4.6.15)
    const getCostBadge = (val: number) => {
        if (val === 0) return { label: 'LOW POWER', classes: 'bg-slate-100 text-slate-500 border-slate-200' };
        if (val < 0.1) return { label: 'STANDARD', classes: 'bg-blue-50 text-blue-600 border-blue-200' };
        if (val < 1.0) return { label: 'HIGH PERF', classes: 'bg-amber-50 text-amber-600 border-amber-200' };
        return { label: 'WATCHLIST', classes: 'bg-red-50 text-red-600 border-red-200 font-black' };
    };
    
    const badge = getCostBadge(cost);

    return (
        <div className="flex justify-between items-center border-b border-border/50 pb-3 last:border-0 last:pb-0">
            <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                <div>
                    <div className="font-bold text-sm flex items-center gap-2">
                        {name}
                        {xpData.level && <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">{xpData.level}</span>}
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-2">
                        {role}
                        {cost > 0 && (
                            <div className="flex items-center gap-1 ml-2 border-l border-border pl-2">
                                <span className={`text-[9px] px-1.5 py-0.5 rounded border ${badge.classes}`}>
                                    {badge.label}
                                </span>
                                <span className="text-[10px] text-slate-500 font-bold">${cost.toFixed(4)} spent</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            <div className="flex flex-col items-end gap-1">
                <div className="flex items-center gap-2">
                    <span className="text-[10px] font-black text-indigo-500 uppercase">ROI: {roi}</span>
                    <span className="text-xs font-mono uppercase bg-muted px-2 py-1 rounded">{status}</span>
                </div>
                <span className="text-xs font-bold text-indigo-600 font-mono">{xpData.total_xp} XP</span>
            </div>
        </div>
    );
};
