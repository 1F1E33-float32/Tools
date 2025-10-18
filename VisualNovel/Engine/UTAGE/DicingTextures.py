import json
import os
import math
import argparse
from PIL import Image

def reconstruct_from_json(json_path, atlas_dir, output_dir):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cell_size = data['cellSize']
    padding = data['padding']
    texture_list = data.get('textureDataList', [])

    atlas_images = {}

    os.makedirs(output_dir, exist_ok=True)
    for td in texture_list:
        name = td['name']
        atlas_name = td['atlasName']
        width, height = td['width'], td['height']
        indices = td['cellIndexList']
        transparent_index = td['transparentIndex']

        if atlas_name not in atlas_images:
            img_path = os.path.join(atlas_dir, f"{atlas_name}.png")
            if not os.path.isfile(img_path):
                raise FileNotFoundError(f"Atlas image not found: {img_path}")
            atlas_images[atlas_name] = Image.open(img_path).convert("RGBA")
        atlas_img = atlas_images[atlas_name]
        atlas_w, atlas_h = atlas_img.size

        content_size = cell_size - 2 * padding
        cols = math.ceil(width / content_size)
        rows = math.ceil(height / content_size)
        cells_per_row = atlas_w // cell_size

        result = Image.new('RGBA', (width, height), (0,0,0,0))

        idx = 0
        for row in range(rows):
            for col in range(cols):
                ci = indices[idx]
                idx += 1
                if ci == transparent_index:
                    continue  # 跳过全透明单元

                # 计算在 atlas 中的 cell 坐标（Unity 底部原点）
                cell_col = ci % cells_per_row
                cell_row = ci // cells_per_row
                crop_w = min(content_size, width - col * content_size)
                crop_h = min(content_size, height - row * content_size)
                x0 = cell_col * cell_size + padding
                # Unity 贴图原点在左下，而 PIL 原点在左上，需要翻转 Y
                y0_unity = cell_row * cell_size + padding
                y0 = atlas_h - y0_unity - crop_h

                # 从 Atlas 裁剪
                box = (x0, y0, x0 + crop_w, y0 + crop_h)
                patch = atlas_img.crop(box)

                dst_x = col * content_size
                dst_y = height - (row * content_size + crop_h)

                result.paste(patch, (dst_x, dst_y), patch)

        out_path = os.path.join(output_dir, f"{atlas_name}_{name}.png")
        result.save(out_path)
        print(f"Saved: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="Shia_Normal.json")
    parser.add_argument("--atlas-dir", default=".")
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    reconstruct_from_json(args.json, args.atlas_dir, args.output_dir)