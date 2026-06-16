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
    
    dev_crops = {
        "geek_bottom_left": (95, 215, 135, 280),
        "geek_center": (170, 110, 200, 180),
        "geek_right_top": (250, 115, 285, 185),
        "geek_right_bottom": (245, 225, 285, 295)
    }
    
    for name, bbox in dev_crops.items():
        cropped = dev_img.crop(bbox)
        cropped.save(os.path.join(output_chars_dir, f"dev_{name}.png"))
        print(f"  Saved character crop: dev_{name}.png")
        
    dev_clean = dev_img.copy()
    
    # Geek 2 (center x:170-200): Copy from x:140-170, y:110-180 (exact same horizontal strip)
    patch_center = dev_img.crop((140, 110, 170, 180))
    dev_clean.paste(patch_center, (170, 110))
    
    # Geek 3 (right top x:250-285): Copy from x:215-250, y:115-185
    patch_rt = dev_img.crop((215, 115, 250, 185))
    dev_clean.paste(patch_rt, (250, 115))
    
    # Geek 4 (right bottom x:245-285): Copy from x:205-245, y:225-295
    patch_rb = dev_img.crop((205, 225, 245, 295))
    dev_clean.paste(patch_rb, (245, 225))
    
    # Geek 1 (bottom left x:95-135, y:215-280): Copy from x:55-95, y:215-280
    patch_bl = dev_img.crop((55, 215, 95, 280))
    dev_clean.paste(patch_bl, (95, 215))
    
    # Save clean dev background
    dev_clean.save(dev_path)
    print("🟢 Overwrote Assets/Rooms/dev_room_bg.png with cleaned version.")
    
    # 2. Processing Sales Room Background
    print("Processing sales_room_bg.png...")
    sales_img = Image.open(sales_path).convert("RGBA")
    
    sales_crops = {
        "sales_console_left": (100, 125, 135, 185),
        "sales_console_right": (235, 120, 270, 180),
        "sales_center_desk": (170, 225, 205, 290),
        "sales_stand_right": (280, 210, 310, 280),
        "sales_peeking_left": (0, 260, 20, 320)
    }
    
    for name, bbox in sales_crops.items():
        cropped = sales_img.crop(bbox)
        cropped.save(os.path.join(output_chars_dir, f"sales_{name}.png"))
        print(f"  Saved character crop: sales_{name}.png")
        
    sales_clean = sales_img.copy()
    
    # Left console guy (x:100-135, y:125-185) -> Copy from x:65-100, y:125-185
    patch_s_cl = sales_img.crop((65, 125, 100, 185))
    sales_clean.paste(patch_s_cl, (100, 125))
    
    # Right console girl (x:235-270, y:120-180) -> Copy from x:200-235, y:120-180
    patch_s_cr = sales_img.crop((200, 120, 235, 180))
    sales_clean.paste(patch_s_cr, (235, 120))
    
    # Center desk guy (x:170-205, y:225-290) -> Copy from x:135-170, y:225-290
    patch_s_cd = sales_img.crop((135, 225, 170, 290))
    sales_clean.paste(patch_s_cd, (170, 225))
    
    # Right standing girl (x:280-310, y:210-280) -> Copy from x:250-280, y:210-280
    patch_s_sr = sales_img.crop((250, 210, 280, 280))
    sales_clean.paste(patch_s_sr, (280, 210))
    
    # Far left guy peeking out (x:0-20, y:260-320) -> Copy from x:20-40, y:260-320
    patch_s_pl = sales_img.crop((20, 260, 40, 320))
    sales_clean.paste(patch_s_pl, (0, 260))
    
    # Save clean sales background
    sales_clean.save(sales_path)
    print("🟢 Overwrote Assets/Rooms/sales_room_bg.png with cleaned version.")
    print("=== Finished Refined Pixel-Art Clean Stamp Successfully! ===")

if __name__ == "__main__":
    main()
