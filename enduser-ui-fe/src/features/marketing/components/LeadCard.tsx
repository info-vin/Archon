import React from 'react';
import { motion } from 'framer-motion';
import { ExternalLinkIcon, SparklesIcon, UserIcon, MapIcon, ActivityIcon } from '@/components/Icons.tsx';
import { Lead } from './LeadsCardStack.tsx';

interface LeadCardProps {
    lead: Lead;
    style: any;
    onDragEnd: any;
    onPitch: () => void;
    onHistory: () => void;
}

export const LeadCard = ({ lead, style, onDragEnd, onPitch, onHistory }: LeadCardProps) => {
    const handleMap = (e: React.MouseEvent) => {
        e.stopPropagation();
        window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(lead.company_name)}`, '_blank');
    };

    const handlePitchClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onPitch();
    };

    const handleHistoryClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onHistory();
    };

    return (
        <motion.div
            drag="x"
            dragConstraints={{ left: -100, right: 100 }}
            dragElastic={0.7}
            style={{ ...style, touchAction: 'none' }}
            onDragEnd={onDragEnd}
            className="absolute top-0 left-0 w-full h-full bg-card rounded-2xl shadow-xl border border-border overflow-hidden flex flex-col cursor-grab active:cursor-grabbing"
            whileTap={{ scale: 0.98 }}
        >
            {/* Header / Image Area - Reduced height for efficiency */}
            <div className="h-[18%] bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center p-3 relative shrink-0">
                <div className="absolute top-3 right-3 bg-background/50 backdrop-blur px-2 py-1 rounded text-[10px] font-mono">
                    {lead.match_score ? `${lead.match_score}% MATCH` : 'NEW'}
                </div>
                <div className="text-center w-full px-2">
                    <h2 className="text-lg md:text-xl font-black leading-tight break-words">{lead.company_name}</h2>
                    <p className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-widest mt-0.5">
                      {lead.source !== 'manual' ? lead.source : 'DIRECT'}
                    </p>
                </div>
            </div>

            {/* Body - Compact layout */}
            <div className="p-4 flex-1 flex flex-col gap-2 relative">
                <div className="flex-1 min-h-0 pr-1">
                    <span className="text-[9px] font-black text-amber-600 dark:text-amber-400 uppercase tracking-widest mb-1 flex items-center gap-1">
                        <SparklesIcon className="w-3 h-3" />
                        AI Prediction
                    </span>
                    <div className="space-y-1 mt-0.5 bg-amber-50/50 dark:bg-amber-900/10 p-3 rounded-xl border border-amber-100/50 dark:border-amber-900/20 mb-1">
                        {(() => {
                            const text = lead.identified_need || "";
                            if (text.includes(" -> ")) {
                                const [line1, line2] = text.split(" -> ");
                                return (
                                    <>
                                        <p className="text-xs text-slate-600 dark:text-slate-400 leading-tight italic">"{line1}"</p>
                                        <p className="text-base font-black text-indigo-600 dark:text-indigo-300 leading-tight">
                                            {line2}
                                        </p>
                                    </>
                                );
                            }
                            return <p className="text-sm text-slate-700 dark:text-slate-300 font-medium leading-relaxed">{text}</p>;
                        })()}
                    </div>
                </div>

                 <div className="flex items-center gap-3 mt-3 shrink-0 py-2 border-t border-dotted border-border/50">
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                         <UserIcon className="w-4 h-4 opacity-70" />
                    </div>
                    <div className="flex-1">
                        <p className="text-sm font-semibold">{lead.job_title}</p>
                        <p className="text-[10px] text-muted-foreground">Hiring Manager (Inferred)</p>
                    </div>
                </div>

                <div className="mt-auto pt-4 border-t border-border flex justify-between items-center text-xs text-muted-foreground">
                    <span>Source: {lead.source}</span>
                    <a 
                        href={lead.source_job_url} 
                        target="_blank" 
                        rel="noreferrer"
                        className="flex items-center gap-1 text-indigo-600 font-medium hover:underline z-10"
                        onPointerDown={(e) => e.stopPropagation()} 
                    >
                        View Job Post <ExternalLinkIcon className="w-3 h-3" />
                    </a>
                </div>

                {/* FAB Actions (One-Tap) */}
                <div className="absolute bottom-20 right-6 flex flex-col gap-3 z-20">
                     <button 
                        onClick={handleHistoryClick}
                        className="w-12 h-12 bg-white rounded-full shadow-lg border border-gray-100 flex items-center justify-center text-amber-500 hover:bg-amber-50 active:scale-95 transition-all focus-visible:ring-2 focus-visible:ring-indigo-500"
                        onPointerDown={(e) => e.stopPropagation()}
                        title="View Timeline"
                        aria-label={`View Timeline for ${lead.company_name}`}
                    >
                        <ActivityIcon className="w-6 h-6" />
                    </button>
                    <button 
                        onClick={handleMap}
                        className="w-12 h-12 bg-white rounded-full shadow-lg border border-gray-100 flex items-center justify-center text-blue-500 hover:bg-blue-50 active:scale-95 transition-all focus-visible:ring-2 focus-visible:ring-indigo-500"
                        onPointerDown={(e) => e.stopPropagation()}
                        title="Open Map"
                        aria-label={`Open Map for ${lead.company_name}`}
                    >
                        <MapIcon className="w-6 h-6" />
                    </button>
                    <button 
                        onClick={handlePitchClick}
                        className={`w-12 h-12 rounded-full shadow-lg flex items-center justify-center text-white active:scale-95 transition-all focus-visible:ring-2 focus-visible:ring-indigo-500 ${lead.pitch_content ? 'bg-green-600 hover:bg-green-700 shadow-green-200' : 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-200'}`}
                        onPointerDown={(e) => e.stopPropagation()}
                        title={lead.pitch_content ? "View Saved Pitch" : "Generate AI Pitch"}
                        aria-label={lead.pitch_content ? `View Saved Pitch for ${lead.company_name}` : `Generate AI Pitch for ${lead.company_name}`}
                    >
                        <SparklesIcon className="w-6 h-6" />
                    </button>
                </div>
            </div>
                {/* Action Indicators (Visible on Drag) */}
                <div className="absolute top-6 left-6 opacity-0 data-[swiping=right]:opacity-100 transition-opacity">
                    <div className="border-4 border-green-500 text-green-500 font-bold px-2 py-1 rounded transform -rotate-12 text-xl">LIKE</div>
                </div>
                 <div className="absolute top-6 right-6 opacity-0 data-[swiping=left]:opacity-100 transition-opacity">
                    <div className="border-4 border-red-500 text-red-500 font-bold px-2 py-1 rounded transform rotate-12 text-xl">NOPE</div>
                </div>
            </motion.div>
        );
    };
