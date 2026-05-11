import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { AiUsageStats } from '@/types';
import { RefreshCwIcon, AlertTriangleIcon, ActivityIcon } from '@/components/Icons';
import TokenUsageTable, { TokenUsageDetail } from './TokenUsageTable';
import { ROIAnalyticsBadge } from './ROIAnalyticsBadge';

export const AdminCostDashboard: React.FC = () => {
    const [aiStats, setAiStats] = useState<AiUsageStats | null>(null);
    const [recentUsage, setRecentUsage] = useState<TokenUsageDetail[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                // Physically fetch data from endpoints
                const [aiData, recentData] = await Promise.all([
                    api.getAiUsage(),
                    api.getRecentTokenUsage()
                ]);
                
                if (isMounted) {
                    setAiStats(aiData);
                    setRecentUsage(recentData || []);
                }
            } catch (err: any) {
                if (isMounted) {
                    setError(err.message || "Failed to load cost data");
                }
            } finally {
                if (isMounted) {
                    // Physical delay to allow Headless renderer to paint the UI
                    setTimeout(() => setLoading(false), 300);
                }
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, []);

    if (loading) {
        return (
            <div className="flex justify-center items-center p-20 flex-col gap-4">
                <RefreshCwIcon className="animate-spin w-10 h-10 text-indigo-600" />
                <p className="text-muted-foreground animate-pulse">Computing Token ROI & Usage...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 text-red-700 p-6 rounded-xl border border-red-200 flex items-start gap-4">
                <AlertTriangleIcon className="w-6 h-6 shrink-0" />
                <div>
                    <h4 className="font-bold">Dashboard Unreachable</h4>
                    <p className="text-sm mt-1">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 font-sans pb-20">
            <div>
                <h2 className="text-2xl font-bold text-gray-800">Token Cost & ROI Analytics</h2>
                <p className="text-sm text-muted-foreground mt-1">Real-time usage and financial impact based on physical token consumption.</p>
            </div>

            {/* ROI Overview Badge */}
            <ROIAnalyticsBadge data={{
                total_monthly_usd: aiStats?.total_cost_usd || 0,
                total_monthly_tokens: aiStats?.total_used || 0,
                usage_percentage: aiStats?.usage_percentage || 0,
                is_real_data: aiStats?.is_real_data || false
            }} />

            {/* Recent Transaction Log (TokenUsageTable) */}
            <div className="bg-card rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col">
                <div className="p-6 border-b border-border flex justify-between items-center bg-muted/10">
                    <h3 className="text-lg font-bold flex items-center gap-2">
                        <ActivityIcon className="w-5 h-5 text-indigo-500" />
                        Live Token Transactions (Top 20)
                    </h3>
                </div>
                {recentUsage.length > 0 ? (
                    <TokenUsageTable details={recentUsage} />
                ) : (
                    <div className="p-12 text-center text-muted-foreground italic">
                        No token transactions found in the database.
                    </div>
                )}
            </div>
        </div>
    );
};
