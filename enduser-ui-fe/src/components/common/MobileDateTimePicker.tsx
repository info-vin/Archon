import React, { useState } from 'react';
import { Button } from '../Button';
import { XIcon, CalendarIcon, ClockIcon, CheckCircleIcon } from '../Icons';

interface MobileDateTimePickerProps {
    value: string; // ISO string or empty
    onChange: (value: string) => void;
    label: string;
}

export const MobileDateTimePicker: React.FC<MobileDateTimePickerProps> = ({ value, onChange, label }) => {
    const [isOpen, setIsOpen] = useState(false);
    
    // Parse current value or default to now
    const date = value ? new Date(value) : new Date();
    
    // Internal state for picker
    const [tempDate, setTempDate] = useState(date);

    const handleConfirm = () => {
        onChange(tempDate.toISOString());
        setIsOpen(false);
    };

    const adjustDate = (unit: 'day' | 'hour' | 'minute', amount: number) => {
        const newDate = new Date(tempDate);
        if (unit === 'day') newDate.setDate(newDate.getDate() + amount);
        if (unit === 'hour') newDate.setHours(newDate.getHours() + amount);
        if (unit === 'minute') newDate.setMinutes(newDate.getMinutes() + amount);
        setTempDate(newDate);
    };

    const setPreset = (days: number) => {
        const newDate = new Date();
        newDate.setDate(newDate.getDate() + days);
        newDate.setHours(14, 0, 0, 0); // Default to 2 PM
        setTempDate(newDate);
    };

    const formatDisplay = (d: Date) => {
        return d.toLocaleString('zh-TW', { 
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true 
        });
    };

    const PickerColumn = ({ label, value, onUp, onDown }: any) => (
        <div className="flex flex-col items-center gap-2">
            <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest">{label}</span>
            <button 
                type="button"
                onClick={onUp}
                className="w-12 h-12 flex items-center justify-center bg-slate-100 dark:bg-slate-800 rounded-xl active:bg-indigo-100"
            >
                <span className="text-xl">▲</span>
            </button>
            <div className="w-16 h-16 flex items-center justify-center bg-white dark:bg-slate-900 border-2 border-indigo-500 rounded-2xl shadow-inner">
                <span className="text-xl font-black">{value}</span>
            </div>
            <button 
                type="button"
                onClick={onDown}
                className="w-12 h-12 flex items-center justify-center bg-slate-100 dark:bg-slate-800 rounded-xl active:bg-indigo-100"
            >
                <span className="text-xl">▼</span>
            </button>
        </div>
    );

    const pickerId = `date-picker-${label.replace(/\s+/g, '-').toLowerCase()}`;

    return (
        <div className="w-full">
            <label htmlFor={pickerId} className="block text-sm font-medium mb-1 text-slate-700 dark:text-slate-300">{label}</label>
            <button
                id={pickerId}
                type="button"
                onClick={() => setIsOpen(true)}
                className="w-full p-3 flex items-center justify-between border dark:border-slate-700 rounded-xl bg-white dark:bg-slate-800 text-sm hover:border-indigo-500 transition-all"
            >
                <div className="flex items-center gap-2">
                    <CalendarIcon className="w-4 h-4 text-indigo-500" />
                    <span className="font-bold">{value ? formatDisplay(new Date(value)) : 'Set Date & Time'}</span>
                </div>
                <ClockIcon className="w-4 h-4 text-slate-400" />
            </button>

            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-end md:items-center justify-center bg-black/60 backdrop-blur-sm p-0 md:p-4 animate-in fade-in duration-200">
                    <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-t-[2.5rem] md:rounded-[2.5rem] shadow-2xl overflow-hidden flex flex-col animate-in slide-in-from-bottom duration-300 border-t dark:border-slate-800">
                        {/* Header */}
                        <div className="p-6 border-b dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-950">
                            <div>
                                <h3 className="text-lg font-black tracking-tight">SET DUE DATE</h3>
                                <p className="text-xs text-slate-500 uppercase font-bold tracking-widest">{formatDisplay(tempDate)}</p>
                            </div>
                            <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full">
                                <XIcon className="w-6 h-6 text-slate-400" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="p-8 space-y-8">
                            {/* Presets */}
                            <div className="flex gap-2">
                                <button 
                                    type="button"
                                    onClick={() => setPreset(1)}
                                    className="flex-1 py-3 px-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-100 transition-all"
                                >
                                    Tomorrow
                                </button>
                                <button 
                                    type="button"
                                    onClick={() => setPreset(3)}
                                    className="flex-1 py-3 px-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-100 transition-all"
                                >
                                    +3 Days
                                </button>
                                <button 
                                    type="button"
                                    onClick={() => setPreset(7)}
                                    className="flex-1 py-3 px-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-100 transition-all"
                                >
                                    Next Week
                                </button>
                            </div>

                            {/* Wheels */}
                            <div className="flex justify-center items-center gap-4">
                                <PickerColumn 
                                    label="Day" 
                                    value={tempDate.getDate()} 
                                    onUp={() => adjustDate('day', 1)} 
                                    onDown={() => adjustDate('day', -1)} 
                                />
                                <div className="text-2xl font-black text-slate-300 mt-6">:</div>
                                <PickerColumn 
                                    label="Hour" 
                                    value={tempDate.getHours()} 
                                    onUp={() => adjustDate('hour', 1)} 
                                    onDown={() => adjustDate('hour', -1)} 
                                />
                                <div className="text-2xl font-black text-slate-300 mt-6">:</div>
                                <PickerColumn 
                                    label="Min" 
                                    value={tempDate.getMinutes().toString().padStart(2, '0')} 
                                    onUp={() => adjustDate('minute', 5)} 
                                    onDown={() => adjustDate('minute', -5)} 
                                />
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="p-6 bg-slate-50 dark:bg-slate-950 border-t dark:border-slate-800">
                            <Button 
                                variant="primary" 
                                accentColor="green"
                                className="w-full py-5 rounded-2xl text-base font-black shadow-xl shadow-emerald-200 dark:shadow-none"
                                onClick={handleConfirm}
                                icon={<CheckCircleIcon className="w-5 h-5" />}
                            >
                                CONFIRM SELECTION
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
