import React from 'react';

export const NexusFooter: React.FC = () => {
    return (
        <footer className="mt-12 pt-8 border-t border-gray-200 text-xs text-gray-400 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
                <h5 className="font-bold text-gray-500 uppercase tracking-widest mb-2">Metrics Definition</h5>
                <ul className="space-y-1">
                    <li>• <strong className="text-gray-600">Reliability:</strong> 6-month strategic SLA attainment (Bi-weekly).</li>
                    <li>• <strong className="text-gray-600">ROI:</strong> 60-day intelligence yield (Pages Saved / URLs Scanned).</li>
                </ul>
            </div>
            <div>
                 <h5 className="font-bold text-gray-500 uppercase tracking-widest mb-2">Color Codes</h5>
                 <ul className="space-y-1">
                    <li className="flex items-center gap-2"><div className="w-2 h-2 bg-green-500 rounded-full"></div> Optimal Range</li>
                    <li className="flex items-center gap-2"><div className="w-2 h-2 bg-amber-500 rounded-full"></div> Warning / Action Needed</li>
                    <li className="flex items-center gap-2"><div className="w-2 h-2 bg-red-500 rounded-full"></div> Critical Exception</li>
                 </ul>
            </div>
            <div>
                <h5 className="font-bold text-gray-500 uppercase tracking-widest mb-2">System Info</h5>
                <p>ManagerNexus v7.1 | Build 2026.02.12</p>
                <p className="mt-1">© Archon Intelligence Systems</p>
            </div>
        </footer>
    );
};
