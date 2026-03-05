import React from 'react';

interface StatusAlertsProps {
  shouldShowProviderAlert: boolean;
  providerAlertClassName: string;
  providerAlertMessage: string | null;
}

export const StatusAlerts: React.FC<StatusAlertsProps> = ({
  shouldShowProviderAlert,
  providerAlertClassName,
  providerAlertMessage
}) => {
  if (!shouldShowProviderAlert) return null;
  return (
    <div className={`p-4 border rounded-lg mb-4 ${providerAlertClassName}`}>
      <p className="text-sm">{providerAlertMessage}</p>
    </div>
  );
};
