import React from 'react';
import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip, 
    ResponsiveContainer, ReferenceLine, Label 
} from 'recharts';
import { SparklesIcon } from '../../../components/Icons';

interface SlaReliabilityProps {
    slaReliability: any;
}

export const SlaReliability: React.FC<SlaReliabilityProps> = ({ slaReliability }) => {
    return (
        <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 mb-8 min-h-[300px] flex flex-col">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-1 flex items-center gap-2">
                        <SparklesIcon className="w-3 h-3 text-indigo-500" /> Strategic Discipline Trend (180 Days)
                    </h4>
                    <p className="text-xl font-black text-gray-800">Current Health: <span className={(slaReliability?.current_sla || 0) >= 95 ? 'text-green-600' : 'text-amber-600'}>{slaReliability?.current_sla || 0}%</span></p>
                </div>
                <div className="text-right">
                    <p className="text-[10px] font-black text-gray-400 uppercase">Target SLA</p>
                    <p className="text-lg font-black text-gray-300">95.0%</p>
                </div>
            </div>
            <div className="flex-1 min-h-[220px]">
                {slaReliability?.trend && slaReliability.trend.length > 0 ? (
                    <ResponsiveContainer width="100%" height={220}>
                        <AreaChart data={slaReliability.trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorSLA" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#f1f5f9" />
                            <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}} interval={1} />
                            <YAxis axisLine={false} tickLine={false} tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}} domain={[80, 100]} />
                            <ReTooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontSize: '12px'}} />
                            <Area type="monotone" dataKey="rate" stroke="#4f46e5" fillOpacity={1} fill="url(#colorSLA)" strokeWidth={3} name="SLA %" isAnimationActive={false} />
                            <ReferenceLine y={95} stroke="#10b981" strokeDasharray="3 3" strokeWidth={1}>
                                <Label value="Goal" position="right" fill="#10b981" fontSize={9} fontWeight="bold" />
                            </ReferenceLine>
                        </AreaChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-full flex items-center justify-center text-gray-400 italic text-xs">Calibrating long-term reliability sensors...</div>
                )}
            </div>
        </div>
    );
};
