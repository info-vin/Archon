import React, { useEffect } from 'react';
import { useMachine } from '@xstate/react';
import { analyticsMachine } from '../machines/analyticsMachine';
import { ActivityIcon, RefreshCwIcon, AlertTriangleIcon, BarChart2Icon } from 'lucide-react';

export const AdminCorrectionAnalytics: React.FC = () => {
  const [state, send] = useMachine(analyticsMachine);
  const { data, error, timeRange } = state.context;

  useEffect(() => {
    send({ type: 'FETCH' });
  }, [send]);

  const isLoading = state.matches('loading');
  const isError = state.matches('error');

  // Compute stats
  const totalEdits = data.length;
  const avgCorrection = totalEdits > 0 
    ? (data.reduce((acc, curr) => acc + (curr.correction_rate || 0), 0) / totalEdits).toFixed(1)
    : 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden font-inter">
      <div className="p-6 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <ActivityIcon className="w-5 h-5 text-indigo-600" />
            AI Cognitive Analytics
          </h2>
          <p className="text-sm text-gray-500 mt-1">Tracking human correction rates on AI-generated content.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <select 
            data-testid="time-range-select"
            value={timeRange}
            onChange={(e) => send({ type: 'SET_TIME_RANGE', range: e.target.value })}
            className="text-sm bg-white border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={isLoading}
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          
          <button 
            data-testid="refresh-analytics-btn"
            onClick={() => send({ type: 'FETCH' })}
            disabled={isLoading}
            className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            aria-label="Refresh analytics"
            title="Refresh analytics"
          >
            <RefreshCwIcon className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="p-6">
        {isError ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl flex items-center gap-3 border border-red-100">
            <AlertTriangleIcon className="w-5 h-5 flex-shrink-0" />
            <p data-testid="error-msg" className="font-medium">{error}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-indigo-50/50 rounded-xl p-5 border border-indigo-100">
              <p data-testid="stat-card-title" className="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-1">Avg. Correction Rate</p>
              <div className="flex items-end gap-2">
                <span data-testid="stat-card-value" className="text-3xl font-black text-gray-900">{avgCorrection}%</span>
              </div>
            </div>
            <div className="bg-emerald-50/50 rounded-xl p-5 border border-emerald-100">
              <p className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-1">Total Monitored Edits</p>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-black text-gray-900">{totalEdits}</span>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
            <BarChart2Icon className="w-4 h-4" /> Recent Corrections
          </h3>
          
          {data.length === 0 && !isLoading && !isError ? (
             <div className="py-8 text-center text-gray-500 border border-dashed border-gray-200 rounded-xl">
               No correction data found for this time range.
             </div>
          ) : (
            <div className="border border-gray-100 rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 font-semibold text-gray-600">Date</th>
                    <th className="px-4 py-3 font-semibold text-gray-600">Post ID</th>
                    <th className="px-4 py-3 font-semibold text-gray-600 text-right">Change Volume</th>
                    <th className="px-4 py-3 font-semibold text-gray-600 text-right">Correction Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.map((item, idx) => (
                    <tr key={idx} data-testid="correction-row" className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-4 py-3 text-gray-500">{new Date(item.created_at).toLocaleDateString()}</td>
                      <td data-testid="post-id-cell" className="px-4 py-3 font-mono text-xs text-gray-500">
                        {item.post_id?.substring(0,8)}...
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">
                        <span className="text-xs mr-1 text-gray-400">old:</span>{item.old_length} <span className="text-xs mx-1 text-gray-400">new:</span>{item.new_length}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={`inline-flex px-2 py-1 rounded-md text-xs font-bold ${
                          item.correction_rate > 30 ? 'bg-red-100 text-red-700' :
                          item.correction_rate > 10 ? 'bg-amber-100 text-amber-700' :
                          'bg-emerald-100 text-emerald-700'
                        }`}>
                          {item.correction_rate}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
