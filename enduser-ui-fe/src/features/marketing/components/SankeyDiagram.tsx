import React, { useMemo } from 'react';

interface SankeyNode {
    name: string;
}

interface SankeyLink {
    source: number;
    target: number;
    value: number;
}

interface SankeyData {
    nodes: SankeyNode[];
    links: SankeyLink[];
}

interface SankeyDiagramProps {
    data: SankeyData;
}

export const SankeyDiagram: React.FC<SankeyDiagramProps> = ({ data }) => {
    // Simple 3-column layout logic (Industry -> Need -> Solution)
    // 1. Group nodes into columns based on connectivity
    // 2. Calculate y-positions based on node value flow
    
    // NOTE: This is a simplified "fake" sankey layout for visualization purposes
    // since utilizing d3-sankey fully in a raw component without d3-selection overhead is complex.
    // We assume the data structure comes in a way we can loosely categorize.
    // If not, we will rely on a simple visual assumption: 
    // Column 0: Source (Industries)
    // Column 1: Middle (Needs)
    // Column 2: Target (Archon Solution)
    
    // We determine columns by traversing links.
    // Indegree 0 -> Col 0
    // Indegree > 0 && Outdegree > 0 -> Col 1
    // Outdegree 0 -> Col 2
    
    const layout = useMemo(() => {
        if (!data || !data.nodes || !data.links) return { nodes: [], links: [] };

        const nodeMap = data.nodes.map((n, i) => ({ ...n, id: i, in: 0, out: 0, col: 0, x: 0, y: 0, height: 0, color: '' }));
        const links = data.links.map(l => ({ ...l }));

        // Calculate degrees
        links.forEach(l => {
            nodeMap[l.source].out += l.value;
            nodeMap[l.target].in += l.value;
        });

        // Assign columns
        nodeMap.forEach(n => {
            if (n.in === 0) n.col = 0; // Source
            else if (n.out === 0) n.col = 2; // Target
            else n.col = 1; // Middle
        });

        // Layout Parameters
        const width = 600;
        const height = 300;
        const colWidth = 20;
        const nodePadding = 20;

        // Calculate X
        nodeMap.forEach(n => {
            if (n.col === 0) n.x = 20;
            else if (n.col === 1) n.x = width / 2 - colWidth / 2;
            else n.x = width - 20 - colWidth;
        });
        
        // Calculate Y and Height per column
        [0, 1, 2].forEach(col => {
            const colNodes = nodeMap.filter(n => n.col === col);
            const totalValue = colNodes.reduce((sum, n) => sum + Math.max(n.in, n.out), 0);
            
            // Available height for drawing nodes (leaving space for padding)
            const availableHeight = height - (colNodes.length - 1) * nodePadding;
            const scale = availableHeight / (totalValue || 1); // Avoid div by zero
            
            let currentY = 0;
            colNodes.forEach(n => {
                const nodeVal = Math.max(n.in, n.out);
                n.height = Math.max(nodeVal * scale, 5); // Min height 5
                n.y = currentY;
                currentY += n.height + nodePadding;
                
                // Colors
                if (col === 0) n.color = '#818cf8'; // Indigo 400
                if (col === 1) n.color = '#f472b6'; // Pink 400
                if (col === 2) n.color = '#34d399'; // Emerald 400
            });
        });

        // Helper to get link coordinates
        const linkPaths = links.map((l, i) => {
            const source = nodeMap[l.source];
            const target = nodeMap[l.target];
            
            // Simple sigmoid path
            const sx = source.x + colWidth;
            // Distribute start Y along the source node height
            // We need to keep track of accumulated flow offsets. Simplified: Center it or stack it?
            // Stacking is complex without proper d3-sankey state.
            // Simplified: Draw from center to center with thickness relative to value
            
            const sy = source.y + source.height / 2;
            const tx = target.x;
            const ty = target.y + target.height / 2;
            
            const path = `M${sx},${sy} C${sx + 50},${sy} ${tx - 50},${ty} ${tx},${ty}`;
            
            return {
                 d: path,
                 strokeWidth: Math.max(l.value * 0.5, 1), // Scale width simply
                 color: source.color,
                 key: i
            };
        });

        return { nodes: nodeMap, links: linkPaths };

    }, [data]);

    return (
        <svg width="100%" height="300" viewBox="0 0 600 300" className="overflow-visible">
             <defs>
                <linearGradient id="gradientLink" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#818cf8" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#34d399" stopOpacity="0.4" />
                </linearGradient>
            </defs>
            
            {/* Links */}
            {layout.links.map(l => (
                <path 
                    key={l.key} 
                    d={l.d} 
                    stroke={l.color} 
                    strokeOpacity="0.3" 
                    fill="none" 
                    strokeWidth={l.strokeWidth} 
                    className="hover:stroke-opacity-60 transition-all duration-300"
                />
            ))}

            {/* Nodes */}
            {layout.nodes.map(n => (
                <g key={n.id}>
                    <rect 
                        x={n.x} 
                        y={n.y} 
                        width={20} 
                        height={n.height} 
                        fill={n.color} 
                        rx={4}
                        className="shadow-sm"
                    />
                    <text 
                        x={n.col === 0 ? n.x - 10 : (n.col === 2 ? n.x + 30 : n.x + 10)} 
                        y={n.y + n.height / 2} 
                        dy=".35em" 
                        textAnchor={n.col === 0 ? "end" : "start"}
                        className="text-[10px] font-bold fill-gray-600 pointer-events-none"
                    >
                        {n.name}
                    </text>
                </g>
            ))}
        </svg>
    );
};
