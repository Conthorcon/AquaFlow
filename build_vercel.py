"""Copy static vào public/static mỗi lần build để tránh deploy file cũ."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
shutil.copytree(ROOT / "web/static", ROOT / "public/static", dirs_exist_ok=True)
