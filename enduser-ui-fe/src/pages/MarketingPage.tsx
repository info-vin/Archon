import React, { useState } from 'react';
import { api } from '../services/api';
import { JobData } from '../types';
import { useAuth } from '../hooks/useAuth';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';

const MarketingPage: React.FC = () => {
  const { user } = useAuth();
  const [keyword, setKeyword] = useState('Data Analyst');
  const [jobs, setJobs] = useState<JobData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // State for generated pitch modal/display
  const [generatedPitch, setGeneratedPitch] = useState<{ forCompany: string; content: string } | null>(null);

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

  const handleGeneratePitch = (job: JobData) => {
      // In a real app, this would call an LLM Agent endpoint.
      // Here we simulate the output based on our "Case 5" seed data.
      
      const pitchTemplate = `Subject: Collaboration Opportunity: Solving data challenges at ${job.company}

Dear Hiring Manager,

I noticed that ${job.company} is currently expanding its data team and looking for a ${job.title}. This suggests you might be tackling challenges related to data integration or analytics scaling.

At Archon, we specialize in helping companies like yours leverage data for tangible growth. For instance, we recently helped a major retail chain reduce inventory costs by 40% and increase revenue by 30% through our automated analytics platform.

You can read the full case study here: "零售巨頭如何利用數據分析提升 30% 營收" (Attached).

I would love to share more about how our "Sales Intelligence" module could support your new ${job.title} in hitting the ground running.

Best regards,
[Your Name]
Archon Sales Team`;

      setGeneratedPitch({
          forCompany: job.company,
          content: pitchTemplate
      });
      
      // Scroll to pitch section
      setTimeout(() => {
          if (typeof document !== 'undefined') {
            document.getElementById('pitch-section')?.scrollIntoView({ behavior: 'smooth' });
          }
      }, 100);
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
                            <span className={`px-2 py-1 rounded text-xs font-medium ${job.source === 'mock' ? 'bg-gray-100 text-gray-600' : 'bg-green-100 text-green-700'}`}>
                                {job.source === 'mock' ? 'MOCK SOURCE' : '104 DATA'}
                            </span>
                        </div>
                        
                        {/* Insight Section */}
                        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 mb-4 rounded-r insight">
                            <p className="text-xs font-bold text-yellow-800 uppercase tracking-wide">AI Insight</p>
                            <p className="text-sm text-yellow-900 mt-1">{job.identified_need || "Analyzing requirements..."}</p>
                        </div>
                        
                        <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
                            <a 
                                href={job.url || '#'}
                                target="_blank"
                                rel="noreferrer"
                                className="text-gray-500 hover:text-gray-700 text-sm flex items-center gap-1"
                            >
                                View Job
                            </a>
                            <button 
                                onClick={() => handleGeneratePitch(job)}
                                className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 shadow-sm transition-transform active:scale-95"
                            >
                                Generate Pitch
                            </button>
                        </div>
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
