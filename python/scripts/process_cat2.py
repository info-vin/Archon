import os
from PIL import Image

def optimize_image(filepath, max_size, make_square=True):
    if not os.path.exists(filepath):
        print(f"Not found: {filepath}")
        return
    img = Image.open(filepath)
    width, height = img.size
    
    if make_square and width != height:
        new_dim = min(width, height)
        left = (width - new_dim) // 2
        top = (height - new_dim) // 2
        right = (width + new_dim) // 2
        bottom = (height + new_dim) // 2
        img = img.crop((left, top, right, bottom))
        width, height = img.size

    resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
    
    if width > max_size or height > max_size:
        ratio = min(max_size / width, max_size / height)
        new_w = int(width * ratio)
        new_h = int(height * ratio)
        img = img.resize((new_w, new_h), resample_filter)
        
    img.save(filepath, 'PNG', optimize=True)
    print(f"Optimized {filepath} to {img.size}")

def create_mockup():
    frame_path = '../recontextualization/assets/images/card_frame_blank.png'
    icon_path = '../recontextualization/assets/images/chip_green_target.png'
    out_path = '../recontextualization/assets/images/mockup_sample_card.png'
    
    if not os.path.exists(frame_path) or not os.path.exists(icon_path):
        return

    frame = Image.open(frame_path).convert("RGBA")
    icon = Image.open(icon_path).convert("RGBA")

    # 卡牌底框中央的發光容器通常偏上方 (因為下方要留文字區塊)
    # 我們將晶片圖示縮小到卡牌寬度的 65%，並放置在卡牌高度的 38% 處
    target_icon_w = int(frame.width * 0.65)
    resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
    icon = icon.resize((target_icon_w, target_icon_w), resample_filter)

    paste_x = (frame.width - target_icon_w) // 2
    paste_y = int(frame.height * 0.38) - (target_icon_w // 2)

    mockup = frame.copy()
    mockup.paste(icon, (paste_x, paste_y), icon)
    mockup.save(out_path, 'PNG', optimize=True)
    print(f"Created Mockup at {out_path} ({mockup.size})")

if __name__ == '__main__':
    print("Processing Category 2...")
    optimize_image('../recontextualization/assets/images/chip_green_target.png', 512, make_square=True)
    optimize_image('../recontextualization/assets/images/chip_red_noise.png', 512, make_square=True)
    # 實體卡牌框是 11:16, 不裁切為正方, 最大邊長限制在 1024
    optimize_image('../recontextualization/assets/images/card_frame_blank.png', 1024, make_square=False)
    
    create_mockup()
