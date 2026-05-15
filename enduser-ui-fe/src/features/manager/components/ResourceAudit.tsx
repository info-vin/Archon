import React from 'react';
import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip, 
    ResponsiveContainer, Line 
} from 'recharts';

interface ResourceAuditProps {
    aiStats: any;
    isMaximized: boolean;
}

export const ResourceAudit: React.FC<ResourceAuditProps> = ({ aiStats, isMaximized }) => {
    return (
        <div className="space-y-8">
            {/* 1. Monetary Burn-up Chart */}
            <div className="bg-white rounded-3xl border border-gray-100 p-6 shadow-sm">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h4 className={`font-black text-gray-800 uppercase tracking-tight ${isMaximized ? 'text-lg' : 'text-sm'}`}>Monetary Burn-up</h4>
                        <p className="text-[10px] text-gray-400 font-bold uppercase mt-0.5">Y-Axis: Cumulative USD | X-Axis: 30 Day Timeline</p>
                    </div>
                    <div className="text-right">
                        <div className={`font-black text-indigo-600 tracking-tighter ${isMaximized ? 'text-3xl' : 'text-xl'}`}>${aiStats?.total_monthly_usd?.toFixed(2)}</div>
                        <div className="text-[8px] font-black text-gray-400 uppercase">{(aiStats?.total_monthly_tokens / 1000000).toFixed(2)}M Tokens Transferred</div>
                    </div>
                </div>
                
                <div className={`${isMaximized ? 'h-[450px]' : 'h-[280px]'} w-full transition-all duration-500`} key={`burn-${isMaximized}`}>
                    <ResponsiveContainer width="100%" height={isMaximized ? 500 : 320}>
                        <AreaChart data={aiStats?.burn_trend || []}>
                            <defs>
                                <linearGradient id="colorBurn" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#f1f5f9" />
                            <XAxis 
                                dataKey="date" 
                                axisLine={false} 
                                tickLine={false} 
                                tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}}
                                interval={6}
                            />
                            <YAxis 
                                domain={[0, 'auto']}
                                axisLine={false} 
                                tickLine={false} 
                                tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}}
                                dx={-5}
                            />
                            <ReTooltip 
                                contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: 'bold'}}
                            />
                            <Area 
                                type="monotone" 
                                dataKey="cost" 
                                stroke="#4f46e5" 
                                strokeWidth={3} 
                                fillOpacity={1} 
                                fill="url(#colorBurn)" 
                                animationDuration={1500}
                            />
                            {/* Budget Reference Line */}
                            <Line 
                                type="monotone" 
                                dataKey={() => aiStats?.budget_limit} 
                                stroke="#ef4444" 
                                strokeDasharray="10 10" 
                                strokeWidth={2} 
                                dot={false}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
                <div className="mt-4 flex gap-4 text-[9px] font-black uppercase text-gray-400">
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-indigo-500 rounded-full" /> Actual Spend</div>
                    <div className="flex items-center gap-1.5"><div className="w-3 h-0.5 bg-red-400 border-t border-dashed" /> Budget Cap (${aiStats?.budget_limit})</div>
                </div>
            </div>

            {/* 2. Team Synergy Matrix */}
            <div className="space-y-4">
                <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest px-1">Collaboration Efficiency Matrix</h4>
                <div className="bg-gray-50 rounded-3xl border border-gray-100 divide-y divide-gray-200 overflow-hidden shadow-sm">
                    {aiStats?.team?.map((member: any) => (
                        <div key={member.name} className="p-5 bg-white hover:bg-gray-50 transition-colors">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                                <div className="flex items-center gap-4 min-w-[180px]">
                                    <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 text-xs font-black">
                                        {member.name.substring(0, 2).toUpperCase()}
                                    </div>
                                    <div>
                                        <div className="text-sm font-bold text-gray-800">{member.name}</div>
                                        <div className="text-[9px] font-black text-indigo-500 uppercase tracking-tighter">{member.role}</div>
                                    </div>
                                </div>
                                
                                <div className="flex-1">
                                    <div className="flex justify-between text-[8px] font-black text-gray-400 mb-1.5 uppercase tracking-tighter">
                                        <span>Duty Window</span>
                                        <span className="text-indigo-600">Avg Assist: {member.avg_window}h/day</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                                        <div 
                                            className="h-full bg-indigo-500 rounded-full shadow-[0_0_8px_rgba(79,70,229,0.2)]"
                                            style={{ width: `${Math.min(100, (member.avg_window / 12) * 100)}%` }}
                                        />
                                    </div>
                                </div>

                                <div className="text-right min-w-[100px]">
                                    <div className="text-sm font-black text-gray-800">${member.total_cost.toFixed(2)}</div>
                                    <div className="text-[9px] font-bold text-gray-400 uppercase">{(member.total_tokens / 1000).toFixed(0)}k tkns</div>
                                </div>
                            </div>
                            
                            <div className="mt-4 flex flex-wrap gap-2">
                                {member.task_distribution.map((task: any) => (
                                    <span key={task.type} className={`px-2 py-0.5 text-[8px] font-black rounded-md uppercase tracking-tighter border ${
                                        task.type === 'Crawler/Research' 
                                        ? 'bg-amber-50 text-amber-600 border-amber-100' 
                                        : 'bg-indigo-50 text-indigo-600 border-indigo-100'
                                    }`}>
                                        {task.type}: {task.count} ops | {(task.tokens / 1000).toFixed(1)}k tkns
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
