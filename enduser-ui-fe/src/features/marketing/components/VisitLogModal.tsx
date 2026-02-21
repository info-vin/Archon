import React, { useState, useRef } from 'react';
import { api } from '@/services/api';
import { XIcon, MapPinIcon, CheckCircleIcon, SparklesIcon, MicrophoneIcon, TrashIcon, UploadIcon } from '@/components/Icons';

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

    // Audio Recording State
    // Audio Upload State (Replaces Recording)
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleLocation = () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
                (_) => {
                    // GAP-010: Mock Location Fallback
                    const useMock = confirm("Could not get location. Use mock location (Taipei 101)?");
                    if (useMock) {
                        setLocation({ lat: 25.0330, lng: 121.5654 });
                    }
                }
            );
        } else {
             // GAP-010: Mock Location Fallback
             const useMock = confirm("Geolocation not supported. Use mock location (Taipei 101)?");
             if (useMock) {
                 setLocation({ lat: 25.0330, lng: 121.5654 });
             }
        }
    };

    // GAP-009: Simulate Voice Input
    const simulateVoiceInput = () => {
        setNotes((prev) => {
            const mockTranscript = "[Mock Voice] 客戶對新的 AI 功能非常感興趣，特別是自動化報表的部分。建議下週二安排產品演示。";
            return prev ? prev + "\n" + mockTranscript : mockTranscript;
        });
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setAudioFile(e.target.files[0]);
        }
    };

    const clearAudio = () => {
        setAudioFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('visit_type', type); // Ensure type is passed
            if (location) {
                formData.append('latitude', location.lat.toString());
                formData.append('longitude', location.lng.toString());
            }
            
            // Append audio if exists
            if (audioFile) {
                formData.append('audio_file', audioFile, audioFile.name);
            }

            formData.append('notes', notes); 

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
                            {summary?.voice_transcript && (
                                <div className="mt-2 pt-2 border-t border-gray-200">
                                    <p className="font-semibold text-gray-700 mb-1 text-xs uppercase">Transcript</p>
                                    <p className="text-gray-500 text-xs italic line-clamp-3">{summary.voice_transcript}</p>
                                </div>
                            )}
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
                        <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-100 flex items-center gap-2 text-indigo-700 font-medium">
                            <span className="bg-indigo-600 text-white text-xs px-2 py-1 rounded-full">Type</span>
                            {type}
                        </div>
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
                            <div className="flex justify-between items-center mb-1">
                                <label className="block text-sm font-medium text-gray-700">Voice Log (Optional)</label>
                                <button
                                    onClick={simulateVoiceInput}
                                    className="text-xs text-indigo-600 hover:underline font-medium"
                                >
                                    Simulate Voice
                                </button>
                            </div>
                            {!audioFile ? (
                                <button 
                                    onClick={() => fileInputRef.current?.click()}
                                    className="w-full p-4 rounded-xl border-2 border-dashed border-gray-300 hover:border-indigo-500 hover:bg-indigo-50 text-gray-600 flex items-center justify-center gap-3 transition-colors"
                                >
                                    <UploadIcon className="w-5 h-5" />
                                    <span className="font-semibold">Upload Audio Recording</span>
                                    <input 
                                        type="file" 
                                        ref={fileInputRef}
                                        className="hidden"
                                        accept="audio/*,.m4a,.mp3,.wav"
                                        onChange={handleFileSelect}
                                    />
                                </button>
    
                            ) : (
                                <div className="flex items-center gap-2 p-3 bg-indigo-50 border border-indigo-100 rounded-xl">
                                    <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600">
                                        <MicrophoneIcon className="w-4 h-4" />
                                    </div>
                                    <div className="flex-1 overflow-hidden">
                                        <p className="text-sm font-bold text-gray-800 truncate">{audioFile?.name}</p>
                                        <p className="text-xs text-gray-500">Ready to upload</p>
                                    </div>
                                    <button onClick={clearAudio} className="p-2 hover:bg-red-100 rounded-full text-red-500 transition-colors">
                                        <TrashIcon className="w-4 h-4" />
                                    </button>
                                </div>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Notes / Transcript</label>
                            <textarea 
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                                rows={3}
                                placeholder={audioFile ? "Additional notes..." : "Type summary or upload audio..."}
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
