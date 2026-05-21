import React, { useState } from 'react';
import { api } from '../../../services/api';
import { RefreshCwIcon } from '../../../components/Icons';

export const MarketingIngestion: React.FC = () => {
    const [url, setUrl] = useState('');
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!url || !url.trim()) {
            setStatus('error');
            setMessage('Please enter a valid URL.');
            return;
        }

        setStatus('loading');
        setMessage('');

        try {
            const res = await api.crawlKnowledgeItem(url.trim(), 'marketing', ['ingested', 'marketing']);
            if (res && res.success) {
                setStatus('success');
                setMessage('Crawling successfully started in background.');
                setUrl('');
                // Fade out success message after 5 seconds
                setTimeout(() => {
                    setStatus(prev => prev === 'success' ? 'idle' : prev);
                    setMessage(prev => prev === 'Crawling successfully started in background.' ? '' : prev);
                }, 5000);
            } else {
                setStatus('error');
                setMessage(res?.message || 'Failed to start crawling.');
            }
        } catch (err: any) {
            setStatus('error');
            setMessage(err.message || 'An error occurred while initiating crawl.');
        }
    };

    return (
        <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-700/50 shadow-inner font-sans">
            <h3 className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3">
                Raw Material Ingestion
            </h3>
            <form onSubmit={handleSubmit} className="flex gap-2">
                <div className="flex-1 relative">
                    <label htmlFor="ingest-url" className="sr-only">URL to ingest</label>
                    <input
                        id="ingest-url"
                        type="url"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="Paste trend report or blog URL..."
                        disabled={status === 'loading'}
                        className="w-full pl-3 pr-3 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-900 dark:text-white transition-all disabled:opacity-50"
                    />
                </div>
                <button
                    type="submit"
                    disabled={status === 'loading'}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-lg text-xs transition-colors disabled:opacity-50 flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                    {status === 'loading' && <RefreshCwIcon className="w-3 h-3 animate-spin text-white" />}
                    {status === 'loading' ? 'INGESTING...' : 'INGEST'}
                </button>
            </form>
            
            {message && (
                <div 
                    aria-live="polite"
                    className={`mt-2.5 text-[11px] font-medium transition-all ${
                        status === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'
                    }`}
                >
                    {message}
                </div>
            )}
        </div>
    );
};
