import hashlib
import math
import random


class LogoGenerator:
    """
    Physical SVG Generator for project branding (Nana Banana Plugin).
    Generates geometric patterns without LLM calls to ensure zero-token cost.
    """

    @staticmethod
    def generate_svg(seed_text: str, width: int = 512, height: int = 512) -> str:
        # Create a deterministic random based on seed
        seed_hash = int(hashlib.md5(seed_text.encode()).hexdigest(), 16)
        rng = random.Random(seed_hash)

        # Color palette (Tron/Cyberpunk theme as per Style Guide)
        colors = ["#00f0ff", "#ff007f", "#7000ff", "#39ff14", "#ffb703"]
        bg_color = "#0b0c10"

        # Start SVG
        svg = (
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        )

        # Glow filter and gradient definitions
        svg += (
            "<defs>"
            '<filter id="neon-glow" x="-50%" y="-50%" width="200%" height="200%">'
            '<feGaussianBlur stdDeviation="8" result="coloredBlur"/>'
            "<feMerge>"
            '<feMergeNode in="coloredBlur"/>'
            '<feMergeNode in="SourceGraphic"/>'
            "</feMerge>"
            "</filter>"
            '<linearGradient id="cyber-grad" x1="0%" y1="0%" x2="100%" y2="100%">'
            '<stop offset="0%" stop-color="#00f0ff" stop-opacity="0.8" />'
            '<stop offset="100%" stop-color="#7000ff" stop-opacity="0.2" />'
            "</linearGradient>"
            "</defs>"
        )

        svg += f'<rect width="100%" height="100%" fill="{bg_color}"/>'

        # Cyberpunk Tech Grid Lines
        for i in range(20, width, 40):
            svg += f'<line x1="{i}" y1="0" x2="{i}" y2="{height}" stroke="#1f2833" stroke-width="0.5" stroke-dasharray="2, 8" />'
        for j in range(20, height, 40):
            svg += f'<line x1="0" y1="{j}" x2="{width}" y2="{j}" stroke="#1f2833" stroke-width="0.5" stroke-dasharray="2, 8" />'

        # Concentric Center Circles
        cx_center, cy_center = width // 2, height // 2
        svg += f'<circle cx="{cx_center}" cy="{cy_center}" r="180" stroke="#1f2833" stroke-width="1.5" fill="none" />'
        svg += f'<circle cx="{cx_center}" cy="{cy_center}" r="120" stroke="#1f2833" stroke-width="1" stroke-dasharray="5, 15" fill="none" />'

        # Generate 5-9 geometric shapes for richer aesthetics
        for _ in range(rng.randint(5, 10)):
            shape_type = rng.choice(["circle", "rect", "poly", "ring", "hexagon", "crosshair"])
            color = rng.choice(colors)
            opacity = rng.uniform(0.3, 0.7)

            # 40% chance of glow effect
            glow = ' filter="url(#neon-glow)"' if rng.random() < 0.4 else ""

            if shape_type == "circle":
                cx, cy = rng.randint(50, width - 50), rng.randint(50, height - 50)
                r = rng.randint(20, 100)
                svg += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" fill-opacity="{opacity}" stroke="{color}" stroke-dasharray="10, 5" stroke-opacity="0.5"{glow} />'
            elif shape_type == "rect":
                x, y = rng.randint(50, width - 150), rng.randint(50, height - 150)
                w, h = rng.randint(40, 180), rng.randint(40, 180)
                fill_color = "url(#cyber-grad)" if rng.random() < 0.3 else color
                svg += (
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill_color}" fill-opacity="{opacity}" rx="8" stroke="{color}" stroke-opacity="0.6"{glow} />'
                )
            elif shape_type == "ring":
                cx, cy = rng.randint(50, width - 50), rng.randint(50, height - 50)
                r = rng.randint(30, 90)
                svg += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="3" stroke-opacity="{opacity}" stroke-dasharray="4, 12"{glow} />'
            elif shape_type == "hexagon":
                cx, cy = rng.randint(50, width - 50), rng.randint(50, height - 50)
                r = rng.randint(30, 100)
                points = []
                for i in range(6):
                    angle_deg = 60 * i
                    angle_rad = math.radians(angle_deg)
                    px = cx + r * math.cos(angle_rad)
                    py = cy + r * math.sin(angle_rad)
                    points.append(f"{px:.1f},{py:.1f}")
                svg += f'<polygon points="{" ".join(points)}" fill="{color}" fill-opacity="{opacity}" stroke="{color}" stroke-opacity="0.8"{glow} />'
            elif shape_type == "crosshair":
                cx, cy = rng.randint(55, width - 55), rng.randint(55, height - 55)
                r = rng.randint(15, 40)
                svg += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="1.5" stroke-opacity="{opacity}" />'
                svg += f'<line x1="{cx - r - 10}" y1="{cy}" x2="{cx + r + 10}" y2="{cy}" stroke="{color}" stroke-width="1.5" stroke-opacity="{opacity}"{glow} />'
                svg += f'<line x1="{cx}" y1="{cy - r - 10}" x2="{cx}" y2="{cy + r + 10}" stroke="{color}" stroke-width="1.5" stroke-opacity="{opacity}"{glow} />'
            else:
                # Triangle/Polygon
                points = []
                for _ in range(3):
                    points.append(f"{rng.randint(50, width - 50)},{rng.randint(50, height - 50)}")
                svg += f'<polygon points="{" ".join(points)}" fill="{color}" fill-opacity="{opacity}" stroke="{color}" stroke-opacity="0.8"{glow} />'

        svg += "</svg>"
        return svg


def generate_logo_svg(seed: str) -> str:
    return LogoGenerator.generate_svg(seed)

