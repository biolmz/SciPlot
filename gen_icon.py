# -*- coding: utf-8 -*-
"""生成应用图标 icon.ico（多尺寸）。"""
from PIL import Image, ImageDraw

def make(size):
    s = size * 4  # 超采样
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 圆角深蓝底
    r = int(s * 0.22)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=(43, 108, 176, 255))
    # 坐标轴
    ax_l = int(s * 0.18); ax_b = int(s * 0.75); ax_t = int(s * 0.20); ax_r = int(s * 0.86)
    d.line([ax_l, ax_b, ax_l, ax_t], fill=(255, 255, 255, 200), width=int(s * 0.035))
    d.line([ax_l, ax_b, ax_r, ax_b], fill=(255, 255, 255, 200), width=int(s * 0.035))
    # 折线
    pts = [(0.18, 0.68), (0.40, 0.45), (0.56, 0.55), (0.75, 0.32)]
    px = [(int(x * s), int(y * s)) for x, y in pts]
    d.line(px, fill=(255, 255, 255, 255), width=int(s * 0.055), joint="curve")
    # 数据点
    pr = int(s * 0.055)
    for x, y in px:
        d.ellipse([x - pr, y - pr, x + pr, y + pr], fill=(224, 138, 30, 255))
    return img.resize((size, size), Image.LANCZOS)

icon = make(256)
icon.save("assets/icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon.ico 已生成")
