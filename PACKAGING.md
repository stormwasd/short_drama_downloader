# 打包说明

## 打包步骤

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 确保资源文件存在
- 确保 `resources/icon.ico` 文件存在（用于exe图标）

### 3. 执行打包
```bash
python build_exe.py
```

或者直接使用PyInstaller：
```bash
pyinstaller short_drama.spec
```

## 打包配置说明

### short_drama.spec
- **入口文件**: `src/main.py`
- **输出名称**: `Dramaseek.exe`
- **图标**: `resources/icon.ico`（如果存在）
- **数据文件**: 包含 `resources/icon.ico` 到打包后的 `resources/` 目录
- **隐藏导入**: 包含所有必要的模块（PyQt5、yt_dlp、requests等）
- **控制台**: 不显示控制台窗口（`console=False`）

### 打包后的文件结构
```
dist/
  └── Dramaseek.exe  (单个可执行文件)
```

### 注意事项
1. 打包后的exe是单个文件，包含所有依赖
2. 数据库文件会创建在exe所在目录
3. 图标文件已包含在exe中，会自动加载
4. 打包过程可能需要几分钟，请耐心等待

## 常见问题

### 1. 打包失败
- 检查所有依赖是否已安装
- 检查Python语法是否有错误
- 查看错误信息中的具体提示

### 2. exe文件过大
- 这是正常的，因为包含了Python解释器和所有依赖
- 通常大小在50-100MB左右

### 3. exe无法运行
- 确保目标系统是Windows
- 检查是否有杀毒软件拦截
- 查看是否有错误日志文件生成

