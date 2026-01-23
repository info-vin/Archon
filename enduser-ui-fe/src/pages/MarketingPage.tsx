import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { JobData } from '../types';
import { useAuth } from '../hooks/useAuth';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { SourceBadge } from '../components/SourceBadge';
import { SearchIcon, TableIcon, ShieldCheckIcon, XIcon, PlusIcon, SparklesIcon } from '../components/Icons';

const MarketingPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'search' | 'leads'>('search');
  
  // Search State
  const [keyword, setKeyword] = useState('Data Analyst');
  const [jobs, setJobs] = useState<JobData[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedJobIdx, setExpandedJobIdx] = useState<number | null>(null);
  const [generatedPitch, setGeneratedPitch] = useState<{ forCompany: string; content: string } | null>(null);

  // Leads State
  const [leads, setLeads] = useState<any[]>([]);
  const [isLeadsLoading, setIsLeadsLoading] = useState(false);
  const [promoteModalOpen, setPromoteModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState<any>(null);

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
    try {
      const results = await api.searchJobs(keyword);
      setJobs(results);
    } catch (err: any) {
      console.error("Search failed:", err);
      setError("Failed to fetch job market data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePitch = async (job: JobData) => {
      setGenerating(true);
      setError(null);
      try {
          const result = await api.generatePitch(
              job.title, 
              job.company, 
              job.description_full || job.description || ""
          );
          setGeneratedPitch({
              forCompany: job.company,
              content: result.content
          });
          setTimeout(() => {
              if (typeof document !== 'undefined') {
                document.getElementById('pitch-section')?.scrollIntoView({ behavior: 'smooth' });
              }
          }, 100);
      } catch (err: any) {
          console.error("Pitch generation failed:", err);
          setError("Failed to generate pitch. Please try again.");
      } finally {
          setGenerating(false);
      }
  };

  const openPromoteModal = (lead: any) => {
      setSelectedLead(lead);
      setPromoteModalOpen(true);
  };

  return (
    <PermissionGuard permission="leads:view:all" userRole={user?.role} fallback={<div className="p-8 text-center text-gray-500">Access Denied: This feature is for Sales & Marketing roles only.</div>}>
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      <header className="flex justify-between items-end">
        <div>
            <h1 className="text-3xl font-bold text-gray-800">Sales Intelligence</h1>
            <p className="text-gray-500 mt-2">Identify opportunities and manage your sales pipeline.</p>
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
                <button
                    type="submit"
                    disabled={loading}
                    className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                    {loading ? 'Analyzing Market...' : 'Find Leads'}
                </button>
                </form>
            </div>

            <div className="flex gap-6 flex-col lg:flex-row">
                <div className="flex-1 space-y-4">
                    {error && <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-100">{error}</div>}
                    
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

                    {jobs.length > 0 && (
                        <>
                        <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                            Identified Leads 
                            <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300 text-xs px-2 py-1 rounded-full">{jobs.length}</span>
                        </h2>
                        <div className="grid gap-4">
                            {jobs.map((job, idx) => (
                            <div key={idx} className="bg-card p-5 rounded-xl shadow-sm border border-border hover:border-primary/50 transition-colors lead-card">
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
                                <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
                                    <div className="flex gap-3">
                                        <a 
                                            href={job.url || '#'} 
                                            target="_blank" 
                                            rel="noreferrer" 
                                            onClick={(e) => !job.url && e.preventDefault()}
                                            className={`text-sm flex items-center gap-1 ${!job.url ? 'text-gray-400 cursor-not-allowed' : 'text-gray-500 hover:text-gray-700'}`}
                                        >
                                            View Link
                                        </a>
                                        <button onClick={() => setExpandedJobIdx(expandedJobIdx === idx ? null : idx)} className="text-indigo-600 hover:text-indigo-800 text-sm font-medium transition-colors">
                                            {expandedJobIdx === idx ? 'Hide Details' : 'View Full JD'}
                                        </button>
                                    </div>
                                    <button onClick={() => handleGeneratePitch(job)} disabled={generating} className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 shadow-sm transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed">
                                        {generating ? 'Generating...' : 'Generate Pitch'}
                                    </button>
                                </div>
                                {expandedJobIdx === idx && (
                                    <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200 text-sm text-gray-700 whitespace-pre-line animate-in fade-in slide-in-from-top-2 duration-200 full-description">
                                        <h4 className="font-bold mb-2 text-gray-900 border-b pb-1">Full Job Description</h4>
                                        {job.description_full || job.description || "No detailed description available."}
                                    </div>
                                )}
                            </div>
                            ))}
                        </div>
                        </>
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
                                <span className="text-sm text-muted-foreground">Target: {generatedPitch.forCompany}</span>
                            </div>
                            <div className="bg-muted p-4 rounded-lg border border-border">
                                <textarea readOnly className="w-full h-96 bg-transparent border-none resize-none focus:ring-0 text-foreground font-mono text-sm leading-relaxed" value={generatedPitch.content} />
                            </div>
                            <div className="mt-4 flex gap-3 justify-end">
                                <button className="text-gray-600 hover:text-gray-800 px-4 py-2 text-sm font-medium" onClick={() => setGeneratedPitch(null)}>Close</button>
                                <button className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 shadow-sm font-medium flex items-center gap-2" onClick={() => alert("Pitch approved and saved to knowledge base!")}>
                                    <ShieldCheckIcon className="w-4 h-4" />
                                    <span>Approve & Save</span>
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
          </>
      )}

      {/* --- LEADS TAB --- */}
      {activeTab === 'leads' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                  <h2 className="text-lg font-bold text-gray-800">My Leads</h2>
                  <button onClick={fetchLeads} className="text-indigo-600 text-sm font-medium hover:text-indigo-800">Refresh</button>
              </div>
              <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                      <thead className="bg-gray-50 text-gray-500 font-medium">
                          <tr>
                              <th className="px-6 py-3">Company</th>
                              <th className="px-6 py-3">Status</th>
                              <th className="px-6 py-3">Source</th>
                              <th className="px-6 py-3">Follow Up</th>
                              <th className="px-6 py-3 text-right">Action</th>
                          </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                          {isLeadsLoading ? (
                              <tr><td colSpan={5} className="p-8 text-center text-gray-500">Loading leads...</td></tr>
                          ) : leads.length === 0 ? (
                              <tr><td colSpan={5} className="p-8 text-center text-gray-500">No leads found. Start by searching for jobs.</td></tr>
                          ) : (
                              leads.map(lead => (
                                  <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
                                      <td className="px-6 py-4 font-medium text-gray-900">{lead.company_name}</td>
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
                                          <a href={lead.source_job_url} target="_blank" rel="noreferrer" className="hover:text-indigo-600 underline decoration-dotted">104 Link</a>
                                      </td>
                                      <td className="px-6 py-4 text-gray-500">{lead.next_followup_date ? new Date(lead.next_followup_date).toLocaleDateString() : '-'}</td>
                                      <td className="px-6 py-4 text-right">
                                          {lead.status !== 'converted' && (
                                              <button 
                                                  onClick={() => openPromoteModal(lead)}
                                                  className="text-indigo-600 hover:text-indigo-800 font-medium text-xs border border-indigo-200 px-3 py-1 rounded hover:bg-indigo-50 transition-colors"
                                              >
                                                  Promote to Vendor
                                              </button>
                                          )}
                                      </td>
                                  </tr>
                              ))
                          )}
                      </tbody>
                  </table>
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
    </div>
    </PermissionGuard>
  );
};

const PromoteForm: React.FC<{ lead: any; onClose: () => void; onSuccess: () => void }> = ({ lead, onClose, onSuccess }) => {
    const [email, setEmail] = useState('');
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
        } catch (err) {
            alert("Failed to promote vendor.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contact Email</label>
                <input 
                    type="email" 
                    value={email} 
                    onChange={e => setEmail(e.target.value)} 
                    className="w-full p-2 border border-gray-300 bg-white text-gray-900 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    placeholder="contact@company.com" 
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Internal Notes</label>
                <textarea 
                    value={notes} 
                    onChange={e => setNotes(e.target.value)} 
                    className="w-full p-2 border border-gray-300 bg-white text-gray-900 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    rows={3} 
                    placeholder="Details about this lead..."
                />
            </div>
            <div className="flex gap-3 justify-end pt-2">
                <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600 font-medium hover:bg-gray-100 rounded-lg">Cancel</button>
                <button 
                    type="submit" 
                    disabled={loading}
                    className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                >
                    <ShieldCheckIcon className="w-4 h-4" />
                    {loading ? 'Promoting...' : 'Confirm Promotion'}
                </button>
            </div>
        </form>
    );
};

export default MarketingPage;