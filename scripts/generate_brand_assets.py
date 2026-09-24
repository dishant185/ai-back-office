import os
import numpy as np
from PIL import Image

src_path = 'logo/ChatGPT Image Sep 21, 2026, 03_37_05 PM.png'
img = Image.open(src_path)

out_brand_dir = 'frontend/src/assets/brand'
out_public_dir = 'frontend/public'
os.makedirs(out_brand_dir, exist_ok=True)
os.makedirs(out_public_dir, exist_ok=True)

# 1. Mark: Emblem only (row 25 to 646, cols 519 to 1040)
mark = img.crop((519, 25, 1040, 646))
mark.save(os.path.join(out_brand_dir, 'novera-mark.png'), 'PNG')
mark.save(os.path.join(out_public_dir, 'novera-mark.png'), 'PNG')

# 2. Wordmark: "NOVERA" only (row 665 to 863, cols 119 to 1424)
wordmark = img.crop((119, 665, 1424, 863))
wordmark.save(os.path.join(out_brand_dir, 'novera-wordmark.png'), 'PNG')
wordmark.save(os.path.join(out_public_dir, 'novera-wordmark.png'), 'PNG')

# 2b. Light wordmark for dark backgrounds:
wm_arr = np.array(wordmark, dtype=np.float32)
r, g, b, a = wm_arr[:, :, 0], wm_arr[:, :, 1], wm_arr[:, :, 2], wm_arr[:, :, 3]
is_brass = (r > 100) & (b < 80) & (g > 80)
is_dark = (r < 80) & (g < 80) & (b < 80) & (a > 20) & (~is_brass)
wm_arr[is_dark, 0] = 255
wm_arr[is_dark, 1] = 255
wm_arr[is_dark, 2] = 255
wordmark_light = Image.fromarray(wm_arr.astype(np.uint8))
wordmark_light.save(os.path.join(out_brand_dir, 'novera-wordmark-light.png'), 'PNG')
wordmark_light.save(os.path.join(out_public_dir, 'novera-wordmark-light.png'), 'PNG')

# 3. Full Logo (Emblem + NOVERA + Tagline): tight bbox crop
full = img.crop((119, 25, 1424, 955))
full.save(os.path.join(out_brand_dir, 'novera-full.png'), 'PNG')
full.save(os.path.join(out_public_dir, 'novera-full.png'), 'PNG')

# 3b. Full light logo:
full_arr = np.array(full, dtype=np.float32)
# The text is below y = 640
fr, fg, fb, fa = full_arr[:, :, 0], full_arr[:, :, 1], full_arr[:, :, 2], full_arr[:, :, 3]
y_indices = np.arange(full_arr.shape[0])[:, None]
is_text_zone = y_indices > 630
f_brass = (fr > 100) & (fb < 80) & (fg > 80)
f_dark = (fr < 80) & (fg < 80) & (fb < 80) & (fa > 20) & (~f_brass) & is_text_zone
full_arr[f_dark, 0] = 255
full_arr[f_dark, 1] = 255
full_arr[f_dark, 2] = 255
full_light = Image.fromarray(full_arr.astype(np.uint8))
full_light.save(os.path.join(out_brand_dir, 'novera-full-light.png'), 'PNG')
full_light.save(os.path.join(out_public_dir, 'novera-full-light.png'), 'PNG')

# 4. Compact Logo (horizontal lockup: emblem + wordmark)
m_h = 220
m_w = int(mark.width * (m_h / mark.height))
mark_scaled = mark.resize((m_w, m_h), Image.Resampling.LANCZOS)

w_h = 170
w_w = int(wordmark.width * (w_h / wordmark.height))
wordmark_scaled = wordmark.resize((w_w, w_h), Image.Resampling.LANCZOS)
wordmark_light_scaled = wordmark_light.resize((w_w, w_h), Image.Resampling.LANCZOS)

gap = 36
comp_w = m_w + gap + w_w
comp_h = max(m_h, w_h)

# Dark text version (for light backgrounds)
compact = Image.new('RGBA', (comp_w, comp_h), (0, 0, 0, 0))
compact.paste(mark_scaled, (0, (comp_h - m_h) // 2), mark_scaled)
compact.paste(wordmark_scaled, (m_w + gap, (comp_h - w_h) // 2), wordmark_scaled)
compact.save(os.path.join(out_brand_dir, 'novera-compact.png'), 'PNG')
compact.save(os.path.join(out_public_dir, 'novera-compact.png'), 'PNG')

# Light text version (for dark backgrounds)
compact_light = Image.new('RGBA', (comp_w, comp_h), (0, 0, 0, 0))
compact_light.paste(mark_scaled, (0, (comp_h - m_h) // 2), mark_scaled)
compact_light.paste(wordmark_light_scaled, (m_w + gap, (comp_h - w_h) // 2), wordmark_light_scaled)
compact_light.save(os.path.join(out_brand_dir, 'novera-compact-light.png'), 'PNG')
compact_light.save(os.path.join(out_public_dir, 'novera-compact-light.png'), 'PNG')

# 5. Favicon PNG and SVG
fav = mark.resize((64, 64), Image.Resampling.LANCZOS)
fav.save(os.path.join(out_public_dir, 'favicon.png'), 'PNG')

# Master copy
img.save(os.path.join(out_brand_dir, 'novera-logo-master.png'), 'PNG')
img.save(os.path.join(out_public_dir, 'novera-logo-master.png'), 'PNG')

print("All Novera logo variants generated successfully!")
