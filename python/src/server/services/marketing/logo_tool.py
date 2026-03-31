import hashlib
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
        colors = ["#BF7AF0", "#2ECC71", "#FF69B4", "#3498DB", "#F1C40F"]
        bg_color = "#0F0F0F"

        # Start SVG
        svg = (
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        )
        svg += f'<rect width="100%" height="100%" fill="{bg_color}"/>'

        # Generate 3-5 geometric shapes
        for _ in range(rng.randint(3, 6)):
            shape_type = rng.choice(["circle", "rect", "poly"])
            color = rng.choice(colors)
            opacity = rng.uniform(0.4, 0.8)

            if shape_type == "circle":
                cx, cy = rng.randint(0, width), rng.randint(0, height)
                r = rng.randint(50, 150)
                svg += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" fill-opacity="{opacity}" />'
            elif shape_type == "rect":
                x, y = rng.randint(0, width), rng.randint(0, height)
                w, h = rng.randint(100, 300), rng.randint(100, 300)
                svg += (
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="{opacity}" rx="10" />'
                )
            else:
                # Triangle/Polygon
                points = []
                for _ in range(3):
                    points.append(f"{rng.randint(0, width)},{rng.randint(0, height)}")
                svg += f'<polygon points="{" ".join(points)}" fill="{color}" fill-opacity="{opacity}" />'

        svg += "</svg>"
        return svg


def generate_logo_svg(seed: str) -> str:
    return LogoGenerator.generate_svg(seed)
