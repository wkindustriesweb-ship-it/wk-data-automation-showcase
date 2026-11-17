import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from src.data_pipeline import EXPECTED_COLUMNS, create_raw_dump, run_pipeline
from src.build_static_site import SITE, build_static_site


class PipelineTests(unittest.TestCase):
    def test_synthetic_etl_counts_and_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            raw = work / "raw.csv"
            out = work / "deliverables"
            self.assertEqual(create_raw_dump(raw), 162)
            report = run_pipeline(raw, out)

            self.assertEqual(report["raw_rows"], 162)
            self.assertEqual(report["duplicate_rows_removed"], 12)
            self.assertEqual(report["final_records"], 150)
            self.assertEqual(report["correction_counts"]["field_values_normalized"], 96)
            self.assertEqual(report["correction_counts"]["website_urls_repaired"], 13)
            self.assertEqual(report["correction_counts"]["phones_normalized"], 19)
            self.assertEqual(report["validation"]["valid_rows"], 150)
            self.assertEqual(report["validation"]["invalid_rows"], 0)
            self.assertEqual(report["validation"]["schema_completeness_pct"], 100.0)

            csv_path = out / "WK_B2B_Cleaned_Leads_Sample.csv"
            xlsx_path = out / "WK_B2B_Cleaned_Leads_Sample.xlsx"
            json_path = out / "WK_B2B_Cleaned_Leads_Sample.json"
            audit_path = out / "cleaning_audit_report.json"
            for path in (csv_path, xlsx_path, json_path, audit_path):
                self.assertTrue(path.exists(), path.name)
                self.assertGreater(path.stat().st_size, 0)

            df = pd.read_csv(csv_path, dtype=str)
            self.assertEqual(df.columns.tolist(), EXPECTED_COLUMNS)
            self.assertEqual(len(df), 150)
            self.assertEqual(df["Company_ID"].nunique(), 150)
            self.assertTrue(df["Record_Provenance"].eq("SYNTHETIC_SAMPLE").all())
            scores = pd.to_numeric(df["Data_Quality_Score"])
            self.assertGreaterEqual(float(scores.min()), 98.0)
            self.assertLessEqual(float(scores.max()), 100.0)
            self.assertTrue(df["Website"].str.startswith("https://www.").all())
            self.assertTrue(df["Website"].str.endswith(".example").all())
            self.assertTrue(df["Public_Contact_Email"].str.endswith(".example").all())

            loaded_json = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(len(loaded_json), 150)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertIn("synthetic", audit["data_provenance"].lower())
            self.assertIn("not an accuracy", audit["quality_metrics"]["scoring_method"])

            wb = load_workbook(xlsx_path, read_only=True)
            self.assertEqual(wb.sheetnames, ["Executive Summary", "Cleaned Records"])
            self.assertIn("SYNTHETIC SAMPLE", wb["Executive Summary"]["A2"].value)
            self.assertEqual(wb["Cleaned Records"].max_row, 151)
            wb.close()

    def test_default_run_writes_source_audit_copy(self):
        report = run_pipeline()
        project_root = Path(__file__).resolve().parents[1]
        source_audit = project_root / "data" / "cleaning_audit_report.json"
        download_audit = project_root / "deliverables" / "cleaning_audit_report.json"
        self.assertTrue(source_audit.exists())
        self.assertEqual(
            json.loads(source_audit.read_text(encoding="utf-8")),
            json.loads(download_audit.read_text(encoding="utf-8")),
        )
        self.assertEqual(report["final_records"], 150)

    def test_repeated_run_keeps_same_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            raw = work / "raw.csv"
            create_raw_dump(raw)
            first = run_pipeline(raw, work / "one")
            second = run_pipeline(raw, work / "two")
            self.assertEqual(first["correction_counts"], second["correction_counts"])
            self.assertEqual(first["quality_metrics"], second["quality_metrics"])
            self.assertEqual(first["validation"], second["validation"])

    def test_static_site_bundle_is_minimal_and_complete(self):
        files = set(build_static_site())
        expected = {
            "index.html",
            "assets/etl_architecture_diagram.svg",
            "deliverables/WK_B2B_Cleaned_Leads_Sample.csv",
            "deliverables/WK_B2B_Cleaned_Leads_Sample.xlsx",
            "deliverables/WK_B2B_Cleaned_Leads_Sample.json",
            "deliverables/cleaning_audit_report.json",
        }
        self.assertEqual(files, expected)
        self.assertFalse((SITE / ".nojekyll").exists())
        self.assertFalse((SITE / "data").exists())
        self.assertFalse((SITE / "src").exists())


if __name__ == "__main__":
    unittest.main()
