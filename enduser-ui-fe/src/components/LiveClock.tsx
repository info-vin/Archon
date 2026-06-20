import React, { useState, useEffect } from 'react';
import ThemeToggle from './ThemeToggle.tsx';

// PERFORMANCE: Hoisted Intl.DateTimeFormat instances outside the component to prevent expensive
// re-instantiations on every tick of the 1-second interval timer.
const desktopFormatter = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
const mobileFormatter = new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });

const LiveClock: React.FC = () => {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timerId = setInterval(() => setTime(new Date()), 1000); // Update every second to keep the minute fresh
        return () => clearInterval(timerId);
    }, []);

    const formatTime = (date: Date, formatter: Intl.DateTimeFormat) => {
        try {
           return formatter.format(date);
        } catch (e) {
           // Fallback for very old browsers or weird environments
           const hours = String(date.getHours()).padStart(2, '0');
           const minutes = String(date.getMinutes()).padStart(2, '0');
           return `${hours}:${minutes}`;
        }
    };

    return (
        <div className="flex items-center justify-center bg-card border border-border rounded-md px-3 py-1.5 h-10">
            <div className="text-sm font-semibold tracking-wider text-foreground">
                <span className="hidden md:inline">
                    {formatTime(time, desktopFormatter)}
                </span>
                <span className="md:hidden">
                    {formatTime(time, mobileFormatter)}
                </span>
            </div>
            <div className="border-l border-border h-5 mx-2"></div>
            <ThemeToggle className="p-1 rounded-md hover:bg-secondary transition-colors" />
        </div>
    );
};

export default LiveClock;