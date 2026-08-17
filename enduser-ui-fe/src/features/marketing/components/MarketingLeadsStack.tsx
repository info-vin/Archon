import React from 'react';
import { RefreshCwIcon, MapPinIcon, ActivityIcon, SparklesIcon } from '../../../components/Icons';
import { Button } from '../../../components/Button';
import { EmptyState as CommonEmptyState } from '../../../components/common/EmptyState';
import { api } from '../../../services/api';
import { LeadsCardStack, Lead } from './LeadsCardStack';

// PERFORMANCE: Hoisted static dictionary to prevent O(N) string allocations and manipulations in render loops
const STATUS_DISPLAY: Record<string, string> = {
  'new': 'NEW',
  'pending': 'PENDING',
  'shortlisted': 'SHORTLISTED',
  'converted': 'CONVERTED',
  'archived': 'ARCHIVED',
  'review_queue': 'REVIEW QUEUE'
};

// PERFORMANCE: Hoisted Intl.DateTimeFormat outside the component to prevent expensive re-instantiations during list rendering
const dateFormatter = new Intl.DateTimeFormat();
const safeFormatLeadDate = (dateVal: any) => {
  const d = new Date(dateVal);
  return isNaN(d.getTime()) ? 'Invalid Date' : dateFormatter.format(d);
};

// PERFORMANCE: Extract chained ternary string operations into O(1) static lookup dictionaries
const MOBILE_STATUS_STYLE_MAP: Record<string, string> = {
  'converted': 'bg-green-100 text-green-700'
};
const MOBILE_DEFAULT_STYLE = 'bg-indigo-100 text-indigo-700';

const DESKTOP_STATUS_STYLE_MAP: Record<string, string> = {
  'new': 'bg-blue-100 text-blue-700',
  'converted': 'bg-green-100 text-green-700'
};
const DESKTOP_DEFAULT_STYLE = 'bg-gray-100 text-gray-600';

// PERFORMANCE: Pre-calculate complex string manipulations (toUpperCase, replace) to avoid O(N) allocation during render loops
const STATUS_FORMAT_MAP: Record<string, string> = {
  'new': 'NEW',
  'converted': 'CONVERTED',
  'review_queue': 'REVIEW QUEUE',
  'contacted': 'CONTACTED',
  'qualified': 'QUALIFIED',
  'proposal_sent': 'PROPOSAL SENT',
  'negotiation': 'NEGOTIATION',
  'lost': 'LOST'
};

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
  onGeneratePitch: (lead: any) => void;
}

export const MarketingLeadsStack: React.FC<MarketingLeadsStackProps> = ({
  leads, isLeadsLoading, sortConfig, filterMode, setFilterMode,
  requestSort, fetchLeads, sortedLeads, setActiveTab, onOpenVisitLog, onGeneratePitch
}) => {
  // Scenario A: Swipeable Stack for New/Pending Leads
  const pendingLeads: Lead[] = sortedLeads
    .filter(l => l.status === 'new' || l.status === 'pending')
    .map(l => ({
        id: l.id,
        company_name: l.company_name,
        job_title: l.job_title,
        source: l.source,
        source_job_url: l.source_job_url,
        identified_need: l.identified_need || "",
        status: l.status,
        match_score: l.ai_score,
        pitch_content: l.pitch_content
    }));

  const shortlistedLeads = sortedLeads.filter(l => l.status !== 'new' && l.status !== 'pending' && l.status !== 'archived');

  const handleSwipeRight = async (lead: Lead) => {
    try {
        await api.updateLead(lead.id, { status: 'shortlisted' });
        await fetchLeads();
    } catch (err) {
        console.error("Failed to shortlist via swipe:", err);
    }
  };

  const handleSwipeLeft = async (lead: Lead) => {
    try {
        await api.updateLead(lead.id, { status: 'archived' });
        await fetchLeads();
    } catch (err) {
        console.error("Failed to archive via swipe:", err);
    }
  };

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
            className="text-red-500 text-sm font-medium hover:text-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-red-500 rounded-md px-2 py-1 -mx-2"
          >
            Clear History
          </button>
          <button onClick={fetchLeads} className="text-indigo-600 text-sm font-medium hover:text-indigo-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-500 rounded-md px-2 py-1 -mx-2">Refresh</button>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <div className="px-6 py-4 flex items-center justify-between border-b border-gray-100 bg-gray-50/50">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-500">Filter:</span>
            <button onClick={() => setFilterMode('all')} aria-pressed={filterMode === 'all'} className={`text-xs font-medium px-3 py-1 border rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-gray-800 ${filterMode === 'all' ? 'bg-gray-800 text-white border-gray-800' : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'}`}>All Leads</button>
            <button onClick={() => setFilterMode('review_queue')} aria-pressed={filterMode === 'review_queue'} className={`text-xs font-bold px-3 py-1 border rounded-full flex items-center gap-1 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-600 ${filterMode === 'review_queue' ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100'}`}><span className={`w-2 h-2 rounded-full ${filterMode === 'review_queue' ? 'bg-white' : 'bg-indigo-500'} animate-pulse`}></span>Review Queue</button>
          </div>
        </div>

        {isLeadsLoading ? (
          <div className="p-12 flex justify-center"><RefreshCwIcon className="w-8 h-8 text-indigo-600 animate-spin" /></div>
        ) : leads.length === 0 ? (
          <div className="p-12"><CommonEmptyState title="Your Pipeline is Empty" description="Identify potential customers in the Job Search tab." actionLabel="Go to Search" onAction={() => setActiveTab('search')} /></div>
        ) : (
          <>
            {/* MOBILE: Swipeable Stack for New Leads */}
            {pendingLeads.length > 0 && (
                <div className="md:hidden pt-4 pb-12 bg-gray-50/30 border-b border-gray-100">
                    <div className="px-6 mb-2">
                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Hunter Mode: Swipe to Shortlist</span>
                    </div>
                    <LeadsCardStack 
                        leads={pendingLeads}
                        onSwipeRight={handleSwipeRight}
                        onSwipeLeft={handleSwipeLeft}
                    />
                </div>
            )}

            {/* MOBILE: Shortlisted/Converted Items (Classic List with Scenario B Pitch) */}
            <div className="md:hidden space-y-4 p-4">
              {shortlistedLeads.length > 0 && <h3 className="text-xs font-bold text-gray-500 px-2 uppercase tracking-tight mb-2">My Shortlist ({shortlistedLeads.length})</h3>}
              {shortlistedLeads.map(lead => (
                <div key={lead.id} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 space-y-3 transition-all active:scale-[0.98] active:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 font-bold text-lg">
                        {lead.company_name[0]}
                      </div>
                      <div>
                        <div className="font-bold text-gray-900 leading-tight">{lead.company_name}</div>
                        <div className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">{lead.job_title}</div>
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      MOBILE_STATUS_STYLE_MAP[lead.status] || MOBILE_DEFAULT_STYLE
                    }`}>
                      {STATUS_DISPLAY[lead.status] || STATUS_FORMAT_MAP[lead.status] || lead.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="bg-gray-50/80 p-3 rounded-xl border border-gray-50 text-xs text-gray-700 italic">
                    {lead.identified_need || "Qualified lead data..."}
                  </div>
                  <div className="grid grid-cols-3 gap-2 pt-2">
                    <Button variant="outline" size="sm" className="text-indigo-600 border-indigo-100 bg-indigo-50/30 font-bold text-[10px] h-9 rounded-xl" onClick={() => onOpenVisitLog(lead)}>
                      <MapPinIcon className="w-3.5 h-3.5 mr-1" /> HUNTER
                    </Button>
                    {/* Scenario B: Restore One-Tap Pitch */}
                    <Button variant="outline" size="sm" className="text-amber-600 border-amber-100 bg-amber-50/30 font-bold text-[10px] h-9 rounded-xl" onClick={() => onGeneratePitch(lead)}>
                      <SparklesIcon className="w-3.5 h-3.5 mr-1" /> PITCH
                    </Button>
                    <a href={lead.source_job_url} target="_blank" rel="noreferrer" className="flex items-center justify-center bg-gray-900 text-white rounded-xl text-[10px] font-bold h-9">
                      VIEW URL
                    </a>
                  </div>
                </div>
              ))}
              {pendingLeads.length === 0 && shortlistedLeads.length === 0 && (
                  <p className="text-center py-8 text-gray-400 text-sm italic">All caught up!</p>
              )}
            </div>

            {/* Desktop Table View */}
            <table className="hidden md:table w-full text-sm text-left">
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
                    <td className="px-6 py-4 text-xs text-gray-500 whitespace-nowrap">{safeFormatLeadDate(lead.created_at || Date.now())}</td>
                    <td className="px-6 py-4 min-w-0 max-w-[200px]">
                      <div className="font-medium text-gray-900 truncate" title={lead.company_name}>{lead.company_name}</div>
                      <div className="text-xs text-gray-500 truncate" title={lead.job_title}>{lead.job_title}</div>
                    </td>
                    <td className="px-6 py-4 w-1/4">
                      <div className="text-xs text-gray-600 line-clamp-2">{lead.identified_need || "Pending Analysis..."}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1">
                        <span className={`px-2 py-1 rounded-full text-xs font-bold text-center ${
                          DESKTOP_STATUS_STYLE_MAP[lead.status] || DESKTOP_DEFAULT_STYLE
                        }`}>
                          {STATUS_DISPLAY[lead.status] || STATUS_FORMAT_MAP[lead.status] || lead.status.toUpperCase().replace('_', ' ')}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4"><a href={lead.source_job_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline text-xs">View Post</a></td>
                    <td className="px-6 py-4 text-xs whitespace-nowrap">{lead.next_followup_date ? safeFormatLeadDate(lead.next_followup_date) : <span className="text-amber-600 bg-amber-50 px-2 py-0.5 rounded">Schedule</span>}</td>
                    <td className="px-6 py-4 text-right flex justify-end gap-2">
                      <Button variant="ghost" size="sm" className="text-indigo-600 hover:bg-indigo-50" onClick={() => onOpenVisitLog(lead)} aria-label="Log Visit (Hunter Mode)" title="Log Visit (Hunter Mode)">
                        <MapPinIcon className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" aria-label="Track Activity" title="Track Activity" onClick={() => alert("Activity Tracker: " + lead.company_name)}><ActivityIcon className="w-4 h-4" /></Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
};
