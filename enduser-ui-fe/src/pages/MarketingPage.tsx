import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../services/api';
import { JobData } from '../types';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { SourceBadge } from '../components/SourceBadge';
import { SearchIcon, TableIcon, ShieldCheckIcon, XIcon, SparklesIcon, RefreshCwIcon, ExternalLinkIcon } from '../components/Icons';
import { Button } from '../components/Button';
import { EmptyState } from '../components/common/EmptyState';
import { LeadsCardStack } from '../features/marketing/components/LeadsCardStack';

const MarketingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'search' | 'leads'>('search');
  
  // Search State
  const [keyword, setKeyword] = useState('Data Analyst');
  const [jobs, setJobs] = useState<JobData[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generatingStatus, setGeneratingStatus] = useState("");
  const [statusTimer, setStatusTimer] = useState<NodeJS.Timeout | null>(null);

  // Cleanup effect
  useEffect(() => {
    return () => {
      if (statusTimer) clearInterval(statusTimer);
    };
  }, [statusTimer]);
  const [error, setError] = useState<string | null>(null);
  const [searchProgress, setSearchProgress] = useState(0); // Progress Bar for Job Search
  const [expandedJobIdx, setExpandedJobIdx] = useState<number | null>(null);
  const [generatedPitch, setGeneratedPitch] = useState<{ job: JobData; content: string } | null>(null);

  // Leads State
  const [leads, setLeads] = useState<any[]>([]);
  const [isLeadsLoading, setIsLeadsLoading] = useState(false);
  const [promoteModalOpen, setPromoteModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState<any>(null);
  const [viewPitchModalOpen, setViewPitchModalOpen] = useState(false);
  const [selectedPitchLead, setSelectedPitchLead] = useState<any>(null);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>({ key: 'created_at', direction: 'desc' });
  const [filterMode, setFilterMode] = useState<'all' | 'review_queue'>('all');

  // ... (existing code)

  const openPromoteModal = (lead: any) => {
      setSelectedLead(lead);
      setPromoteModalOpen(true);
  };

  const openViewPitchModal = (lead: any) => {
      setSelectedPitchLead(lead);
      setViewPitchModalOpen(true);
  };

  const sortedLeads = useMemo(() => {
    let sortableLeads = [...leads];
    
    // Filter First
    if (filterMode === 'review_queue') {
        sortableLeads = sortableLeads.filter(l => l.status === 'new' || l.status === 'pending');
    }

    if (sortConfig !== null) {
      sortableLeads.sort((a, b) => {
        // Handle dates specifically
        if (sortConfig.key === 'created_at' || sortConfig.key === 'next_followup_date') {
             const dateA = new Date(a[sortConfig.key] || 0).getTime();
             const dateB = new Date(b[sortConfig.key] || 0).getTime();
             return sortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA;
        }
        
        // Handle strings
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableLeads;
  }, [leads, sortConfig]);

  const requestSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const hasMockData = jobs.some(job => job.source === 'mock');

  useEffect(() => {
      if (activeTab === 'leads') {
          fetchLeads();
      }
  }, [activeTab]);

  const fetchLeads = async () => {
      setIsLeadsLoading(true);
      try {
          const data = await api.getLeads();
          setLeads(data);
      } catch (err) {
          console.error("Failed to load leads", err);
      } finally {
          setIsLeadsLoading(false);
      }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;

    setLoading(true);
    setError(null);
    setGeneratedPitch(null);
    setSearchProgress(0);

    // Progress Simulation
    const progressInterval = setInterval(() => {
        setSearchProgress(prev => {
            if (prev >= 90) return prev; // Stall at 90%
            return prev + Math.floor(Math.random() * 10) + 5;
        });
    }, 1500);

    try {
      const results = await api.searchJobs(keyword);
      clearInterval(progressInterval);
      setSearchProgress(100);
      
      // Short delay to show 100%
      setTimeout(() => {
          setJobs(results);
          setLoading(false);
      }, 500);
    } catch (err: any) {
      clearInterval(progressInterval);
      console.error("Search failed:", err);
      setError("Failed to fetch job market data. Please try again.");
      setLoading(false);
    }
  };

  const handleGeneratePitch = async (job: JobData) => {
      setGenerating(true);
      setError(null);
      setGeneratingStatus("Analyzing job requirements...");
      
      // Dynamic Status Updates for long-running RAG tasks
      const interval = setInterval(() => {
          setGeneratingStatus(prev => {
              if (prev.includes("Analyzing")) return "Consulting Archon RAG knowledge base...";
              if (prev.includes("Consulting")) return "Synthesizing personalized pitch with Pro model...";
              if (prev.includes("Synthesizing")) return "Finalizing polish, almost there...";
              return prev;
          });
      }, 15000);
      setStatusTimer(interval);

      // Implement 60s Timeout Boundary for complex RAG + Pro models
      const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error("TIMEOUT")), 60000)
      );

      try {
          const generatePromise = api.generatePitch(
              job.title, 
              job.company, 
              job.description_full || job.description || ""
          );

          const result = await Promise.race([generatePromise, timeoutPromise]) as any;
          if (interval) clearInterval(interval);
          setStatusTimer(null);

          setGeneratedPitch({
              job: job,
              content: result.content
          });
          
          setTimeout(() => {
              if (typeof document !== 'undefined') {
                document.getElementById('pitch-section')?.scrollIntoView({ behavior: 'smooth' });
              }
          }, 100);
      } catch (err: any) {
          if (interval) clearInterval(interval);
          setStatusTimer(null);
          console.error("Pitch generation failed:", err);
          if (err.message === "TIMEOUT") {
              setError("Generation timed out. The AI model is taking too long. Please try again.");
          } else {
              setError("Failed to generate pitch. Please try again.");
          }
      } finally {
          setGenerating(false);
          setGeneratingStatus("");
      }
  };



  return (
    <PermissionGuard permission="leads:view:sales" fallback={<div className="p-8 text-center text-gray-500">Access Denied: This feature is for Sales & Marketing roles only.</div>}>
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-8">
      <header className="flex justify-between items-end">
        <div>
            <h1 className="text-3xl font-bold text-gray-800">Sales Intelligence</h1>
            <p className="text-gray-500 mt-2 hidden md:block">Identify opportunities and manage your sales pipeline.</p>
        </div>
        
        {/* Tab Navigation */}
        <div className="flex bg-gray-100 p-1 rounded-lg">
            <button 
                onClick={() => setActiveTab('search')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'search' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
            >
                <SearchIcon className="w-4 h-4" />
                Job Search
            </button>
            <button 
                onClick={() => setActiveTab('leads')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'leads' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
            >
                <TableIcon className="w-4 h-4" />
                My Leads
            </button>
        </div>
      </header>

      {/* --- SEARCH TAB --- */}
      {activeTab === 'search' && (
          <>
            <div className="bg-card p-6 rounded-xl shadow-sm border border-border">
                <form onSubmit={handleSearch} className="flex gap-4">
                <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="Enter job title (e.g., Data Analyst)"
                    className="flex-1 p-3 border border-input bg-background text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-primary focus:outline-none"
                />
                <Button
                    type="submit"
                    disabled={loading}
                    isLoading={loading}
                    variant="primary"
                    accentColor="indigo"
                    size="lg"
                >
                    {loading ? 'Analyzing Market...' : 'Find Leads'}
                </Button>
                </form>
            </div>

            <div className="flex gap-6 flex-col lg:flex-row">
                <div className="flex-1 space-y-4">
                    {error && (
                        <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-100 flex justify-between items-center">
                            <span>{error}</span>
                            <button onClick={() => setError(null)} className="p-1 hover:bg-red-100 rounded-full transition-colors"><XIcon className="w-4 h-4" /></button>
                        </div>
                    )}
                    
                    {hasMockData && (
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
                            <svg className="h-5 w-5 text-amber-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <div>
                                <h4 className="text-sm font-semibold text-amber-800">Connection Limited</h4>
                                <p className="text-xs text-amber-700 mt-1">
                                    Direct connection to 104 is currently restricted. Displaying simulated data for demonstration. 
                                    The system will automatically retry live fetching later.
                                </p>
                            </div>
                        </div>
                    )}

                    {generating && (
                        <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4 flex items-center gap-3 animate-pulse">
                            <RefreshCwIcon className="w-5 h-5 text-indigo-600 animate-spin" />
                            <div className="flex-1">
                                <p className="text-sm font-bold text-indigo-900">{generatingStatus}</p>
                                <p className="text-xs text-indigo-700">Archon is crafting a high-impact response for this lead.</p>
                            </div>
                        </div>
                    )}

                    {loading ? (
                        <div className="flex flex-col items-center justify-center p-12 space-y-6 w-full max-w-md mx-auto">
                            <div className="w-full space-y-2">
                                <div className="flex justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                    <span>Scanning Job Boards...</span>
                                    <span>{searchProgress}%</span>
                                </div>
                                <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                                    <div 
                                        className="h-full bg-indigo-600 rounded-full transition-all duration-300 ease-out"
                                        style={{ width: `${searchProgress}%` }}
                                    />
                                </div>
                                <p className="text-xs text-center text-gray-400 pt-2">
                                    Analysing results from 104.com.tw. Please wait approx 15-20s (Anti-Blocking active).
                                </p>
                            </div>
                        </div>
                    ) : jobs.length > 0 ? (
                        <>
                        <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                            Identified Leads 
                            <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 text-xs px-2 py-1 rounded-full">{jobs.length}</span>
                        </h2>
                        <div className="grid gap-4">
                            {jobs.map((job, idx) => (
                            <div 
                                key={idx} 
                                className={`bg-card p-5 rounded-xl shadow-sm border transition-all cursor-pointer ${expandedJobIdx === idx ? 'border-indigo-500 ring-1 ring-indigo-500' : 'border-border hover:border-primary/50'}`}
                                onClick={() => setExpandedJobIdx(expandedJobIdx === idx ? null : idx)}
                            >
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <h3 className="text-lg font-bold text-card-foreground">{job.company}</h3>
                                        <p className="text-sm text-muted-foreground">Hiring: {job.title}</p>
                                    </div>
                                    <SourceBadge source={job.source} />
                                </div>
                                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 mb-4 rounded-r insight">
                                    <p className="text-xs font-bold text-yellow-800 uppercase tracking-wide">AI Insight</p>
                                    <p className="text-sm text-yellow-900 mt-1">{job.identified_need || "Analyzing requirements..."}</p>
                                </div>
                                
                                {expandedJobIdx === idx && (
                                    <div className="mt-4 mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200 text-sm text-gray-700 whitespace-pre-line animate-in fade-in slide-in-from-top-2 duration-200 full-description cursor-auto" onClick={e => e.stopPropagation()}>
                                        <h4 className="font-bold mb-2 text-gray-900 border-b pb-1">Full Job Description</h4>
                                        {job.description_full || job.description || "No detailed description available."}
                                        {job.url && (
                                             <div className="mt-4 pt-2 border-t border-gray-200">
                                                <a 
                                                    href={job.url} 
                                                    target="_blank" 
                                                    rel="noreferrer" 
                                                    className="text-indigo-600 hover:text-indigo-800 text-xs font-bold flex items-center gap-1"
                                                >
                                                    View Original Post on 104 <ExternalLinkIcon className="w-3 h-3" />
                                                </a>
                                             </div>
                                        )}
                                    </div>
                                )}

                                <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
                                    <div className="text-xs text-muted-foreground flex items-center gap-2 cursor-pointer" onClick={(e) => { e.stopPropagation(); setExpandedJobIdx(null); }}>
                                        <span className={expandedJobIdx === idx ? 'text-indigo-600 font-bold hover:text-indigo-800' : ''}>
                                            {expandedJobIdx === idx ? 'Tap to collapse' : 'Tap card to details'}
                                        </span>
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            variant="secondary"
                                            size="sm"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                // create lead (simulation)
                                                api.createLead({
                                                    company_name: job.company,
                                                    job_title: job.title,
                                                    source: job.source,
                                                    source_job_url: job.url,
                                                    identified_need: job.identified_need,
                                                    status: 'new'
                                                }).then(() => {
                                                    alert("Added to Leads Pipeline!");
                                                    // setActiveTab('leads'); // Keep user in search flow
                                                }).catch(() => alert("Failed to add lead"));
                                            }}
                                        >
                                            Add Lead
                                        </Button>
                                        <Button
                                            variant="primary"
                                            size="sm"
                                            accentColor="indigo"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleGeneratePitch(job);
                                            }}
                                            disabled={generating} 
                                            isLoading={generating}
                                            icon={!generating && <SparklesIcon className="w-4 h-4" />}
                                        >
                                            {generating ? 'Drafting...' : 'Generate Pitch'}
                                        </Button>
                                    </div>
                                </div>
                            </div>
                            ))}
                            {/* Extra physical space to ensure mobile scrolling clears navigation bars */}
                            <div className="h-40 md:hidden pb-20"></div>
                        </div>
                        </>
                    ) : (
                        <EmptyState 
                            title="No Leads Found" 
                            description="Enter a job title above to start scanning the market for potential customers."
                            icon={<SearchIcon className="w-12 h-12 text-gray-300 dark:text-gray-500" />}
                        />
                    )}
                </div>

                {generatedPitch && (
                    <div id="pitch-section" className="lg:w-1/2 space-y-4">
                         {/* AI Prompt Reference Card (ENH-005) */}
                         <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100 text-sm">
                            <h4 className="font-bold text-indigo-900 mb-2 flex items-center gap-2">
                                <SparklesIcon className="w-4 h-4" />
                                AI System Prompt
                            </h4>
                            <p className="text-indigo-800 font-mono text-xs bg-white/50 p-2 rounded">
                                "You are a top-tier Sales Representative... Write a personalized, professional, and compelling email pitch... Structure: 1. Hook, 2. Value Prop, 3. CTA."
                            </p>
                         </div>

                        <div className="bg-card p-6 rounded-xl shadow-lg border border-border sticky top-6 generated-pitch">
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-bold text-card-foreground">Generated Pitch</h2>
                                <span className="text-sm text-muted-foreground">Target: {generatedPitch.job.company}</span>
                            </div>
                            <div className="bg-muted p-4 rounded-lg border border-border">
                                <textarea readOnly className="w-full h-96 bg-transparent border-none resize-none focus:ring-0 text-foreground font-mono text-sm leading-relaxed" value={generatedPitch.content} />
                            </div>
                            <div className="mt-4 flex gap-3 justify-end">
                                <Button variant="ghost" onClick={() => setGeneratedPitch(null)}>Close</Button>
                                <Button
                                    variant="primary"
                                    accentColor="green"
                                    icon={<ShieldCheckIcon className="w-4 h-4" />}
                                    onClick={() => {
                                        // Save Pitch using stored full job context
                                        const job = generatedPitch.job;

                                        api.createLead({
                                            company_name: job.company,
                                            job_title: job.title,
                                            source: job.source,
                                            source_job_url: job.url,
                                            identified_need: job.identified_need,
                                            status: 'new',
                                            pitch_content: generatedPitch.content
                                        }).then(() => {
                                            alert("Pitch saved and Lead created!");
                                            setGeneratedPitch(null);
                                        }).catch((err) => {
                                            console.error(err);
                                            alert("Failed to save pitch: " + err.message);
                                        });
                                    }}
                                >
                                    Approve & Save
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
          </>
      )}

      {/* --- LEADS TAB --- */}
      {activeTab === 'leads' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
              <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                  <h2 className="text-lg font-bold text-gray-800">My Leads</h2>
                  <div className="flex gap-3">
                    <button 
                        onClick={async () => {
                            if (confirm("Are you sure you want to delete ALL leads? This cannot be undone.")) {
                                try {
                                    await api.resetLeads();
                                    fetchLeads();
                                    alert("Leads history cleared.");
                                } catch (e: any) {
                                    alert(e.message);
                                }
                            }
                        }}
                        className="text-red-500 text-sm font-medium hover:text-red-700"
                    >
                        Clear History
                    </button>
                    <button onClick={fetchLeads} className="text-indigo-600 text-sm font-medium hover:text-indigo-800">Refresh</button>
                  </div>
              </div>
              
              {/* Desktop Table View */}
              <div className="hidden md:block overflow-x-auto">
                  <div className="px-6 py-4 flex items-center justify-between border-b border-gray-100 bg-gray-50/50">
                        <div className="flex items-center gap-4">
                            <span className="text-sm font-medium text-gray-500">Filter:</span>
                            <button 
                                onClick={() => setFilterMode('all')} 
                                className={`text-xs font-medium px-3 py-1 border rounded-full transition-colors ${filterMode === 'all' ? 'bg-gray-800 text-white border-gray-800' : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'}`}
                            >
                                All Leads
                            </button>
                            <button 
                                onClick={() => setFilterMode('review_queue')}
                                className={`text-xs font-bold px-3 py-1 border rounded-full flex items-center gap-1 transition-colors ${filterMode === 'review_queue' ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100'}`}
                            >
                                <span className={`w-2 h-2 rounded-full ${filterMode === 'review_queue' ? 'bg-white' : 'bg-indigo-500'} animate-pulse`}></span>
                                Review Queue
                            </button>
                        </div>
                  </div>

                  {isLeadsLoading ? (
                      <div className="p-12 flex justify-center">
                          <RefreshCwIcon className="w-8 h-8 text-indigo-600 animate-spin" />
                      </div>
                  ) : leads.length === 0 ? (
                      <div className="p-12">
                        <EmptyState 
                            title="Your Pipeline is Empty" 
                            description="Identify potential customers in the Job Search tab to build your lead pipeline."
                            actionLabel="Go to Search"
                            onAction={() => setActiveTab('search')}
                        />
                      </div>
                  ) : (
                      <table className="w-full text-sm text-left">
                          <thead className="bg-gray-50 text-gray-500 font-medium">
                               <tr>
                                  <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => requestSort('created_at')}>
                                      <div className="flex items-center gap-1">Date {sortConfig?.key === 'created_at' && (sortConfig.direction === 'asc' ? '▲' : '▼')}</div>
                                  </th>
                                  <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => requestSort('company_name')}>
                                      <div className="flex items-center gap-1">Company {sortConfig?.key === 'company_name' && (sortConfig.direction === 'asc' ? '▲' : '▼')}</div>
                                  </th>
                                  <th className="px-6 py-3 w-1/4">
                                     <div className="flex items-center gap-1">Job Summary</div>
                                  </th>
                                  <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => requestSort('status')}>
                                     <div className="flex items-center gap-1">Status {sortConfig?.key === 'status' && (sortConfig.direction === 'asc' ? '▲' : '▼')}</div>
                                  </th>
                                  <th className="px-6 py-3">Source</th>
                                  <th className="px-6 py-3 cursor-pointer hover:bg-gray-100 transition-colors" onClick={() => requestSort('next_followup_date')}>
                                     <div className="flex items-center gap-1">Follow Up {sortConfig?.key === 'next_followup_date' && (sortConfig.direction === 'asc' ? '▲' : '▼')}</div>
                                  </th>
                                  <th className="px-6 py-3 text-right">Action</th>
                              </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                              {sortedLeads.map(lead => (
                                  <tr key={lead.id} className="hover:bg-gray-50 transition-colors group">
                                      <td className="px-6 py-4 text-xs text-gray-500 whitespace-nowrap">
                                          {new Date(lead.created_at || Date.now()).toLocaleDateString()}
                                      </td>
                                      <td className="px-6 py-4">
                                          <div className="font-medium text-gray-900">{lead.company_name}</div>
                                          <div className="text-xs text-gray-500">{lead.job_title}</div>
                                      </td>
                                      <td className="px-6 py-4">
                                          <div className="text-xs text-gray-600 line-clamp-2" title={lead.identified_need || lead.description}>
                                              {lead.identified_need || "Pending Analysis..."}
                                          </div>
                                      </td>
                                      <td className="px-6 py-4">
                                          <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                                              lead.status === 'new' ? 'bg-blue-100 text-blue-700' :
                                              lead.status === 'converted' ? 'bg-green-100 text-green-700' :
                                              'bg-gray-100 text-gray-600'
                                          }`}>
                                              {lead.status.toUpperCase()}
                                          </span>
                                      </td>
                                      <td className="px-6 py-4 text-gray-500">
                                          <a href={lead.source_job_url} target="_blank" rel="noreferrer" className="hover:text-indigo-600 underline decoration-dotted text-xs">View Post</a>
                                      </td>
                                      <td className="px-6 py-4 text-gray-500 text-xs">
                                          {lead.next_followup_date ? (
                                              new Date(lead.next_followup_date).toLocaleDateString()
                                          ) : (
                                              <span className="text-amber-600 bg-amber-50 px-2 py-0.5 rounded cursor-pointer hover:bg-amber-100">Schedule</span>
                                          )}
                                      </td>
                                      <td className="px-6 py-4 text-right">
                                          <div className="flex justify-end items-center gap-2">
                                            {/* Alice's Triple Quick Actions - RESTORED */}
                                            
                                            {/* 1. Interaction History (Activity) */}
                                            <button 
                                                className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all"
                                                title="Interaction Logs"
                                                onClick={(e) => { e.stopPropagation(); alert("Activity Tracker: " + lead.company_name); }}
                                            >
                                                <RefreshCwIcon className="w-4 h-4" />
                                            </button>

                                            {/* 2. Map / Location */}
                                            <button 
                                                className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all"
                                                title="View on Map"
                                                onClick={(e) => { e.stopPropagation(); alert("Opening Map for: " + (lead.location_address || lead.company_name)); }}
                                            >
                                                <SearchIcon className="w-4 h-4" />
                                            </button>

                                            {/* 3. AI Generated Pitch */}
                                            {lead.pitch_content && (
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); openViewPitchModal(lead); }}
                                                    className="p-2 text-indigo-600 bg-indigo-50 hover:bg-indigo-600 hover:text-white rounded-full shadow-sm transition-all active:scale-90"
                                                    title="View AI Pitch"
                                                >
                                                    <SparklesIcon className="w-4 h-4" />
                                                </button>
                                            )}

                                            {/* Promote Button (Primary) */}
                                            {lead.status !== 'converted' && (
                                                <Button
                                                    variant="outline"
                                                    size="xs"
                                                    accentColor="indigo"
                                                    onClick={() => openPromoteModal(lead)}
                                                    className="ml-1 px-3"
                                                >
                                                    Promote
                                                </Button>
                                            )}
                                          </div>
                                      </td>
                                  </tr>
                              ))}
                          </tbody>
                      </table>
                  )}
              </div>

               {/* Mobile Card Stack View (Tinder Mode) - Natural Page Scrolling */}
               <div className="md:hidden p-2 min-h-[550px] flex flex-col justify-start">
                   {isLeadsLoading ? (
                        <div className="flex justify-center p-12">
                           <RefreshCwIcon className="w-8 h-8 text-indigo-600 animate-spin" />
                       </div>
                   ) : leads.length === 0 ? (
                       <EmptyState 
                            title="No Leads" 
                            description="Search for jobs to find leads."
                            actionLabel="Go to Search"
                            onAction={() => setActiveTab('search')}
                        />
                   ) : (
                       <LeadsCardStack 
                            leads={sortedLeads.filter(l => l.status === 'new' || l.status === 'pending')} 
                            onSwipeRight={(lead) => {
                                api.updateLead(lead.id, { status: 'shortlisted' })
                                   .catch(err => console.error("Failed to shortlist", err));
                            }}
                            onSwipeLeft={(lead) => {
                                api.updateLead(lead.id, { status: 'archived' })
                                   .catch(err => console.error("Failed to archive", err));
                            }}
                       />
                   )}
               </div>
          </div>
      )}

      {/* Promote Modal */}
      {promoteModalOpen && selectedLead && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
              <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 relative animate-in fade-in zoom-in-95 duration-200">
                  <button onClick={() => setPromoteModalOpen(false)} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
                      <XIcon className="w-5 h-5" />
                  </button>
                  <h3 className="text-xl font-bold text-gray-800 mb-1">Promote to Vendor</h3>
                  <p className="text-sm text-gray-500 mb-6">Convert {selectedLead.company_name} into an official vendor.</p>
                  
                  <PromoteForm 
                      lead={selectedLead} 
                      onClose={() => setPromoteModalOpen(false)} 
                      onSuccess={() => {
                          setPromoteModalOpen(false);
                          fetchLeads(); // Refresh list
                      }} 
                  />
              </div>
          </div>
      )}

      {/* View Pitch Modal (GAP-024) */}
      {viewPitchModalOpen && selectedPitchLead && (
          <PitchViewModal 
              lead={selectedPitchLead} 
              onClose={() => setViewPitchModalOpen(false)} 
          />
      )}
    </div>
    </PermissionGuard>
  );
};

const PromoteForm: React.FC<{ lead: any; onClose: () => void; onSuccess: () => void }> = ({ lead, onClose, onSuccess }) => {
    const [email, setEmail] = useState(lead.contact_email || '');
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        
        try {
            await api.promoteLead(lead.id, {
                vendor_name: lead.company_name,
                contact_email: email,
                notes: notes
            });
            onSuccess();
        } catch (err: any) {
            alert(err.message || "Failed to promote vendor.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label htmlFor="contact-email" className="block text-sm font-medium text-gray-700 mb-1">Contact Email</label>
                <input 
                    id="contact-email"
                    type="email" 
                    value={email} 
                    onChange={e => setEmail(e.target.value)} 
                    className="w-full p-2 border border-gray-300 bg-white text-gray-900 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    placeholder="contact@company.com" 
                />
            </div>
            <div>
                <label htmlFor="internal-notes" className="block text-sm font-medium text-gray-700 mb-1">Internal Notes</label>
                <textarea 
                    id="internal-notes"
                    value={notes} 
                    onChange={e => setNotes(e.target.value)} 
                    className="w-full p-2 border border-gray-300 bg-white text-gray-900 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    rows={3} 
                    placeholder="Details about this lead..."
                />

            </div>

            {/* AI Enriched Data Display */}
            {lead.enrichment_status === 'success' && (
                <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-100 text-xs">
                    <h4 className="font-bold text-indigo-700 mb-1 flex items-center gap-1">
                        <SparklesIcon className="w-3 h-3" /> AI Insights (Auto-Enriched)
                    </h4>
                    <div className="space-y-1 text-indigo-900">
                        {lead.contact_email && <p><span className="font-semibold">Email:</span> {lead.contact_email}</p>}
                        {/* Extract fields from identified_need if captured there */}
                        {lead.identified_need?.includes('[Auto-Enriched Data]') && (
                            <div className="whitespace-pre-wrap font-mono text-[10px] mt-1 bg-white/50 p-1 rounded">
                                {lead.identified_need.split('[Auto-Enriched Data]')[1]}
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="flex gap-3 justify-end pt-2">
                <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
                <Button
                    type="submit" 
                    disabled={loading}
                    isLoading={loading}
                    variant="primary"
                    accentColor="indigo"
                    icon={<ShieldCheckIcon className="w-4 h-4" />}
                >
                    {loading ? 'Promoting...' : 'Confirm Promotion'}
                </Button>
            </div>
        </form>
    );
};

const PitchViewModal: React.FC<{ lead: any; onClose: () => void }> = ({ lead, onClose }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(lead.pitch_content || "");
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6 relative animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
                    <XIcon className="w-5 h-5" />
                </button>
                <div className="mb-4">
                    <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                        <SparklesIcon className="w-5 h-5 text-indigo-600" />
                        Generated Pitch
                    </h3>
                    <p className="text-sm text-gray-500">Target: {lead.company_name}</p>
                </div>
                
                <div className="flex-1 overflow-y-auto bg-gray-50 p-4 rounded-lg border border-gray-200 mb-4">
                    {lead.pitch_content ? (
                        <div className="whitespace-pre-wrap font-mono text-sm text-gray-800 leading-relaxed">
                            {lead.pitch_content}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-40 text-gray-400">
                            <p>No pitch content available for this lead.</p>
                        </div>
                    )}
                </div>

                <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
                    <Button variant="ghost" onClick={onClose}>Close</Button>
                    {lead.pitch_content && (
                        <Button
                            variant="primary"
                            accentColor="indigo"
                            onClick={handleCopy}
                            icon={copied ? <ShieldCheckIcon className="w-4 h-4" /> : undefined}
                        >
                            {copied ? 'Copied!' : 'Copy to Clipboard'}
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MarketingPage;