import React from 'react';
import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip, 
    ResponsiveContainer, ReferenceLine, Label 
} from 'recharts';
import { ZapIcon, SearchIcon } from '../../../components/Icons';
import UserAvatar from '../../../components/UserAvatar';

interface ActiveForceProps {
    forceReadiness: any;
    team: any[];
    overview: any;
    setSelectedMember: (member: any) => void;
}

export const ActiveForce: React.FC<ActiveForceProps> = ({
    forceReadiness, team, overview, setSelectedMember
}) => {
    return (
        <div className="space-y-8">
            {/* Combat Power HUD */}
            <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 mb-8 min-h-[300px] flex flex-col">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-1 flex items-center gap-2">
                            <ZapIcon className="w-3 h-3 text-indigo-500" /> 90-Day Combat Power vs. Average Baseline
                        </h4>
                        <p className="text-xl font-black text-gray-800">Rating: <span className="text-indigo-600">A+ ⚡</span></p>
                    </div>
                    <div className="text-right">
                        <p className="text-[10px] font-black text-gray-400 uppercase">Automation Rate</p>
                        <p className="text-lg font-black text-indigo-600">{forceReadiness?.automation_rate || 68}%</p>
                    </div>
                </div>
                
                <div className="flex-1 min-h-[220px]">
                    {forceReadiness?.trend && forceReadiness.trend.length > 0 ? (
                        <ResponsiveContainer width="100%" height={220}>
                            <AreaChart data={forceReadiness.trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorActualForce" x1="0" y1="0" x2="0" y2="1">
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
                                    interval={8} 
                                />
                                <YAxis 
                                    axisLine={false} 
                                    tickLine={false} 
                                    tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}}
                                    domain={[0, 'auto']}
                                />
                                <ReTooltip 
                                    contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: 'bold'}}
                                />
                                <ReferenceLine 
                                    y={forceReadiness?.baseline || 0} 
                                    stroke="#ef4444" 
                                    strokeDasharray="5 5" 
                                    strokeWidth={2}
                                >
                                    <Label value={`Avg: ${forceReadiness?.baseline}`} position="top" fill="#ef4444" fontSize={10} fontWeight="bold" />
                                </ReferenceLine>

                                <Area 
                                    type="monotone" 
                                    dataKey="actual" 
                                    stroke="#4f46e5" 
                                    fillOpacity={1} 
                                    fill="url(#colorActualForce)" 
                                    strokeWidth={3} 
                                    name="Daily Output" 
                                    isAnimationActive={false}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-full flex items-center justify-center text-gray-400 italic text-xs">
                            Initializing combat power sensors...
                        </div>
                    )}
                </div>
                <div className="flex justify-center gap-6 mt-4 border-t border-gray-100 pt-4">
                    <span className="flex items-center gap-2 text-[9px] font-black text-indigo-600 uppercase tracking-widest"><div className="w-2 h-2 rounded-full bg-indigo-600"/> Current Output</span>
                    <span className="flex items-center gap-2 text-[9px] font-black text-gray-400 uppercase tracking-widest"><div className="w-2 h-2 border-t-2 border-gray-400 border-dashed w-4"/> 90-Day Baseline</span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {team.map(member => (
                    <div key={member.id} className="p-4 bg-white border border-gray-100 rounded-2xl flex items-center justify-between hover:border-indigo-200 transition-all">
                        <div className="flex items-center gap-3">
                            <UserAvatar name={member.name} role={member.role} />
                            <div>
                                <h4 className="font-bold text-gray-800 text-sm">{member.name}</h4>
                                <div className="flex items-center gap-1.5">
                                    <div className={`w-1.5 h-1.5 rounded-full ${member.status === 'active' ? 'bg-green-500' : 'bg-amber-500'}`} />
                                    <span className="text-xs text-gray-500 uppercase">{member.role}</span>
                                </div>
                            </div>
                        </div>
                        <button 
                            onClick={() => setSelectedMember(member)}
                            className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
                            aria-label={`View details for ${member.name}`}
                            title={`View details for ${member.name}`}
                        >
                            <SearchIcon className="w-4 h-4" />
                        </button>
                    </div>
                ))}
                {/* Agent Cards - Dynamic */}
                {overview?.active_agents?.map((agent: any) => (
                    <div key={agent.id} className="p-4 bg-indigo-50/50 border border-indigo-100 rounded-2xl flex items-center justify-between opacity-80">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white"><ZapIcon className="w-4 h-4"/></div>
                            <div>
                                <h4 className="font-bold text-indigo-900 text-sm">{agent.name}</h4>
                                <p className="text-[10px] text-indigo-600 uppercase">{agent.role || 'AI Agent'}</p>
                            </div>
                        </div>
                        <span className={`px-2 py-1 text-[10px] font-bold rounded ${agent.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-500'}`}>
                            {agent.status === 'active' ? 'ONLINE' : 'STANDBY'}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
};
