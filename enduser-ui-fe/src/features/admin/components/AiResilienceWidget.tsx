import React from 'react';
import { api } from '@/services/api';
import { AiHealthStatus } from '@/types';

export const AiResilienceWidget: React.FC = () => {
    const [health, setHealth] = React.useState<AiHealthStatus | null>(null);

    React.useEffect(() => {
        api.getAiHealth().then(setHealth).catch(console.error);
    }, []);

    if (!health) return null;

    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
            <h3 className="text-lg font-bold mb-4 flex items-center justify-between">
                <span>AI Resilience Matrix</span>
                <span className={`text-xs px-2 py-1 rounded uppercase ${health.status === 'healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {health.status}
                </span>
            </h3>
            <div className="space-y-3">
                {health.models.map(m => (
                    <div key={`${m.agent}-${m.model}`} className="flex justify-between items-center text-sm">
                        <div>
                            <div className="font-bold">{m.agent}</div>
                            <div className="text-xs text-muted-foreground font-mono">{m.model}</div>
                        </div>
                        <div className="flex items-center gap-2">
                            {m.latency_ms && <span className="text-xs text-muted-foreground">{m.latency_ms}ms</span>}
                            <div className={`w-2 h-2 rounded-full ${m.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
