import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';

// PERFORMANCE: Hoisted Intl.NumberFormat to avoid expensive re-instantiations during render
const numberFormatter = new Intl.NumberFormat();

interface AiUsageData {
    total_budget: number;
    total_used: number;
    usage_percentage: number;
}

interface AiCollaborationWidgetProps {
    data: AiUsageData | null;
    onClick?: () => void;
}

export const AiCollaborationWidget: React.FC<AiCollaborationWidgetProps> = ({ data, onClick }) => {
    if (!data) return <div className="h-40 bg-gray-50 rounded-xl animate-pulse"></div>;

    const remaining = data.total_budget - data.total_used;
    const chartData = [
        { name: 'Used by Agents', value: data.total_used },
        { name: 'Available Budget', value: remaining }
    ];

    const COLORS = ['#6366f1', '#e5e7eb']; // Indigo-500, Gray-200

    const isExceeded = data.total_used >= data.total_budget;

    return (
        <>
            {isExceeded && (
                <div 
                    data-testid="budget-warning-banner" 
                    className="w-full mb-4 p-4 rounded-xl border border-red-500/30 bg-red-950/20 backdrop-blur-md text-red-400 font-bold flex items-center justify-between shadow-[0_0_15px_rgba(239,68,68,0.15)] animate-pulse"
                >
                    <div className="flex items-center gap-2">
                        <span className="text-lg">⚠️</span>
                        <span>AI Budget Exhausted! Shared AI Token allocation is fully depleted. Some automated tasks may be suspended.</span>
                    </div>
                    <span className="text-xs uppercase px-2 py-0.5 rounded bg-red-500/20 border border-red-500/30">Limit Exceeded</span>
                </div>
            )}
            <div 
                onClick={onClick}
                onKeyDown={(e) => {
                    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
                        e.preventDefault();
                        onClick();
                    }
                }}
                role={onClick ? 'button' : undefined}
                tabIndex={onClick ? 0 : undefined}
                aria-label={onClick ? 'View token consumption details' : undefined}
                className={`bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row items-center gap-8 min-h-[200px] ${onClick ? 'cursor-pointer hover:border-indigo-200 hover:shadow-md transition-all group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2' : ''}`}
            >
            <div className="flex-1">
                <h3 className={`text-lg font-bold text-gray-900 mb-1 ${onClick ? 'group-hover:text-indigo-600' : ''}`}>Human-AI Collaboration</h3>
                <p className="text-sm text-gray-500 mb-4">Resource allocation between human tasks and AI automation agents. {onClick && 'Click for details.'}</p>
                
                <div className="space-y-4">
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600 font-medium">Used Credits</span>
                            <span className="font-mono font-bold text-indigo-600">{numberFormatter.format(data?.total_used || 0)}</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                            <div style={{ width: `${data?.usage_percentage || 0}%` }} className="bg-indigo-500 h-full rounded-full transition-all duration-1000"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="w-40 h-40 relative">
                <ResponsiveContainer width={160} height={160}>
                    <PieChart>
                        <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={35}
                            outerRadius={55}
                            fill="#8884d8"
                            paddingAngle={5}
                            dataKey="value"
                            startAngle={90}
                            endAngle={-270}
                            stroke="none"
                        >
                            {chartData.map((_, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip 
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                            itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                        />
                    </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                    <span className="text-xl font-bold text-indigo-600">{data.usage_percentage}%</span>
                    <span className="text-[8px] uppercase tracking-widest text-gray-400">Load</span>
                </div>
            </div>
        </div>
        </>
    );
};
