import React, { useState, useRef, useEffect } from 'react';
import { getHeaders } from '../../services/api/base';
import { getBaseUrl } from '../../services/api/apiClient';

// Minimal Inline Icons to avoid massive imports if they don't exist

const PauseIcon = ({ className = "w-4 h-4" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={className}>
        <path fillRule="evenodd" d="M6.75 5.25a.75.75 0 0 1 .75-.75H9a.75.75 0 0 1 .75.75v13.5a.75.75 0 0 1-.75.75H7.5a.75.75 0 0 1-.75-.75V5.25Zm7.5 0A.75.75 0 0 1 15 4.5h1.5a.75.75 0 0 1 .75.75v13.5a.75.75 0 0 1-.75.75H15a.75.75 0 0 1-.75-.75V5.25Z" clipRule="evenodd" />
    </svg>
);

const LoaderIcon = ({ className = "w-4 h-4 animate-spin" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={className}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
    </svg>
);

const MicIcon = ({ className = "w-4 h-4" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={className}>
        <path d="M8.25 4.5a3.75 3.75 0 1 1 7.5 0v8.25a3.75 3.75 0 1 1-7.5 0V4.5Z" />
        <path d="M6 10.5a.75.75 0 0 1 .75.75v1.5a5.25 5.25 0 1 0 10.5 0v-1.5a.75.75 0 0 1 1.5 0v1.5a6.751 6.751 0 0 1-6 6.709v2.291h3a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5h3v-2.291a6.751 6.751 0 0 1-6-6.709v-1.5A.75.75 0 0 1 6 10.5Z" />
    </svg>
);

export interface AudioPlayerProps {
    text?: string;
    scene: 'commander_briefing' | 'marketing_pitch';
    voice?: string;
    label?: string;
    className?: string;
    agentData?: Record<string, any>;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ 
    text = "", 
    scene, 
    voice, 
    label = "Play Audio", 
    className = "",
    agentData
}) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isExpanded, setIsExpanded] = useState(false);
    
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

    // Clean up URL on unmount
    useEffect(() => {
        return () => {
            if (audioUrl) {
                URL.revokeObjectURL(audioUrl);
            }
        };
    }, [audioUrl]);

    const handlePlayPause = async () => {
        setError(null);
        
        // If already have audio loaded, just toggle play/pause
        if (audioUrl && audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
                setIsPlaying(false);
            } else {
                audioRef.current.play();
                setIsPlaying(true);
            }
            return;
        }

        // If not loaded, we need to fetch
        setIsLoading(true);
        setIsExpanded(true);
        try {
            const apiUrl = getBaseUrl();
            const headers = await getHeaders({
                'Content-Type': 'application/json'
            });
            
            const response = await fetch(`${apiUrl}/api/audio/generate`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ text, scene, voice, agent_data: agentData })
            });

            if (!response.ok) {
                let errorText = 'Unknown error';
                try {
                    const errorJson = await response.json();
                    errorText = errorJson.detail || errorText;
                } catch (e) {
                    errorText = `HTTP ${response.status}`;
                }
                throw new Error(errorText);
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            setAudioUrl(url);
            
            // It takes a tick for the audio element to mount/update src
            setTimeout(() => {
                if (audioRef.current) {
                    audioRef.current.play();
                    setIsPlaying(true);
                }
            }, 100);

        } catch (err: any) {
            console.error("Audio generation failed:", err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleEnded = () => {
        setIsPlaying(false);
    };

    // Waveform simulation
    const renderWaveform = () => {
        return (
            <div className="flex items-center gap-[2px] h-4 mx-2">
                {[...Array(12)].map((_, i) => (
                    <div 
                        key={i} 
                        className={`w-1 bg-current rounded-full transition-all duration-150 ${isPlaying ? 'animate-pulse' : 'h-1 opacity-50'}`}
                        style={{
                            height: isPlaying ? `${Math.max(20, Math.random() * 100)}%` : '20%',
                            animationDelay: `${i * 0.1}s`
                        }}
                    />
                ))}
            </div>
        );
    };

    return (
        <div className={`flex items-center text-xs font-bold rounded-lg border shadow-sm transition-all overflow-hidden ${
            error ? 'bg-red-50 border-red-100 text-red-600' : 'bg-white border-gray-100 text-gray-700'
        } ${className}`}>
            
            <button
                onClick={handlePlayPause}
                disabled={isLoading}
                aria-label={isLoading ? "Loading audio" : isPlaying ? "Pause audio" : label}
                aria-pressed={isPlaying}
                className="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-50 active:bg-gray-100 transition-colors disabled:opacity-50"
            >
                {isLoading ? (
                    <LoaderIcon />
                ) : isPlaying ? (
                    <PauseIcon className="w-4 h-4 text-purple-600" />
                ) : (
                    <MicIcon className="w-4 h-4 text-purple-600" />
                )}
                {!isExpanded && <span>{label}</span>}
            </button>

            {isExpanded && (
                <div className="flex items-center px-2 border-l border-gray-100 bg-gray-50/50">
                    {error ? (
                        <span className="text-red-500 font-medium px-2 py-1 truncate max-w-[150px]" title={error}>
                            Failed
                        </span>
                    ) : (
                        renderWaveform()
                    )}
                    
                    {audioUrl && (
                        <audio 
                            ref={audioRef} 
                            src={audioUrl} 
                            onEnded={handleEnded}
                            className="hidden" 
                        />
                    )}
                </div>
            )}
        </div>
    );
};