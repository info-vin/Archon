import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export const FallbackStatusBadge: React.FC = () => {
    const [status, setStatus] = useState<{ active_tier: number; internet_connected: boolean } | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const data = await api.getFallbackStatus();
                setStatus(data);
            } catch (error) {
                console.error("Failed to fetch fallback status:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 10000); // Poll every 10 seconds
        return () => clearInterval(interval);
    }, []);

    if (loading || !status) {
        return (
            <div className="flex items-center gap-2 px-3 py-1 bg-secondary text-muted-foreground text-xs rounded-full border border-border animate-pulse">
                <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                <span>Connecting...</span>
            </div>
        );
    }

    const { active_tier, internet_connected } = status;

    if (active_tier === 2) {
        return (
            <div className="flex items-center gap-2 px-3 py-1 bg-amber-500/10 text-amber-500 text-xs font-semibold rounded-full border border-amber-500/30 shadow-[0_0_10px_rgba(245,158,11,0.2)]">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping"></span>
                <span>HF 降階備援作用中</span>
            </div>
        );
    }

    if (active_tier === 3 || !internet_connected) {
        return (
            <div className="flex items-center gap-2 px-3 py-1 bg-orange-600/10 text-orange-500 text-xs font-semibold rounded-full border border-orange-500/30 shadow-[0_0_10px_rgba(249,115,22,0.2)]">
                <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                <span>本地離線模式 (Ollama)</span>
            </div>
        );
    }

    return (
        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 text-emerald-500 text-xs font-semibold rounded-full border border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
            <span>主要雲端已連線</span>
        </div>
    );
};
