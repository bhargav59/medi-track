from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules

datas = collect_data_files('flet')
datas += copy_metadata('flet')
hiddenimports = collect_submodules('flet')
