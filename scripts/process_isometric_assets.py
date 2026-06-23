import os
import sys
from PIL import Image

# Define paths
SOURCE_DIR = "../PRPs"
OUTPUT_DIR = "../archon-agency-tycoon/Assets/Rooms/isometric"

# Define chroma key color (Magenta #FF00FF) and tolerance
CHROMA_COLOR = (255, 0, 255)
TOLERANCE = 80 # Adjust based on AI generation artifacts (bloom/anti-aliasing)

TARGET_SIZE = 128 # Target size for each isometric cell

def remove_background(img):
    img = img.convert("RGBA")
    data = img.getdata()
    
    new_data = []
    for item in data:
        # Check if color is close to Magenta #FF00FF
        if item[0] >= 255 - TOLERANCE and item[1] <= TOLERANCE and item[2] >= 255 - TOLERANCE:
            new_data.append((255, 255, 255, 0)) # Transparent
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    return img

def process_spritesheet(file_path, output_prefix):
    print(f"Processing spritesheet: {file_path}")
    img = Image.open(file_path)
    img = remove_background(img)
    
    width, height = img.size
    cell_w = width // 2
    cell_h = height // 2
    
    # AI failed to rotate the object and just generated 4 variations of the same angle.
    # We will only extract the Top-Left cell and use it as the definitive SW (South-West) asset.
    # In Godot, we will use `flip_h = true` to get the SE (South-East) direction!
    x, y = 0, 0
    box = (x, y, x + cell_w, y + cell_h)
    cell = img.crop(box)
    
    # Crop tight bounding box around visible pixels
    bbox = cell.getbbox()
    if bbox:
        cell = cell.crop(bbox)
    
    # Resize using NEAREST to preserve pixel art look
    cell.thumbnail((TARGET_SIZE, TARGET_SIZE), Image.Resampling.NEAREST)
    
    out_path = os.path.join(OUTPUT_DIR, f"{output_prefix}_SW.png")
    cell.save(out_path, "PNG")
    print(f"  -> Saved {out_path}")

def process_single_tile(file_path, output_name):
    print(f"Processing single tile: {file_path}")
    img = Image.open(file_path)
    img = remove_background(img)
    
    # Crop tight bounding box
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        
    # Resize using NEAREST
    img.thumbnail((TARGET_SIZE*2, TARGET_SIZE), Image.Resampling.NEAREST)
    
    out_path = os.path.join(OUTPUT_DIR, f"{output_name}.png")
    img.save(out_path, "PNG")
    print(f"  -> Saved {out_path}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Process Spritesheets
    spritesheets = [
        ("isometric_desk_spritesheet.jpg", "desk"),
        ("isometric_server_spritesheet.jpg", "server_rack"),
        ("isometric_sofa_spritesheet.jpg", "sofa"),
        ("isometric_wall_spritesheet.jpg", "wall_corner"),
        ("isometric_chair_spritesheet.jpg", "chair")
    ]
    
    for filename, prefix in spritesheets:
        path = os.path.join(SOURCE_DIR, filename)
        if os.path.exists(path):
            process_spritesheet(path, prefix)
        else:
            print(f"Warning: {path} not found.")
            
    # Process Single Tile
    tile_path = os.path.join(SOURCE_DIR, "isometric_floor_tile_chroma.jpg")
    if os.path.exists(tile_path):
        process_single_tile(tile_path, "floor_tile")
    else:
        print(f"Warning: {tile_path} not found.")

if __name__ == "__main__":
    main()
