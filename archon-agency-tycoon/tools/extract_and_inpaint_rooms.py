import os
from PIL import Image

def main():
    print("=== Starting Refined Pixel-Art Clone Stamp & Inpainting ===")
    
    # Paths
    base_dir = "/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon"
    dev_path = os.path.join(base_dir, "Assets/Rooms/dev_room_bg.png")
    sales_path = os.path.join(base_dir, "Assets/Rooms/sales_room_bg.png")
    output_chars_dir = os.path.join(base_dir, "Assets/Characters/Extracted")
    
    os.makedirs(output_chars_dir, exist_ok=True)
    
    if not os.path.exists(dev_path) or not os.path.exists(sales_path):
        print(f"Error: Missing background images")
        return
        
    # 1. Processing Dev Room Background
    print("Processing dev_room_bg.png...")
    dev_img = Image.open(dev_path).convert("RGBA")
    dev_clean = dev_img.copy()
    
    # Geek 2 (center x:170-200, y:110-180) -> cover x:170-210 with shift +32 from 138-178
    dev_clean.paste(dev_img.crop((138, 110, 178, 170)), (170, 110))
    dev_clean.paste(dev_img.crop((202, 170, 242, 180)), (170, 170))
    
    # Geek 3 (right top x:250-285, y:115-185) -> cover x:245-290 with shift +32 from 213-258
    dev_clean.paste(dev_img.crop((213, 115, 258, 185)), (245, 115))
    
    # Geek 4 (right bottom x:245-285, y:225-295) -> cover x:245-290 with shift +32 from 213-258
    dev_clean.paste(dev_img.crop((213, 225, 258, 295)), (245, 225))
    
    # Geek 1 & adjacent geek (bottom left x:60-135, y:215-280)
    # Double cascade shift (+32 in X) to completely replace bottom-left desks with clean servers
    # 1. Erase first geek (60-108) by shifting clean server rack (28-76) by +32
    dev_clean.paste(dev_img.crop((28, 215, 76, 255)), (60, 215))
    dev_clean.paste(dev_img.crop((127, 255, 175, 280)), (60, 255))
    # 2. Erase second geek (92-140) by shifting the newly cleaned server rack (60-108) by +32
    dev_clean.paste(dev_clean.crop((60, 215, 108, 255)), (92, 215))
    dev_clean.paste(dev_clean.crop((60, 255, 108, 280)), (92, 255))
    
    # Save clean dev background
    dev_clean.save(dev_path)
    print("🟢 Overwrote Assets/Rooms/dev_room_bg.png with cleaned version.")
    
    # 2. Processing Sales Room Background
    print("Processing sales_room_bg.png...")
    sales_img = Image.open(sales_path).convert("RGBA")
    sales_clean = sales_img.copy()
    
    # Left console guy -> cover x:95-140 with shift by +32 from 63-108
    sales_clean.paste(sales_img.crop((63, 125, 108, 185)), (95, 125))
    
    # Right console girl -> cover x:230-275 with shift by +32 from 198-243
    sales_clean.paste(sales_img.crop((198, 120, 243, 180)), (230, 120))
    
    # Center desk guy -> cover x:165-215 with shift by +32 from 133-183
    sales_clean.paste(sales_img.crop((133, 225, 183, 290)), (165, 225))
    
    # Right standing girl -> cover x:275-315 with shift by +32 from 243-283
    sales_clean.paste(sales_img.crop((243, 210, 283, 280)), (275, 210))
    
    # Far left guy peeking out -> cover x:0-32 with shift by -32 from 32-64
    sales_clean.paste(sales_img.crop((32, 260, 64, 320)), (0, 260))
    
    # Save clean sales background
    sales_clean.save(sales_path)
    print("🟢 Overwrote Assets/Rooms/sales_room_bg.png with cleaned version.")
    print("=== Finished Refined Pixel-Art Clean Stamp Successfully! ===")

if __name__ == "__main__":
    main()

