import math
import os
import platform
import shutil
from datetime import datetime  # 导入 datetime 模块

import wx
import wx.lib.colourselect as colourselect
from PIL import Image

from create_image import create_custom_image


class ImageGeneratorUI(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(900, 720))
        self.panel = wx.Panel(self)
        self.params = {}
        self.preview_size = (500, 500)
        self.create_widgets()

    def create_widgets(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 左侧参数面板
        input_panel = wx.Panel(self.panel)
        input_sizer = wx.BoxSizer(wx.VERTICAL)
        input_panel.SetSizer(input_sizer)

        # 基础设置
        self.add_param_group(input_sizer, "基础设置", [
            ("宽度", wx.SpinCtrl, None, None, 1, 4096, 800),
            ("高度", wx.SpinCtrl, None, None, 1, 4096, 800),
            ("目标大小", [
                wx.SpinCtrlDouble,
                wx.Choice,
                {
                    "min": 0.0,
                    "max": 104857600,
                    "initial": 1.0,
                    "inc": 0.1,
                    "choices": ["B", "KB", "MB", "GB"],
                    "default_choice": 2  # 默认选中MB
                }
            ], None, None, 0, 104857600, 1.0),
            ("格式", wx.Choice, None, wx.EVT_CHOICE, [
                "PNG",
                "JPEG",
                "BMP",
                "GIF",
                "WEBP",
                "ICO",
                "TIFF",
            ])
        ])

        # 背景设置
        self.add_param_group(input_sizer, "背景设置", [
            ("背景颜色", colourselect.ColourSelect, None, colourselect.EVT_COLOURSELECT, wx.WHITE),
            ("背景图片", wx.TextCtrl, None, None),  # 移除 on_background_image
            ("缩放方式", wx.Choice, None, wx.EVT_CHOICE, ['fill', 'cover', 'contain', 'none'])
        ])

        # 文字设置
        self.add_param_group(input_sizer, "文字设置", [
            ("文字内容", wx.TextCtrl, None, None),
            ("文字颜色", colourselect.ColourSelect, None, colourselect.EVT_COLOURSELECT, wx.BLACK),
            ("字体路径", wx.TextCtrl, None, None, self.get_default_font_path()),
            ("字体大小", wx.SpinCtrl, None, None, 1, 10000, 30)
        ])

        # 高级选项
        advanced_sizer = wx.StaticBoxSizer(wx.VERTICAL, input_panel, "高级选项")
        self.circle_mask_checkbox = wx.CheckBox(input_panel, label="圆形")
        self.circle_mask_checkbox.Bind(wx.EVT_CHECKBOX, self.on_param_changed)  # 关键：绑定事件
        advanced_sizer.Add(self.circle_mask_checkbox, 0, wx.ALL | wx.EXPAND, 5)

        input_sizer.Add(advanced_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # 右侧预览面板
        preview_panel = wx.Panel(self.panel)
        preview_sizer = wx.BoxSizer(wx.VERTICAL)
        self.preview_bitmap = wx.StaticBitmap(preview_panel)
        preview_panel.SetSizer(preview_sizer)
        preview_panel.SetBackgroundColour(wx.NullColour)

        # 生成按钮容器（放在预览面板底部）
        btn_container = wx.Panel(preview_panel)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_container.SetSizer(btn_sizer)

        # 创建生成按钮（移出左侧参数面板）
        self.generate_btn = wx.Button(btn_container, label="保存图片", size=(180, 40), style=wx.BORDER_NONE)
        self.generate_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        self.generate_btn.SetForegroundColour(wx.WHITE)
        self.generate_btn.Bind(wx.EVT_BUTTON, self.on_generate)
        btn_sizer.AddStretchSpacer()  # 水平拉伸占位
        btn_sizer.Add(self.generate_btn, 0, wx.ALL, 10)

        # 预览面板布局调整
        preview_sizer.Add(self.preview_bitmap, 1, wx.ALL | wx.CENTER, 10)
        preview_sizer.Add(btn_container, 0, wx.BOTTOM | wx.RIGHT | wx.LEFT | wx.ALIGN_RIGHT, 10)

        # 主布局
        main_sizer.Add(input_panel, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(preview_panel, 1, wx.EXPAND | wx.ALL, 10)
        self.panel.SetSizer(main_sizer)
        self.Center()
        self.Show()

        self.update_preview()

    def add_param_group(self, parent_sizer, title, items):
        container = parent_sizer.GetContainingWindow()
        group = wx.StaticBoxSizer(wx.VERTICAL, container, title)
        grid = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

        for item in items:
            label_text, widget_type, handler, event, *params = item
            label = wx.StaticText(container, label=label_text)
            grid.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

            if widget_type == wx.TextCtrl:
                if params:
                    widget = wx.TextCtrl(container, value=params[0], size=(100, -1))
                else:
                    widget = wx.TextCtrl(container, size=(100, -1))
                widget.Bind(wx.EVT_TEXT, self.on_param_changed)
                grid.Add(widget, 0, wx.ALL | wx.EXPAND, 5)
                self.params[label_text] = widget

            elif widget_type == wx.SpinCtrl:
                widget = wx.SpinCtrl(container, min=params[0], max=params[1], initial=params[2])
                widget.Bind(wx.EVT_SPINCTRL, self.on_param_changed)
                grid.Add(widget, 0, wx.ALL | wx.EXPAND, 5)
                self.params[label_text] = widget

            elif widget_type == wx.SpinCtrlDouble:
                widget = wx.SpinCtrlDouble(
                    container,
                    min=params[0],
                    max=params[1],
                    initial=params[2],
                    inc=0.1
                )
                widget.SetDigits(2)
                widget.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_param_changed)
                grid.Add(widget, 0, wx.ALL | wx.EXPAND, 5)
                self.params[label_text] = widget

            elif widget_type == wx.Choice:
                widget = wx.Choice(container, choices=params[0])
                widget.SetSelection(0)
                widget.Bind(wx.EVT_CHOICE, self.on_param_changed)
                grid.Add(widget, 0, wx.ALL | wx.EXPAND, 5)
                self.params[label_text] = widget

            elif widget_type == colourselect.ColourSelect:
                # 处理颜色选择控件
                initial_color = params[0] if params else wx.WHITE
                widget = colourselect.ColourSelect(
                    container,
                    colour=initial_color,
                    size=(100, 25),
                    style=wx.BORDER_NONE
                )
                widget.SetBackgroundColour(wx.WHITE)
                widget.Bind(colourselect.EVT_COLOURSELECT, self.on_param_changed)
                grid.Add(widget, 0, wx.ALL | wx.EXPAND, 5)
                self.params[label_text] = widget

            elif isinstance(widget_type, list) and len(widget_type) >= 2:
                # 处理组合控件（如目标大小）
                widgets = []
                params_dict = widget_type[-1]
                for idx, sub_type in enumerate(widget_type[:-1]):
                    if sub_type == wx.SpinCtrlDouble:
                        widget = wx.SpinCtrlDouble(
                            container,
                            min=params[0],
                            max=params[1],
                            initial=params[2],
                            inc=params_dict.get("inc", 0.1)
                        )
                        widget.SetDigits(2)
                        widgets.append(widget)
                    elif sub_type == wx.Choice:
                        widget = wx.Choice(
                            container,
                            choices=params_dict["choices"]
                        )
                        default_choice = params_dict.get("default_choice", 0)
                        widget.SetSelection(default_choice)
                        widgets.append(widget)
                    # 绑定事件
                    widget.Bind(wx.EVT_SPINCTRLDOUBLE if sub_type == wx.SpinCtrlDouble else wx.EVT_CHOICE,
                                self.on_param_changed)

                # 使用水平布局组合控件
                hbox = wx.BoxSizer(wx.HORIZONTAL)
                for w in widgets:
                    hbox.Add(w, 0, wx.ALL | wx.EXPAND, 5)
                grid.Add(hbox, 0, wx.ALL | wx.EXPAND, 5)
                self.params[label_text] = {
                    "spin": widgets[0],
                    "unit": widgets[1]
                }

            else:
                # 其他未处理的控件类型
                print(f"未处理的控件类型：{widget_type}")
                continue

            # 添加浏览按钮
            if label_text in ["背景图片", "字体路径"]:
                browse_btn = wx.Button(container, label="浏览")
                browse_btn.Bind(wx.EVT_BUTTON, lambda e, key=label_text: self.on_browse(e, key))
                grid.Add(browse_btn, 0, wx.ALL, 5)
            else:
                grid.AddSpacer(5)

        # 确保每行有3个元素（label + 控件 + 浏览按钮或占位符）
        while grid.GetItemCount() % 3 != 0:
            grid.AddSpacer(0)

        group.Add(grid, 0, wx.ALL | wx.EXPAND, 5)
        parent_sizer.Add(group, 0, wx.ALL | wx.EXPAND, 10)

    def get_default_font_path(self):
        """根据系统返回默认字体路径"""
        system = platform.system()
        if system == "Windows":
            return "C:/Windows/Fonts/simsun.ttc"
        elif system == "Darwin":
            return "/System/Library/Fonts/PingFang.ttc"
        elif system == "Linux":
            return "/usr/share/fonts/noto/NOTO_SANS_CJK_BOLD.TTF"
        else:
            return ""  # 未知系统返回空字符串

    def on_param_changed(self, event):
        self.update_preview()
        event.Skip()

    def on_background_color(self, event):
        self.update_preview()
        event.Skip()

    def on_text_color(self, event):
        self.update_preview()
        event.Skip()

    def on_browse(self, event, var_key):
        if var_key in ["背景图片", "字体路径"]:
            dlg = wx.FileDialog(
                self,
                "选择文件",
                style=wx.FD_OPEN
            )
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.params[var_key].SetValue(path)
                self.update_preview()

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
            img = img.crop((int(left), 0, int(left + target_width), target_height))  # 添加int转换
        else:
            # 图片更高，以宽度为基准缩放
            new_width = target_width
            new_height = int(img_height * (new_width / img_width))
            img = img.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)
            top = (new_height - target_height) // 2
            img = img.crop((0, int(top), target_width, int(top + target_height)))  # 添加int转换
        return img

    def get_params(self):
        # 获取脚本所在目录的绝对路径
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))

        format = self.params["格式"].GetStringSelection()
        output_path = os.path.join(BASE_DIR, f".temp/preview.{format.lower()}")

        print(f"output_path:{output_path}")

        # 处理目标大小的单位转换
        spin = self.params["目标大小"]["spin"]
        unit = self.params["目标大小"]["unit"].GetStringSelection()
        target_size = math.ceil(spin.GetValue()) * {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3
        }.get(unit, 1)

        print(f"target_size:{target_size}")

        return {
            'output_path': output_path,
            'width': int(self.params["宽度"].GetValue()),  # 强制转换为int
            'height': int(self.params["高度"].GetValue()),  # 强制转换为int
            'target_size': target_size,
            'format': format,
            'background_color': tuple(
                self.params["背景颜色"].GetColour().Get()[:3]  # 直接获取RGB元组
            ),
            'background_image': self.params["背景图片"].GetValue(),
            'text': self.params["文字内容"].GetValue(),
            'text_color': tuple(
                self.params["文字颜色"].GetColour().Get()[:3]
            ),
            'font_path': self.params["字体路径"].GetValue(),
            'font_size': int(self.params["字体大小"].GetValue()),  # 强制转换为int
            'resize_method': self.params["缩放方式"].GetStringSelection(),
            'circle_mask': self.circle_mask_checkbox.GetValue()
        }

    def update_preview(self):
        try:
            preview_params = self.get_params()

            print(f"update_preview：{preview_params}")

            output_path = preview_params['output_path']
            format = preview_params['format']

            # 生成图像字节流
            create_custom_image(**preview_params)

            # 在 update_preview 方法中：
            if format.upper() == 'SVG':
                # 使用 cairosvg 将SVG转换为PNG预览
                from cairosvg import svg2png
                import io

                # 生成临时PNG预览
                png_data = svg2png(file_obj=open(output_path, 'rb'))
                pil_image = Image.open(io.BytesIO(png_data))
            else:
                pil_image = Image.open(output_path)

            # 处理PIL到wx.Image的转换
            if pil_image.mode == 'RGBA':
                wx_image = wx.Image(pil_image.width, pil_image.height)
                wx_image.SetData(pil_image.convert("RGB").tobytes())
                wx_image.SetAlpha(pil_image.getchannel("A").tobytes())
            else:
                wx_image = wx.Image(pil_image.width, pil_image.height)
                wx_image.SetData(pil_image.convert("RGB").tobytes())

            # 异常处理：加载失败时显示错误提示
            if not wx_image.IsOk():
                raise ValueError("无法加载生成的图像")

            # 动态计算缩放后的尺寸
            img_width = pil_image.width
            img_height = pil_image.height

            # 计算缩放比例（保持宽高比）
            scale_w = self.preview_size[0] / img_width
            scale_h = self.preview_size[1] / img_height
            scale = min(scale_w, scale_h)  # 取较小的缩放比例

            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            scaled_image = wx_image.Scale(
                new_width,
                new_height,
                wx.IMAGE_QUALITY_HIGH
            )

            # 创建居中显示的 Bitmap
            preview_bitmap = scaled_image.ConvertToBitmap()
            self.preview_bitmap.SetBitmap(preview_bitmap)
            self.preview_bitmap.SetSize(preview_bitmap.GetSize())

            # 强制Sizer重新布局
            if self.preview_bitmap.GetContainingSizer():
                self.preview_bitmap.GetContainingSizer().Layout()

        except Exception as e:
            # 显示错误提示并清空预览
            self.preview_bitmap.SetBitmap(wx.NullBitmap)
            print(e)

    def on_generate(self, event):
        try:
            preview_params = self.get_params()
            temp_path = preview_params['output_path']
            format = preview_params['format'].upper()

            # 使用 PIL 打开生成的图片
            pil_image = Image.open(temp_path)

            # 将 PIL.Image 转换为 wx.Image
            width, height = pil_image.size

            size = os.path.getsize(temp_path)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            default_filename = f"image_{timestamp}.{format.lower()}"

            with wx.FileDialog(
                    self,
                    "保存生成的图片",
                    wildcard="All files (*.*)|*.*|"
                             "PNG files (*.png)|*.png|"
                             "JPEG files (*.jpg)|*.jpg",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                    defaultFile=default_filename
            ) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    output_path = dlg.GetPath()

                    # 自动补全文件扩展名（如果未指定）
                    if not output_path.lower().endswith((format.lower(), f".{format.lower()}")):
                        output_path += f".{format.lower()}"

                    # 直接保存缓存的 actual_image
                    if size:
                        # 检查临时文件是否存在
                        if os.path.exists(temp_path):
                            # 复制临时文件到目标路径
                            shutil.copy2(temp_path, output_path)
                        else:
                            raise ValueError("预览图片未生成，请先调整参数！")
                    else:
                        raise ValueError("预览图片未生成，请先调整参数！")
                else:
                    print("保存操作已取消")
        except Exception as e:
            wx.GenericMessageDialog(
                self,
                str(e),
                "错误"
            ).ShowModal()


if __name__ == "__main__":
    app = wx.App()
    frame = ImageGeneratorUI(None, "图片生成器")
    frame.Show()
    app.MainLoop()
