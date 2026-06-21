#!/usr/bin/env python3
import os
import sys
import argparse
from PIL import Image

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def remove_chroma_key(img, chroma_color=(255, 0, 255), tolerance=60):
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    r_ch, g_ch, b_ch = chroma_color
    for item in data:
        r, g, b, a = item
        # Euclidean distance in RGB space
        dist = ((r - r_ch)**2 + (g - g_ch)**2 + (b - b_ch)**2)**0.5
        if dist < tolerance:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img

def slice_sheet(img, cols, rows, target_count):
    width, height = img.size
    cell_w = width // cols
    cell_h = height // rows
    frames = []
    for r in range(rows):
        for c in range(cols):
            if len(frames) >= target_count:
                break
            box = (c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h)
            frames.append(img.crop(box))
    return frames

def align_foot(cell_img, target_y=30):
    width, height = cell_img.size
    pixels = cell_img.load()
    bottom_y = -1
    for y in range(height - 1, -1, -1):
        for x in range(width):
            if pixels[x, y][3] > 10:  # alpha threshold
                bottom_y = y
                break
        if bottom_y != -1:
            break
            
    if bottom_y == -1:
        return cell_img
        
    dy = target_y - bottom_y
    if dy == 0:
        return cell_img
        
    new_cell = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    new_cell.paste(cell_img, (0, dy))
    return new_cell

def make_dummy_frames(count, color, label=""):
    frames = []
    for i in range(count):
        # Create a 32x32 cell
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        # Draw a placeholder box representing a character
        pixels = img.load()
        # Draw feet at Y=30
        for x in range(12, 20):
            pixels[x, 30] = color
        # Draw body
        for y in range(16, 30):
            for x in range(10, 22):
                pixels[x, y] = color
        # Draw head
        for y in range(8, 16):
            for x in range(12, 20):
                pixels[x, y] = (color[0]//2, color[1]//2, color[2]//2, 255)
        frames.append(img)
    return frames

def main():
    parser = argparse.ArgumentParser(description="AI Spritesheet Normalizer and Baker")
    parser.add_argument("--role", type=str, default="Neon-Hacker", help="Name or role of the character")
    parser.add_argument("--slot1", type=str, default="", help="Step 1 Box Art path")
    parser.add_argument("--slot2", type=str, default="", help="Step 2 South Anchor path")
    parser.add_argument("--slot3", type=str, default="", help="Step 3 Neutral Reset path")
    parser.add_argument("--slot4", type=str, default="", help="Step 4 Directions path")
    parser.add_argument("--slot5", type=str, default="", help="Step 5 Walk Cycle path")
    parser.add_argument("--slot6", type=str, default="", help="Step 6 Attack/Work Sheet path")
    parser.add_argument("--slot7", type=str, default="", help="Step 7 Idle Sheet path")
    parser.add_argument("--output", type=str, default="", help="Output spritesheet path")
    parser.add_argument("--chroma", type=str, default="#FF00FF", help="Chroma color hex")
    
    args = parser.parse_args()
    
    print(f"Baking spritesheet for {args.role}...")
    
    chroma_color = hex_to_rgb(args.chroma)
    
    # 1. Output folder setup
    if args.output:
        out_dir = os.path.dirname(args.output)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
            
    # Process avatar (Slot 1) if provided
    if args.slot1 and os.path.exists(args.slot1) and args.output:
        avatar_path = os.path.join(os.path.dirname(args.output), "portrait.png")
        try:
            with Image.open(args.slot1) as av_img:
                av_img.save(avatar_path)
                print(f"Saved portrait to {avatar_path}")
        except Exception as e:
            print(f"Warning: Failed to save portrait: {e}")

    # 2. Slice/Prepare Idle (10 frames, Slot 7)
    idle_frames = []
    if args.slot7 and os.path.exists(args.slot7):
        try:
            with Image.open(args.slot7) as img:
                img_clean = remove_chroma_key(img, chroma_color)
                sliced = slice_sheet(img_clean, 5, 2, 10)
                idle_frames = [align_foot(f.resize((32, 32), Image.Resampling.LANCZOS)) for f in sliced]
                print(f"Successfully sliced 10 Idle frames from {args.slot7}")
        except Exception as e:
            print(f"Error processing Slot 7: {e}")
            
    if not idle_frames:
        print("Using dummy frames for Idle")
        idle_frames = make_dummy_frames(10, (0, 255, 255, 255)) # Cyan for Idle

    # 3. Slice/Prepare Walk (6 frames, Slot 5)
    walk_frames = []
    if args.slot5 and os.path.exists(args.slot5):
        try:
            with Image.open(args.slot5) as img:
                img_clean = remove_chroma_key(img, chroma_color)
                # Check aspect ratio to determine dimensions (could be 6x1 horizontal strip)
                w, h = img.size
                cols = 6 if w >= h * 4 else 1
                rows = 1 if cols == 6 else 6
                sliced = slice_sheet(img_clean, cols, rows, 6)
                walk_frames = [align_foot(f.resize((32, 32), Image.Resampling.LANCZOS)) for f in sliced]
                print(f"Successfully sliced 6 Walk frames from {args.slot5}")
        except Exception as e:
            print(f"Error processing Slot 5: {e}")
            
    if not walk_frames:
        print("Using dummy frames for Walk")
        walk_frames = make_dummy_frames(6, (255, 255, 0, 255)) # Yellow for Walk

    # 4. Slice/Prepare Work (10 frames, Slot 6)
    work_frames = []
    if args.slot6 and os.path.exists(args.slot6):
        try:
            with Image.open(args.slot6) as img:
                img_clean = remove_chroma_key(img, chroma_color)
                sliced = slice_sheet(img_clean, 5, 2, 10)
                work_frames = [align_foot(f.resize((32, 32), Image.Resampling.LANCZOS)) for f in sliced]
                print(f"Successfully sliced 10 Work frames from {args.slot6}")
        except Exception as e:
            print(f"Error processing Slot 6: {e}")
            
    if not work_frames:
        print("Using dummy frames for Work")
        work_frames = make_dummy_frames(10, (255, 0, 255, 255)) # Magenta for Work

    # 5. Pack into horizontal spritesheet (26 cells of 32x32 = 832x32 size)
    total_frames = idle_frames + walk_frames + work_frames
    sheet_width = 32 * len(total_frames)
    sheet_height = 32
    
    sheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))
    for idx, frame in enumerate(total_frames):
        sheet.paste(frame, (idx * 32, 0))
        
    # 6. Save output
    out_path = args.output if args.output else "spritesheet.png"
    sheet.save(out_path)
    print(f"Bake complete! Saved spritesheet to: {out_path} ({sheet_width}x{sheet_height})")

if __name__ == "__main__":
    main()
