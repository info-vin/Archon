import React from 'react';

interface TaskCrawlerSettingsProps {
  assigneeId: string;
  assignableUsers: any[];
  isLoadingUsers: boolean;
  crawlerTargets: any[];
  crawlerTargetId: string;
  setCrawlerTargetId: (id: string) => void;
  isRecurring: boolean;
  setIsRecurring: (val: boolean) => void;
  frequency: string;
  setFrequency: (val: string) => void;
  inputClass: string;
}

export const TaskCrawlerSettings: React.FC<TaskCrawlerSettingsProps> = ({
  assigneeId,
  assignableUsers,
  isLoadingUsers,
  crawlerTargets,
  crawlerTargetId,
  setCrawlerTargetId,
  isRecurring,
  setIsRecurring,
  frequency,
  setFrequency,
  inputClass
}) => {
  const selected = assignableUsers.find(u => u.id === assigneeId);
  const isLibrarian = selected?.name.toLowerCase().includes('librarian') || selected?.role === 'ai_agent';
  
  if (!isLibrarian || isLoadingUsers) {
      return null;
  }

  return (
      <div className="mt-4 p-4 bg-rose-50 dark:bg-rose-900/10 border border-rose-100 dark:border-rose-800 rounded-lg space-y-3 transition-all animate-in fade-in slide-in-from-top-2">
          <p className="text-[10px] font-bold text-rose-600 dark:text-rose-400 uppercase tracking-widest flex items-center gap-1">
              <span className="w-2 h-2 bg-rose-500 rounded-full animate-pulse"></span>
              David's Architect Tools
          </p>
          
          <div>
              <label htmlFor="crawlerTarget" className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Associate Knowledge Target (from 3737)</label>
              <select
                  id="crawlerTarget"
                  value={crawlerTargetId || ''}
                  onChange={(e) => setCrawlerTargetId(e.target.value)}
                  className={`${inputClass} border-rose-200 focus:ring-rose-500 focus:border-rose-500`}
              >
                  <option value="">-- No Specific Target --</option>
                  {crawlerTargets.map(t => (
                      <option key={t.id} value={t.id}>{t.target_url}</option>
                  ))}
              </select>
          </div>

          <div className="flex items-center gap-2 pt-1">
              <input 
                  type="checkbox" 
                  id="isRecurring" 
                  checked={isRecurring} 
                  onChange={(e) => setIsRecurring(e.target.checked)}
                  className="rounded border-rose-300 text-rose-600 focus:ring-rose-500 h-4 w-4"
              />
              <label htmlFor="isRecurring" className="text-xs font-bold text-rose-800 dark:text-rose-200 cursor-pointer">Add to Periodic Schedule (Expertise Loop)</label>
          </div>

          {isRecurring && (
              <div className="pl-6 border-l-2 border-rose-200 dark:border-rose-800 py-1 space-y-2">
                  <label htmlFor="frequency" className="block text-[10px] font-bold text-rose-600 uppercase">Sync Frequency</label>
                  <select 
                      id="frequency"
                      value={frequency} 
                      onChange={(e) => setFrequency(e.target.value)}
                      className={`${inputClass} py-1 text-xs border-rose-100`}
                  >
                      <option value="daily">Daily (System Patrol at 04:00 AM)</option>
                      <option value="weekly">Weekly (Monday morning)</option>
                      <option value="monthly">Monthly (1st day)</option>
                  </select>
              </div>
          )}
      </div>
  );
};
