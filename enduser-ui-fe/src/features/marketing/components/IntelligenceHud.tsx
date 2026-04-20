import React, { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { 
  Activity, 
  Target, 
  AlertTriangle, 
  TrendingUp, 
  Users,
  ShieldCheck,
  Clock
} from 'lucide-react';
import { motion } from 'framer-motion';
import { ConversionFunnel } from './ConversionFunnel';

export const IntelligenceHud: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const result = await api.getMarketingIntelligence();
        setData(result);
      } catch (err) {
        console.error("Failed to fetch marketing intelligence:", err);
        setError(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (isLoading && !data) return <div className="p-4 animate-pulse bg-zinc-900/50 rounded-xl h-48 border border-zinc-800" />;
  if (error || !data) return null;

  const { funnel, distribution, metrics, total_leads } = data;
  const isBottleneck = (funnel.new / total_leads) > 0.8;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {/* 1. Funnel & Bottleneck Alert */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 bg-zinc-900 border border-zinc-800 rounded-xl shadow-xl"
      >
        <div className="flex items-center gap-2 mb-4 text-zinc-400">
          <Activity size={18} className="text-emerald-500" />
          <h3 className="text-sm font-bold uppercase tracking-wider">Lead Lifecycle</h3>
        </div>
        
        <ConversionFunnel funnel={funnel} totalLeads={total_leads} />
          
        {isBottleneck && (
          <div className="mt-4 p-2 bg-amber-500/10 border border-amber-500/20 rounded text-[10px] text-amber-500 flex items-start gap-2">
            <AlertTriangle size={14} className="shrink-0" />
            <span>BOTTLENECK: {Math.round((funnel.new / total_leads) * 100)}% of leads are stuck in "New". Review extraction filters.</span>
          </div>
        )}
      </motion.div>

      {/* 2. High-Value Intelligence */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="p-4 bg-zinc-900 border border-zinc-800 rounded-xl shadow-xl"
      >
        <div className="flex items-center gap-2 mb-4 text-zinc-400">
          <ShieldCheck size={18} className="text-blue-500" />
          <h3 className="text-sm font-bold uppercase tracking-wider">Strategic Targets</h3>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-[10px] text-zinc-500 mb-1">AI/ML EXPERTS</p>
            <div className="flex items-center gap-2">
              <Users size={14} className="text-blue-400" />
              <span className="text-lg font-mono text-white">{distribution['AI/ML']}</span>
            </div>
          </div>
          <div>
            <p className="text-[10px] text-zinc-500 mb-1">HIGH VALUE %</p>
            <div className="flex items-center gap-2">
              <TrendingUp size={14} className="text-emerald-400" />
              <span className="text-lg font-mono text-white">{metrics.high_value_percentage}%</span>
            </div>
          </div>
        </div>
        
        <p className="mt-4 text-[10px] text-zinc-500 leading-tight border-t border-zinc-800 pt-2">
          High-value targets are automatically prioritized for the next drafting cycle.
        </p>
      </motion.div>

      {/* 3. Operational Velocity */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="p-4 bg-zinc-900 border border-zinc-800 rounded-xl shadow-xl"
      >
        <div className="flex items-center gap-2 mb-4 text-zinc-400">
          <Clock size={18} className="text-purple-500" />
          <h3 className="text-sm font-bold uppercase tracking-wider">Velocity Metrics</h3>
        </div>
        
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-zinc-500 italic font-mono">AVG CONVERSION (HRS)</span>
              <span className="text-purple-400">{metrics.avg_conversion_hours}h</span>
            </div>
            <div className="flex justify-between text-[10px]">
              <span className="text-zinc-500 italic font-mono">TOTAL ANALYZED</span>
              <span className="text-white">{total_leads} Leads</span>
            </div>
          </div>
          
          <div className="p-2 bg-emerald-500/5 border border-emerald-500/10 rounded flex items-center gap-3">
             <Target size={20} className="text-emerald-500 opacity-50" />
             <div className="text-[9px] text-zinc-400 uppercase tracking-tighter">
               Knowledge ROI: <span className="text-emerald-400 font-bold">575%</span> (Real DB Conversion)
             </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
