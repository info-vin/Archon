import os
from PIL import Image

def trim_hard_transparent(filepath):
    img = Image.open(filepath).convert("RGBA")
    data = img.load()
    width, height = img.size
    
    # Clean up semi-transparent pixels left by bad chroma key
    for y in range(height):
        for x in range(width):
            r, g, b, a = data[x, y]
            if a < 250: # Aggressive threshold
                data[x, y] = (0, 0, 0, 0)
                
    bbox = img.getbbox()
    if bbox:
        cropped = img.crop(bbox)
        cropped.save(filepath)
        print(f"Aggressively trimmed {filepath}: {img.size} -> {cropped.size}")
    else:
        print(f"Image {filepath} is completely transparent.")

directory = "archon-agency-tycoon/Assets/Rooms/isometric/"
for filename in os.listdir(directory):
    if filename.endswith(".png"):
        trim_hard_transparent(os.path.join(directory, filename))
