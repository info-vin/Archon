import { MetricCategory } from '../hooks/useManagerNexusStats';
import { Skeleton } from '../../../components/Skeleton';

export interface HUDCardProps {
    id: MetricCategory;
    label: string;
    value: string;
    sub: string;
    active: boolean;
    status: 'good' | 'bad' | 'warning' | 'neutral';
    onClick: (id: MetricCategory) => void;
    tooltip?: string;
    loading?: boolean;
}

export const HUDCard: React.FC<HUDCardProps> = ({
    id, label, value, sub, active, status, onClick, tooltip, loading
}) => {
    const statusColor = status === 'good' ? 'bg-green-500' : 
                       status === 'bad' ? 'bg-red-500' : 
                       status === 'warning' ? 'bg-amber-500' : 
                       'bg-slate-400';
    return (
        <div 
            onClick={() => onClick(id)} 
            className={`group relative p-5 rounded-3xl border transition-all cursor-pointer select-none ${
                active 
                ? 'bg-white border-indigo-500 shadow-xl scale-[1.02] ring-4 ring-indigo-50/50' 
                : 'bg-white border-gray-100 hover:border-gray-300 hover:shadow-md'
            }`}
        >
            <div className="flex justify-between items-start mb-3">
                <span className={`text-[10px] font-black uppercase tracking-widest transition-colors ${active ? 'text-indigo-600' : 'text-gray-400 group-hover:text-indigo-500'}`}>
                    {label}
                </span>
                <div className={`w-2 h-2 rounded-full ${statusColor} shadow-[0_0_8px_currentColor] ${active ? 'animate-pulse' : ''}`} />
            </div>
            <div className={`text-2xl font-black tracking-tighter ${active ? 'text-indigo-600' : 'text-gray-800'}`}>
                {loading ? <Skeleton className="h-8 w-20 mb-1" /> : value}
            </div>
            <div className="text-[9px] text-gray-400 font-bold opacity-60 mt-1 uppercase tracking-tighter truncate">
                {loading ? <Skeleton className="h-3 w-16" /> : sub}
            </div>
            
            {/* Tooltip */}
            {tooltip && (
                <div className="absolute opacity-0 group-hover:opacity-100 transition-opacity bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-900 text-white text-[10px] rounded-lg whitespace-nowrap pointer-events-none z-10">
                    {tooltip}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                </div>
            )}
        </div>
    );
};
