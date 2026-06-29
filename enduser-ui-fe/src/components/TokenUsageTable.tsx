import React from 'react';

interface TokenUsageDetail {
  id: string;
  timestamp: string;
  source_type: 'Human' | 'Machine';
  user_name: string;
  model: string;
  tokens: number;
  cost: number;
  context: string;
}

interface TokenUsageTableProps {
  details: TokenUsageDetail[];
}

// PERFORMANCE: Hoisted Intl.DateTimeFormat outside the component to prevent expensive re-instantiations
const timeFormatter = new Intl.DateTimeFormat(undefined, {
  hour: 'numeric',
  minute: 'numeric',
  second: 'numeric',
});

const TokenUsageTable: React.FC<TokenUsageTableProps> = ({ details }) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-gray-100 text-xs font-bold text-gray-400 uppercase tracking-wider">
            <th className="px-4 py-3">Time</th>
            <th className="px-4 py-3">Source</th>
            <th className="px-4 py-3">Model</th>
            <th className="px-4 py-3 text-right">Tokens</th>
            <th className="px-4 py-3 text-right">Cost (USD)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {details.map((row) => (
            <tr key={row.id} className="text-sm hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                {timeFormatter.format(new Date(row.timestamp))}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-col">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full w-fit mb-1 ${
                    row.source_type === 'Human' ? 'bg-green-50 text-green-700' : 'bg-indigo-50 text-indigo-700'
                  }`}>
                    {row.source_type}
                  </span>
                  <span className="font-medium text-gray-900">{row.user_name}</span>
                </div>
              </td>
              <td className="px-4 py-3 text-gray-600 font-mono text-xs">{row.model}</td>
              <td className="px-4 py-3 text-right font-mono text-gray-900">{row.tokens.toLocaleString()}</td>
              <td className="px-4 py-3 text-right font-mono text-gray-900">${row.cost.toFixed(4)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TokenUsageTable;
