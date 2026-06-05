import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

// Initialize mermaid config for dark mode / custom neon theme
mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    themeVariables: {
        background: '#0f172a', // slate-900
        primaryColor: '#0f172a',
        primaryTextColor: '#f8fafc',
        lineColor: '#f59e0b', // amber-500 neon
        arrowheadColor: '#f59e0b',
        textColor: '#cbd5e1',
        nodeBorder: '#f59e0b',
        actorBorder: '#f59e0b',
        actorBkg: '#1e293b', // slate-800
        signalColor: '#cbd5e1',
        signalTextColor: '#f8fafc',
    }
});

interface MermaidRendererProps {
    code: string;
}

export const MermaidRenderer: React.FC<MermaidRendererProps> = ({ code }) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [svg, setSvg] = useState<string>('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;
        const uniqueId = `mermaid-${Math.random().toString(36).substr(2, 9)}`;

        const renderChart = async () => {
            if (!code.trim()) return;
            try {
                setError(null);
                // Clean input code
                const cleanCode = code.trim();
                const { svg: renderedSvg } = await mermaid.render(uniqueId, cleanCode);
                if (isMounted) {
                    setSvg(renderedSvg);
                }
            } catch (err: any) {
                console.error('Mermaid parsing error:', err);
                if (isMounted) {
                    setError(err.message || 'Failed to parse Mermaid diagram');
                }
                // Reset internal mermaid error element if any
                const badElement = document.getElementById(uniqueId);
                if (badElement) {
                    badElement.remove();
                }
            }
        };

        renderChart();

        return () => {
            isMounted = false;
        };
    }, [code]);

    if (error) {
        return (
            <div className="my-6 p-4 rounded-xl border border-amber-500/20 bg-amber-500/5 text-amber-500 font-mono text-sm overflow-x-auto">
                <div className="font-bold mb-2">⚠️ Mermaid Render Fallback:</div>
                <pre className="text-xs opacity-90">{code}</pre>
            </div>
        );
    }

    return (
        <div 
            ref={containerRef} 
            className="my-8 p-6 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-md flex justify-center overflow-x-auto"
            dangerouslySetInnerHTML={{ __html: svg || '<span className="text-muted-foreground animate-pulse">Rendering diagram...</span>' }}
        />
    );
};
