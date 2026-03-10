import React from 'react';
import { JobData } from '../../../types';
import { SourceBadge } from '../../../components/SourceBadge';
import { SearchIcon, XIcon, SparklesIcon, RefreshCwIcon, ExternalLinkIcon, ShieldCheckIcon } from '../../../components/Icons';
import { Button } from '../../../components/Button';
import { EmptyState } from '../../../components/common/EmptyState';
import { api } from '../../../services/api';

interface MarketingJobSearchProps {
  keyword: string;
  setKeyword: (val: string) => void;
  jobs: JobData[];
  loading: boolean;
  error: string | null;
  setError: (val: string | null) => void;
  searchProgress: number;
  expandedJobIdx: number | null;
  setExpandedJobIdx: (idx: number | null) => void;
  generating: boolean;
  generatingStatus: string;
  generatedPitch: { job: JobData; content: string } | null;
  setGeneratedPitch: (val: { job: JobData; content: string } | null) => void;
  handleSearch: (e?: React.FormEvent) => Promise<void>;
  handleGeneratePitch: (job: JobData) => Promise<void>;
}

export const MarketingJobSearch: React.FC<MarketingJobSearchProps> = ({
  keyword, setKeyword, jobs, loading, error, setError,
  searchProgress, expandedJobIdx, setExpandedJobIdx,
  generating, generatingStatus, generatedPitch, setGeneratedPitch,
  handleSearch, handleGeneratePitch
}) => {
  const hasMockData = jobs.some(job => job.source === 'mock');

  return (
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
          <Button type="submit" disabled={loading} isLoading={loading} variant="primary" accentColor="indigo" size="lg">
            {loading ? 'Analyzing Market...' : 'Find Leads'}
          </Button>
        </form>
      </div>

      <div className="flex gap-6 flex-col lg:flex-row">
        <div className="flex-1 space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-100 flex justify-between items-center">
              <span>{error}</span>
              <button onClick={() => setError(null)} aria-label="Dismiss error" className="p-1 hover:bg-red-100 rounded-full transition-colors focus-visible:ring-2 focus-visible:ring-red-500 outline-none"><XIcon className="w-4 h-4" /></button>
            </div>
          )}
          
          {hasMockData && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
              <svg className="h-5 w-5 text-amber-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <h4 className="text-sm font-semibold text-amber-800">Connection Limited</h4>
                <p className="text-xs text-amber-700 mt-1">Simulated data displayed. System will retry live fetching later.</p>
              </div>
            </div>
          )}

          {generating && (
            <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4 flex items-center gap-3 animate-pulse">
              <RefreshCwIcon className="w-5 h-5 text-indigo-600 animate-spin" />
              <div className="flex-1">
                <p className="text-sm font-bold text-indigo-900">{generatingStatus}</p>
                <p className="text-xs text-indigo-700">Archon is crafting a high-impact response.</p>
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
                  <div className="h-full bg-indigo-600 rounded-full transition-all duration-300 ease-out" style={{ width: `${searchProgress}%` }} />
                </div>
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
                  <div key={idx} className={`bg-card p-5 rounded-xl shadow-sm border transition-all cursor-pointer ${expandedJobIdx === idx ? 'border-indigo-500 ring-1 ring-indigo-500' : 'border-border hover:border-primary/50'}`} onClick={() => setExpandedJobIdx(expandedJobIdx === idx ? null : idx)}>
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
                            <a href={job.url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:text-indigo-800 text-xs font-bold flex items-center gap-1">View Original Post on 104 <ExternalLinkIcon className="w-3 h-3" /></a>
                          </div>
                        )}
                      </div>
                    )}
                    <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
                      <div className="text-xs text-muted-foreground flex items-center gap-2 cursor-pointer" onClick={(e) => { e.stopPropagation(); setExpandedJobIdx(null); }}>
                        <span className={expandedJobIdx === idx ? 'text-indigo-600 font-bold hover:text-indigo-800' : ''}>{expandedJobIdx === idx ? 'Tap to collapse' : 'Tap card to details'}</span>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); api.createLead({ company_name: job.company, job_title: job.title, source: job.source, source_job_url: job.url, identified_need: job.identified_need, status: 'new' }).then(() => alert("Added to Pipeline!")).catch(() => alert("Failed to add lead")); }}>Add Lead</Button>
                        <Button variant="primary" size="sm" accentColor="indigo" onClick={(e) => { e.stopPropagation(); handleGeneratePitch(job); }} disabled={generating} isLoading={generating} icon={!generating && <SparklesIcon className="w-4 h-4" />}>
                          {generating ? 'Drafting...' : 'Generate Pitch'}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
                <div className="h-40 md:hidden pb-20"></div>
              </div>
            </>
          ) : (
            <EmptyState title="No Leads Found" description="Enter a job title above to start scanning." icon={<SearchIcon className="w-12 h-12 text-gray-300 dark:text-gray-500" />} />
          )}
        </div>

        {generatedPitch && (
          <div id="pitch-section" className="lg:w-1/2 space-y-4">
            <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100 text-sm">
              <h4 className="font-bold text-indigo-900 mb-2 flex items-center gap-2"><SparklesIcon className="w-4 h-4" />AI System Prompt</h4>
              <p className="text-indigo-800 font-mono text-xs bg-white/50 p-2 rounded">"You are a top-tier Sales Representative... Write a personalized pitch..."</p>
            </div>
            <div className="bg-card p-6 rounded-xl shadow-lg border border-border sticky top-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-card-foreground">Generated Pitch</h2>
                <span className="text-sm text-muted-foreground">Target: {generatedPitch.job.company}</span>
              </div>
              <div className="bg-muted p-4 rounded-lg border border-border">
                <textarea readOnly className="w-full h-96 bg-transparent border-none resize-none focus:ring-0 text-foreground font-mono text-sm leading-relaxed" value={generatedPitch.content} />
              </div>
              <div className="mt-4 flex gap-3 justify-end">
                <Button variant="ghost" onClick={() => setGeneratedPitch(null)}>Close</Button>
                <Button variant="primary" accentColor="green" icon={<ShieldCheckIcon className="w-4 h-4" />} onClick={() => { const job = generatedPitch.job; api.createLead({ company_name: job.company, job_title: job.title, source: job.source, source_job_url: job.url, identified_need: job.identified_need, status: 'new', pitch_content: generatedPitch.content }).then(() => { alert("Saved!"); setGeneratedPitch(null); }).catch((err) => alert("Failed: " + err.message)); }}>Approve & Save</Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};
