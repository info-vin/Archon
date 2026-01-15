import React, { useState, useEffect } from 'react';
import ContentRenderer from './ContentRenderer.tsx';
import { solutionsCategories, SolutionItem } from './solutionsConfig';

const SolutionsPage: React.FC = () => {
    // Default to the first item of the first category
    const defaultItem = solutionsCategories[0].items[0];
    const [activeItemId, setActiveItemId] = useState<string>(defaultItem.id);

    // Scroll to top when active item changes
    useEffect(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, [activeItemId]);

    // Helper to find the active item object
    const getActiveItem = (): SolutionItem | undefined => {
        for (const category of solutionsCategories) {
            const found = category.items.find(item => item.id === activeItemId);
            if (found) return found;
        }
        return undefined;
    };

    const activeItem = getActiveItem() || defaultItem;

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
                <aside className="w-full md:w-72 flex-shrink-0">
                    <nav className="bg-card rounded-lg shadow-sm border border-border overflow-hidden sticky top-20">
                        {solutionsCategories.map((category) => (
                            <div key={category.title} className="border-b border-border last:border-b-0">
                                <div className="px-4 py-3 bg-secondary/50 font-semibold text-xs text-muted-foreground uppercase tracking-wider">
                                    {category.title}
                                </div>
                                <ul>
                                    {category.items.map((item) => (
                                        <li key={item.id}>
                                            <button
                                                onClick={() => setActiveItemId(item.id)}
                                                className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors text-left ${
                                                    activeItemId === item.id 
                                                        ? 'bg-secondary text-primary font-medium border-l-4 border-l-primary' 
                                                        : 'text-muted-foreground border-l-4 border-l-transparent hover:bg-secondary/30'
                                                }`}
                                            >
                                                <span className={`${activeItemId === item.id ? 'text-primary' : 'text-muted-foreground/70'}`}>
                                                    {item.icon}
                                                </span>
                                                {item.label}
                                                {item.protected && (
                                                    <span className="ml-auto text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded border border-amber-200">
                                                        LOCK
                                                    </span>
                                                )}
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </nav>
                </aside>

                {/* Main Content Area */}
                <main className="flex-1 min-w-0">
                    <ContentRenderer item={activeItem} />
                </main>
            </div>
        </div>
    );
};

export default SolutionsPage;