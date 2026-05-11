import React from 'react';
import { 
    AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip as ReTooltip 
} from 'recharts';
import { SparklesIcon } from '../../../components/Icons';

interface PerformancePulseChartProps {
    data: any[];
}

export const PerformancePulseChart: React.FC<PerformancePulseChartProps> = ({ data }) => {
    return (
        <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 mb-8 min-h-[300px] flex flex-col">
            <h4 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                <SparklesIcon className="w-3 h-3" /> 30-Day Performance Pulse (Daily)
            </h4>
            <div className="flex-1 min-h-[220px]">
                {data && data.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%" minHeight={220}>
                        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <XAxis
                                dataKey="date"
                                axisLine={false}
                                tickLine={false}
                                fontSize={10}
                                interval={data.length > 0 ? Math.max(0, Math.floor(data.length / 3)) : 0}
                                tick={{fill: '#94a3b8'}}
                            />
                            <YAxis yAxisId="left" hide domain={[0, 'auto']} />
                            <YAxis yAxisId="right" hide domain={[0, 24]} />
                            <ReTooltip
                                contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'}}
                            />
                            <Area yAxisId="left" type="monotone" dataKey="bob_tokens" stroke="#6366f1" fillOpacity={1} fill="url(#colorTokens)" strokeWidth={2} name="Bob's Tokens" isAnimationActive={false} />
                            <Area yAxisId="right" type="monotone" dataKey="decision_hours" stroke="#f59e0b" fill="transparent" strokeWidth={2} strokeDasharray="5 5" name="Decision Gap (Hrs)" isAnimationActive={false} />
                        </AreaChart>                    </ResponsiveContainer>
                ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground italic text-xs">
                        No performance data recorded in the last 30 days.
                    </div>
                )}
            </div>
            {data && data.length > 0 && (
                <div className="flex justify-center gap-6 mt-4">
                    <span className="flex items-center gap-2 text-[10px] font-bold text-indigo-600"><div className="w-2 h-2 rounded-full bg-indigo-600"/> Cumulative Tokens</span>
                    <span className="flex items-center gap-2 text-[10px] font-bold text-amber-600"><div className="w-2 h-2 border-t-2 border-amber-600 border-dashed w-4"/> Wait Time (Max 24h)</span>
                </div>
            )}
        </div>
    );
};
