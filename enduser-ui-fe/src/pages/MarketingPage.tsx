import React from 'react';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { SearchIcon, TableIcon } from '../components/Icons';
import { useMarketingLogic } from '../features/marketing/hooks/useMarketingLogic';
import { MarketingJobSearch } from '../features/marketing/components/MarketingJobSearch';
import { MarketingLeadsStack } from '../features/marketing/components/MarketingLeadsStack';
import { VisitLogModal } from '../features/marketing/components/VisitLogModal';

const MarketingPage: React.FC = () => {
  const {
    activeTab, setActiveTab,
    keyword, setKeyword,
    jobs, loading, error, setError,
    generating, generatingStatus,
    searchProgress, expandedJobIdx, setExpandedJobIdx,
    generatedPitch, setGeneratedPitch,
    leads, isLeadsLoading,
    sortConfig, filterMode, setFilterMode,
    sortedLeads, requestSort,
    visitLogModalOpen, selectedLeadForLog, handleOpenVisitLog, handleCloseVisitLog,
    handleSearch, handleGeneratePitch, fetchLeads
  } = useMarketingLogic();

  return (
    <PermissionGuard 
      permission="leads:view:sales" 
      fallback={<div className="p-8 text-center text-gray-500">Access Denied: This feature is for Sales & Marketing roles only.</div>}
    >
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-8">
        <header className="flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-3">Sales Intelligence</h1>
            <p className="text-gray-500 mt-2 hidden md:block">Identify opportunities and manage your sales pipeline.</p>
          </div>
          
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

        {activeTab === 'search' ? (
          <MarketingJobSearch
            keyword={keyword}
            setKeyword={setKeyword}
            jobs={jobs}
            loading={loading}
            error={error}
            setError={setError}
            searchProgress={searchProgress}
            expandedJobIdx={expandedJobIdx}
            setExpandedJobIdx={setExpandedJobIdx}
            generating={generating}
            generatingStatus={generatingStatus}
            generatedPitch={generatedPitch}
            setGeneratedPitch={setGeneratedPitch}
            handleSearch={handleSearch}
            handleGeneratePitch={handleGeneratePitch}
          />
        ) : (
          <MarketingLeadsStack
            leads={leads}
            isLeadsLoading={isLeadsLoading}
            sortConfig={sortConfig}
            filterMode={filterMode}
            setFilterMode={setFilterMode}
            requestSort={requestSort}
            fetchLeads={fetchLeads}
            sortedLeads={sortedLeads}
            setActiveTab={setActiveTab}
            onOpenVisitLog={handleOpenVisitLog}
          />
        )}

        {visitLogModalOpen && selectedLeadForLog && (
          <VisitLogModal
            isOpen={visitLogModalOpen}
            onClose={handleCloseVisitLog}
            leadId={selectedLeadForLog.id}
            companyName={selectedLeadForLog.company_name}
          />
        )}
      </div>
    </PermissionGuard>
  );
};

export default MarketingPage;
