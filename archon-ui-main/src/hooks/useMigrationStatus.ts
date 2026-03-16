import { useState, useEffect } from 'react';
import { callAPIWithETag } from '../features/shared/api/apiClient';

interface MigrationStatus {
  migrationRequired: boolean;
  message?: string;
  loading: boolean;
}

export const useMigrationStatus = (): MigrationStatus => {
  const [status, setStatus] = useState<MigrationStatus>({
    migrationRequired: false,
    loading: true,
  });

  useEffect(() => {
    const checkMigrationStatus = async (): Promise<void> => {
      try {
        const healthData = await callAPIWithETag<any>('/health');
        
        if (healthData.status === 'migration_required') {
          setStatus({
            migrationRequired: true,
            message: healthData.message,
            loading: false,
          });
        } else {
          setStatus({
            migrationRequired: false,
            loading: false,
          });
        }
      } catch (error) {
        console.error('Failed to check migration status:', error);
        setStatus({
          migrationRequired: false,
          loading: false,
        });
      }
    };

    checkMigrationStatus();
    
    // Check periodically (every 30 seconds) to detect when migration is complete
    const interval = setInterval(checkMigrationStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return status;
};