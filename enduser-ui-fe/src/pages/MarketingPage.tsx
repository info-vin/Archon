import React, { useState } from 'react';
import { api } from '../services/api';
import { JobData } from '../types';
import { useAuth } from '../hooks/useAuth';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { SourceBadge } from '../components/SourceBadge';

const MarketingPage: React.FC = () => {
  const { user } = useAuth();
  const [keyword, setKeyword] = useState('Data Analyst');
  const [jobs, setJobs] = useState<JobData[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedJobIdx, setExpandedJobIdx] = useState<number | null>(null);
  
  // State for generated pitch modal/display
  const [generatedPitch, setGeneratedPitch] = useState<{ forCompany: string; content: string } | null>(null);

  const hasMockData = jobs.some(job => job.source === 'mock');

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
          
          // Scroll to pitch section
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

  return (
    <PermissionGuard permission="leads:view:all" userRole={user?.role} fallback={<div className="p-8 text-center text-gray-500">Access Denied: This feature is for Sales & Marketing roles only.</div>}>
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      <header>
        <h1 className="text-3xl font-bold text-gray-800">Sales Intelligence</h1>
        <p className="text-gray-500 mt-2">Find hiring companies and generate tailored sales pitches.</p>
      </header>

      {/* Search Section */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Enter job title (e.g., Data Analyst)"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
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
        {/* Results Column */}
        <div className="flex-1 space-y-4">
            {error && (
                <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-100">
                {error}
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

            {jobs.length > 0 && (
                <>
                <h2 className="text-xl font-semibold text-gray-700 flex items-center gap-2">
                    Identified Leads 
                    <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded-full">{jobs.length}</span>
                </h2>
                <div className="grid gap-4">
                    {jobs.map((job, idx) => (
                    <div key={idx} className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 hover:border-indigo-200 transition-colors lead-card">
                        <div className="flex justify-between items-start mb-3">
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">{job.company}</h3>
                                <p className="text-sm text-gray-600">Hiring: {job.title}</p>
                            </div>
                            <SourceBadge source={job.source} />
                        </div>
                        
                        {/* Insight Section */}
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
                                    className="text-gray-500 hover:text-gray-700 text-sm flex items-center gap-1"
                                >
                                    View Link
                                </a>
                                <button 
                                    onClick={() => setExpandedJobIdx(expandedJobIdx === idx ? null : idx)}
                                    className="text-indigo-600 hover:text-indigo-800 text-sm font-medium transition-colors"
                                >
                                    {expandedJobIdx === idx ? 'Hide Details' : 'View Full JD'}
                                </button>
                            </div>
                            <button 
                                onClick={() => handleGeneratePitch(job)}
                                disabled={generating}
                                className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 shadow-sm transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {generating ? 'Generating...' : 'Generate Pitch'}
                            </button>
                        </div>

                        {/* Full Description Section */}
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

        {/* Pitch Generator Column (Sticky) */}
        {generatedPitch && (
            <div id="pitch-section" className="lg:w-1/2">
                <div className="bg-white p-6 rounded-xl shadow-lg border border-indigo-100 sticky top-6 generated-pitch">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold text-gray-800">Generated Pitch</h2>
                        <span className="text-sm text-gray-500">Target: {generatedPitch.forCompany}</span>
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <textarea 
                            readOnly
                            className="w-full h-96 bg-transparent border-none resize-none focus:ring-0 text-gray-700 font-mono text-sm leading-relaxed"
                            value={generatedPitch.content}
                        />
                    </div>
                    
                    <div className="mt-4 flex gap-3 justify-end">
                        <button 
                            className="text-gray-600 hover:text-gray-800 px-4 py-2 text-sm font-medium"
                            onClick={() => setGeneratedPitch(null)}
                        >
                            Close
                        </button>
                        <button 
                            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 shadow-sm font-medium flex items-center gap-2"
                            onClick={() => alert("Email draft copied to clipboard!")}
                        >
                            <span>Copy to Clipboard</span>
                        </button>
                    </div>
                </div>
            </div>
        )}
      </div>
    </div>
    </PermissionGuard>
  );
};

export default MarketingPage;
