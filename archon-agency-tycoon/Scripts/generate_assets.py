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

# Cute Capsule-style Character Generator (SVG)
def generate_character_svg(primary_color, eye_color="#FFFFFF"):
    # A much cuter, rounded capsule shape (like Among Us or Fall Guys)
    return f"""<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <!-- Soft Drop Shadow -->
  <ellipse cx="32" cy="58" rx="16" ry="4" fill="#000000" opacity="0.3"/>
  
  <!-- Main Body (Capsule) -->
  <rect x="16" y="12" width="32" height="46" fill="{primary_color}" rx="16"/>
  
  <!-- Backpack (optional cute detail) -->
  <rect x="8" y="24" width="16" height="24" fill="{primary_color}" rx="6" opacity="0.8"/>
  
  <!-- Visor (Glass Panel) -->
  <rect x="22" y="20" width="22" height="14" fill="#93C5FD" rx="6" stroke="#1E3A8A" stroke-width="2"/>
  
  <!-- Visor Highlight (Shine) -->
  <rect x="34" y="22" width="6" height="4" fill="#EFF6FF" rx="2" opacity="0.8"/>
</svg>"""

# Neon office furniture SVG definitions
desk_svg = """<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="8" y="32" width="48" height="12" fill="#1E3A8A" stroke="#3B82F6" stroke-width="2" rx="2"/>
  <rect x="12" y="44" width="6" height="16" fill="#1D4ED8"/>
  <rect x="46" y="44" width="6" height="16" fill="#1D4ED8"/>
  <rect x="16" y="12" width="32" height="20" fill="#0F172A" stroke="#10B981" stroke-width="2" rx="2"/>
  <rect x="22" y="16" width="20" height="12" fill="#1E293B"/>
</svg>"""

server_svg = """<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="12" y="4" width="40" height="56" fill="#1E293B" stroke="#10B981" stroke-width="3" rx="4"/>
  <line x1="16" y1="14" x2="48" y2="14" stroke="#334155" stroke-width="2"/>
  <circle cx="22" cy="14" r="2" fill="#EF4444"/>
  <circle cx="30" cy="14" r="2" fill="#10B981"/>
  <circle cx="38" cy="14" r="2" fill="#F59E0B"/>
  <line x1="16" y1="26" x2="48" y2="26" stroke="#334155" stroke-width="2"/>
  <circle cx="22" cy="26" r="2" fill="#10B981"/>
  <circle cx="30" cy="26" r="2" fill="#10B981"/>
  <circle cx="38" cy="26" r="2" fill="#10B981"/>
  <line x1="16" y1="38" x2="48" y2="38" stroke="#334155" stroke-width="2"/>
  <circle cx="22" cy="38" r="2" fill="#F59E0B"/>
  <circle cx="30" cy="38" r="2" fill="#EF4444"/>
  <line x1="16" y1="50" x2="48" y2="50" stroke="#334155" stroke-width="2"/>
  <rect x="20" y="48" width="24" height="4" fill="#3B82F6"/>
</svg>"""

sofa_svg = """<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="8" y="24" width="48" height="28" fill="#581C87" stroke="#C084FC" stroke-width="2" rx="6"/>
  <rect x="4" y="28" width="8" height="20" fill="#4C1D95" rx="3"/>
  <rect x="52" y="28" width="8" height="20" fill="#4C1D95" rx="3"/>
  <rect x="12" y="36" width="40" height="12" fill="#6B21A8" rx="2"/>
</svg>"""

whiteboard_svg = """<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="8" width="44" height="36" fill="#1E293B" stroke="#F59E0B" stroke-width="3" rx="2"/>
  <rect x="14" y="12" width="36" height="28" fill="#F8FAFC"/>
  <rect x="18" y="16" width="12" height="4" fill="#EF4444" opacity="0.6"/>
  <rect x="18" y="24" width="20" height="2" fill="#3B82F6" opacity="0.6"/>
  <rect x="18" y="30" width="16" height="2" fill="#10B981" opacity="0.6"/>
  <line x1="8" y1="44" x2="8" y2="60" stroke="#475569" stroke-width="4"/>
  <line x1="56" y1="44" x2="56" y2="60" stroke="#475569" stroke-width="4"/>
  <line x1="4" y1="44" x2="60" y2="44" stroke="#475569" stroke-width="4"/>
</svg>"""

with open(os.path.join(ICONS_DIR, "icon_coin.svg"), "w") as f: f.write(coin_svg)
with open(os.path.join(ICONS_DIR, "icon_alert.svg"), "w") as f: f.write(alert_svg)
with open(os.path.join(ICONS_DIR, "icon_star.svg"), "w") as f: f.write(star_svg)

# Neon colors for roles
with open(os.path.join(CHARS_DIR, "char_dev.svg"), "w") as f: f.write(generate_character_svg("#10B981", "#A7F3D0")) # Emerald Green
with open(os.path.join(CHARS_DIR, "char_sales.svg"), "w") as f: f.write(generate_character_svg("#8B5CF6", "#BFDBFE")) # Blue
with open(os.path.join(CHARS_DIR, "char_qa.svg"), "w") as f: f.write(generate_character_svg("#F59E0B", "#FDE68A")) # Amber
with open(os.path.join(CHARS_DIR, "char_bot.svg"), "w") as f: f.write(generate_character_svg("#6B7280", "#EF4444")) # Gray with Red Eyes

# Furniture SVGs
with open(os.path.join(ICONS_DIR, "furn_desk.svg"), "w") as f: f.write(desk_svg)
with open(os.path.join(ICONS_DIR, "furn_server.svg"), "w") as f: f.write(server_svg)
with open(os.path.join(ICONS_DIR, "furn_sofa.svg"), "w") as f: f.write(sofa_svg)
with open(os.path.join(ICONS_DIR, "furn_whiteboard.svg"), "w") as f: f.write(whiteboard_svg)

print("Successfully generated placeholder SVG assets.")

