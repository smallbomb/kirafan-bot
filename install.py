from subprocess import check_call
from sys import platform, executable


def install(packages):
    for package in packages:
        check_call([executable, "-m", "pip", "install", package])


deps = [
    "opencv-python>=4.5.1.48",
    "keyboard>=0.13.5",
    "PyAutoGUI>=0.9.52",
    "typeguard>=2.10.0",
    "pygame>=2.0.1",
    "Pillow>=8.1.0",
]

if platform == 'win32':
    deps.append("pywin32>=300")
if platform.startswith('linux'):
    deps.append("python-xlib>=0.29")

install(deps)
