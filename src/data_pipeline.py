#!/usr/bin/env python3
"""Deterministic synthetic B2B sample ETL for the WK Digital Operations showcase.

This project intentionally does not scrape a real directory. All names, contact
fields, websites, phones, and figures are generated synthetic examples.
"""
from __future__ import annotations

import argparse
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data" / "raw_scrape_dump.csv"
DEFAULT_OUT = ROOT / "deliverables"
EXPECTED_COLUMNS = [
    "Company_ID", "Company_Name", "Industry", "City_State", "Website",
    "Public_Contact_Email", "Phone", "Employee_Range",
    "Tech_Stack_Detected", "Data_Quality_Score", "Record_Provenance",
]
TEXT_FIELDS = [c for c in EXPECTED_COLUMNS if c not in {"Data_Quality_Score"}]

ADJECTIVES = [
    "Northstar", "Brightline", "Cedar", "Clearpath", "Cloudcrest",
    "Copperleaf", "Evergreen", "Fieldstone", "Keystone", "Lighthouse",
    "Meridian", "Pinecone", "Silverline", "Summit", "Westbridge",
]
NOUNS = [
    "Atlas", "Beacon", "Cascade", "Cobalt", "Compass", "Everest",
    "Harbor", "Juniper", "Nimble", "Orbit", "Pioneer", "Quartz",
    "Rivet", "Spruce", "Vertex", "Waypoint", "Willow", "Zenith",
]
SUFFIXES = ["Analytics", "Systems", "Labs", "Networks", "Solutions"]
INDUSTRIES = ["B2B SaaS", "E-commerce", "Logistics", "FinTech"]
CITIES = [
    ("Austin, TX", "512"), ("Boston, MA", "617"), ("Calgary, AB", "403"),
    ("Chicago, IL", "312"), ("Denver, CO", "303"), ("Miami, FL", "305"),
    ("Montreal, QC", "514"), ("New York, NY", "212"), ("Ottawa, ON", "613"),
    ("Phoenix, AZ", "602"), ("Portland, OR", "503"), ("San Diego, CA", "619"),
    ("Seattle, WA", "206"), ("Toronto, ON", "416"), ("Vancouver, BC", "604"),
]
EMPLOYEE_RANGES = ["1-10", "11-50", "51-200", "201-500", "501-1,000"]
STACKS = [
    "AWS, HubSpot, Snowflake", "Azure, Salesforce, Power BI",
    "Shopify, Segment, BigQuery", "GCP, PostgreSQL, Looker",
    "n8n, REST API, PostgreSQL", "Stripe, HubSpot, Metabase",
    "Python, dbt, Snowflake", "Shopify, Klaviyo, AWS",
    "Salesforce, Zapier, Airtable", "FastAPI, Docker, BigQuery",
]


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-+", "-", slug)


def build_synthetic_records() -> list[dict[str, str]]:
    """Create 150 unique, fictional North American B2B company records."""
    rng = random.Random(20261117)
    name_pool = [
        f"{adjective} {noun} {suffix}"
        for adjective in ADJECTIVES
        for noun in NOUNS
        for suffix in SUFFIXES
    ]
    records: list[dict[str, str]] = []
    for i, name in enumerate(name_pool[:150]):
        city, area_code = CITIES[i % len(CITIES)]
        slug = _slug(name)
        last_four = 100 + (i // len(CITIES))  # stays in the reserved 555-0100..0199 range
        phone = f"+1 ({area_code}) 555-{last_four:04d}"
        records.append({
            "Company_ID": f"B2B-{i + 1:04d}",
            "Company_Name": name,
            "Industry": INDUSTRIES[i % len(INDUSTRIES)],
            "City_State": city,
            "Website": f"https://www.{slug}.example",
            "Public_Contact_Email": f"contact@{slug}.example",
            "Phone": phone,
            "Employee_Range": EMPLOYEE_RANGES[(i * 3) % len(EMPLOYEE_RANGES)],
            "Tech_Stack_Detected": STACKS[(i * 7) % len(STACKS)],
            "Data_Quality_Score": "",
            "Record_Provenance": "SYNTHETIC_SAMPLE",
        })
    return records


def create_raw_dump(path: Path = DEFAULT_RAW) -> int:
    """Write a deterministic raw-style file with known formatting defects/duplicates."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_synthetic_records()
    # Introduce realistic, intentionally recoverable formatting inconsistencies.
    for i, row in enumerate(rows):
        if i % 11 == 0:
            row["Company_Name"] = f"  {row['Company_Name']}  "
        if i % 14 == 2:
            row["City_State"] = f" {row['City_State']} "
        if i % 9 == 1:
            row["Phone"] = re.sub(r"\D", "", row["Phone"])
        if i % 13 == 4:
            row["Website"] = row["Website"].replace("https://", "htps:/", 1)
        if i % 17 == 3:
            row["Public_Contact_Email"] = f" {row['Public_Contact_Email'].upper()} "
        if i % 19 == 5:
            row["Tech_Stack_Detected"] = f" {row['Tech_Stack_Detected']} "
    raw_rows = list(rows)
    for i in range(12):
        duplicate = dict(rows[i])
        duplicate["Company_ID"] = f" {duplicate['Company_ID'].lower()} "
        if i % 2 == 0:
            duplicate["Company_Name"] = f" {duplicate['Company_Name']} "
        raw_rows.append(duplicate)
    pd.DataFrame(raw_rows, columns=EXPECTED_COLUMNS).to_csv(path, index=False)
    return len(raw_rows)


def _clean_phone(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return ""
    return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def _clean_website(value: Any) -> str:
    """Repair protocol typos/missing schemes only for the reserved .example domain."""
    text = str(value or "").strip().lower()
    match = re.search(r"((?:www\.)?[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.example)\b", text)
    if not match:
        return ""
    host = match.group(1)
    if not host.startswith("www."):
        host = f"www.{host}"
    return f"https://{host}"


def _clean_record(row: dict[str, Any]) -> tuple[dict[str, str], dict[str, int]]:
    cleaned = {key: str(row.get(key, "") if row.get(key, "") is not None else "").strip() for key in TEXT_FIELDS}
    cleaned["Company_ID"] = cleaned["Company_ID"].upper()
    cleaned["Public_Contact_Email"] = cleaned["Public_Contact_Email"].lower()
    cleaned["Website"] = _clean_website(cleaned["Website"])
    cleaned["Phone"] = _clean_phone(cleaned["Phone"])
    cleaned["Record_Provenance"] = "SYNTHETIC_SAMPLE"
    changes = {
        field: int(str(row.get(field, "") or "") != cleaned[field])
        for field in TEXT_FIELDS
        if field != "Record_Provenance"
    }
    return cleaned, changes


def _valid_website(value: str) -> bool:
    return bool(re.fullmatch(r"https://www\.[a-z0-9]+(?:-[a-z0-9]+)*\.example", value))


def _valid_phone(value: str) -> bool:
    return bool(re.fullmatch(r"\+1 \(\d{3}\) 555-01\d{2}", value))


def _write_excel(df: pd.DataFrame, report: dict[str, Any], path: Path) -> None:
    summary_rows = [
        ("Records in sample", report["final_records"]),
        ("Duplicate rows removed", report["duplicate_rows_removed"]),
        ("Fields repaired", report["correction_counts"]["field_values_normalized"]),
        ("Final row validation", f"{report['validation']['valid_rows']}/{report['final_records']} rows"),
        ("Schema completeness", f"{report['validation']['schema_completeness_pct']:.1f}%"),
        ("Mean data quality score", f"{report['quality_metrics']['mean_score_pct']:.1f}%"),
        ("Source classification", "Synthetic demonstration data only"),
    ]
    summary = pd.DataFrame(summary_rows, columns=["Metric", "Value"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Executive Summary", index=False, startrow=4)
        df.to_excel(writer, sheet_name="Cleaned Records", index=False)
    from openpyxl import load_workbook
    wb = load_workbook(path)
    ws = wb["Executive Summary"]
    ws.merge_cells("A1:B1")
    ws["A1"] = "WK Digital Operations | B2B Data Cleaning Sample"
    ws["A1"].font = Font(name="Aptos Display", size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="0F172A")
    ws["A1"].alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 32
    ws.merge_cells("A2:B2")
    ws["A2"] = "SYNTHETIC SAMPLE — fictional records; not real leads, verified companies, client data, or production results."
    ws["A2"].font = Font(name="Aptos", size=10, bold=True, color="9A3412")
    ws["A2"].fill = PatternFill("solid", fgColor="FFEDD5")
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[2].height = 32
    for cell in ws[5]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2563EB")
    for row in ws.iter_rows(min_row=6, max_col=2):
        for cell in row:
            cell.fill = PatternFill("solid", fgColor="F1F5F9" if cell.row % 2 == 0 else "FFFFFF")
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.column_dimensions["A"].width = 31
    ws.column_dimensions["B"].width = 78
    ws.freeze_panes = "A6"
    records_ws = wb["Cleaned Records"]
    records_ws.freeze_panes = "A2"
    records_ws.auto_filter.ref = records_ws.dimensions
    for cell in records_ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0F172A")
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    records_ws.row_dimensions[1].height = 30
    for column_cells in records_ws.columns:
        letter = column_cells[0].column_letter
        width = min(52, max(14, max(len(str(c.value or "")) for c in column_cells) + 2))
        records_ws.column_dimensions[letter].width = width
    score_col = EXPECTED_COLUMNS.index("Data_Quality_Score") + 1
    for row in range(2, records_ws.max_row + 1):
        records_ws.cell(row=row, column=score_col).number_format = '0.0"%"'
    tab = Table(displayName="CleanedSyntheticSample", ref=records_ws.dimensions)
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False, showRowStripes=True, showColumnStripes=False)
    records_ws.add_table(tab)
    wb.save(path)


def run_pipeline(raw_path: Path = DEFAULT_RAW, outdir: Path = DEFAULT_OUT) -> dict[str, Any]:
    """Clean raw sample, calculate checks from data, and write client-ready outputs."""
    raw_path = Path(raw_path)
    outdir = Path(outdir)
    if not raw_path.exists():
        create_raw_dump(raw_path)
    raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    missing = [column for column in EXPECTED_COLUMNS if column not in raw.columns]
    if missing:
        raise ValueError(f"Raw file is missing required columns: {missing}")
    raw = raw[EXPECTED_COLUMNS].fillna("")
    raw_row_count = len(raw)

    raw_values = raw.to_dict(orient="records")
    cleaned_rows: list[dict[str, str]] = []
    repair_rows: list[dict[str, int]] = []
    for row in raw_values:
        cleaned, changes = _clean_record(row)
        cleaned_rows.append(cleaned)
        repair_rows.append(changes)
    normalized = pd.DataFrame(cleaned_rows, columns=TEXT_FIELDS)
    before_dedup_rows = len(normalized)
    duplicate_rows_removed = int(normalized.duplicated(subset=["Company_ID"], keep="first").sum())
    keep_mask = ~normalized.duplicated(subset=["Company_ID"], keep="first")
    normalized = normalized.loc[keep_mask].reset_index(drop=True)
    first_repairs = [changes for changes, keep in zip(repair_rows, keep_mask.tolist()) if keep]

    scores: list[float] = []
    for changes in first_repairs:
        repair_count = sum(changes.values())
        scores.append(round(max(98.0, 100.0 - 0.5 * repair_count), 1))
    normalized["Data_Quality_Score"] = scores
    normalized["Record_Provenance"] = "SYNTHETIC_SAMPLE"
    normalized = normalized[EXPECTED_COLUMNS]

    correction_by_field: dict[str, int] = {}
    for field, total in ((field, sum(row[field] for row in repair_rows)) for field in TEXT_FIELDS if field != "Record_Provenance"):
        correction_by_field[field] = int(total)
    whitespace_cells = 0
    for row in raw_values:
        for field in TEXT_FIELDS:
            value = str(row.get(field, "") or "")
            if value != value.strip():
                whitespace_cells += 1

    pre_dedup_urls_valid = sum(_valid_website(_clean_website(row["Website"])) and row["Website"].strip() == _clean_website(row["Website"]) for row in raw_values)
    broken_urls_detected = raw_row_count - int(pre_dedup_urls_valid)
    repaired_urls = correction_by_field.get("Website", 0)
    repaired_phones = correction_by_field.get("Phone", 0)
    repaired_emails = correction_by_field.get("Public_Contact_Email", 0)

    required_fields = [c for c in EXPECTED_COLUMNS if c != "Data_Quality_Score"]
    completeness = normalized[required_fields].apply(lambda row: all(str(v).strip() != "" for v in row), axis=1)
    checks = {
        "required_fields_present": int(completeness.sum()),
        "unique_company_ids": int(normalized["Company_ID"].is_unique),
        "valid_example_domain_websites": int(normalized["Website"].map(_valid_website).sum()),
        "valid_synthetic_example_emails": int(normalized["Public_Contact_Email"].map(lambda x: bool(re.fullmatch(r"[a-z0-9._+-]+@[a-z0-9-]+(?:-[a-z0-9]+)*\.example", x))).sum()),
        "valid_reserved_format_phones": int(normalized["Phone"].map(_valid_phone).sum()),
        "quality_scores_in_requested_range": int(normalized["Data_Quality_Score"].between(98, 100).sum()),
        "expected_provenance_label": int(normalized["Record_Provenance"].eq("SYNTHETIC_SAMPLE").sum()),
    }
    valid_rows = int((
        completeness
        & normalized["Website"].map(_valid_website)
        & normalized["Public_Contact_Email"].map(lambda x: bool(re.fullmatch(r"[a-z0-9._+-]+@[a-z0-9-]+(?:-[a-z0-9]+)*\.example", x)))
        & normalized["Phone"].map(_valid_phone)
        & normalized["Data_Quality_Score"].between(98, 100)
    ).sum())
    total_schema_cells = len(normalized) * len(required_fields)
    complete_schema_cells = int(normalized[required_fields].map(lambda x: str(x).strip() != "").to_numpy().sum())
    mean_score = round(float(normalized["Data_Quality_Score"].mean()), 2) if len(normalized) else 0.0
    report: dict[str, Any] = {
        "project": "WK Digital Operations — Synthetic B2B ETL Showcase",
        "data_provenance": "All records and figures are synthetic demonstrations. No real company directory or personal contact data was used.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_file": str(raw_path.relative_to(ROOT)) if raw_path.is_relative_to(ROOT) else raw_path.name,
        "raw_rows": raw_row_count,
        "rows_after_normalization_before_deduplication": before_dedup_rows,
        "duplicate_rows_removed": duplicate_rows_removed,
        "final_records": int(len(normalized)),
        "correction_counts": {
            "field_values_normalized": int(sum(correction_by_field.values())),
            "whitespace_padded_cells_trimmed": int(whitespace_cells),
            "company_names_normalized": correction_by_field.get("Company_Name", 0),
            "company_ids_normalized": correction_by_field.get("Company_ID", 0),
            "city_values_normalized": correction_by_field.get("City_State", 0),
            "website_urls_repaired": int(repaired_urls),
            "broken_or_noncanonical_urls_detected": int(broken_urls_detected),
            "phones_normalized": int(repaired_phones),
            "emails_normalized": int(repaired_emails),
            "tech_stack_values_normalized": correction_by_field.get("Tech_Stack_Detected", 0),
        },
        "quality_metrics": {
            "scoring_method": "Heuristic sample score = 100.0 minus 0.5 points per source field value normalized for the retained record, floored at 98.0; it is not an accuracy, verification, or production metric.",
            "minimum_score_pct": float(normalized["Data_Quality_Score"].min()) if len(normalized) else 0.0,
            "mean_score_pct": mean_score,
            "maximum_score_pct": float(normalized["Data_Quality_Score"].max()) if len(normalized) else 0.0,
        },
        "validation": {
            "checks_per_record": len(checks),
            "valid_rows": valid_rows,
            "invalid_rows": int(len(normalized) - valid_rows),
            "schema_completeness_pct": round(100 * complete_schema_cells / total_schema_cells, 2) if total_schema_cells else 0.0,
            "checks": checks,
            "check_definitions": [
                "All required output fields are populated",
                "Company_ID values are unique",
                "Websites use canonical HTTPS on reserved .example domains",
                "Public contact email placeholders use reserved .example domains",
                "Phone placeholders use the reserved 555-0100..0199 pattern",
                "Heuristic quality scores are within 98–100",
                "Every record is labeled SYNTHETIC_SAMPLE",
            ],
        },
        "limitations": [
            "Synthetic examples only; no records represent real leads or verified companies.",
            "The quality score is a transparent demo heuristic, not factual accuracy or production performance.",
            "The .example hostnames and contact emails are reserved placeholders and are not contact channels.",
        ],
    }

    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / "WK_B2B_Cleaned_Leads_Sample.csv"
    xlsx_path = outdir / "WK_B2B_Cleaned_Leads_Sample.xlsx"
    json_path = outdir / "WK_B2B_Cleaned_Leads_Sample.json"
    report_path = outdir / "cleaning_audit_report.json"
    normalized.to_csv(csv_path, index=False)
    normalized.to_json(json_path, orient="records", indent=2, force_ascii=False)
    _write_excel(normalized, report, xlsx_path)
    report_text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    report_path.write_text(report_text, encoding="utf-8")
    if outdir.resolve() == DEFAULT_OUT.resolve():
        data_report_path = ROOT / "data" / "cleaning_audit_report.json"
        data_report_path.parent.mkdir(parents=True, exist_ok=True)
        data_report_path.write_text(report_text, encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="Input raw CSV (default: data/raw_scrape_dump.csv)")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUT, help="Output directory (default: deliverables/)")
    parser.add_argument("--generate-raw", action="store_true", help="Regenerate the deterministic synthetic raw input before processing")
    args = parser.parse_args()
    if args.generate_raw:
        rows = create_raw_dump(args.raw)
        print(f"Generated {rows} synthetic raw rows at {args.raw}")
    report = run_pipeline(args.raw, args.outdir)
    print(json.dumps({
        "raw_rows": report["raw_rows"],
        "duplicate_rows_removed": report["duplicate_rows_removed"],
        "final_records": report["final_records"],
        "corrections": report["correction_counts"],
        "mean_quality_score_pct": report["quality_metrics"]["mean_score_pct"],
        "valid_rows": report["validation"]["valid_rows"],
        "invalid_rows": report["validation"]["invalid_rows"],
        "schema_completeness_pct": report["validation"]["schema_completeness_pct"],
    }, indent=2))


if __name__ == "__main__":
    main()
