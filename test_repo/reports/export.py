"""Report export to various file formats.

Imports shared.config for export format settings.
"""

import json
import csv
import os

from shared.config import get


def export_report(report, filepath):
    """Export a report dict to the configured format."""
    fmt = get("export_format", "json")
    if fmt == "csv":
        return _to_csv(report, filepath)
    return _to_json(report, filepath)


def _to_json(report, filepath):
    """Write report as JSON."""
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
    return filepath


def _to_csv(report, filepath):
    """Write report as CSV."""
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        if report.get("headers"):
            writer.writerow(report["headers"])
        for row in report.get("rows", []):
            writer.writerow(row)
    return filepath


def get_export_path(filename):
    """Build an export path using the configured base directory."""
    base = get("export_dir", ".")
    return os.path.join(base, filename)

# --- Added by Agent C: Enhanced CSV export ---
def export_csv_with_options(report, filepath, delimiter=","):
    import csv
    with open(filepath, 'w', newline='') as f:
        w = csv.writer(f, delimiter=delimiter)
        if report.get("headers"): w.writerow(report["headers"])
        for row in report.get("rows", []): w.writerow(row)
    return filepath
