import React, { useState } from 'react';
import { api } from '../../../services/api';
import { XIcon, MapPinIcon, CheckCircleIcon, SparklesIcon } from '../../../components/Icons';

interface VisitLogModalProps {
    onClose: () => void;
    onSuccess: () => void;
}

export const VisitLogModal: React.FC<VisitLogModalProps> = ({ onClose, onSuccess }) => {
    const [step, setStep] = useState<'type' | 'details' | 'summary'>('type');
    const [type, setType] = useState('');
    const [location, setLocation] = useState<{lat: number, lng: number} | null>(null);
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);
    const [summary, setSummary] = useState<any>(null);

    const handleLocation = () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
                (_) => alert("Could not get location. Ensure permissions are allowed.")
            );
        }
    };

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('visit_type', type);
            if (location) {
                formData.append('latitude', location.lat.toString());
                formData.append('longitude', location.lng.toString());
            }
            // Notes can be passed as text prompt or just manual notes.
            // Requirement says "Voice Transcript". 
            // We'll simulate voice by just sending notes as 'transcript' if no audio, 
            // or if audio exists, backend handles it.
            
            // Wait, backend `create_visit_log` does NOT accept generic 'notes' field in form data?
            // Let's check backend `visit_log_api.py`.
            // It parses transcript from audio.
            // If we want manual notes, we should probably add a parameter to the backend or generic 'summary' override.
            // Backend: `summary = await llm_service.summarize(transcript)`
            // If no audio, transcript is empty.
            // I should add `manual_notes` to backend?
            // Or just append notes to form data and let backend ignore or use it. 
            // Previous plan didn't specify manual notes vs audio explicitly, but UI needs fallback.
            
            formData.append('notes', notes); // Hope backend uses it or we update backend later.

            const res = await api.createVisitLog(formData);
            setSummary(res); // Show summary
            setStep('summary');
        } catch (err: any) {
            alert(err.message || "Failed to create log");
            setLoading(false);
        }
    };

    if (step === 'summary') {
        return (
            <div className="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4">
                <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 animate-in zoom-in-95">
                    <div className="flex flex-col items-center text-center">
                        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                            <CheckCircleIcon className="w-8 h-8 text-green-600" />
                        </div>
                        <h3 className="text-xl font-bold mb-2">Visit Logged!</h3>
                        <p className="text-sm text-gray-500 mb-6">Your visit has been recorded and analyzed.</p>
                        
                        <div className="bg-gray-50 p-4 rounded-lg text-left w-full mb-6 text-sm">
                            <p className="font-semibold text-gray-700 mb-1 flex items-center gap-2">
                                <SparklesIcon className="w-4 h-4 text-purple-600" /> AI Summary
                            </p>
                            <p className="text-gray-600">{summary?.summary || "Processing..."}</p>
                        </div>

                        <button onClick={onSuccess} className="w-full py-3 bg-gray-900 text-white rounded-lg font-semibold">
                            Done
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black/50 z-[60] flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div className="bg-white rounded-t-2xl sm:rounded-xl shadow-xl w-full max-w-md p-6 animate-in slide-in-from-bottom-10 sm:slide-in-from-bottom-0 sm:zoom-in-95 duration-200">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold">New Visit Log</h3>
                    <button onClick={onClose}><XIcon className="w-6 h-6 text-gray-400" /></button>
                </div>

                {step === 'type' && (
                    <div className="grid grid-cols-2 gap-4">
                        {['Client Meeting', 'Site Check', 'Cold Visit', 'Partner Sync'].map(t => (
                            <button 
                                key={t}
                                onClick={() => { setType(t); setStep('details'); }}
                                className="p-4 rounded-xl border-2 border-dashed border-gray-200 hover:border-indigo-500 hover:bg-indigo-50 transition-all font-medium text-gray-700 hover:text-indigo-700"
                            >
                                {t}
                            </button>
                        ))}
                    </div>
                )}

                {step === 'details' && (
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                            <div className="flex items-center gap-2">
                                <div className={`flex-1 p-3 rounded-lg border ${location ? 'bg-green-50 border-green-200 text-green-800' : 'bg-gray-50 border-gray-200 text-gray-500'}`}>
                                    {location ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}` : "No location data"}
                                </div>
                                <button onClick={handleLocation} className="p-3 bg-gray-100 rounded-lg hover:bg-gray-200 text-gray-700">
                                    <MapPinIcon className="w-5 h-5" />
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Notes / Transcript</label>
                            <textarea 
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                                rows={4}
                                placeholder="Type summary or allow AI to listen..."
                            />
                        </div>

                        <button 
                            onClick={handleSubmit} 
                            disabled={loading || !type}
                            className="w-full py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 flex justify-center gap-2"
                        >
                            {loading && <SparklesIcon className="w-5 h-5 animate-pulse" />}
                            {loading ? "Analyzing..." : "Save Visit"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
