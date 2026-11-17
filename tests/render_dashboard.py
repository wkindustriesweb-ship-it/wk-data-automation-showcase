#!/usr/bin/env python3
"""Run browser checks against a local HTTP server and save the dashboard preview."""
from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT = ROOT / "assets" / "dashboard_preview.png"
SITE_ROOT = ROOT / "site"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> None:
    handler = partial(QuietHandler, directory=str(SITE_ROOT if SITE_ROOT.exists() else ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    page_errors: list[str] = []
    console_errors: list[str] = []
    failed_requests: list[str] = []
    checks: dict[str, object] = {}
    SCREENSHOT.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1600, "height": 1120}, device_scale_factor=1.5)
            page = context.new_page()
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("requestfailed", lambda request: failed_requests.append(f"{request.url}: {request.failure}"))
            response = page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="domcontentloaded", timeout=30000)
            if not response or response.status != 200:
                raise AssertionError(f"Dashboard HTTP status was {response.status if response else 'no response'}")
            page.wait_for_function("document.querySelector('#kpi-records').textContent.trim() === '150'", timeout=20000)
            checks["http_status"] = response.status
            checks["title"] = page.title()
            checks["sample_kpis_loaded"] = {
                "records": page.locator("#kpi-records").inner_text(),
                "mean_heuristic_score": page.locator("#kpi-quality").inner_text(),
                "duplicates_removed": page.locator("#kpi-duplicates").inner_text(),
                "valid_rows": page.locator("#kpi-valid").inner_text(),
            }

            # Live full-text search should isolate the first deterministic synthetic row.
            page.locator("#search").fill("Northstar Atlas Analytics")
            page.wait_for_function("document.querySelector('#record-count').textContent.includes('1 matching')")
            checks["search"] = page.locator("#record-count").inner_text()
            checks["search_row"] = page.locator("#records-body tr").inner_text()

            # Industry and location filters are independent and combinable.
            page.locator("#search").fill("")
            page.locator("#industry-filter").select_option("E-commerce")
            industry_count = page.locator("#record-count").inner_text()
            page.locator("#city-filter").select_option("Toronto, ON")
            combined_count = page.locator("#record-count").inner_text()
            if "0 matching" in combined_count:
                raise AssertionError("Combined industry/city filters unexpectedly returned no records")
            checks["industry_filter"] = industry_count
            checks["combined_filters"] = combined_count

            # The volume-sensitive estimator updates its range and handoff items.
            page.locator("#task-type").select_option("automation")
            page.locator("#volume").select_option("75000")
            checks["estimator"] = page.locator("#estimate-value").inner_text()
            if "indicative" not in checks["estimator"]:
                raise AssertionError("Estimator did not label its timing as indicative")
            checks["deliverables"] = page.locator("#deliverable-list").inner_text()

            # All download URLs should resolve from the repository's local static tree.
            download_results = {}
            for relative in [
                "deliverables/WK_B2B_Cleaned_Leads_Sample.csv",
                "deliverables/WK_B2B_Cleaned_Leads_Sample.xlsx",
                "deliverables/cleaning_audit_report.json",
            ]:
                result = page.request.get(f"http://127.0.0.1:{port}/{relative}")
                download_results[relative] = {"status": result.status, "bytes": len(result.body())}
                if result.status != 200 or not result.body():
                    raise AssertionError(f"Download artifact did not resolve: {relative}")
            checks["downloads"] = download_results

            # Reset filters, verify the custom diagram and capture the review-ready dashboard.
            page.locator("#industry-filter").select_option("")
            page.locator("#city-filter").select_option("")
            page.locator("#task-type").select_option("scraping")
            page.locator("#volume").select_option("500")
            page.wait_for_function("document.querySelector('#record-count').textContent.includes('of 150')")
            page.wait_for_function("document.querySelector('.diagram-thumb').complete && document.querySelector('.diagram-thumb').naturalWidth === 1600")
            page.screenshot(path=str(SCREENSHOT), full_page=True, animations="disabled")
            checks["diagram"] = page.locator(".diagram-thumb").evaluate("img => ({width:img.naturalWidth,height:img.naturalHeight})")
            checks["responsive_viewport"] = {"width": 1600, "height": 1120, "device_scale_factor": 1.5}
            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_timeout(250)
            mobile = page.evaluate("""() => ({
              viewportWidth: window.innerWidth,
              documentWidth: document.documentElement.scrollWidth,
              kpiColumns: getComputedStyle(document.querySelector('.kpis')).gridTemplateColumns.split(' ').length
            })""")
            checks["mobile_viewport"] = mobile
            if mobile["documentWidth"] > mobile["viewportWidth"] or mobile["kpiColumns"] != 2:
                raise AssertionError(f"Responsive mobile layout check failed: {mobile}")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    checks["page_errors"] = page_errors
    checks["console_errors"] = console_errors
    checks["failed_requests"] = failed_requests
    checks["screenshot"] = str(SCREENSHOT)
    checks["screenshot_bytes"] = SCREENSHOT.stat().st_size if SCREENSHOT.exists() else 0
    print(json.dumps(checks, indent=2))
    if page_errors:
        raise AssertionError("Dashboard has uncaught browser exceptions; see report above")
    if not SCREENSHOT.exists() or SCREENSHOT.stat().st_size < 10000:
        raise AssertionError("Dashboard preview screenshot is missing or unexpectedly small")


if __name__ == "__main__":
    main()
