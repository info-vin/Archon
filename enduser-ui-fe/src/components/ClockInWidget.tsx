import React, { useState, useEffect } from 'react';
import { ClockIcon, MapPinIcon } from './Icons';

import { api } from '../services/api';

// PERFORMANCE: Hoisted Intl.DateTimeFormat outside the component to prevent expensive re-instantiations during render loops.
const timeFormatter = new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' });

export const ClockInWidget: React.FC = () => {
    const [status, setStatus] = useState<'in' | 'out'>('out');
    const [lastTime, setLastTime] = useState<Date | null>(null);
    const [locationName, setLocationName] = useState<string>("Ready to Scan");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Fetch initial status from backend
        const fetchStatus = async () => {
            try {
                const res = await api.getAttendanceStatus();
                setStatus(res.status === 'PRESENT' || res.status === 'MOCK_PRESENT' ? 'in' : 'out');
                if (res.clock_in_time) setLastTime(new Date(res.clock_in_time));
                if (res.location) setLocationName(res.location);
            } catch (e) {
                console.error("Failed to fetch attendance status", e);
            }
        };
        fetchStatus();
    }, []);

    const handleClockIn = async (lat?: number, lng?: number, info: string = "") => {
        try {
            setLoading(true);
            setLocationName("Syncing...");
            await api.clockIn({
                latitude: lat,
                longitude: lng,
                location_name: info,
                status: info.includes("Mock") ? "MOCK_PRESENT" : "PRESENT"
            });
            setStatus('in');
            setLastTime(new Date());
            setLocationName(info || "Office");
        } catch (e) {
            alert("Clock In Failed");
        } finally {
            setLoading(false);
        }
    };

    const handleClockOut = async () => {
        try {
            setLoading(true);
            await api.clockOut();
            setStatus('out');
            setLastTime(new Date());
            setLocationName("Ready to Scan");
        } catch (e) {
            alert("Clock Out Failed");
        } finally {
            setLoading(false);
        }
    };

    const toggleClock = () => {
        if (loading) return;

        if (status === 'in') {
            handleClockOut();
        } else {
            // Clock In Logic with GAP-010 Fallback
            if (navigator.geolocation) {
                setLocationName("Locating...");
                navigator.geolocation.getCurrentPosition(
                    (pos) => handleClockIn(pos.coords.latitude, pos.coords.longitude, "Taipei City, TW"),
                    () => {
                        const useMock = confirm("GPS Unavailable. Use mock location (Taipei 101)?");
                        if (useMock) handleClockIn(25.0330, 121.5654, "Taipei 101 (Mock)");
                        else setLocationName("GPS Error");
                    }
                );
            } else {
                const useMock = confirm("Geolocation not supported. Use mock location (Taipei 101)?");
                if (useMock) handleClockIn(25.0330, 121.5654, "Taipei 101 (Mock)");
                else setLocationName("GPS Error");
            }
        }
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
                        {lastTime ? (isNaN(lastTime.getTime()) ? 'Invalid Date' : timeFormatter.format(lastTime)) : '--:--'}
                    </p>
                    <p className="text-xs font-semibold text-gray-600">
                        {status === 'in' ? 'Clocked In' : 'Clocked Out'}
                    </p>
                </div>
            </div>

            <button 
                onClick={toggleClock}
                disabled={loading}
                aria-disabled={loading}
                aria-busy={loading}
                className={`w-full mt-4 py-3 rounded-xl flex items-center justify-center gap-2 font-bold text-white shadow-md transition-all active:scale-95 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 ${
                    status === 'out' 
                    ? 'bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 shadow-indigo-200' 
                    : 'bg-gray-800 hover:bg-gray-900 shadow-gray-200'
                }`}
            >
                <ClockIcon className="w-5 h-5" />
                {loading ? 'Syncing...' : (status === 'out' ? 'Clock In' : 'Clock Out')}
            </button>
        </div>
    );
};
