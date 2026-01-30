import React, { useState } from 'react';
import { motion, useMotionValue, useTransform, AnimatePresence } from 'framer-motion';
import { CheckCircleIcon, XCircleIcon, UserIcon, ExternalLinkIcon, SparklesIcon, MapIcon } from '../../../components/Icons.tsx';

// Temporary Type Definition (Should be shared)
export interface Lead {
    id: string;
    company_name: string;
    job_title: string;
    source: string;
    identified_need: string;
    status: string;
    source_job_url?: string;
    match_score?: number; // 0-100
}

interface LeadsCardStackProps {
    leads: Lead[];
    onSwipeRight: (lead: Lead) => void; // Shortlist/Cart
    onSwipeLeft: (lead: Lead) => void;  // Archive
}

const Card = ({ lead, style, onDragEnd }: { lead: Lead, style: any, onDragEnd: any }) => {
    const handleMap = (e: React.MouseEvent) => {
        e.stopPropagation();
        window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(lead.company_name)}`, '_blank');
    };

    const handlePitch = (e: React.MouseEvent) => {
        e.stopPropagation();
        alert(`AI Pitch for ${lead.company_name}:\n\n"Hi, I noticed ${lead.company_name} is looking for ${lead.job_title}. Archon can help with ${lead.identified_need}..."`);
    };

    return (
        <motion.div
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            style={style}
            onDragEnd={onDragEnd}
            className="absolute top-0 left-0 w-full h-full bg-card rounded-2xl shadow-xl border border-border overflow-hidden flex flex-col"
            whileTap={{ cursor: "grabbing" }}
        >
            {/* Header / Image Area Placeholder */}
            <div className="h-1/3 bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center p-6 relative">
                <div className="absolute top-4 right-4 bg-background/50 backdrop-blur px-2 py-1 rounded text-xs font-mono">
                    {lead.match_score ? `${lead.match_score}% MATCH` : 'NEW'}
                </div>
                <div className="text-center">
                    <h2 className="text-2xl font-bold line-clamp-2">{lead.company_name}</h2>
                    <p className="text-sm text-muted-foreground mt-1">{lead.source}</p>
                </div>
            </div>

            {/* Body */}
            <div className="p-6 flex-1 flex flex-col gap-4 relative">
                <div>
                    <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Requirement</span>
                    <p className="text-lg font-medium mt-1 leading-snug">{lead.identified_need}</p>
                </div>

                <div className="flex items-center gap-3 mt-2">
                    <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center">
                         <UserIcon className="w-5 h-5 opacity-70" />
                    </div>
                    <div className="flex-1">
                        <p className="text-sm font-semibold">{lead.job_title}</p>
                        <p className="text-xs text-muted-foreground">Hiring Manager (Inferred)</p>
                    </div>
                </div>

                <div className="mt-auto pt-4 border-t border-border flex justify-between items-center">
                    <a 
                        href={lead.source_job_url} 
                        target="_blank" 
                        rel="noreferrer"
                        className="text-xs flex items-center gap-1 text-primary hover:underline z-10"
                        onPointerDown={(e) => e.stopPropagation()} 
                    >
                        Available Job Post <ExternalLinkIcon className="w-3 h-3" />
                    </a>
                </div>

                {/* FAB Actions (One-Tap) */}
                <div className="absolute bottom-20 right-6 flex flex-col gap-3 z-20">
                    <button 
                        onClick={handleMap}
                        className="w-12 h-12 bg-white rounded-full shadow-lg border border-gray-100 flex items-center justify-center text-blue-500 hover:bg-blue-50 active:scale-95 transition-all"
                        onPointerDown={(e) => e.stopPropagation()}
                        title="Open Map"
                    >
                        <MapIcon className="w-6 h-6" />
                    </button>
                    <button 
                        onClick={handlePitch}
                        className="w-12 h-12 bg-indigo-600 rounded-full shadow-lg shadow-indigo-200 flex items-center justify-center text-white hover:bg-indigo-700 active:scale-95 transition-all"
                        onPointerDown={(e) => e.stopPropagation()}
                        title="Generate Pitch"
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

export const LeadsCardStack: React.FC<LeadsCardStackProps> = ({ leads, onSwipeRight, onSwipeLeft }) => {
    const [index, setIndex] = useState(0);

    const activeLead = leads[index];
    const x = useMotionValue(0);
    const scale = useTransform(x, [-150, 0, 150], [0.9, 1, 0.9]);
    const rotate = useTransform(x, [-150, 0, 150], [-10, 0, 10]);
    const opacity = useTransform(x, [-150, 0, 150], [0, 1, 0]);
    
    // Background card transform
    const bgScale = useTransform(x, [-150, 0, 150], [1, 0.95, 1]);

    const handleDragEnd = (_: any, info: any) => {
        if (info.offset.x > 100) {
            onSwipeRight(activeLead);
            setTimeout(() => { setIndex(index + 1); x.set(0); }, 200);
        } else if (info.offset.x < -100) {
            onSwipeLeft(activeLead);
            setTimeout(() => { setIndex(index + 1); x.set(0); }, 200);
        }
    };
    
    if (index >= leads.length) {
         return (
             <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-card rounded-2xl border border-dashed border-border mx-4">
                 <div className="w-16 h-16 bg-secondary/50 rounded-full flex items-center justify-center mb-4">
                     <CheckCircleIcon className="w-8 h-8 text-muted-foreground" />
                 </div>
                 <h3 className="text-xl font-semibold">All Caught Up!</h3>
                 <p className="text-muted-foreground mt-2">No more new leads in your queue. Check back later or adjust your filters.</p>
                 <button 
                    onClick={() => setIndex(0)} 
                    className="mt-6 px-4 py-2 bg-secondary rounded-lg text-sm hover:bg-secondary/80"
                 >
                     Review Again (Demo)
                 </button>
             </div>
         );
    }

    return (
        <div className="relative w-full max-w-sm mx-auto h-[600px] flex items-center justify-center mt-4">
            <AnimatePresence>
                 {/* Next Card (Background) */}
                 {leads[index + 1] && (
                    <motion.div
                        className="absolute w-full h-full scale-95 top-4 opacity-50 bg-card rounded-2xl border border-border pointer-events-none"
                        style={{ scale: bgScale }}
                    />
                )}

                {/* Active Card */}
                <Card 
                    key={activeLead.id}
                    lead={activeLead}
                    style={{ x, rotate, opacity, scale }}
                    onDragEnd={handleDragEnd}
                />
            </AnimatePresence>

            {/* Controls */}
            <div className="absolute -bottom-20 flex gap-6">
                <button 
                    onClick={() => { onSwipeLeft(activeLead); setTimeout(() => { setIndex(index + 1); }, 200); }}
                    className="w-14 h-14 bg-background border border-border rounded-full flex items-center justify-center shadow-lg text-red-500 hover:bg-red-50 active:scale-95 transition-all"
                >
                    <XCircleIcon className="w-8 h-8" />
                </button>
                 <button 
                    onClick={() => { onSwipeRight(activeLead); setTimeout(() => { setIndex(index + 1); }, 200); }}
                    className="w-14 h-14 bg-background border border-border rounded-full flex items-center justify-center shadow-lg text-green-500 hover:bg-green-50 active:scale-95 transition-all"
                >
                    <CheckCircleIcon className="w-8 h-8" />
                </button>
            </div>
        </div>
    );
};
