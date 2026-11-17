#!/usr/bin/env python3
"""Build the minimal static site bundle for the explicitly authorized Pages upload.

The bundle intentionally excludes the raw input, ETL source, tests, and git metadata.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def build_static_site() -> list[str]:
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "assets").mkdir(parents=True)
    (SITE / "deliverables").mkdir(parents=True)
    shutil.copy2(ROOT / "index.html", SITE / "index.html")
    shutil.copy2(ROOT / "assets" / "etl_architecture_diagram.svg", SITE / "assets" / "etl_architecture_diagram.svg")
    for name in (
        "WK_B2B_Cleaned_Leads_Sample.csv",
        "WK_B2B_Cleaned_Leads_Sample.xlsx",
        "WK_B2B_Cleaned_Leads_Sample.json",
        "cleaning_audit_report.json",
    ):
        shutil.copy2(ROOT / "deliverables" / name, SITE / "deliverables" / name)
    return [str(path.relative_to(SITE)) for path in sorted(SITE.rglob("*")) if path.is_file()]


if __name__ == "__main__":
    files = build_static_site()
    print(f"Built {SITE} with {len(files)} files:")
    for name in files:
        print(f"- {name}")
