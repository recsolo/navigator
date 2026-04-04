from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
DESKTOP_DIR = ROOT / "desktop"
LAUNCHER = DESKTOP_DIR / "backend_launcher.py"
DIST_DIR = DESKTOP_DIR / "dist-backend"
BUILD_DIR = DESKTOP_DIR / "build-tmp"
CATALOG_FILE = BACKEND_DIR / "app" / "data" / "tool_catalog.json"


BACKEND_EXE_NAME = "navigator-backend"
LEGACY_BACKEND_EXE_NAME = "navagator-backend"


def main() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        BACKEND_EXE_NAME,
        "--paths",
        str(BACKEND_DIR),
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR / "work"),
        "--specpath",
        str(BUILD_DIR / "spec"),
        "--collect-submodules",
        "uvicorn",
        "--collect-submodules",
        "fastapi",
        "--collect-submodules",
        "starlette",
        "--collect-submodules",
        "pydantic",
        "--collect-submodules",
        "anyio",
        "--add-data",
        f"{CATALOG_FILE};app/data",
        str(LAUNCHER),
    ]

    print("Building backend executable with PyInstaller...")
    subprocess.run(command, check=True, cwd=ROOT)

    legacy_exe = DIST_DIR / f"{LEGACY_BACKEND_EXE_NAME}.exe"
    new_exe = DIST_DIR / f"{BACKEND_EXE_NAME}.exe"
    if legacy_exe.exists() and not new_exe.exists():
        legacy_exe.rename(new_exe)

    print(f"Built backend executable at {new_exe}")


if __name__ == "__main__":
    main()
