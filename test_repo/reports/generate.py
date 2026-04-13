"""Report generation from data sets.

Standalone module with no shared imports.
"""

import datetime
import statistics


def generate_report(data, title="Report"):
    """Build a report structure from a list of row dicts."""
    if not data:
        return {"title": title, "headers": [], "rows": [], "summary": {}}
    headers = list(data[0].keys())
    return {
        "title": title,
        "generated_at": datetime.datetime.now().isoformat(),
        "headers": headers,
        "rows": [list(row.values()) for row in data],
        "summary": _calculate_summary(data),
    }


def _calculate_summary(data):
    """Compute basic summary statistics for numeric columns."""
    summary = {"row_count": len(data)}
    if not data:
        return summary
    for key in data[0]:
        values = [row[key] for row in data if isinstance(row.get(key), (int, float))]
        if values:
            summary[f"{key}_mean"] = round(statistics.mean(values), 2)
            summary[f"{key}_total"] = sum(values)
    return summary


def _format_header(title):
    """Format a report header with timestamp."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"=== {title} === Generated: {now}"

# --- Added by Agent C: CSV report generation ---
def generate_csv_report(data, columns=None):
    if not data: return ""
    columns = columns or list(data[0].keys())
    lines = [",".join(columns)]
    for row in data: lines.append(",".join(str(row.get(c, "")) for c in columns))
    return "\n".join(lines)
