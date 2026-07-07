import sys
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (1024, 768), color=(30, 30, 35))
draw = ImageDraw.Draw(img)

try:
    font_large = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 36)
    font_med = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 24)
    font_small = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 16)
except:
    font_large = ImageFont.load_default()
    font_med = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Draw Tabs
tabs = ["Profile & Relics", "Deck Management", "Card Workshop", "Teammates"]
x_offset = 20
for i, tab in enumerate(tabs):
    w = 180
    bg = (60, 60, 70) if i == 3 else (40, 40, 45)
    draw.rectangle([x_offset, 10, x_offset + w, 50], fill=bg)
    draw.text((x_offset + 10, 20), tab, font=font_small, fill=(255,255,255))
    x_offset += w + 5

# Teammates Content
draw.text((350, 80), "隊員編制與戰術中樞", font=font_large, fill=(255,255,255))

# Left Box (Recruited Agents)
draw.text((50, 150), "已入隊特務 (Recruited Agents)", font=font_med, fill=(255,255,255))
# Glassmorphism box
draw.rectangle([50, 190, 400, 600], fill=(25, 38, 51), outline=(51, 102, 153), width=2)
# Agent inside
draw.rectangle([60, 200, 390, 240], fill=(50, 50, 60))
draw.text((70, 210), "bob - Lv.2.0", font=font_small, fill=(255,255,255))

# Right Box (Config)
draw.text((450, 150), "戰術設定 (Tactical Settings)", font=font_med, fill=(255,255,255))

# Model
draw.text((450, 210), "核心引擎 (Core Engine)", font=font_small, fill=(255,255,255))
draw.rectangle([450, 240, 650, 270], fill=(50, 50, 60))
draw.text((460, 245), "Local/Fallback Model v", font=font_small, fill=(255,255,255))
# Slot
draw.rectangle([660, 210, 800, 350], outline=(100,200,100), width=2)
draw.text((680, 270), "[EQUIP SLOT]", font=font_small, fill=(100,200,100))

# ReAct
draw.text((450, 380), "戰術覆寫 (Tactical Override - ReAct)", font=font_small, fill=(255,255,255))
draw.ellipse([670, 380, 710, 400], fill=(80,80,80)) # check toggle

# Budget
draw.text((450, 430), "行動體力 (Stamina / AP Budget): 500", font=font_small, fill=(255,255,255))
draw.rectangle([450, 460, 800, 470], fill=(60,60,60))
draw.ellipse([550, 455, 570, 475], fill=(200,200,200)) # slider knob

# Ingested
draw.text((450, 510), "知識同步率 (Knowledge Sync Rate)", font=font_small, fill=(255,255,255))

# Note: The NavHBox is technically still physically in the scene tree but hidden by the tab embed script in CharacterDashboard!
# But since the user might be looking at TeammateDashboard.tscn directly in the editor, they still see NavHBox!
# If the user opens TeammateDashboard.tscn directly, the hide() in CharacterDashboard.gd hasn't run.
draw.text((250, 680), "NavHBox is technically hidden at runtime by Hub, but exists in .tscn", font=font_small, fill=(255, 100, 100))

img.save('/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/teammates_gamified.png')
print("Image rendered")
