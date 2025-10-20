#!/usr/bin/env python3
"""
把白底 PNG 转为透明底，尽量“不变色”。

问题背景：
- 旧实现仅用「alpha = 255 - min(R,G,B)」作为透明度，RGB 不做校正。
- 这会让本应完全不透明的有色区域也变半透明（例如棕色、灰色），
  在非白色背景或预览器的棋盘格上看起来会“发暗/发灰”。

改进思路：
- 使用与“Color to Alpha（白→透明）”等价的反去背（un-premultiply）公式：
  设 w=min(R,G,B)，a=255-w；新的颜色通道 c' = (c - w) * 255 / a（a>0），否则置 0。
  这样能尽量还原被白色背景稀释前的前景颜色，边缘仍保留抗锯齿。
- 可选：对明显不是白边的像素直接钳为完全不透明，避免主体发灰。

用法：
  python scripts/tools/images/png_white_to_alpha.py arch_white.png

说明：
- threshold（默认0）：小于该 alpha 的像素直接置为透明，可清理轻微背景噪点（如 1~10）。
- 可通过 --simple 保留旧算法（仅替换 alpha，不校正 RGB）。
"""

import sys
import argparse
from PIL import Image, ImageChops

def white_to_alpha_preserve(im: Image.Image, threshold: int = 0, opaque_floor: int = 235) -> Image.Image:
    """将白底转透明，并用反去背恢复颜色，尽量避免发灰。

    参数：
    - threshold: 低于该 alpha 的像素直接置 0（清噪）。
    - opaque_floor: 当 min(R,G,B) 小于该值（像素离白色较远）时，将 alpha 钳为 255，
      只对靠近纯白的边缘做半透明处理。建议 220~245，None 表示不钳制。
    """

    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            wmin = min(r, g, b)  # 估计被白色“稀释”的量
            a = 255 - wmin

            # 清理弱 alpha 噪点
            if a <= threshold:
                px[x, y] = (0, 0, 0, 0)
                continue

            # 主体区域钳为不透明（避免整体发灰）
            if opaque_floor is not None and wmin < opaque_floor:
                a = 255
                # 仍做一次轻度反去背，避免白边残留
                # 此时分母为 255，等效于：c' = c - wmin
                rr = max(0, min(255, r - wmin))
                gg = max(0, min(255, g - wmin))
                bb = max(0, min(255, b - wmin))
                px[x, y] = (rr, gg, bb, a)
                continue

            if a == 0:
                px[x, y] = (0, 0, 0, 0)
                continue

            # 反去背：恢复颜色
            rr = int(round((r - wmin) * 255.0 / a))
            gg = int(round((g - wmin) * 255.0 / a))
            bb = int(round((b - wmin) * 255.0 / a))
            rr = 0 if rr < 0 else (255 if rr > 255 else rr)
            gg = 0 if gg < 0 else (255 if gg > 255 else gg)
            bb = 0 if bb < 0 else (255 if bb > 255 else bb)
            px[x, y] = (rr, gg, bb, a)

    return im


def white_to_alpha_simple(im: Image.Image, threshold: int = 0) -> Image.Image:
    """旧实现：仅根据与白色的距离生成 alpha，不纠正 RGB。"""
    im = im.convert("RGBA")
    r, g, b, a = im.split()
    # alpha = max(255-r, 255-g, 255-b) = 255 - min(r,g,b)
    mask = ImageChops.lighter(
        ImageChops.invert(r),
        ImageChops.lighter(ImageChops.invert(g), ImageChops.invert(b)),
    )
    if threshold and threshold > 0:
        mask = mask.point(lambda p: 0 if p < threshold else p)
    im.putalpha(mask)
    return im


def main():
    parser = argparse.ArgumentParser(description="将白底 PNG 转为透明底，尽量不变色")
    parser.add_argument("input", help="输入 PNG")
    parser.add_argument("output", nargs="?", help="输出 PNG（默认加 -transparent 后缀）")
    parser.add_argument("threshold", nargs="?", type=int, default=0, help="alpha 噪点阈值（默认 0）")
    parser.add_argument("--simple", action="store_true", help="使用旧算法（仅改 alpha，不校正 RGB）")
    parser.add_argument("--opaque-floor", type=int, default=235, help="主体不透明阈值（默认 235，None 关闭）")
    args = parser.parse_args()

    src = args.input
    dst = args.output if args.output else (src.rsplit('.', 1)[0] + "-transparent.png")
    thr = args.threshold

    im = Image.open(src)
    if args.simple:
        out = white_to_alpha_simple(im, threshold=thr)
    else:
        out = white_to_alpha_preserve(im, threshold=thr, opaque_floor=args.opaque_floor)

    # 尽量保留 ICC/gamma 信息，减少色偏
    save_kwargs = {}
    if 'icc_profile' in im.info:
        save_kwargs['icc_profile'] = im.info['icc_profile']
    if 'gamma' in im.info:
        # Pillow 支持 PNG gAMA 参数
        save_kwargs['gamma'] = im.info['gamma']

    out.save(dst, **save_kwargs)
    print(f"[done] saved: {dst}")


if __name__ == "__main__":
    main()
