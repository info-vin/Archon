import { useState } from 'react';
import { CheckCircleIcon, CopyIcon, ShareIcon, XIcon, SparklesIcon } from '@/components/Icons.tsx';
import { Lead } from './LeadsCardStack.tsx';

interface PitchDrawerProps {
    lead: Lead;
    onClose: () => void;
}

export const LeadPitchDrawer = ({ lead, onClose }: PitchDrawerProps) => {
    // P3: Use saved pitch content if available, else fallback to template
    const pitchText = lead.pitch_content || `Hi, I noticed ${lead.company_name} is looking for ${lead.job_title}. Archon can help with ${lead.identified_need}. we have helped similar companies streamline their workflow by 30%. Would you be open to a 15-min chat?`;
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(pitchText);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleShare = async () => {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: `Pitch for ${lead.company_name}`,
                    text: pitchText,
                });
            } catch (err) {
                console.error("Share failed", err);
            }
        } else {
            alert("Sharing not supported on this device.");
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 z-[70] flex items-end justify-center sm:items-center p-0 sm:p-4 animate-in fade-in duration-200" onClick={onClose}>
            <div 
                className="bg-white w-full max-w-md rounded-t-2xl sm:rounded-2xl p-6 shadow-2xl animate-in slide-in-from-bottom-full sm:zoom-in-95 duration-300"
                onClick={(e) => e.stopPropagation()}
            >
                {/* GAP-006: Visual Drag Handle */}
                <div className="w-full flex justify-center pt-3 pb-1" onClick={onClose} onTouchStart={onClose}>
                    <div className="w-12 h-1.5 bg-gray-300 rounded-full cursor-pointer hover:bg-gray-400 transition-colors" />
                </div>

                <div className="flex justify-between items-center mb-4 border-b pb-4 px-6 pt-2">
                    <div className="flex items-center gap-2">
                        <div className="bg-indigo-100 p-2 rounded-lg text-indigo-600">
                            <SparklesIcon className="w-5 h-5" />
                        </div>
                        <h3 className="text-lg font-bold">{lead.pitch_content ? 'Saved Pitch' : 'AI Pitch Generator'}</h3>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2" aria-label="Close Pitch Generator">
                        <XIcon className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                <div className="bg-gray-50 p-4 rounded-xl border border-gray-100 mb-6 max-h-[50vh] overflow-y-auto">
                    <p className="text-gray-800 leading-relaxed text-base whitespace-pre-wrap font-medium font-mono text-sm">
                        {pitchText}
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <button 
                        onClick={handleCopy}
                        aria-label="Copy Pitch"
                        className={`flex items-center justify-center gap-2 py-3 rounded-xl font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 ${copied ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                    >
                        {copied ? <CheckCircleIcon className="w-5 h-5" /> : <CopyIcon className="w-5 h-5" />}
                        {copied ? "Copied" : "Copy Text"}
                    </button>
                    <button 
                        onClick={handleShare}
                        aria-label="Share Pitch"
                        className="flex items-center justify-center gap-2 py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2"
                    >
                        <ShareIcon className="w-5 h-5" />
                        Share
                    </button>
                </div>
            </div>
        </div>
    );
};