import os
from PIL import Image, ImageDraw

def draw_chamfered_square(size, chamfer_ratio=0.15):
    """產生一個倒角正方形 (八角形) 的座標"""
    c = size * chamfer_ratio
    return [
        (c, 0),
        (size - c, 0),
        (size, c),
        (size, size - c),
        (size - c, size),
        (c, size),
        (0, size - c),
        (0, c)
    ]

def create_mockup():
    frame_path = '../recontextualization/assets/images/card_frame_blank.png'
    icon_path = '../recontextualization/assets/images/chip_green_target.png'
    out_path = '../recontextualization/assets/images/mockup_sample_card.png'
    
    if not os.path.exists(frame_path) or not os.path.exists(icon_path):
        print("Images not found.")
        return

    frame = Image.open(frame_path).convert("RGBA")
    icon = Image.open(icon_path).convert("RGBA")

    # 1. 調整尺寸：讓晶片大幅縮小，以符合底框中央凹槽的大小
    # 設定晶片寬度約為底框寬度的 42% 
    target_icon_w = int(frame.width * 0.42)
    resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
    icon = icon.resize((target_icon_w, target_icon_w), resample_filter)

    # 2. 建立倒角正方形遮罩 (Chamfered Square / Octagon Mask)
    # 我們將倒角比例設為 0.2 (20%)，這更符合賽博龐克卡槽的常見形狀
    mask = Image.new('L', (target_icon_w, target_icon_w), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(draw_chamfered_square(target_icon_w, 0.18), fill=255)
    
    # 將遮罩套用到晶片的 Alpha 通道
    icon.putalpha(mask)

    # 3. 定位與合成 (Y 軸微調)
    paste_x = (frame.width - target_icon_w) // 2
    # 將 Y 軸定在 38.5% 高度處 (稍微對齊卡牌上半部的視覺中心)
    paste_y = int(frame.height * 0.385) - (target_icon_w // 2)

    mockup = frame.copy()
    mockup.paste(icon, (paste_x, paste_y), icon)
    
    mockup.save(out_path, 'PNG', optimize=True)
    print(f"Octagon Mockup created at {out_path}")

if __name__ == '__main__':
    create_mockup()
