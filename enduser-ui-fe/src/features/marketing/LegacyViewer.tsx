import React from 'react';
import { ExternalLinkIcon } from '../../components/Icons.tsx';

interface LegacyViewerProps {
    src: string;
    title: string;
    height?: string;
}

const LegacyViewer: React.FC<LegacyViewerProps> = ({ src, title, height = "800px" }) => {
    return (
        <div className="w-full bg-white rounded-lg shadow-sm border border-border overflow-hidden">
            <div className="bg-secondary p-4 border-b border-border flex justify-between items-center">
                <h3 className="font-semibold text-foreground">{title}</h3>
                <div className="flex items-center space-x-2">
                    <a 
                        href={src} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center text-xs text-primary hover:underline"
                    >
                        <ExternalLinkIcon className="w-3 h-3 mr-1" />
                        Open in New Tab
                    </a>
                    <span className="text-xs text-muted-foreground bg-secondary-foreground/10 px-2 py-1 rounded">
                        Legacy Content
                    </span>
                </div>
            </div>
            <iframe 
                src={src} 
                title={title}
                className="w-full border-0"
                style={{ height: height }}
                loading="lazy"
            />
        </div>
    );
};

export default LegacyViewer;
