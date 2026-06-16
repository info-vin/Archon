import os
import argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
import shutil

# ==============================================================================
# 核心自動化整合腳本 (V2.0)：全動態斷崖偵測 (Godot Pipeline Version)
# ==============================================================================

def process_spritesheet(image_path, output_dir, target_size=(64, 64)):
    if not os.path.exists(image_path):
        print(f"❌ 錯誤：找不到輸入檔案 {image_path}")
        return

    if os.path.exists(output_dir): 
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # --- 步驟 A: 影像讀取與去背 ---
    print(f"🎨 正在載入圖片 {image_path} 並執行硬邊去背...")
    img_pil = Image.open(image_path).convert("RGBA")
    img_data = np.array(img_pil)
    r, g, b, a = img_data[:,:,0], img_data[:,:,1], img_data[:,:,2], img_data[:,:,3]
    white_mask = (r >= 250) & (g >= 250) & (b >= 250)
    img_data[white_mask] = [255, 255, 255, 0]

    # --- 步驟 B: 物理連通域分析 ---
    binary_mask = img_data[:, :, 3] > 0
    labeled_array, num_features = label(binary_mask)

    all_detected = []
    for i in range(1, num_features + 1):
        rows, cols = np.where(labeled_array == i)
        if len(rows) == 0: continue
        min_y, max_y = np.min(rows), np.max(rows)
        min_x, max_x = np.min(cols), np.max(cols)
        w, h = max_x - min_x + 1, max_y - min_y + 1
        
        # 過濾掉頂部文字標籤與過小的噪點
        if min_y < 50 or w < 3 or h < 3: continue
        
        all_detected.append({
            'id': i,
            'bbox': (min_y, max_y, min_x, max_x),
            'size': (w, h),
            'area': np.sum(labeled_array == i)
        })

    all_detected.sort(key=lambda x: x['area'], reverse=True)

    # --- 步驟 C: 全動態斷崖偵測 (零硬編碼修正) ---
    if len(all_detected) < 3:
        print("⚠️ 警告：偵測到的物件過少，可能圖片格式不符或需要調整閾值。")
        final_count = len(all_detected)
    else:
        areas_sorted = np.array([item['area'] for item in all_detected])
        log_areas = np.log10(areas_sorted)
        d1 = np.diff(log_areas)
        d2 = np.diff(d1)

        # 動態決定搜尋範圍：排除掉面積最小的 20% 物件（通常是無意義噪點），
        # 在剩下的 80% 空間中尋找最劇烈的面積下降轉折點。
        dynamic_limit = int(len(d2) * 0.8)
        final_count = np.argmax(d2[:max(1, dynamic_limit)]) + 1

    print(f"📊 總偵測物件：{len(all_detected)}")
    print(f"📊 自動判定資產數量：{final_count} 個 (已排除雜訊區)")

    # --- 步驟 D: 標準化置中與導出 ---
    print(f"✂️ 正在執行標準化導出至 {output_dir}...")
    final_selection = all_detected[:final_count]

    # Calculate uniform scale factor based on the largest dimension of any component
    max_dim_all = max(max(item['size']) for item in final_selection)
    scale = 60.0 / max_dim_all
    print(f"📏 Using uniform scale factor: {scale:.5f} (max dim: {max_dim_all})")

    for idx, item in enumerate(final_selection):
        min_y, max_y, min_x, max_x = item['bbox']
        obj_w, obj_h = item['size']

        raw_crop = img_data[min_y:max_y+1, min_x:max_x+1].copy()
        mask = (labeled_array[min_y:max_y+1, min_x:max_x+1] != item['id'])
        raw_crop[mask] = [0, 0, 0, 0]

        sprite_pil = Image.fromarray(raw_crop)

        # Apply uniform scale factor
        new_w, new_h = int(obj_w * scale), int(obj_h * scale)
        new_w = max(1, new_w)
        new_h = max(1, new_h)
        sprite_pil = sprite_pil.resize((new_w, new_h), Image.Resampling.NEAREST)

        final_w, final_h = sprite_pil.size
        canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
        canvas.paste(sprite_pil, ((target_size[0] - final_w)//2, (target_size[1] - final_h)//2))
        
        # 導出檔案
        out_filename = os.path.join(output_dir, f"part_{idx:03d}.png")
        canvas.save(out_filename)

    print("=" * 50)
    print(f"✅ 全自動整合流程結束！")
    print(f"   - 成功處理 {final_count} 個部件")
    print(f"   - 檔案存放於: {output_dir}")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="自動化角色精靈圖切片與標準化工具 (Godot Pipeline)")
    parser.add_argument("-i", "--input", default="raw_assets/alice_spritesheet.png", help="輸入的原始精靈圖路徑")
    parser.add_argument("-o", "--output", default="archon-agency-tycoon/Assets/Characters/Alice_Parts", help="輸出 Godot 專案的資料夾路徑")
    parser.add_argument("-s", "--size", type=int, default=64, help="目標畫布大小 (預設 64, 即 64x64)")
    
    args = parser.parse_args()
    
    process_spritesheet(args.input, args.output, (args.size, args.size))
