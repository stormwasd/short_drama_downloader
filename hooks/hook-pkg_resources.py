# PyInstaller hook to disable pkg_resources
# 这个hook会阻止PyInstaller自动导入pkg_resources，避免jaraco依赖问题

# 不收集任何pkg_resources相关的模块
hiddenimports = []
datas = []
binaries = []

