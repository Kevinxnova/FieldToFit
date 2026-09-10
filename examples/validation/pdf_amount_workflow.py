"""Reviewed entry point for the complete PDF amount task, no user code execution."""
import json
from pathlib import Path
import runpy
import tempfile

workflow = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'task_packets' / 'pdf_amount.py'))
with tempfile.TemporaryDirectory(prefix='fieldtofit-pdf-amount-') as folder:
    print(json.dumps(workflow['demo'](Path(folder)), ensure_ascii=False, indent=2))
