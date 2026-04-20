import React from 'react';

export interface TokenUsageDetail {
  id: string;
  timestamp: string;
  user_name: string;
  role: string;
  model: string;
  tokens: number;
  cost: number;
  context: string;
}

interface TokenUsageTableProps {
  details: TokenUsageDetail[];
}

const TokenUsageTable: React.FC<TokenUsageTableProps> = ({ details }) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-border text-xs font-bold text-muted-foreground uppercase tracking-wider">
            <th className="px-4 py-3 text-left">Time</th>
            <th className="px-4 py-3 text-left">Entity</th>
            <th className="px-4 py-3 text-left">Model</th>
            <th className="px-4 py-3 text-right">Tokens</th>
            <th className="px-4 py-3 text-right">Cost (USD)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/50">
          {details.map((row) => (
            <tr key={row.id} className="text-sm hover:bg-muted/30 transition-colors">
              <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                {new Date(row.timestamp).toLocaleTimeString()}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-col">
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full w-fit mb-1 ${
                    row.role === 'ai_agent' || row.role === 'system' ? 'bg-indigo-100 text-indigo-700' : 'bg-green-100 text-green-700'
                  }`}>
                    {row.role.toUpperCase()}
                  </span>
                  <span className="font-medium">{row.user_name}</span>
                </div>
              </td>
              <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{row.model}</td>
              <td className="px-4 py-3 text-right font-mono">{row.tokens.toLocaleString()}</td>
              <td className="px-4 py-3 text-right font-mono font-bold">
                ${row.cost > 0 ? row.cost.toFixed(4) : "0.0000"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TokenUsageTable;
