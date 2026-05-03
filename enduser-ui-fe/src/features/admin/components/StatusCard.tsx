import React from 'react';

interface StatusCardProps {
    title: string;
    value: string;
    subtext: string;
    status: 'good' | 'bad' | 'warning' | 'neutral';
}

export const StatusCard: React.FC<StatusCardProps> = ({ title, value, subtext, status }) => {
    const colors = {
        good: 'bg-green-50 text-green-700 border-green-200',
        bad: 'bg-red-50 text-red-700 border-red-200',
        warning: 'bg-amber-50 text-amber-700 border-amber-200',
        neutral: 'bg-card text-foreground border-border'
    };
    
    return (
        <div className={`p-4 rounded-xl border ${colors[status]} shadow-sm flex flex-col`}>
            <span className="text-xs font-bold uppercase tracking-wider opacity-70 mb-1">{title}</span>
            <span className="text-2xl font-bold mb-1">{value}</span>
            <span className="text-xs opacity-80 truncate">{subtext}</span>
        </div>
    );
};
