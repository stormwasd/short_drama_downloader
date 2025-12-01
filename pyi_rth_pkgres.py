# PyInstaller runtime hook
# 禁用pkg_resources的自动导入，避免jaraco依赖问题
# 这个文件会覆盖PyInstaller默认的pyi_rth_pkgres.py

# 不执行任何pkg_resources相关的操作
# 这样可以避免jaraco依赖问题

