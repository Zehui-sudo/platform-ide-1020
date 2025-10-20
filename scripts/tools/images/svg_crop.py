#!/usr/bin/env python3
"""
SVG 裁剪工具：移除多余空白，让图形贴近边缘
"""

import argparse
import re
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_path_data(path_str):
    """解析 SVG 路径数据，提取所有坐标"""
    # 简单的正则表达式解析
    # 匹配数字（包括小数）
    numbers = re.findall(r"[-+]?\d*\.?\d+", path_str)
    coords = [float(n) for n in numbers]

    # 将坐标配对
    points = []
    for i in range(0, len(coords), 2):
        if i + 1 < len(coords):
            points.append((coords[i], coords[i + 1]))

    return points


def find_bounds(svg_content):
    """找到所有路径的边界"""
    x_min = float('inf')
    y_min = float('inf')
    x_max = float('-inf')
    y_max = float('-inf')

    # 查找所有 path 元素
    path_pattern = r'<path[^>]*d="([^"]*)"[^>]*>'
    paths = re.findall(path_pattern, svg_content)

    for path_data in paths:
        points = parse_path_data(path_data)
        for x, y in points:
            x_min = min(x_min, x)
            y_min = min(y_min, y)
            x_max = max(x_max, x)
            y_max = max(y_max, y)

    return x_min, y_min, x_max, y_max


def crop_svg(input_path, output_path, padding=20):
    """裁剪 SVG，移除多余空白"""
    # 读取文件
    with open(input_path, 'r') as f:
        content = f.read()

    # 找到当前边界
    x_min, y_min, x_max, y_max = find_bounds(content)

    print(f"原始边界: x={x_min:.1f}, y={y_min:.1f}, x_max={x_max:.1f}, y_max={y_max:.1f}")

    # 计算偏移量和缩放
    width = x_max - x_min
    height = y_max - y_min

    # SVG 的画布大小
    svg_size = 1024

    # 计算缩放比例（留出 padding）
    available_size = svg_size - 2 * padding
    scale_x = available_size / width if width > 0 else 1
    scale_y = available_size / height if height > 0 else 1
    scale = min(scale_x, scale_y)  # 使用较小的缩放比例以保持比例

    # 计算居中的偏移
    scaled_width = width * scale
    scaled_height = height * scale
    offset_x = (svg_size - scaled_width) / 2 - x_min * scale
    offset_y = (svg_size - scaled_height) / 2 - y_min * scale

    print(f"缩放比例: {scale:.2f}")
    print(f"偏移: x={offset_x:.1f}, y={offset_y:.1f}")

    # 转换所有路径
    def transform_path(match):
        path_data = match.group(1)
        points = parse_path_data(path_data)

        # 应用变换
        transformed_points = []
        for x, y in points:
            new_x = x * scale + offset_x
            new_y = y * scale + offset_y
            transformed_points.extend([new_x, new_y])

        # 重新构建路径
        # 简单替换坐标值
        new_path = path_data
        numbers = re.findall(r"[-+]?\d*\.?\d+", path_data)
        for i, num in enumerate(numbers):
            if i < len(transformed_points):
                new_path = new_path.replace(num, f"{transformed_points[i]:.1f}", 1)

        return match.group(0).replace(match.group(1), new_path)

    # 应用变换
    content = re.sub(r'<path[^>]*d="([^"]*)"[^>]*>', transform_path, content)

    # 保存新文件
    with open(output_path, 'w') as f:
        f.write(content)

    print(f"✓ 已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="SVG 裁剪工具 - 移除多余空白")
    parser.add_argument("input", help="输入 SVG 文件")
    parser.add_argument("-o", "--output", help="输出 SVG 文件")
    parser.add_argument("-p", "--padding", type=int, default=20, help="边距大小")

    args = parser.parse_args()

    if not args.output:
        path = Path(args.input)
        args.output = path.parent / f"{path.stem}_cropped.svg"

    crop_svg(args.input, args.output, args.padding)


if __name__ == "__main__":
    main()
