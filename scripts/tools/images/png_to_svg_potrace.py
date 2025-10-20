#!/usr/bin/env python3
"""
PNG → SVG（potrace）转换脚本

特性
- 保留长宽比缩放（最长边=resolution），自动裁剪并居中
- Otsu 阈值 + 轻度去噪，自动判断白底/黑底，支持透明图
- 参数夹值：平滑(alphamax)与 speck 过滤(turdsize)稳定可控
- 两种渲染模式：fill（实心面）或 stroke（描边，更像线稿）
- 支持批量处理

快速用法
- 基本：自动检测并输出（默认填充模式）
  python scripts/tools/images/png_to_svg_potrace.py input.png [-o output.svg]

- 线稿描边输出（推荐手绘/线条图）
  python scripts/tools/images/png_to_svg_potrace.py course_icon.png \
         --stroke --stroke-width 2

- 高质量（更平滑、更少噪点）
  python scripts/tools/images/png_to_svg_potrace.py course_icon.png \
         --quality best --smooth 0.7 --detail 0.3 --stroke

- 指定填充颜色（仅填充模式有效）
  python scripts/tools/images/png_to_svg_potrace.py input.png -o output.svg --fill-color black
  python scripts/tools/images/png_to_svg_potrace.py input.png -o output.svg --fill-color white

- 手动控制前景方向
  --invert      将黑变白、白变黑（对白底黑线通常不需要手动）
  --no-invert   禁止自动反转

- 分辨率与裁剪
  --resolution 1024  指最长边缩放到 1024（保持比例）
  --no-crop          关闭自动裁剪与居中
  --padding 20       自动裁剪时的边距像素

- 批量目录转换
  python scripts/tools/images/png_to_svg_potrace.py input_dir/ -o output_dir/ --batch [--stroke]

- 先转透明再矢量化（纸张噪点较多时强烈推荐）
  python scripts/tools/images/png_white_to_alpha.py input.png input-transparent.png 10
  python scripts/tools/images/png_to_svg_potrace.py input-transparent.png -o output.svg --stroke

依赖
- pip install pypotrace pillow
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Tuple, Optional

from PIL import Image, ImageFilter, ImageOps
import numpy as np

try:
    import potrace
    HAVE_POTRACE = True
except ImportError:
    HAVE_POTRACE = False
    print("错误：未安装 potrace 库")
    print("请安装：pip install pypotrace")
    sys.exit(1)


class PotraceConfig:
    """Potrace 配置参数"""
    def __init__(self):
        # 基础参数
        self.turdsize = 2  # 忽略小于此大小的斑点
        self.alphamax = 1.0  # 曲线平滑度 (0.0-1.3333)
        self.opttolerance = 0.2  # 优化容差
        self.turnpolicy = 'minority'  # 转角策略

        # 高级参数
        self.opticurve = True  # 是否优化曲线
        self.gamma = 0.0  # gamma 值（用于彩色模式）

    @classmethod
    def from_quality(cls, quality: str) -> 'PotraceConfig':
        """根据质量预设创建配置"""
        config = cls()

        if quality == 'draft':
            config.turdsize = 5
            config.alphamax = 1.3333
            config.opttolerance = 0.5
            config.opticurve = False
        elif quality == 'normal':
            config.turdsize = 2
            config.alphamax = 1.0
            config.opttolerance = 0.2
            config.opticurve = True
        elif quality == 'best':
            config.turdsize = 1
            config.alphamax = 0.5
            config.opttolerance = 0.1
            config.opticurve = True

        return config


def preprocess_image(img_path: str, resolution: int = 1024, invert: bool = None) -> Tuple[np.ndarray, Dict]:
    """预处理图像，返回二值数据和元数据。

    改进点：
    - 保留长宽比缩放（最长边=resolution），避免拉伸导致的失真；
    - 使用 Otsu 自适应阈值并配合中值滤波，降低纸张噪点；
    - 透明图直接使用 alpha 作为位图。
    """
    img = Image.open(img_path)

    original_size = img.size

    # 检查透明
    has_transparency = False
    if img.mode == 'RGBA':
        alpha = np.array(img.split()[-1])
        if np.min(alpha) < 255:
            has_transparency = True

    # 计算按比例的新尺寸
    ow, oh = img.size
    if max(ow, oh) != resolution:
        if ow >= oh:
            nw = resolution
            nh = int(round(oh * (resolution / ow)))
        else:
            nh = resolution
            nw = int(round(ow * (resolution / oh)))
    else:
        nw, nh = ow, oh

    metadata = {
        'original_size': original_size,
        'resized_size': (nw, nh),
        'has_transparency': has_transparency,
    }

    # 透明图：alpha 直接二值
    if has_transparency:
        rgba = img.convert('RGBA')
        alpha = rgba.split()[-1].resize((nw, nh), Image.Resampling.LANCZOS)
        binary = np.array(alpha) > 128
        if invert is None:
            invert = True  # 透明图通常是“前景=非透明”
        metadata['inverted'] = invert
        # 记录前景比例，便于调试
        metadata['fg_ratio'] = float(binary.mean())
        return binary, metadata

    # 非透明图：灰度 -> 自适应二值
    if img.mode != 'L':
        img = img.convert('L')
    if (ow, oh) != (nw, nh):
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)

    # 轻度增强和去噪
    img = ImageOps.autocontrast(img, cutoff=2)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    img_array = np.array(img)

    # 判断前景颜色（暗像素占比小则视为白底黑线）
    if invert is None:
        dark_ratio = (img_array <= 200).sum() / img_array.size
        invert = dark_ratio < 0.35

    # Otsu 阈值
    hist, _ = np.histogram(img_array.ravel(), bins=256, range=(0, 256))
    total = img_array.size
    sum_total = np.dot(np.arange(256), hist)
    sum_b = 0.0
    w_b = 0.0
    var_max = -1.0
    thr = 128
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        var_between = w_b * w_f * (m_b - m_f) ** 2
        if var_between > var_max:
            var_max = var_between
            thr = t

    if invert:
        binary = img_array < thr
    else:
        binary = img_array > thr

    # 前景比例与自适应回退：若前景几乎铺满（>0.85）或几乎为零（<0.01），
    # 多半是方向判断失误，自动翻转一次。
    fg_ratio = float(binary.mean())
    # 极端占比回退：即使我们已做了自动判断，也允许在极端情况下翻转一次
    # 以防 Otsu/对比度处理导致“前景全白/全黑”。
    if fg_ratio > 0.985 or fg_ratio < 0.005:
        binary = ~binary
        invert = not (invert if invert is not None else False)
        fg_ratio = 1.0 - fg_ratio

    metadata['inverted'] = invert
    metadata['fg_ratio'] = fg_ratio
    return binary, metadata


def trace_with_potrace(bitmap: np.ndarray, config: PotraceConfig) -> potrace.Path:
    """使用 potrace 进行矢量化"""
    # 创建位图
    bmp = potrace.Bitmap(bitmap)

    # 设置参数
    params = {
        'turdsize': config.turdsize,
        'alphamax': config.alphamax,
        'opttolerance': config.opttolerance,
        'opticurve': config.opticurve,
        'turnpolicy': config.turnpolicy
    }

    # 执行矢量化
    path = bmp.trace(**params)

    return path


def path_to_svg(path: potrace.Path, scale: float = 1.0,
                offset: Tuple[float, float] = (0, 0),
                metadata: Optional[Dict] = None) -> str:
    """将 potrace 路径转换为 SVG 字符串"""
    svg_paths = []

    # 获取图像边界（尽量不做“背景排除”，防止误删）
    bounds = calculate_bounds(path, metadata)
    image_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])

    for i, curve in enumerate(path.curves):
        path_data = []

        # 计算路径边界和面积
        points = []
        x_min = float('inf')
        y_min = float('inf')
        x_max = float('-inf')
        y_max = float('-inf')

        # 起始点
        start = curve.start_point
        points.append((start.x, start.y))
        x_min = min(x_min, start.x)
        y_min = min(y_min, start.y)
        x_max = max(x_max, start.x)
        y_max = max(y_max, start.y)
        path_data.append(f"M {start.x * scale + offset[0]:.2f} {start.y * scale + offset[1]:.2f}")

        # 处理每一段
        for segment in curve.segments:
            if segment.is_corner:
                # 直线段
                c = segment.c
                end = segment.end_point
                points.append((c.x, c.y))
                points.append((end.x, end.y))
                x_min = min(x_min, c.x, end.x)
                y_min = min(y_min, c.y, end.y)
                x_max = max(x_max, c.x, end.x)
                y_max = max(y_max, c.y, end.y)
                path_data.append(f"L {c.x * scale + offset[0]:.2f} {c.y * scale + offset[1]:.2f}")
                path_data.append(f"L {end.x * scale + offset[0]:.2f} {end.y * scale + offset[1]:.2f}")
            else:
                # 贝塞尔曲线
                c1 = segment.c1
                c2 = segment.c2
                end = segment.end_point
                points.append((end.x, end.y))
                x_min = min(x_min, c1.x, c2.x, end.x)
                y_min = min(y_min, c1.y, c2.y, end.y)
                x_max = max(x_max, c1.x, c2.x, end.x)
                y_max = max(y_max, c1.y, c2.y, end.y)
                path_data.append(
                    f"C {c1.x * scale + offset[0]:.2f} {c1.y * scale + offset[1]:.2f} "
                    f"{c2.x * scale + offset[0]:.2f} {c2.y * scale + offset[1]:.2f} "
                    f"{end.x * scale + offset[0]:.2f} {end.y * scale + offset[1]:.2f}"
                )

        # 计算路径边界框
        path_width = x_max - x_min
        path_height = y_max - y_min
        path_area = path_width * path_height

        # 判断是否为背景：仅在透明图场景下才尝试过滤极可能的整幅背景形状，
        # 避免误删正常大形状（例如粗圆环）。
        is_background = False
        if metadata and metadata.get('has_transparency'):
            # 透明图若出现近乎整幅的大块，视为背景（极少见）
            if path_area > image_area * 0.995:
                is_background = True

        # 闭合路径
        path_data.append("Z")

        # 只有非背景路径才添加到结果中
        if not is_background:
            svg_paths.append(" ".join(path_data))

    return "\n".join([f'<path d="{p}" />' for p in svg_paths])


def calculate_bounds(path: potrace.Path, metadata: Optional[Dict] = None) -> Tuple[float, float, float, float]:
    """计算路径的边界框（尽量不排除背景，避免误删）。"""
    x_min = float('inf')
    y_min = float('inf')
    x_max = float('-inf')
    y_max = float('-inf')

    # 获取图像边界
    all_x = []
    all_y = []
    for curve in path.curves:
        # 起始点
        all_x.append(curve.start_point.x)
        all_y.append(curve.start_point.y)
        # 所有点
        for segment in curve.segments:
            if segment.is_corner:
                all_x.append(segment.c.x)
                all_y.append(segment.c.y)
                all_x.append(segment.end_point.x)
                all_y.append(segment.end_point.y)
            else:
                all_x.append(segment.c1.x)
                all_y.append(segment.c1.y)
                all_x.append(segment.c2.x)
                all_y.append(segment.c2.y)
                all_x.append(segment.end_point.x)
                all_y.append(segment.end_point.y)

    # 计算整体边界
    image_x_min = min(all_x)
    image_y_min = min(all_y)
    image_x_max = max(all_x)
    image_y_max = max(all_y)
    image_area = (image_x_max - image_x_min) * (image_y_max - image_y_min)

    for i, curve in enumerate(path.curves):
        # 计算当前路径的边界
        curve_x_min = float('inf')
        curve_y_min = float('inf')
        curve_x_max = float('-inf')
        curve_y_max = float('-inf')

        points = []
        # 起始点
        points.append((curve.start_point.x, curve.start_point.y))
        curve_x_min = min(curve_x_min, curve.start_point.x)
        curve_y_min = min(curve_y_min, curve.start_point.y)
        curve_x_max = max(curve_x_max, curve.start_point.x)
        curve_y_max = max(curve_y_max, curve.start_point.y)

        # 所有点
        for segment in curve.segments:
            if segment.is_corner:
                for point in [(segment.c.x, segment.c.y), (segment.end_point.x, segment.end_point.y)]:
                    points.append(point)
                    curve_x_min = min(curve_x_min, point[0])
                    curve_y_min = min(curve_y_min, point[1])
                    curve_x_max = max(curve_x_max, point[0])
                    curve_y_max = max(curve_y_max, point[1])
            else:
                for point in [(segment.c1.x, segment.c1.y), (segment.c2.x, segment.c2.y),
                            (segment.end_point.x, segment.end_point.y)]:
                    points.append(point)
                    curve_x_min = min(curve_x_min, point[0])
                    curve_y_min = min(curve_y_min, point[1])
                    curve_x_max = max(curve_x_max, point[0])
                    curve_y_max = max(curve_y_max, point[1])

        # 背景判断：仅对透明图过滤近乎整幅的大块
        curve_area = (curve_x_max - curve_x_min) * (curve_y_max - curve_y_min)
        is_background = False
        if metadata and metadata.get('has_transparency'):
            if curve_area > image_area * 0.995:
                is_background = True

        # 如果不是背景，更新边界
        if not is_background:
            x_min = min(x_min, curve_x_min)
            y_min = min(y_min, curve_y_min)
            x_max = max(x_max, curve_x_max)
            y_max = max(y_max, curve_y_max)

    # 如果没有找到任何非背景路径，返回整体边界
    if x_min == float('inf'):
        return image_x_min, image_y_min, image_x_max, image_y_max

    return x_min, y_min, x_max, y_max


def generate_svg(paths: str, svg_size: int = 1024,
                metadata: Optional[Dict] = None,
                fill_color: str = "#000000",
                render: str = "fill",
                stroke_color: str = "#000000",
                stroke_width: float = 2.0) -> str:
    """生成完整的 SVG 文件。

    render 取值：
      - "fill": 使用填充（原行为）；
      - "stroke": 使用描边（线稿显示更自然）。
    """
    if render == "fill":
        # 默认使用黑色，避免在白色画布上“看起来空白”
        fc = str(fill_color).lower() if fill_color else "auto"
        if fc in ("white", "#fff", "#ffffff"):
            chosen = "#ffffff"
        else:
            chosen = "#000000"
        style = f"fill: {chosen}; stroke: none; fill-rule: evenodd;"
    else:
        style = f"fill: none; stroke: {stroke_color}; stroke-width: {stroke_width}; stroke-linecap: round; stroke-linejoin: round; vector-effect: non-scaling-stroke;"

    svg_content = f'''<?xml version="1.0" encoding="utf-8"?>
<svg width="{svg_size}" height="{svg_size}" viewBox="0 0 {svg_size} {svg_size}"
     xmlns="http://www.w3.org/2000/svg">
<style>
path {{
  {style}
}}
</style>
{paths}
</svg>'''

    return svg_content


def auto_crop_and_center(path: potrace.Path, target_size: int = 1024,
                        padding: int = 20, metadata: Optional[Dict] = None) -> Tuple[float, Tuple[float, float]]:
    """自动裁剪并居中路径"""
    # 计算边界
    x_min, y_min, x_max, y_max = calculate_bounds(path, metadata)

    # 计算尺寸
    width = x_max - x_min
    height = y_max - y_min

    # 计算缩放
    available_size = target_size - 2 * padding
    scale_x = available_size / width if width > 0 else 1
    scale_y = available_size / height if height > 0 else 1
    scale = min(scale_x, scale_y)

    # 计算偏移（居中）
    scaled_width = width * scale
    scaled_height = height * scale
    offset_x = (target_size - scaled_width) / 2 - x_min * scale
    offset_y = (target_size - scaled_height) / 2 - y_min * scale

    return scale, (offset_x, offset_y)


def auto_crop_and_center_with_bounds(path: potrace.Path, bounds: Tuple[float, float, float, float],
                                   target_size: int = 1024, padding: int = 20) -> Tuple[float, Tuple[float, float]]:
    """使用预计算的边界自动裁剪并居中路径"""
    x_min, y_min, x_max, y_max = bounds

    # 计算尺寸
    width = x_max - x_min
    height = y_max - y_min

    # 计算缩放
    available_size = target_size - 2 * padding
    scale_x = available_size / width if width > 0 else 1
    scale_y = available_size / height if height > 0 else 1
    scale = min(scale_x, scale_y)

    # 计算偏移（居中）
    scaled_width = width * scale
    scaled_height = height * scale
    offset_x = (target_size - scaled_width) / 2 - x_min * scale
    offset_y = (target_size - scaled_height) / 2 - y_min * scale

    return scale, (offset_x, offset_y)


def convert_png_to_svg(input_path: str, output_path: str,
                      quality: str = 'normal', resolution: int = 1024,
                      detail: float = 0.5, smooth: float = 0.5,
                      auto_crop: bool = True, padding: int = 20,
                      invert: Optional[bool] = None,
                      fill_color: str = "auto",
                      use_stroke: bool = False,
                      stroke_width: float = 2.0,
                      debug: bool = False) -> None:
    """主转换函数"""
    print(f"转换: {input_path} -> {output_path}")
    print(f"质量: {quality}, 分辨率: {resolution}")

    # 1. 预处理图像
    print("预处理图像...")
    bitmap, metadata = preprocess_image(input_path, resolution, invert)
    img_type = '透明背景' if metadata['has_transparency'] else '白底黑图' if metadata.get('inverted', False) else '黑底白图'
    print(f"图像类型: {img_type}")
    if invert is not None:
        print(f"手动反转: {'是' if invert else '否'}")

    # 2. 创建配置
    config = PotraceConfig.from_quality(quality)

    # 3. 根据参数调整配置（夹值以避免异常）
    # 平滑映射：smooth 越大，alphamax 越小（限制在 [0.2, 1.3]）
    low, high = 0.2, 1.3
    s = min(max(smooth, 0.0), 1.0)
    config.alphamax = float(high - (high - low) * s)
    # 细节到 speck 过滤映射：detail 越大，turdsize 越小
    # 将范围收窄到 [1..6]，避免默认把小元素误删
    d = min(max(detail, 0.0), 1.0)
    config.turdsize = int(round(1 + (1 - d) * 5))

    # 调试输出：二值图
    if debug:
        from PIL import Image
        dbg = Image.fromarray((bitmap * 255).astype('uint8'), mode='L')
        dbg_path = str(Path(output_path).with_suffix('')) + '.binary.png'
        try:
            dbg.save(dbg_path)
            print(f"已导出调试二值图: {dbg_path} (前景占比 {metadata.get('fg_ratio', 0):.3f})")
        except Exception as e:
            print(f"调试二值图保存失败: {e}")

    # 4. 矢量化
    print("执行矢量化...")
    path = trace_with_potrace(bitmap, config)
    # Fallback: 若没有任何曲线，尝试反转位图再试一次
    try:
        curve_count = len(path.curves)
    except Exception:
        curve_count = 0
    if curve_count == 0:
        print("警告：未得到曲线，尝试翻转前景再矢量化…")
        bitmap = ~bitmap
        metadata['inverted'] = not metadata.get('inverted', False)
        path = trace_with_potrace(bitmap, config)

    # 5. 自动裁剪和居中
    if auto_crop:
        print("自动裁剪和居中...")
        # 先计算实际内容的边界（不包括背景）
        bounds = calculate_bounds(path, metadata)
        scale, offset = auto_crop_and_center_with_bounds(path, bounds, padding=padding)
    else:
        scale = 1024 / resolution
        offset = (0, 0)

    # 6. 生成 SVG 路径
    print("生成 SVG...")
    svg_paths = path_to_svg(path, scale=scale, offset=offset, metadata=metadata)
    if not svg_paths.strip():
        # 二次回退：不做裁剪偏移，原尺寸直接导出，便于发现问题
        print("警告：路径为空，尝试无裁剪/无偏移导出…")
        svg_paths = path_to_svg(path, scale=(1024 / resolution), offset=(0, 0), metadata=metadata)

    # 7. 生成完整的 SVG
    if use_stroke:
        svg_content = generate_svg(svg_paths, metadata=metadata, render="stroke", stroke_width=stroke_width)
    else:
        if fill_color != "auto":
            svg_content = generate_svg(svg_paths, metadata=metadata, fill_color=fill_color, render="fill")
        else:
            svg_content = generate_svg(svg_paths, metadata=metadata, render="fill")

    # 8. 保存文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    print(f"✓ 完成: {output_path}")


def batch_convert(input_dir: str, output_dir: str, **kwargs) -> None:
    """批量转换"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 查找所有 PNG 文件
    png_files = list(input_path.glob('*.png'))

    if not png_files:
        print("未找到 PNG 文件")
        return

    print(f"找到 {len(png_files)} 个文件")

    for png_file in png_files:
        svg_file = output_path / f"{png_file.stem}.svg"
        convert_png_to_svg(str(png_file), str(svg_file), **kwargs)


def main():
    parser = argparse.ArgumentParser(
        description='高质量 PNG→SVG 工具 (potrace)。完整使用示例见脚本顶部注释。',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='质量档位: draft(快) / normal(默认) / best(质量最高)。\n渲染模式: 默认fill，可加 --stroke 输出描边。'
    )

    parser.add_argument('input', help='输入 PNG 文件或目录')
    parser.add_argument('-o', '--output', help='输出 SVG 文件或目录')
    parser.add_argument('--quality', choices=['draft', 'normal', 'best'],
                       default='normal', help='质量预设')
    parser.add_argument('--resolution', type=int, default=1024,
                       help='输入分辨率 (默认: 1024)')
    parser.add_argument('--detail', type=float, default=0.5,
                       help='细节保留级别 (0.0-1.0)')
    parser.add_argument('--smooth', type=float, default=0.5,
                       help='曲线平滑度 (0.0-1.0)')
    parser.add_argument('--no-crop', action='store_true',
                       help='禁用自动裁剪')
    parser.add_argument('--padding', type=int, default=20,
                       help='边距大小（像素）')
    parser.add_argument('--batch', action='store_true',
                       help='批量处理模式')
    parser.add_argument('--invert', action='store_true',
                       help='反转颜色（将黑变白，白变黑）')
    parser.add_argument('--no-invert', action='store_true',
                       help='不自动反转颜色（保持原始颜色关系）')
    parser.add_argument('--fill-color', default='auto',
                       choices=['auto', 'black', 'white'],
                       help='SVG填充颜色（默认auto根据图像类型自动选择）')
    parser.add_argument('--stroke', action='store_true',
                       help='以描边方式输出 SVG（更适合线稿）')
    parser.add_argument('--stroke-width', type=float, default=2.0,
                       help='描边宽度（stroke 模式下生效，默认 2.0）')
    parser.add_argument('--debug', action='store_true', help='输出调试二值图')

    args = parser.parse_args()

    # 处理反转参数
    invert_param = None
    if args.invert:
        invert_param = True
    elif args.no_invert:
        invert_param = False

    # 设置输出路径
    if not args.output:
        if args.batch:
            args.output = 'svg_output'
        else:
            input_path = Path(args.input)
            args.output = str(input_path.with_suffix('.svg'))

    # 执行转换
    if args.batch:
        batch_convert(
            args.input, args.output,
            quality=args.quality,
            resolution=args.resolution,
            detail=args.detail,
            smooth=args.smooth,
            auto_crop=not args.no_crop,
            padding=args.padding,
            invert=invert_param,
            fill_color=args.fill_color,
            use_stroke=args.stroke,
            stroke_width=args.stroke_width,
            debug=args.debug
        )
    else:
        convert_png_to_svg(
            args.input, args.output,
            quality=args.quality,
            resolution=args.resolution,
            detail=args.detail,
            smooth=args.smooth,
            auto_crop=not args.no_crop,
            padding=args.padding,
            invert=invert_param,
            fill_color=args.fill_color,
            use_stroke=args.stroke,
            stroke_width=args.stroke_width,
            debug=args.debug
        )


if __name__ == '__main__':
    main()
