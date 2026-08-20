import React from 'react';
import { 
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip, 
    ResponsiveContainer 
} from 'recharts';
import { SparklesIcon, RefreshCwIcon } from '../../../components/Icons';

interface KnowledgeROIProps {
    knowledgeRoi: any;
    handleRebuildIndex: () => Promise<void>;
    processingId: string | null;
}

export const KnowledgeROI: React.FC<KnowledgeROIProps> = ({ knowledgeRoi, handleRebuildIndex, processingId }) => {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
                {/* 60-Day ROI Trend Chart */}
                <div className="bg-gray-50/50 border border-gray-100 rounded-3xl p-6 mb-6">
                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                        <SparklesIcon className="w-3 h-3 text-indigo-500" /> Intelligence Yield (Conversion %)
                    </h4>
                    <div className="h-[250px]">
                        {knowledgeRoi?.trend && knowledgeRoi.trend.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={knowledgeRoi.trend}>
                                    <defs>
                                        <linearGradient id="colorROI" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={true} stroke="#f1f5f9" />
                                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}} interval={0} />
                                    <YAxis axisLine={false} tickLine={false} tick={{fontSize: 9, fontWeight: 800, fill: '#94a3b8'}} domain={[0, 100]} unit="%" />
                                    <ReTooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontSize: '12px'}} />
                                    <Area type="monotone" dataKey="conversion" stroke="#4f46e5" fillOpacity={1} fill="url(#colorROI)" strokeWidth={3} name="Conv %" isAnimationActive={false} />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex items-center justify-center text-gray-400 italic text-xs">Waiting for Knowledge Sensors...</div>
                        )}
                    </div>
                </div>

                {/* Domain ROI Table */}
                <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm">
                    <table className="w-full text-left text-xs">
                        <thead className="bg-gray-50 border-b border-gray-100">
                            <tr>
                                <th className="p-4 text-[10px] font-black text-gray-400 uppercase">Source Domain</th>
                                <th className="p-4 text-[10px] font-black text-gray-400 uppercase">Conversion</th>
                                <th className="p-4 text-[10px] font-black text-gray-400 uppercase text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {knowledgeRoi?.top_domains?.map((dom: any) => (
                                <tr key={dom.domain} className="group hover:bg-gray-50/50 transition-colors">
                                    <td className="p-4">
                                        <p className="font-bold text-gray-800">{dom.domain}</p>
                                        <p className="text-[9px] text-gray-400">{dom.yield} Nodes Ingested</p>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-1 bg-gray-100 rounded-full overflow-hidden">
                                                <div 
                                                    className={`h-full ${dom.severity === 'good' ? 'bg-green-500' : dom.severity === 'warning' ? 'bg-amber-500' : 'bg-red-500'}`}
                                                    style={{ width: `${dom.conversion}%` }}
                                                />
                                            </div>
                                            <span className="text-[10px] font-black text-gray-600">{dom.conversion}%</span>
                                        </div>
                                    </td>
                                    <td className="p-4 text-right">
                                        <button className="text-[9px] font-black text-indigo-600 uppercase hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 rounded px-1">Block</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="space-y-6">
                <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-4">RAG Control Lever</h4>
                    <div className="space-y-4 text-xs">
                        <div className="flex justify-between items-center pb-2 border-b border-gray-50">
                            <span className="text-gray-500">Embedding</span>
                            <span className="font-bold">v3-small</span>
                        </div>
                        <div className="flex justify-between items-center pb-2 border-b border-gray-50">
                            <span className="text-gray-500">Precision</span>
                            <span className="font-bold text-green-600">92% ✨</span>
                        </div>
                    </div>
                    <button 
                        onClick={handleRebuildIndex}
                        disabled={processingId === 'rebuild_index'}
                        className="w-full mt-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl font-black text-[10px] uppercase shadow-lg shadow-indigo-100 transition-all active:scale-95 flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2"
                        aria-label="Trigger full index rebuild"
                    >
                        {processingId === 'rebuild_index' ? (
                            <>
                                <RefreshCwIcon className="w-4 h-4 animate-spin" />
                                RE-INDEXING...
                            </>
                        ) : (
                            'TRIGGER FULL RE-INDEX'
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};
