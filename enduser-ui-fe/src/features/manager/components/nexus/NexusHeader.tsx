import React, { useMemo } from 'react';
import { FileTextIcon, ClockIcon } from '../../../../components/Icons';
import { AudioPlayer } from '../../../../components/common/AudioPlayer';

export interface NexusHeaderProps {
    onOpenSpec: () => void;
    dailyData?: any; // Pass relevant data to generate the text
}

export const NexusHeader: React.FC<NexusHeaderProps> = ({ onOpenSpec, dailyData }) => {
    // Generate the briefing text based on the available data
    const briefingText = useMemo(() => {
        if (!dailyData) return "目前無法取得今日數據。但系統運作正常。";
        
        const staleCount = dailyData.staleLeads || 0;
        const pendingCount = dailyData.pendingApprovals || 0;
        
        let report = `目前有 ${staleCount} 筆潛在客戶處於「降溫」停滯狀態`;
        if (staleCount > 0) report += "，需要您的立即關注。";
        else report += "。";
        
        if (pendingCount > 0) {
            report += `另外，有 ${pendingCount} 項待審核任務。`;
        }
        
        return report;
    }, [dailyData]);

    return (
        <header className="flex justify-between items-end mb-8">
            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight flex items-center gap-3">Manager Nexus</h1>
                <p className="text-sm text-gray-500 mt-1 font-medium">Command & Control v7.1</p>
            </div>
            <div className="flex items-center gap-4">
                <AudioPlayer 
                    text={briefingText} 
                    scene="commander_briefing" 
                    label="Play Daily Briefing" 
                    className="h-9"
                />
                
                <button
                    onClick={onOpenSpec}
                    className="flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-600 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-amber-100 transition-all active:scale-95 border border-amber-100 h-9"
                >
                    <FileTextIcon className="w-4 h-4" />
                    View Specs
                </button>
                <div className="flex gap-2 text-xs font-bold text-gray-400 bg-white px-3 items-center rounded-lg border border-gray-100 shadow-sm h-9">
                    <ClockIcon className="w-4 h-4" />
                    <span>Dynamic Refresh</span>
                </div>
            </div>
        </header>
    );
};
