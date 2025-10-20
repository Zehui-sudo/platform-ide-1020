#!/usr/bin/env python3
"""
课程目录图标生成器
基于课程目录 JSON 生成适合下拉列表的迷你图标（16-20px）

python scripts/generate_course_icon.py output/reconstructed_outline/python-reconstructed-20251013-121143.json
"""

import argparse
import sys
from io import BytesIO
from google import genai
from PIL import Image, ImageChops
import os


def white_to_alpha(im: Image.Image, threshold: int = 0) -> Image.Image:
    """将白底转透明，保留线条抗锯齿"""
    im = im.convert("RGBA")
    r, g, b, a = im.split()
    # alpha = max(255-r, 255-g, 255-b)
    mask = ImageChops.lighter(
        ImageChops.invert(r),
        ImageChops.lighter(ImageChops.invert(g), ImageChops.invert(b)),
    )
    if threshold and threshold > 0:
        mask = mask.point(lambda p: 0 if p < threshold else p)
    im.putalpha(mask)
    return im


def generate_prompt(json_content):
    """根据 JSON 内容生成 prompt"""
    # 基础 prompt
    base_prompt = f"""你是一名资深图标设计师。请基于下面提供的"课程目录 JSON"产出一个专业的课程图标。

设计要求：
- 生成一个清晰、醒目的图标，线条要粗壮，轮廓要明显
- 线条粗细要足够粗，确保在小尺寸下也能清晰可见
- 图标主体要占画布的 70-80%，不要太小
- 使用纯黑色填充（#000000），白色背景
- 避免使用细线条和复杂细节
- 避免使用文字，用图形元素表达主题

课程目录 JSON：
{json_content}

请分析这个课程的核心主题，并生成一个专业的、有识别度的课程图标。图标应该：
1. 清晰地表达课程的核心概念（如 Python 异步编程可以用蛇形+循环箭头、时钟等元素组合）
2. 线条流畅，填充均匀
3. 具有现代感和专业性"""

    return base_prompt


def main():
    parser = argparse.ArgumentParser(description="基于课程目录 JSON 生成迷你图标")
    parser.add_argument("json_file", help="课程目录 JSON 文件路径")
    parser.add_argument("--out", "-o", default="course_icon.png", help="输出 PNG 路径")
    parser.add_argument("--threshold", "-t", type=int, default=5, help="白底转透明阈值（默认5，清理轻微噪点）")
    parser.add_argument("--model", "-m", default="gemini-2.5-flash-image", help="生成模型名")
    parser.add_argument("--size", "-s", type=int, default=512, help="生成图片的尺寸（默认512x512）")
    parser.add_argument("--white-bg", "-w", action="store_true", help="输出白底版本（不转为透明）")

    args = parser.parse_args()

    # 读取 JSON 文件
    try:
        with open(args.json_file, "r", encoding="utf-8") as f:
            json_content = f.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.json_file}", file=sys.stderr)
        sys.exit(1)

    # 生成 prompt
    prompt = generate_prompt(json_content)
    print(f"已读取课程目录文件: {args.json_file}")
    print("\n生成的 Prompt:")
    print("-" * 50)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("-" * 50)

    # 调用 Gemini API 生成图片
    try:
        client = genai.Client()
        response = client.models.generate_content(model=args.model, contents=[prompt])

        saved = False
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print("\n模型响应:", part.text)
            elif part.inline_data is not None:
                # 加载图片
                img = Image.open(BytesIO(part.inline_data.data))

                # 调整尺寸
                if img.size != (args.size, args.size):
                    img = img.resize((args.size, args.size), Image.Resampling.LANCZOS)

                # 增强对比度和加粗线条
                # 先转为黑白，增强对比
                img = img.convert("L")
                # 应用阈值使图像更清晰
                img = img.point(lambda x: 0 if x < 100 else 255, "1")
                # 转回 RGBA
                img = img.convert("RGBA")

                # 将黑色部分设为纯黑
                datas = img.getdata()
                new_data = []
                for item in datas:
                    # 如果接近黑色，设为纯黑
                    if item[0] < 128:
                        new_data.append((0, 0, 0, 255))
                    else:
                        # 根据是否保留白底决定 alpha 值
                        if args.white_bg:
                            new_data.append((255, 255, 255, 255))  # 白底不透明
                        else:
                            new_data.append((255, 255, 255, 0))    # 白底透明
                img.putdata(new_data)

                # 转换白底为透明（除非指定保留白底）
                if not args.white_bg:
                    img = white_to_alpha(img, threshold=args.threshold)

                # 确保输出目录存在
                os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

                # 保存图片
                img.save(args.out)
                print(f"\n✓ 图标已保存: {args.out}")
                saved = True
                break

        if not saved:
            raise RuntimeError("未收到图像数据，可能是模型未返回图片或调用失败。")

    except Exception as e:
        print(f"\n错误：生成图片失败 - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
