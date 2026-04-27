import React from 'react';
import { useAdminPageLogic } from '../features/admin/hooks/useAdminPageLogic';
import { IdentityMatrix } from '../features/admin/components/IdentityMatrix.tsx';
import { SystemHealthDashboard } from '../features/admin/components/SystemHealthDashboard.tsx';
import { PromptManagement } from '../features/admin/components/PromptManagement.tsx';
import { AdminSystemConfig } from '../features/admin/components/AdminSystemConfig';
import { AdminExtractionConfig } from '../features/admin/components/AdminExtractionConfig';
import { AdminCrawlerConfig } from '../features/admin/components/AdminCrawlerConfig';
import { AdminAuditLogs } from '../features/admin/components/AdminAuditLogs';
import { AdminContentManager } from '../features/admin/components/AdminContentManager';

const AdminPage: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    isOnlyManager,
    canManageUsers
  } = useAdminPageLogic();

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 bg-background text-foreground font-sans">
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-3">
          {isOnlyManager ? 'Manager Control Center' : 'Admin Control Center'}
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          {isOnlyManager 
            ? 'Configure team permissions, workflows, and operational parameters.'
            : 'System-wide configuration and personnel management for L1 Administrators.'}
        </p>
      </header>

      <div className="border-b border-border mb-6">
        <nav className="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
          <TabButton title="System Prompts" isActive={activeTab === 'prompts'} onClick={() => setActiveTab('prompts')} />
          <TabButton title="System Health" isActive={activeTab === 'health'} onClick={() => setActiveTab('health')} />
          {canManageUsers && <TabButton title="User Management" isActive={activeTab === 'users'} onClick={() => setActiveTab('users')} />}
          <TabButton title="Cost & Usage" isActive={activeTab === 'costs'} onClick={() => setActiveTab('costs')} />
          <TabButton title="System Settings" isActive={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
          <TabButton title="Data Extraction" isActive={activeTab === 'extraction'} onClick={() => setActiveTab('extraction')} />
          {!isOnlyManager && <TabButton title="Blog Management" isActive={activeTab === 'blog'} onClick={() => setActiveTab('blog')} />}
          {!isOnlyManager && <TabButton title="Document Versions" isActive={activeTab === 'versions'} onClick={() => setActiveTab('versions')} />}
        </nav>
      </div>

      <div className="flex-1 overflow-auto">
        {activeTab === 'health' && <SystemHealthDashboard />}
        {activeTab === 'users' && canManageUsers && <IdentityMatrix />}
        {activeTab === 'costs' && (
          <div className="space-y-6">
             {/* Reuse the dashboard data or separate component. 
                 For now, we point back to SystemHealthDashboard but we will split its logic later to prevent卡死 */}
             <SystemHealthDashboard />
          </div>
        )}
        {activeTab === 'settings' && <AdminSystemConfig />}
        {activeTab === 'extraction' && (
          <div className="space-y-8">
            <AdminCrawlerConfig />
            <AdminExtractionConfig />
          </div>
        )}
        {activeTab === 'prompts' && <PromptManagement isManagerMode={isOnlyManager} />}
        {activeTab === 'blog' && !isOnlyManager && <AdminContentManager />}
        {activeTab === 'versions' && !isOnlyManager && <AdminAuditLogs />}
      </div>
    </div>
  );
};

const TabButton: React.FC<{ title: string; isActive: boolean; onClick: () => void }> = ({ title, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={`${
      isActive
        ? 'border-indigo-500 text-indigo-500'
        : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
    } whitespace-nowrap py-4 px-1 border-b-2 font-bold text-sm transition-all`}
  >
    {title}
  </button>
);

export default AdminPage;
