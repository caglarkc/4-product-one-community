# pyside6-deploy/Nuitka creates a native package on each target operating system.
# No cross-OS build or signing success is asserted by this source manifest.
[app]
title = STEP Tracker
project_dir = .
input_file = main.py
exec_directory = dist

[python]
python_path =
packages =

[qt]
modules = Core,Gui,Widgets
qml_files =
plugins =
excluded_qml_plugins =

[nuitka]
mode = standalone
extra_args = --include-package=step_tracker --include-package=mss --include-package=pynput --include-package=keyring --include-package=cryptography --include-package=requests --include-package=certifi --include-package-data=certifi --enable-plugin=pyside6 --follow-imports

