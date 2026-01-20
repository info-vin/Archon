from pydantic import BaseModel, Field


class GenerateBrandAssetTool(BaseModel):
    """
    Generates a brand asset (logo) programmatically based on geometric rules.
    This simulates a "Design Agent" that can create vector graphics.
    """
    style: str = Field("eciton", description="The visual style (e.g., 'eciton', 'minimal').")
    format: str = Field("svg", description="Output format (currently only 'svg' supported).")

    async def execute(self) -> str:
        if self.style == "eciton":
            return self._generate_eciton_svg()
        else:
            return self._generate_fallback_svg()

    def _generate_eciton_svg(self) -> str:
        """
        Generates the 'Project ECITON' logo:
        A geometric ant head formed by connected data nodes (hexagonal lattice).
        Colors: Cyan (#00f2ff) to Purple (#a855f7).
        Animation: Nodes pulse to symbolize 'living data'.
        """
        width = 200
        height = 200

        # Define key nodes for an abstract ant head
        # (x, y, radius)
        nodes = [
            (100, 100, 12), # Center Brain
            (70, 70, 8),    # Left Eye
            (130, 70, 8),   # Right Eye
            (60, 130, 6),   # Left Mandible Base
            (140, 130, 6),  # Right Mandible Base
            (80, 160, 4),   # Left Mandible Tip
            (120, 160, 4),  # Right Mandible Tip
            (100, 40, 6),   # Top Antenna Base
        ]

        # Define connections (indices of nodes)
        links = [
            (0, 1), (0, 2), (0, 3), (0, 4), (0, 7),
            (1, 7), (2, 7),
            (3, 5), (4, 6),
            (1, 3), (2, 4)
        ]

        svg_content = f'''
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#00f2ff;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#a855f7;stop-opacity:1" />
                </linearGradient>
                <filter id="glow">
                    <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                    <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>

            <g filter="url(#glow)">
        '''

        # Draw Links
        for start, end in links:
            x1, y1, _ = nodes[start]
            x2, y2, _ = nodes[end]
            svg_content += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="url(#grad1)" stroke-width="2" opacity="0.6" />\n'

        # Draw Nodes with Pulse Animation
        for i, (cx, cy, r) in enumerate(nodes):
            # Vary animation timing for organic feel
            duration = 2 + (i % 3) * 0.5
            svg_content += f'''
            <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#grad1)">
                <animate attributeName="r" values="{r};{r+2};{r}" dur="{duration}s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.8;1;0.8" dur="{duration}s" repeatCount="indefinite" />
            </circle>
            '''

        svg_content += '''
            </g>
        </svg>
        '''

        return svg_content.strip()

    def _generate_fallback_svg(self) -> str:
        return '<svg width="100" height="100"><circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red" /></svg>'
