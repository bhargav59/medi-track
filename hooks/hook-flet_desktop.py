from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules

datas = collect_data_files('flet_desktop')
datas += copy_metadata('flet_desktop')
hiddenimports = collect_submodules('flet_desktop')
