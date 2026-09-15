from pathlib import Path
from app.data.loader import DataLoader
from app.reporting.report_composer import ReportComposer
from app.core.config import settings
import traceback
import json

uploads = list(Path(settings.upload_dir).glob('*.csv'))
print(f"Total CSVs: {len(uploads)}")
latest = max(uploads, key=lambda p: p.stat().st_mtime)
print(f"Testing latest upload: {latest.name}")
frame = DataLoader().load_file(latest)
print(f"Columns: {list(frame.columns)}")




composer = ReportComposer()
try:
    rep = composer.compose_report(frame, dataset_id=latest.name, filename=latest.name)
    print("Report without mappings OK:", rep.report_id)
except Exception as e:
    print("ERROR without mappings:")
    traceback.print_exc()

# Test with simulated mappings
# Often mapping sends mappings where ignored=True, or empty target, or target duplicates
mock_mappings = [
    {"source": col, "target": col.lower().replace(" ", "_"), "ignored": False}
    for col in frame.columns
]
try:
    rep2 = composer.compose_report(frame, dataset_id=latest.name, filename=latest.name, mappings=mock_mappings)
    print("Report with simulated mappings OK:", rep2.report_id)
except Exception as e:
    print("ERROR with mappings:")
    traceback.print_exc()
