"""Explicit native-host packaging entry point; never imports the tracker runtime."""
import argparse
import configparser
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="STEP native PySide6 deploy (run on the target OS)")
    parser.add_argument("--dry-run", action="store_true", help="Print pyside6-deploy's commands without building")
    args = parser.parse_args()
    if sys.platform not in ("win32", "darwin", "linux"):
        parser.error("Supported native build hosts: Windows, macOS, Linux")
    root = Path(__file__).resolve().parent
    spec = configparser.ConfigParser()
    spec.read(root / "pysidedeploy.spec")
    spec["app"]["project_dir"] = str(root)
    spec["app"]["input_file"] = str(root / "main.py")
    spec["app"]["exec_directory"] = str(root / "dist")
    spec["python"]["python_path"] = sys.executable
    extras = spec["nuitka"]["extra_args"]
    if sys.platform == "darwin":
        extras += " --macos-create-app-bundle --macos-app-name=STEPTracker --macos-app-version=0.1.0"
        extras += " --include-package=AppKit --include-package=Foundation --include-package=Quartz --include-package=ApplicationServices --include-package=objc"
    elif sys.platform == "win32":
        extras += " --windows-console-mode=disable"
    else:
        extras += " --include-package=Xlib --include-package=secretstorage --include-package=jeepney"
    spec["nuitka"]["extra_args"] = extras
    generated = root / "deployment"
    generated.mkdir(exist_ok=True)
    config = generated / ("pysidedeploy." + sys.platform + ".spec")
    with config.open("w", encoding="utf-8") as file:
        spec.write(file)
    command = [str(Path(sys.executable).with_name("pyside6-deploy.exe" if sys.platform == "win32" else "pyside6-deploy")),
               "-c", str(config), "--force"]
    if args.dry_run:
        command.append("--dry-run")
    return subprocess.call(command, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
