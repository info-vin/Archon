import React, { useState } from 'react';
import { api } from '../services/api';
import { JobData } from '../types';

const MarketingPage: React.FC = () => {
  const [keyword, setKeyword] = useState('Python');
  const [jobs, setJobs] = useState<JobData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;

    setLoading(true);
    setError(null);
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

  const generateJD = (job: JobData) => {
      // Placeholder for JD generation
      alert(`Generating JD based on ${job.title}...\n(Feature coming in Phase 4.3)`);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      <header>
        <h1 className="text-3xl font-bold text-gray-800">Market Intelligence</h1>
        <p className="text-gray-500 mt-2">Analyze job market trends to write better descriptions.</p>
      </header>

      {/* Search Section */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Enter job title (e.g., Python Engineer)"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Analyzing...' : 'Analyze Market'}
          </button>
        </form>
      </div>

      {/* Results Section */}
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-100">
          {error}
        </div>
      )}

      {jobs.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-700">Market Findings ({jobs.length})</h2>
          <div className="grid gap-4">
            {jobs.map((job, idx) => (
              <div key={idx} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{job.title}</h3>
                    <p className="text-gray-600">{job.company}</p>
                    <div className="flex gap-4 mt-2 text-sm text-gray-500">
                      <span>📍 {job.location || 'Unknown'}</span>
                      <span>💰 {job.salary || 'Negotiable'}</span>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${job.source === 'mock' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                    {job.source === 'mock' ? 'MOCK DATA' : 'LIVE 104'}
                  </span>
                </div>
                
                {job.skills && job.skills.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {job.skills.map((skill, sIdx) => (
                      <span key={sIdx} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
                
                <div className="mt-4 flex gap-3">
                  <a 
                    href={job.url || '#'}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline text-sm flex items-center"
                  >
                    View Original
                  </a>
                  <button 
                    onClick={() => generateJD(job)}
                    className="text-sm bg-gray-900 text-white px-3 py-1 rounded hover:bg-gray-800"
                  >
                    Draft JD
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketingPage;
