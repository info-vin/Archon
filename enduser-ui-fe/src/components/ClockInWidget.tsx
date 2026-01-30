import React, { useState, useEffect } from 'react';
import { ClockIcon, MapPinIcon } from './Icons';

export const ClockInWidget: React.FC = () => {
    const [status, setStatus] = useState<'in' | 'out'>('out');
    const [lastTime, setLastTime] = useState<Date | null>(null);
    const [locationName, setLocationName] = useState<string>("Locating...");

    useEffect(() => {
        // Mock checking initial status
        const savedStatus = localStorage.getItem('clock_status');
        if (savedStatus) setStatus(savedStatus as 'in' | 'out');
        
        const savedTime = localStorage.getItem('clock_time');
        if (savedTime) setLastTime(new Date(savedTime));

        // Mock getting location name
        if (navigator.geolocation) {
             navigator.geolocation.getCurrentPosition(
                () => setLocationName("Taipei City, TW"), // Mock
                () => setLocationName("Unknown Location")
            );
        }
    }, []);

    const toggleClock = () => {
        const newStatus = status === 'in' ? 'out' : 'in';
        const now = new Date();
        
        setStatus(newStatus);
        setLastTime(now);
        
        localStorage.setItem('clock_status', newStatus);
        localStorage.setItem('clock_time', now.toISOString());
    };

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-4 md:hidden">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-bold text-gray-800">Attendance</h3>
                    <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                        <MapPinIcon className="w-3 h-3" />
                        {locationName}
                    </p>
                </div>
                <div className="text-right">
                    <p className="text-xs text-gray-400 font-mono">
                        {lastTime ? lastTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '--:--'}
                    </p>
                    <p className="text-xs font-semibold text-gray-600">
                        {status === 'in' ? 'Clocked In' : 'Clocked Out'}
                    </p>
                </div>
            </div>

            <button 
                onClick={toggleClock}
                className={`w-full mt-4 py-3 rounded-xl flex items-center justify-center gap-2 font-bold text-white shadow-md transition-all active:scale-95 ${
                    status === 'out' 
                    ? 'bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 shadow-indigo-200' 
                    : 'bg-gray-800 hover:bg-gray-900 shadow-gray-200'
                }`}
            >
                <ClockIcon className="w-5 h-5" />
                {status === 'out' ? 'Clock In' : 'Clock Out'}
            </button>
        </div>
    );
};
