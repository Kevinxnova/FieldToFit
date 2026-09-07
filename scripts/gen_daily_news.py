"""Compatibility entry point for the legacy maintenance workflow."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "maintenance/legacy/gen_daily_news.py"), run_name="__main__")
