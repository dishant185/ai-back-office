from PIL import Image
import numpy as np

img = Image.open('logo/ChatGPT Image Sep 21, 2026, 03_37_05 PM.png')
w, h = img.size
a = np.array(img)[:, :, 3]
rows = (a > 10).sum(axis=1)

ranges = []
in_block = False
start = 0
for i, c in enumerate(rows):
    if c > 0 and not in_block:
        in_block = True
        start = i
    elif c == 0 and in_block:
        in_block = False
        ranges.append((start, i))
if in_block:
    ranges.append((start, len(rows)))

print("Row ranges:")
for r in ranges:
    # get col bbox for this range
    sub_a = a[r[0]:r[1], :]
    cols = (sub_a > 10).sum(axis=0)
    col_nz = np.where(cols > 0)[0]
    print(f"Row {r[0]} to {r[1]} (height {r[1]-r[0]}): cols {col_nz[0]} to {col_nz[-1]} (width {col_nz[-1]-col_nz[0]})")
