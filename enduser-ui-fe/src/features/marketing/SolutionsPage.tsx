import React, { useState } from 'react';
import SmartManufacturing from './SmartManufacturing.tsx';
import TechSpecs from './TechSpecs.tsx';
import LegacyViewer from './LegacyViewer.tsx';
import { LayoutGridIcon, ShieldCheckIcon, BarChartIcon, SettingsIcon } from '../../components/Icons.tsx';

type Tab = 'overview' | 'tech-specs' | 'architecture' | 'legacy-demo';

const SolutionsPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<Tab>('overview');

    const renderContent = () => {
        switch (activeTab) {
            case 'overview':
                return <SmartManufacturing />;
            case 'tech-specs':
                return <TechSpecs />;
            case 'architecture':
                return (
                    <LegacyViewer 
                        src="/ai/hightech/SAS in hightech manufacturing_ architecture diagram.html" 
                        title="Architecture Diagram" 
                    />
                );
            case 'legacy-demo':
                return (
                    <div className="space-y-8">
                         <LegacyViewer 
                            src="/ai/original_files/RPA_canvas.html" 
                            title="RPA Flow Demo" 
                        />
                    </div>
                );
            default:
                return <SmartManufacturing />;
        }
    };

    const navItems: { id: Tab; label: string; icon: React.ReactNode }[] = [
        { id: 'overview', label: 'Overview', icon: <LayoutGridIcon className="w-4 h-4" /> },
        { id: 'tech-specs', label: 'Tech Specs', icon: <ShieldCheckIcon className="w-4 h-4" /> },
        { id: 'architecture', label: 'Architecture', icon: <SettingsIcon className="w-4 h-4" /> },
        { id: 'legacy-demo', label: 'Live Demo', icon: <BarChartIcon className="w-4 h-4" /> },
    ];

    return (
        <div className="min-h-screen bg-secondary/30">
            {/* Header Banner */}
            <div className="bg-primary text-primary-foreground py-12">
                <div className="container mx-auto px-4">
                    <h1 className="text-4xl font-bold mb-4">Smart Manufacturing Solutions</h1>
                    <p className="text-xl opacity-90 max-w-2xl">
                        Comprehensive dashboard integrating RPA flows, SAS analytics, and employee well-being strategies.
                    </p>
                </div>
            </div>

            <div className="container mx-auto px-4 py-8 flex flex-col md:flex-row gap-8">
                {/* Left Navigation */}
                <aside className="w-full md:w-64 flex-shrink-0">
                    <nav className="bg-card rounded-lg shadow-sm border border-border overflow-hidden sticky top-20">
                        <div className="p-4 bg-secondary border-b border-border">
                            <h2 className="font-semibold">Contents</h2>
                        </div>
                        <ul className="divide-y divide-border">
                            {navItems.map((item) => (
                                <li key={item.id}>
                                    <button
                                        onClick={() => setActiveTab(item.id)}
                                        className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors hover:bg-secondary/50 ${
                                            activeTab === item.id 
                                                ? 'bg-secondary text-primary font-medium border-l-4 border-l-primary' 
                                                : 'text-muted-foreground border-l-4 border-l-transparent'
                                        }`}
                                    >
                                        {item.icon}
                                        {item.label}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </nav>
                </aside>

                {/* Main Content Area */}
                <main className="flex-1">
                    {renderContent()}
                </main>
            </div>
        </div>
    );
};

export default SolutionsPage;
