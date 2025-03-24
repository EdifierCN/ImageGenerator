import os
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin, ImageFilter


def create_custom_image(
        output_path: str = 'temp.png',
        width: int = 1,
        height: int = 1,
        target_size: float = 1,
        format: str = 'PNG',
        background_color: tuple = (255, 255, 255),
        background_image: str = None,
        text: str = None,
        text_color: tuple = (255, 255, 255),
        font_path: str = None,
        font_size: int = 30,
        resize_method: str = 'cover',
        circle_mask: bool = False,
):
    """
    生成指定尺寸、格式、文件大小的图片，支持背景色/背景图、文字叠加和圆形裁剪

    Args:
        width (int): 图片宽度（默认1px）
        height (int): 图片高度（默认1px）
        target_size (float): 目标文件大小（MB，默认1MB）
        format (str): 图片格式（支持 'PNG', 'JPEG', 'BMP', 'WEBP' 等）
        background_color (tuple): 纯色背景RGB值（如 (255,255,255)）
        background_image (str): 背景图片路径或URL
        text (str): 需要添加的文本内容
        text_color (tuple): 文字颜色RGB值（如 (0,0,0)）
        font_path (str): 字体文件路径
        font_size (int): 文字字体大小
        resize_method (str):
            - 'cover': 缩放填充目标尺寸（可能变形）
            - 'contain': 缩放保持比例居中（可能留白）
            - 'none': 保持原图尺寸
            - 'fill': 短边贴边，长边居中裁剪
        circle_mask (bool): 是否裁剪为圆形（需要正方形尺寸）
    """

    # 1. 创建基础图片
    try:
        if background_image:
            # 加载背景图片
            if background_image.startswith('http'):
                import requests
                response = requests.get(background_image, timeout=10)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content)).convert('RGB')
            else:
                img = Image.open(background_image).convert('RGB')

            # 处理缩放
            if resize_method == 'cover':
                img = img.resize((width, height), resample=Image.Resampling.LANCZOS)
            elif resize_method == 'contain':
                img.thumbnail((width, height), resample=Image.Resampling.LANCZOS)
                left = int((img.width - width) // 2)
                top = int((img.height - height) // 2)
                right = int(left + width)
                bottom = int(top + height)
                img = img.crop((left, top, right, bottom))
            elif resize_method == 'fill':
                img = fill_resize(img, width, height)
            elif resize_method == 'none':
                width, height = img.size
            else:
                raise ValueError("无效的resize_method参数")
        else:
            # 使用纯色背景
            img = Image.new('RGB', (width, height), color=background_color)

        # 根据圆形裁剪需求转换模式
        if circle_mask:
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')
    except Exception as e:
        print(f"背景处理失败：{e}\n回退到纯色背景")
        img = Image.new('RGB', (width, height), color=background_color)

    # 2. 添加文字（如果需要）
    if text:
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.load_default(size=font_size)

            draw = ImageDraw.Draw(img)

            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            print(f"文字尺寸：{text_width}、{text_height}、{font_size}")

            # 计算文字位置，修正基线偏移
            pos_x = (img.width - text_width) // 2
            pos_y = (img.height - text_height) // 2 - text_bbox[1]  # 修正基线偏移

            draw.text(
                (pos_x, pos_y),
                text,
                fill=text_color,
                font=font,
                align='center'
            )
        except Exception as e:
            print(f"文字添加失败：{e}\n跳过文字添加")

    # 3. 应用圆形裁剪（抗锯齿优化）
    if circle_mask:
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, width - 1, height - 1), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(0))
        mask = mask.resize((width, height), resample=Image.Resampling.LANCZOS)
        img.putalpha(mask)
        img = img.filter(ImageFilter.SMOOTH_MORE)

    # 4. 格式兼容性处理
    format_upper = format.upper()

    if format_upper == 'JPEG':
        img = img.convert('RGB')

    # 5. 保存基础图片前创建目录
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # 自动创建目录

    # 5. 保存基础图片
    img.save(output_path, format=format.upper(), quality=100)

    # 6. 计算需要填充的字节数
    current_size = os.path.getsize(output_path)
    target_bytes = target_size
    required_padding = int(target_bytes - current_size)

    if format_upper == 'PNG':
        required_padding = required_padding - 28

    print(f"图片尺寸：{target_bytes}，当前大小：{current_size}字节，需要填充：{required_padding}字节")

    # 符合目标大小
    if required_padding == 0:
        img.save(output_path, format)
        return

    # 7. 根据格式选择填充方式
    if format_upper == 'PNG':
        metadata = b'A' * required_padding
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("Custom_Metadata", metadata.decode(), zip=False)
        img.save(output_path, format='PNG', pnginfo=pnginfo)
    else:
        with open(output_path, 'ab') as f:
            f.write(b'\x00' * required_padding)


def fill_resize(img, target_width, target_height):
    """
    短边贴边，长边居中裁剪的缩放逻辑
    """
    img_width, img_height = img.size
    target_ratio = target_width / target_height
    img_ratio = img_width / img_height

    if img_ratio > target_ratio:
        # 图片更宽，以高度为基准缩放
        new_height = target_height
        new_width = int(img_width * (new_height / img_height))
        img = img.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)
        left = (new_width - target_width) // 2
        img = img.crop((int(left), 0, int(left + target_width), target_height))
    else:
        # 图片更高，以宽度为基准缩放
        new_width = target_width
        new_height = int(img_height * (new_width / img_width))
        img = img.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)
        top = (new_height - target_height) // 2
        img = img.crop((0, int(top), target_width, int(top + target_height)))
    return img
