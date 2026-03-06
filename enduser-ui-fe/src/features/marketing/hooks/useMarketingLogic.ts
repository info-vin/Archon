import { useState, useEffect, useMemo, useCallback } from 'react';
import { api } from '../../../services/api';
import { JobData } from '../../../types';

export const useMarketingLogic = () => {
  const [activeTab, setActiveTab] = useState<'search' | 'leads'>('search');
  
  // Search State (Alice)
  const [keyword, setKeyword] = useState('Data Analyst');
  const [jobs, setJobs] = useState<JobData[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generatingStatus, setGeneratingStatus] = useState("");
  const [statusTimer, setStatusTimer] = useState<NodeJS.Timeout | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchProgress, setSearchProgress] = useState(0);
  const [expandedJobIdx, setExpandedJobIdx] = useState<number | null>(null);
  const [generatedPitch, setGeneratedPitch] = useState<{ job: JobData; content: string } | null>(null);

  // Leads State (Bob)
  const [leads, setLeads] = useState<any[]>([]);
  const [isLeadsLoading, setIsLeadsLoading] = useState(false);
  const [promoteModalOpen, setPromoteModalOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState<any>(null);
  const [viewPitchModalOpen, setViewPitchModalOpen] = useState(false);
  const [selectedPitchLead, setSelectedPitchLead] = useState<any>(null);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>({ key: 'created_at', direction: 'desc' });
  const [filterMode, setFilterMode] = useState<'all' | 'review_queue'>('all');

  // Hunter Mode State (Alice)
  const [visitLogModalOpen, setVisitLogModalOpen] = useState(false);
  const [selectedLeadForLog, setSelectedLeadForLog] = useState<any>(null);

  // Alice Methods
  const handleOpenVisitLog = (lead: any) => {
    setSelectedLeadForLog(lead);
    setVisitLogModalOpen(true);
  };

  const handleCloseVisitLog = () => {
    setVisitLogModalOpen(false);
    setSelectedLeadForLog(null);
    fetchLeads(); // Refresh to show new log markers if any
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!keyword.trim()) return;

    setLoading(true);
    setError(null);
    setGeneratedPitch(null);
    setSearchProgress(0);

    const progressInterval = setInterval(() => {
        setSearchProgress(prev => {
            if (prev >= 90) return prev;
            return prev + Math.floor(Math.random() * 10) + 5;
        });
    }, 1500);

    try {
      const results = await api.searchJobs(keyword);
      if (progressInterval) clearInterval(progressInterval);
      setSearchProgress(100);
      
      setTimeout(() => {
          setJobs(results);
          setLoading(false);
      }, 500);
    } catch (err: any) {
      if (progressInterval) clearInterval(progressInterval);
      console.error("🚨 Alice Search Error:", err);
      setError(err.message || "Failed to fetch job market data. Please try again.");
      setSearchProgress(0);
      setLoading(false);
    }
  };

  const handleGeneratePitch = async (job: JobData) => {
      setGenerating(true);
      setError(null);
      setGeneratingStatus("Analyzing job requirements...");
      
      const interval = setInterval(() => {
          setGeneratingStatus(prev => {
              if (prev.includes("Analyzing")) return "Consulting Archon RAG knowledge base...";
              if (prev.includes("Consulting")) return "Synthesizing personalized pitch with Pro model...";
              if (prev.includes("Synthesizing")) return "Finalizing polish, almost there...";
              return prev;
          });
      }, 15000);
      setStatusTimer(interval);

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

          setGeneratedPitch({ job, content: result.content });
          
          setTimeout(() => {
              document.getElementById('pitch-section')?.scrollIntoView({ behavior: 'smooth' });
          }, 100);
      } catch (err: any) {
          if (interval) clearInterval(interval);
          setStatusTimer(null);
          if (err.message === "TIMEOUT") {
              setError("Generation timed out. The AI model is taking too long.");
          } else {
              setError("Failed to generate pitch.");
          }
      } finally {
          setGenerating(false);
          setGeneratingStatus("");
      }
  };

  // Bob Methods
  const fetchLeads = useCallback(async () => {
      setIsLeadsLoading(true);
      try {
          const data = await api.getLeads();
          setLeads(data);
      } catch (err) {
          console.error("Failed to load leads", err);
      } finally {
          setIsLeadsLoading(false);
      }
  }, []);

  const sortedLeads = useMemo(() => {
    let sortableLeads = [...leads];
    if (filterMode === 'review_queue') {
        sortableLeads = sortableLeads.filter(l => l.status === 'new' || l.status === 'pending');
    }

    if (sortConfig !== null) {
      sortableLeads.sort((a, b) => {
        if (sortConfig.key === 'created_at' || sortConfig.key === 'next_followup_date') {
             const dateA = new Date(a[sortConfig.key] || 0).getTime();
             const dateB = new Date(b[sortConfig.key] || 0).getTime();
             return sortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA;
        }
        if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
        if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return sortableLeads;
  }, [leads, sortConfig, filterMode]);

  const requestSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  useEffect(() => {
      if (activeTab === 'leads') fetchLeads();
  }, [activeTab, fetchLeads]);

  useEffect(() => {
    return () => { if (statusTimer) clearInterval(statusTimer); };
  }, [statusTimer]);

  return {
    activeTab, setActiveTab,
    keyword, setKeyword,
    jobs, setJobs,
    loading, error, setError,
    generating, generatingStatus,
    searchProgress, expandedJobIdx, setExpandedJobIdx,
    generatedPitch, setGeneratedPitch,
    leads, isLeadsLoading,
    promoteModalOpen, setPromoteModalOpen,
    selectedLead, setSelectedLead,
    viewPitchModalOpen, setViewPitchModalOpen,
    selectedPitchLead, setSelectedPitchLead,
    sortConfig, filterMode, setFilterMode,
    sortedLeads, requestSort,
    visitLogModalOpen, selectedLeadForLog, handleOpenVisitLog, handleCloseVisitLog,
    handleSearch, handleGeneratePitch, fetchLeads
  };
};
