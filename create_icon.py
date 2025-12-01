"""
创建应用图标
使用PIL创建一个简单的图标文件
"""
try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    # 创建64x64的图标
    size = 64
    img = Image.new('RGB', (size, size), color='#4CAF50')
    draw = ImageDraw.Draw(img)
    
    # 绘制一个简单的播放图标（三角形）
    triangle_points = [
        (size * 0.3, size * 0.2),
        (size * 0.3, size * 0.8),
        (size * 0.7, size * 0.5)
    ]
    draw.polygon(triangle_points, fill='white')
    
    # 保存为ICO格式
    icon_path = os.path.join('resources', 'icon.ico')
    img.save(icon_path, format='ICO', sizes=[(64, 64)])
    print(f"图标已创建: {icon_path}")
    
except ImportError:
    print("需要安装Pillow库: pip install Pillow")
except Exception as e:
    print(f"创建图标失败: {e}")

