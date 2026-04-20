import React from 'react';
import { motion } from 'framer-motion';

interface FunnelData {
  new: number;
  contacted: number;
  shortlisted: number;
  converted: number;
  archived: number;
}

interface ConversionFunnelProps {
  funnel: FunnelData;
  totalLeads: number;
}

export const ConversionFunnel: React.FC<ConversionFunnelProps> = ({ funnel, totalLeads }) => {
  const stages = [
    { key: 'new', label: 'NEW', color: 'bg-blue-500', value: funnel.new },
    { key: 'contacted', label: 'CONTACTED', color: 'bg-purple-500', value: funnel.contacted },
    { key: 'shortlisted', label: 'QUALIFIED', color: 'bg-indigo-500', value: funnel.shortlisted },
    { key: 'converted', label: 'CONVERTED', color: 'bg-emerald-500', value: funnel.converted },
  ];

  // Calculate percentages relative to the largest stage (usually 'new' or total)
  const maxVal = Math.max(...stages.map(s => s.value), 1);

  return (
    <div className="space-y-4">
      {stages.map((stage, index) => {
        const percentage = totalLeads > 0 ? (stage.value / totalLeads) * 100 : 0;
        const widthPercent = (stage.value / maxVal) * 100;
        
        return (
          <div key={stage.key} className="space-y-1">
            <div className="flex justify-between items-end text-[10px] font-bold tracking-tighter">
              <span className="text-zinc-500">{stage.label}</span>
              <div className="flex items-center gap-2">
                <span className="text-white font-mono">{stage.value}</span>
                <span className="text-zinc-600">({Math.round(percentage)}%)</span>
              </div>
            </div>
            <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden flex">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${widthPercent}%` }}
                transition={{ duration: 1, delay: index * 0.1 }}
                className={`h-full ${stage.color} shadow-[0_0_10px_rgba(0,0,0,0.3)]`}
              />
            </div>
            
            {/* Show Drop-off indicator between stages */}
            {index < stages.length - 1 && stages[index].value > 0 && (
              <div className="flex justify-center -my-1">
                <div className="w-px h-2 bg-zinc-800" />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
