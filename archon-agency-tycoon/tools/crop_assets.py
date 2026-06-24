import sys
from PIL import Image

def remove_background(img):
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    # threshold for white
    for item in data:
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    return img

def process_chairs(path, out_dir):
    img = Image.open(path)
    img = remove_background(img)
    w, h = img.size
    cw = w // 4
    
    # 1: NW, 2: NE, 3: SW, 4: SE
    directions = ["chair_NW.png", "chair_NE.png", "chair_SW.png", "chair_SE.png"]
    
    for i in range(4):
        box = (i * cw, 0, (i + 1) * cw, h)
        cropped = img.crop(box)
        bbox = cropped.getbbox()
        if bbox:
            cropped = cropped.crop(bbox)
        # Pad slightly
        final_img = Image.new("RGBA", (cropped.width + 10, cropped.height + 10), (0,0,0,0))
        final_img.paste(cropped, (5, 5))
        final_img.save(f"{out_dir}/{directions[i]}")
        print(f"Saved {directions[i]}")

def process_walls(path, out_dir):
    img = Image.open(path)
    img = remove_background(img)
    w, h = img.size
    cw = w // 2
    ch = h // 2
    
    # top-left: NW, top-right: NE
    # bottom-left: SW, bottom-right: SE
    coords = [
        (0, 0, cw, ch, "half_wall_NW.png"),
        (cw, 0, w, ch, "half_wall_NE.png"),
        (0, ch, cw, h, "half_wall_SW.png"),
        (cw, ch, w, h, "half_wall_SE.png")
    ]
    
    for x0, y0, x1, y1, name in coords:
        box = (x0, y0, x1, y1)
        cropped = img.crop(box)
        bbox = cropped.getbbox()
        if bbox:
            cropped = cropped.crop(bbox)
        final_img = Image.new("RGBA", (cropped.width + 10, cropped.height + 10), (0,0,0,0))
        final_img.paste(cropped, (5, 5))
        final_img.save(f"{out_dir}/{name}")
        print(f"Saved {name}")

if __name__ == "__main__":
    chair_path = sys.argv[1]
    wall_path = sys.argv[2]
    out_dir = sys.argv[3]
    process_chairs(chair_path, out_dir)
    process_walls(wall_path, out_dir)
