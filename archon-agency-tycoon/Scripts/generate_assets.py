import os

ASSETS_DIR = "../Assets"
ICONS_DIR = os.path.join(ASSETS_DIR, "Icons")
CHARS_DIR = os.path.join(ASSETS_DIR, "Characters")

os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(CHARS_DIR, exist_ok=True)

# 1. Icon: Coin (Funds)
coin_svg = """<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="32" r="28" fill="#F59E0B" stroke="#D97706" stroke-width="4"/>
  <text x="32" y="44" font-family="monospace" font-size="32" font-weight="bold" fill="#FFF" text-anchor="middle">$</text>
</svg>"""

# 2. Icon: Alert (Crisis)
alert_svg = """<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <polygon points="32,4 60,56 4,56" fill="#EF4444" stroke="#B91C1C" stroke-width="4" stroke-linejoin="round"/>
  <text x="32" y="46" font-family="sans-serif" font-size="32" font-weight="bold" fill="#FFF" text-anchor="middle">!</text>
</svg>"""

# 3. Icon: Star (Reputation)
star_svg = """<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <polygon points="32,2 41,20 62,23 47,38 50,58 32,50 14,58 17,38 2,23 23,20" fill="#3B82F6" stroke="#2563EB" stroke-width="4" stroke-linejoin="round"/>
</svg>"""

# Voxel-style Character Generator (SVG)
def generate_character_svg(primary_color, eye_color="#FFFFFF"):
    return f"""<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <!-- Body Base -->
  <rect x="16" y="24" width="32" height="40" fill="{primary_color}" rx="4"/>
  <!-- Head -->
  <rect x="12" y="4" width="40" height="32" fill="{primary_color}" rx="8"/>
  <!-- Visor / Eyes (Tech Style) -->
  <rect x="20" y="14" width="24" height="12" fill="#1F2937" rx="2"/>
  <rect x="24" y="16" width="6" height="8" fill="{eye_color}" rx="1"/>
  <rect x="34" y="16" width="6" height="8" fill="{eye_color}" rx="1"/>
</svg>"""

with open(os.path.join(ICONS_DIR, "icon_coin.svg"), "w") as f: file.write(coin_svg) if 'file' in locals() else f.write(coin_svg)
with open(os.path.join(ICONS_DIR, "icon_alert.svg"), "w") as f: f.write(alert_svg)
with open(os.path.join(ICONS_DIR, "icon_star.svg"), "w") as f: f.write(star_svg)

# Neon colors for roles
with open(os.path.join(CHARS_DIR, "char_dev.svg"), "w") as f: f.write(generate_character_svg("#10B981", "#A7F3D0")) # Emerald Green
with open(os.path.join(CHARS_DIR, "char_sales.svg"), "w") as f: f.write(generate_character_svg("#8B5CF6", "#BFDBFE")) # Blue
with open(os.path.join(CHARS_DIR, "char_qa.svg"), "w") as f: f.write(generate_character_svg("#F59E0B", "#FDE68A")) # Amber
with open(os.path.join(CHARS_DIR, "char_bot.svg"), "w") as f: f.write(generate_character_svg("#6B7280", "#EF4444")) # Gray with Red Eyes

print("Successfully generated placeholder SVG assets.")
