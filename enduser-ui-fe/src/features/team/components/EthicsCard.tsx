import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/services/api';
import { ShieldCheckIcon } from '@/components/Icons';

interface EthicsEvent {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  event_type: string;
  description: string;
  raw_input?: string;
  created_at: string;
}

export function EthicsCard() {
  const { user } = useAuth();
  const [events, setEvents] = useState<EthicsEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.role === 'manager' || user?.role === 'system_admin' || user?.role === 'admin') {
      fetchEvents();
    } else {
      setLoading(false);
    }
  }, [user]);

  const fetchEvents = async () => {
    try {
      const data = await api.getEthicsEvents();
      setEvents(data);
    } catch (error) {
      console.error('Failed to fetch ethics events:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!user || (user.role !== 'manager' && user.role !== 'system_admin' && user.role !== 'admin')) {
    return null;
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-red-50 text-red-600 border-red-100';
      case 'medium': return 'bg-orange-50 text-orange-600 border-orange-100';
      default: return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden col-span-full">
      <div className="p-4 border-b border-gray-100 bg-white flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <ShieldCheckIcon className="h-5 w-5 text-indigo-600" />
          <h3 className="text-base font-bold text-gray-900">Compliance & Ethics Logs (Sentinel)</h3>
        </div>
        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 border border-gray-200">
          {events.length} Events
        </span>
      </div>
      <div className="p-0">
        {loading ? (
             <div className="flex justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center text-gray-500 bg-gray-50/50">
             <ShieldCheckIcon className="h-8 w-8 text-green-500 mb-2" />
             <p className="text-sm font-medium">No compliance violations detected.</p>
             <p className="text-xs text-gray-400 mt-1">System is running within safety guardrails.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 uppercase bg-gray-50/80 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-3 font-medium">Time</th>
                  <th className="px-6 py-3 font-medium">Type</th>
                  <th className="px-6 py-3 font-medium">Severity</th>
                  <th className="px-6 py-3 font-medium">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {events.map((event) => (
                  <tr key={event.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-3 whitespace-nowrap text-gray-500 font-mono text-xs">
                      {new Date(event.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-3 font-medium text-gray-900">{event.event_type}</td>
                    <td className="px-6 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSeverityColor(event.severity)}`}>
                        {event.severity}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-gray-600 max-w-md truncate">
                      {event.description}
                      {event.raw_input && (
                        <div className="text-xs text-gray-400 font-mono mt-1 w-full truncate bg-gray-50 p-1 rounded border border-gray-100">
                          Input: {event.raw_input}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
