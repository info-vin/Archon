import React from 'react';
import { useAuth } from '../../hooks/useAuth.tsx';
import { SolutionItem } from './solutionsConfig';
import LegacyViewer from './LegacyViewer.tsx';
import { ShieldCheckIcon } from '../../components/Icons.tsx';
import { useNavigate } from 'react-router-dom';

interface ContentRendererProps {
    item: SolutionItem;
}

const ContentRenderer: React.FC<ContentRendererProps> = ({ item }) => {
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    // 1. Permission Check
    if (item.protected && !isAuthenticated) {
        return (
            <div className="flex flex-col items-center justify-center h-[600px] bg-white rounded-lg border border-border shadow-sm p-8 text-center">
                <div className="bg-secondary/50 p-6 rounded-full mb-6">
                    <ShieldCheckIcon className="w-16 h-16 text-muted-foreground" />
                </div>
                <h2 className="text-2xl font-bold text-foreground mb-4">Protected Content</h2>
                <p className="text-muted-foreground max-w-md mb-8">
                    This report contains sensitive internal data and is available only to authorized team members.
                    Please log in to view the full details.
                </p>
                <button
                    onClick={() => navigate('/auth')}
                    className="px-6 py-3 bg-primary text-primary-foreground rounded-md font-semibold hover:bg-primary/90 transition-colors"
                >
                    Log In to Access
                </button>
            </div>
        );
    }

    // 2. Render Component
    if (item.type === 'component' && item.component) {
        const Component = item.component;
        return <Component />;
    }

    // 3. Render Legacy Content
    if (item.type === 'legacy' && item.src) {
        return <LegacyViewer src={item.src} title={item.label} />;
    }

    return <div>Content not found</div>;
};

export default ContentRenderer;
