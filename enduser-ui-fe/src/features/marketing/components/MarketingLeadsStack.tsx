import React from 'react';
import { RefreshCwIcon, MapPinIcon } from '../../../components/Icons';
import { Button } from '../../../components/Button';
import { EmptyState as CommonEmptyState } from '../../../components/common/EmptyState';
import { api } from '../../../services/api';

interface MarketingLeadsStackProps {
  leads: any[];
  isLeadsLoading: boolean;
  sortConfig: { key: string; direction: 'asc' | 'desc' } | null;
  filterMode: 'all' | 'review_queue';
  setFilterMode: (val: 'all' | 'review_queue') => void;
  requestSort: (key: string) => void;
  fetchLeads: () => Promise<void>;
  sortedLeads: any[];
  setActiveTab: (val: 'search' | 'leads') => void;
  onOpenVisitLog: (lead: any) => void;
}

export const MarketingLeadsStack: React.FC<MarketingLeadsStackProps> = ({
  leads, isLeadsLoading, sortConfig, filterMode, setFilterMode,
  requestSort, fetchLeads, sortedLeads, setActiveTab, onOpenVisitLog
}) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="p-6 border-b border-gray-100 flex justify-between items-center">
        <h2 className="text-lg font-bold text-gray-800">My Leads</h2>
        <div className="flex gap-3">
          <button 
            onClick={async () => {
              if (confirm("Are you sure you want to delete ALL leads?")) {
                try { await api.resetLeads(); fetchLeads(); } catch (e: any) { alert(e.message); }
              }
            }}
            className="text-red-500 text-sm font-medium hover:text-red-700"
          >
            Clear History
          </button>
          <button onClick={fetchLeads} className="text-indigo-600 text-sm font-medium hover:text-indigo-800">Refresh</button>
        </div>
      </div>
      
      <div className="hidden md:block overflow-x-auto">
        <div className="px-6 py-4 flex items-center justify-between border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-500">Filter:</span>
            <button onClick={() => setFilterMode('all')} className={`text-xs font-medium px-3 py-1 border rounded-full transition-colors ${filterMode === 'all' ? 'bg-gray-800 text-white border-gray-800' : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'}`}>All Leads</button>
            <button onClick={() => setFilterMode('review_queue')} className={`text-xs font-bold px-3 py-1 border rounded-full flex items-center gap-1 transition-colors ${filterMode === 'review_queue' ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100'}`}><span className={`w-2 h-2 rounded-full ${filterMode === 'review_queue' ? 'bg-white' : 'bg-indigo-500'} animate-pulse`}></span>Review Queue</button>
          </div>
        </div>

        {isLeadsLoading ? (
          <div className="p-12 flex justify-center"><RefreshCwIcon className="w-8 h-8 text-indigo-600 animate-spin" /></div>
        ) : leads.length === 0 ? (
          <div className="p-12"><CommonEmptyState title="Your Pipeline is Empty" description="Identify potential customers in the Job Search tab." actionLabel="Go to Search" onAction={() => setActiveTab('search')} /></div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-500 font-medium">
              <tr>
                <th className="px-6 py-3 cursor-pointer hover:bg-gray-100" onClick={() => requestSort('created_at')}>Date {sortConfig?.key === 'created_at' && (sortConfig.direction === 'asc' ? '▲' : '▼')}</th>
                <th className="px-6 py-3 cursor-pointer hover:bg-gray-100" onClick={() => requestSort('company_name')}>Company {sortConfig?.key === 'company_name' && (sortConfig.direction === 'asc' ? '▲' : '▼')}</th>
                <th className="px-6 py-3 w-1/4">Job Summary</th>
                <th className="px-6 py-3 cursor-pointer hover:bg-gray-100" onClick={() => requestSort('status')}>Status {sortConfig?.key === 'status' && (sortConfig.direction === 'asc' ? '▲' : '▼')}</th>
                <th className="px-6 py-3">Source</th>
                <th className="px-6 py-3 cursor-pointer hover:bg-gray-100" onClick={() => requestSort('next_followup_date')}>Follow Up {sortConfig?.key === 'next_followup_date' && (sortConfig.direction === 'asc' ? '▲' : '▼')}</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedLeads.map(lead => (
                <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-xs text-gray-500">{new Date(lead.created_at || Date.now()).toLocaleDateString()}</td>
                  <td className="px-6 py-4"><div className="font-medium text-gray-900">{lead.company_name}</div><div className="text-xs text-gray-500">{lead.job_title}</div></td>
                  <td className="px-6 py-4"><div className="text-xs text-gray-600 line-clamp-2">{lead.identified_need || "Pending Analysis..."}</div></td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <span className={`px-2 py-1 rounded-full text-xs font-bold text-center ${
                        lead.status === 'new' ? 'bg-blue-100 text-blue-700' : 
                        lead.status === 'converted' ? 'bg-green-100 text-green-700' : 
                        lead.status === 'changes_requested' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {lead.status.toUpperCase().replace('_', ' ')}
                      </span>
                      {lead.ai_score !== undefined && (
                        <div className="flex items-center justify-center gap-1">
                          <div className="w-full bg-gray-200 rounded-full h-1">
                            <div className="bg-indigo-600 h-1 rounded-full" style={{ width: `${lead.ai_score}%` }}></div>
                          </div>
                          <span className="text-[10px] font-bold text-indigo-600">{lead.ai_score}</span>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <a href={lead.source_job_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline text-xs">View Post</a>
                      {lead.review_notes && (
                        <p className="text-[10px] text-red-500 italic line-clamp-1" title={lead.review_notes}>Note: {lead.review_notes}</p>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-xs">{lead.next_followup_date ? new Date(lead.next_followup_date).toLocaleDateString() : <span className="text-amber-600 bg-amber-50 px-2 py-0.5 rounded">Schedule</span>}</td>
                  <td className="px-6 py-4 text-right flex justify-end gap-2">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-indigo-600 hover:bg-indigo-50"
                      onClick={() => onOpenVisitLog(lead)}
                      title="Log Visit (Hunter Mode)"
                    >
                      <MapPinIcon className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => alert("Activity Tracker: " + lead.company_name)}><RefreshCwIcon className="w-4 h-4" /></Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

