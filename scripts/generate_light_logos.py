import numpy as np
from PIL import Image

def make_light_text_version(img_path, out_path):
    img = Image.open(img_path).convert('RGBA')
    arr = np.array(img, dtype=np.float32)
    
    # arr has R, G, B, A
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    
    # Identify dark ink letters: alpha > 30 and brightness < 70, and not brass/gold
    # Brass/gold has r significantly higher than b (e.g. r > 100, b < 100)
    # Dark ink has low r, g, b
    is_brass = (r > 100) & (b < 80) & (g > 80)
    is_dark = (r < 75) & (g < 75) & (b < 75) & (a > 30) & (~is_brass)
    
    # For dark ink pixels, change RGB to 255, 255, 255 (white) while preserving alpha
    arr[is_dark, 0] = 255
    arr[is_dark, 1] = 255
    arr[is_dark, 2] = 255
    
    res = Image.fromarray(arr.astype(np.uint8))
    res.save(out_path, 'PNG')
    return res

make_light_text_version('frontend/public/novera-wordmark.png', 'frontend/public/novera-wordmark-light.png')
make_light_text_version('frontend/public/novera-wordmark.png', 'frontend/src/assets/brand/novera-wordmark-light.png')

make_light_text_version('frontend/public/novera-compact.png', 'frontend/public/novera-compact-light.png')
make_light_text_version('frontend/public/novera-compact.png', 'frontend/src/assets/brand/novera-compact-light.png')

make_light_text_version('frontend/public/novera-full.png', 'frontend/public/novera-full-light.png')
make_light_text_version('frontend/public/novera-full.png', 'frontend/src/assets/brand/novera-full-light.png')

print("Light-text variants generated successfully.")
