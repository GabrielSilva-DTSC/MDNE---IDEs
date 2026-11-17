from pathlib import Path
from runpy import run_path


run_path(str(Path(__file__).resolve().parents[1] / "app_etapa2.py"))
