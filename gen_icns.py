# -*- coding: utf-8 -*-
"""生成 macOS 应用图标 icon.icns（含多尺寸 PNG 块）。"""
from PIL import Image, ImageDraw
import struct
import os


def make(size):
    s = size * 4  # 超采样
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(s * 0.22)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=(43, 108, 176, 255))
    ax_l = int(s * 0.18); ax_b = int(s * 0.75); ax_t = int(s * 0.20); ax_r = int(s * 0.86)
    d.line([ax_l, ax_b, ax_l, ax_t], fill=(255, 255, 255, 200), width=int(s * 0.035))
    d.line([ax_l, ax_b, ax_r, ax_b], fill=(255, 255, 255, 200), width=int(s * 0.035))
    pts = [(0.18, 0.68), (0.40, 0.45), (0.56, 0.55), (0.75, 0.32)]
    px = [(int(x * s), int(y * s)) for x, y in pts]
    d.line(px, fill=(255, 255, 255, 255), width=int(s * 0.055), joint="curve")
    pr = int(s * 0.055)
    for x, y in px:
        d.ellipse([x - pr, y - pr, x + pr, y + pr], fill=(224, 138, 30, 255))
    return img.resize((size, size), Image.LANCZOS)


# icns 块类型（PNG）
ICNS_TYPES = {
    16: b"icp4",
    32: b"icp5",
    64: b"icp6",
    128: b"ic07",
    256: b"ic08",
    512: b"ic09",
    1024: b"ic10",
}


def write_icns(path, images):
    """images: {size: PIL.Image}"""
    blocks = b""
    for size, img in sorted(images.items(), reverse=True):
        buf = os.fdopen if False else None
        import io
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        png = bio.getvalue()
        itype = ICNS_TYPES.get(size)
        if itype is None:
            continue
        blocks += itype + struct.pack(">I", 8 + len(png)) + png
    total = 8 + len(blocks)
    data = b"icns" + struct.pack(">I", total) + blocks
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    images = {s: make(s) for s in [16, 32, 64, 128, 256, 512, 1024]}
    write_icns("assets/icon.icns", images)
    # 同时导出一个 1024 PNG 备用
    images[1024].save("assets/icon.png")
    print("icon.icns 与 icon.png 已生成")
