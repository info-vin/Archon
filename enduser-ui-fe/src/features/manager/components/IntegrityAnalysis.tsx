import React from 'react';
import { 
    ResponsiveContainer, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip as ReTooltip, Area, Line 
} from 'recharts';

interface IntegrityAnalysisProps {
    healthTrend: {
        trend: any[];
        audit: any[];
    } | null;
    isMaximized: boolean;
}

export const IntegrityAnalysis: React.FC<IntegrityAnalysisProps> = ({ healthTrend, isMaximized }) => {
    const trendData = healthTrend?.trend || [];
    const auditData = healthTrend?.audit || [];

    return (
        <div className="space-y-8">
            <div className="bg-white rounded-3xl border border-gray-100 p-6 shadow-sm">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h4 className={`font-black text-gray-800 uppercase tracking-tight ${isMaximized ? 'text-lg' : 'text-sm'}`}>Health Variance Trend</h4>
                        <p className="text-[10px] text-gray-400 font-bold uppercase mt-0.5">Y-Axis: Integrity Score (%) | X-Axis: 30 Day Timeline</p>
                    </div>
                </div>
                
                <div className={`${isMaximized ? 'h-[500px]' : 'h-[320px]'} w-full transition-all duration-500`} key={`integrity-${isMaximized}`}>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={trendData.length > 0 ? trendData : [{date: '', daily: 100, baseline: 100}]}>
                            <defs>
                                <linearGradient id="colorDaily" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#f1f5f9" />
                            <XAxis 
                                dataKey="date" 
                                axisLine={false} 
                                tickLine={false} 
                                interval={0}
                                tick={(props: any) => {
                                    const { x, y, payload, index } = props;
                                    const val = payload?.value || '';
                                    if (index % 7 !== 0 && index !== trendData.length - 1) return <g/>;
                                    return (
                                        <text x={x} y={(Number(y) || 0) + 12} fontSize={10} fontWeight={800} fill="#94a3b8" textAnchor="middle" className="uppercase">
                                            {val}
                                        </text>
                                    );
                                }}
                            />
                            <YAxis 
                                domain={trendData.length > 0 ? ['dataMin - 1', 100] : [0, 100]} 
                                axisLine={false} 
                                tickLine={false} 
                                tick={{fontSize: 10, fontWeight: 700, fill: '#94a3b8'}}
                                dx={-10}
                            />
                            <ReTooltip 
                                contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: 'bold'}}
                                cursor={{stroke: '#4f46e5', strokeWidth: 1, strokeDasharray: '4 4'}}
                            />
                            <Area 
                                type="monotone" 
                                dataKey="daily" 
                                stroke="#4f46e5" 
                                strokeWidth={3} 
                                fillOpacity={1} 
                                fill="url(#colorDaily)" 
                                isAnimationActive={false}
                                dot={{ stroke: '#4f46e5', strokeWidth: 2, fill: '#fff', r: 2 }}
                                activeDot={{ r: 6, strokeWidth: 0 }}
                            />
                            <Line 
                                type="monotone" 
                                dataKey="baseline" 
                                stroke="#cbd5e1" 
                                strokeDasharray="5 5" 
                                strokeWidth={2} 
                                dot={false}
                                isAnimationActive={false}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="space-y-4">
                <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest px-1">System Health Audit Trail</h4>
                <div className="bg-gray-50 rounded-3xl border border-gray-100 divide-y divide-gray-200 overflow-hidden">
                    {auditData.length > 0 ? auditData.map((log: any, idx: number) => {
                        const details = log.details || {};
                        const score = details.score || 0;
                        const total = details.total_sources || 0;
                        const indexed = details.indexed_sources || 0;
                        const dbOk = details.db_connected !== false;
                        const searchOk = details.search_active !== false;
                        
                        return (
                            <div key={idx} className="p-4 flex justify-between items-center bg-white hover:bg-gray-50 transition-colors">
                                <div>
                                    <div className="text-sm font-bold text-gray-800">Integrity Audit: {score}%</div>
                                    <div className="flex gap-3 mt-1 text-[9px] font-black uppercase tracking-tighter">
                                        <span className={total > 0 && indexed/total >= 0.95 ? 'text-green-600' : 'text-amber-600'}>Align: {indexed}/{total}</span>
                                        <span className={dbOk ? 'text-green-600' : 'text-red-600'}>DB: {dbOk ? 'READY' : 'LOST'}</span>
                                        <span className={searchOk ? 'text-green-600' : 'text-red-600'}>Search: {searchOk ? 'ACTIVE' : 'FAIL'}</span>
                                    </div>
                                </div>
                                <span className={`text-[10px] font-black px-2.5 py-1 rounded-full ${log.level === 'INFO' ? 'text-green-600 bg-green-50' : 'text-amber-600 bg-amber-50'}`}>{log.level}</span>
                            </div>
                        );
                    }) : (
                        <div className="p-12 text-center text-gray-400 text-xs font-bold uppercase italic">No recent health events found</div>
                    )}
                </div>
            </div>
        </div>
    );
};
