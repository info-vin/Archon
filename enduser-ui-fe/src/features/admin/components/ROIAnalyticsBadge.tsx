
import React from 'react';
import { DollarSign, Cpu, TrendingUp, ShieldCheck } from 'lucide-react';

interface ROIAnalyticsBadgeProps {
  data: {
    total_monthly_usd: number;
    total_monthly_tokens: number;
    usage_percentage: number;
    is_real_data: boolean;
  };
}

export const ROIAnalyticsBadge: React.FC<ROIAnalyticsBadgeProps> = ({ data }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      {/* Monthly Spend Badge */}
      <div className="bg-card p-4 rounded-xl border border-border shadow-sm flex items-center gap-4">
        <div className="p-3 bg-green-500/10 rounded-lg">
          <DollarSign className="w-5 h-5 text-green-600" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground font-medium uppercase">Monthly Spend</p>
          <h4 className="text-xl font-bold">${data.total_monthly_usd.toFixed(2)}</h4>
        </div>
      </div>

      {/* Token Volume Badge */}
      <div className="bg-card p-4 rounded-xl border border-border shadow-sm flex items-center gap-4">
        <div className="p-3 bg-blue-500/10 rounded-lg">
          <Cpu className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground font-medium uppercase">Tokens Used</p>
          <h4 className="text-xl font-bold">{(data.total_monthly_tokens / 1000).toFixed(1)}k</h4>
        </div>
      </div>

      {/* Usage Capacity Badge */}
      <div className="bg-card p-4 rounded-xl border border-border shadow-sm flex items-center gap-4">
        <div className="p-3 bg-purple-500/10 rounded-lg">
          <TrendingUp className="w-5 h-5 text-purple-600" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground font-medium uppercase">Quota Usage</p>
          <div className="flex items-center gap-2">
            <h4 className="text-xl font-bold">{data.usage_percentage}%</h4>
            <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-purple-500" 
                style={{ width: `${data.usage_percentage}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Status Badge */}
      <div className="bg-card p-4 rounded-xl border border-border shadow-sm flex items-center gap-4">
        <div className={`p-3 rounded-lg ${data.is_real_data ? 'bg-indigo-500/10' : 'bg-orange-500/10'}`}>
          <ShieldCheck className={`w-5 h-5 ${data.is_real_data ? 'text-indigo-600' : 'text-orange-600'}`} />
        </div>
        <div>
          <p className="text-xs text-muted-foreground font-medium uppercase">Data Integrity</p>
          <h4 className={`text-sm font-bold ${data.is_real_data ? 'text-indigo-600' : 'text-orange-600'}`}>
            {data.is_real_data ? 'PHYSICAL LOGS' : 'SIMULATED'}
          </h4>
        </div>
      </div>
    </div>
  );
};
