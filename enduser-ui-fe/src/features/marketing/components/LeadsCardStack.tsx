import React, { useState } from 'react';
import { motion, useMotionValue, useTransform, AnimatePresence } from 'framer-motion';
import { CheckCircleIcon, XCircleIcon, RefreshCwIcon } from '@/components/Icons.tsx';

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
    pitch_content?: string;
}

export interface LeadsCardStackProps {
    leads: Lead[];
    onSwipeRight: (lead: Lead) => void; // Shortlist/Cart
    onSwipeLeft: (lead: Lead) => void;  // Archive
}

import { LeadCard } from './LeadCard.tsx';
import { LeadPitchDrawer } from './LeadPitchDrawer.tsx';
import { LeadHistoryDrawer } from './LeadHistoryDrawer.tsx';

export const LeadsCardStack: React.FC<LeadsCardStackProps> = ({ leads, onSwipeRight, onSwipeLeft }) => {
    const [index, setIndex] = useState(0);
    const [pitchLead, setPitchLead] = useState<Lead | null>(null);
    const [historyLead, setHistoryLead] = useState<Lead | null>(null);
    
    // GAP-003: Undo History
    const [history, setHistory] = useState<number[]>([]);

    const activeLead = leads[index];
    const x = useMotionValue(0);
    const scale = useTransform(x, [-150, 0, 150], [0.9, 1, 0.9]);
    const rotate = useTransform(x, [-150, 0, 150], [-10, 0, 10]);
    const opacity = useTransform(x, [-150, 0, 150], [0, 1, 0]);
    
    // Background card transform
    const bgScale = useTransform(x, [-150, 0, 150], [1, 0.95, 1]);

    const handleUndo = () => {
        if (history.length === 0) return;
        const prevIndex = history[history.length - 1];
        setHistory(prev => prev.slice(0, -1));
        setIndex(prevIndex);
        x.set(0);
    };

    const handleSwipe = (dir: 'left' | 'right') => {
        setHistory(prev => [...prev, index]);
        if (dir === 'left') onSwipeLeft(activeLead);
        else onSwipeRight(activeLead);
        setTimeout(() => { setIndex(index + 1); x.set(0); }, 200);
    };

    const handleDragEnd = (_: any, info: any) => {
        if (info.offset.x > 100) {
            setHistory(prev => [...prev, index]);
            onSwipeRight(activeLead);
            setTimeout(() => { setIndex(index + 1); x.set(0); }, 200);
        } else if (info.offset.x < -100) {
            setHistory(prev => [...prev, index]);
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
        <div className="relative w-full max-w-sm mx-auto h-[520px] flex items-center justify-center mt-0">
            <AnimatePresence>
                 {/* Next Card (Background) */}
                 {leads[index + 1] && (
                    <motion.div
                        className="absolute w-full h-full scale-95 top-4 opacity-50 bg-card rounded-2xl border border-border pointer-events-none"
                        style={{ scale: bgScale }}
                    />
                )}

                {/* Active Card */}
                <LeadCard 
                    key={activeLead.id}
                    lead={activeLead}
                    style={{ x, rotate, opacity, scale }}
                    onDragEnd={handleDragEnd}
                    onPitch={() => setPitchLead(activeLead)}
                    onHistory={() => setHistoryLead(activeLead)}
                />
            </AnimatePresence>

            {/* Controls - Tighter Spacing */}
            <div className="absolute -bottom-12 flex gap-6 items-center">
                 <button 
                    onClick={handleUndo}
                    disabled={history.length === 0}
                    className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center shadow-sm text-gray-500 hover:bg-gray-200 disabled:opacity-30 transition-all"
                    title="Undo Last Swipe"
                    aria-label="Undo Last Swipe"
                >
                    <RefreshCwIcon className="w-5 h-5 -scale-x-100" />
                </button>
                <button 
                    onClick={() => handleSwipe('left')}
                    className="w-14 h-14 bg-background border border-border rounded-full flex items-center justify-center shadow-lg text-red-500 hover:bg-red-50 active:scale-95 transition-all"
                    aria-label="Reject Lead"
                >
                    <XCircleIcon className="w-8 h-8" />
                </button>
                 <button 
                    onClick={() => handleSwipe('right')}
                    className="w-14 h-14 bg-background border border-border rounded-full flex items-center justify-center shadow-lg text-green-500 hover:bg-green-50 active:scale-95 transition-all"
                    aria-label="Accept Lead"
                >
                    <CheckCircleIcon className="w-8 h-8" />
                </button>
            </div>

            {/* Pitch Drawer Overlay */}
            {pitchLead && <LeadPitchDrawer lead={pitchLead} onClose={() => setPitchLead(null)} />}
            
            {/* History Drawer Overlay */}
            {historyLead && <LeadHistoryDrawer lead={historyLead} onClose={() => setHistoryLead(null)} />}
        </div>
    );
};
