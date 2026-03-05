import React from 'react';

interface CollabMatrixProps {
    collabSynergy: {
        nodes: string[];
        matrix: any[];
    };
}

export const CollabMatrix: React.FC<CollabMatrixProps> = ({ collabSynergy }) => {
    return (
        <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
                <div className="min-w-[1000px]">
                    {/* Matrix Header */}
                    <div className="grid grid-cols-10 bg-gray-50 border-b border-gray-100">
                        <div className="p-4 text-[9px] font-black text-gray-400 uppercase border-r italic">Origin \ Target</div>
                        {collabSynergy?.nodes.map((node: string) => (
                            <div key={node} className="p-4 text-center text-[9px] font-black text-gray-500 uppercase tracking-widest truncate">{node}</div>
                        ))}
                    </div>
                    {/* Matrix Rows */}
                    {collabSynergy?.matrix.map((row: any) => (
                        <div key={row.from} className="grid grid-cols-10 border-b border-gray-50 group hover:bg-indigo-50/20 transition-colors">
                            <div className="p-4 bg-gray-50/50 border-r border-gray-100 text-xs font-bold text-gray-700">{row.from}</div>
                            {row.interactions.map((cell: any, idx: number) => (
                                <div key={idx} className="p-3 flex flex-col justify-center gap-1.5 relative border-r border-gray-50 last:border-r-0">
                                    {row.from !== cell.to ? (
                                        <>
                                            <div className="flex justify-between items-center text-[8px] font-black uppercase text-gray-400">
                                                <span>Active Window</span>
                                                <span className="text-indigo-600">{(cell.synergy_score || 0)}%</span>
                                            </div>
                                            <div className="h-1 w-full bg-gray-100 rounded-full overflow-hidden">
                                                <div 
                                                    className={`h-full rounded-full transition-all duration-1000 ${
                                                        (cell.synergy_score || 0) > 80 ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]' : 
                                                        (cell.synergy_score || 0) > 40 ? 'bg-indigo-500' : 'bg-amber-400'
                                                    }`}
                                                    style={{ width: `${cell.synergy_score || 0}%` }}
                                                />
                                            </div>
                                            <div className="text-[7px] text-gray-300 font-bold uppercase tracking-tighter truncate">
                                                {cell.count || 0} Cross-links | 7D Momentum
                                            </div>
                                        </>
                                    ) : (
                                        <div className="flex items-center justify-center opacity-10">
                                            <div className="w-1 h-1 rounded-full bg-gray-400" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ))}
                </div>
            </div>
            <div className="p-4 bg-gray-50/30 flex items-center justify-between">
                <div className="flex gap-4 text-[9px] font-black uppercase tracking-widest">
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-green-500 rounded-full" /> Healthy Link (80+)</div>
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-indigo-500 rounded-full" /> Standard Link (40+)</div>
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-amber-400 rounded-full" /> At Risk Link (&lt;40)</div>
                </div>
                <div className="text-[9px] font-black text-gray-400 uppercase italic">Measured by 7D Interaction Persistence</div>
            </div>
        </div>
    );
};
