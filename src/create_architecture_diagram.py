#!/usr/bin/env python3
"""Render the project's original, code-drawn ETL architecture diagram."""
from pathlib import Path
from html import escape

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "etl_architecture_diagram.png"
SVG_OUTPUT = ROOT / "assets" / "etl_architecture_diagram.svg"
BG = "#0F172A"
PANEL = "#16243A"
PANEL_EDGE = "#263953"
TEXT = "#E5EDF8"
MUTED = "#9FB0C6"
BLUE = "#38BDF8"
GREEN = "#10B981"


def write_compact_svg(cards: list[dict[str, object]], pills: list[tuple[str, int, int]]) -> None:
    """Write a small, responsive SVG twin for the static dashboard bundle."""
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">',
        '<defs><pattern id="grid" width="64" height="64" patternUnits="userSpaceOnUse"><path d="M64 0H0V64" fill="none" stroke="#223148" stroke-width=".6" opacity=".35"/></pattern><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 8 4 0 8Z" fill="#7390AC"/></marker></defs>',
        f'<rect width="1600" height="900" fill="{BG}"/><rect width="1600" height="900" fill="url(#grid)"/>',
        f'<g font-family="DejaVu Sans,Arial,sans-serif"><text x="84" y="72" fill="{GREEN}" font-size="11" font-weight="700" letter-spacing="1.4">WK DIGITAL OPERATIONS</text>',
        f'<text x="84" y="130" fill="{TEXT}" font-size="29" font-weight="700">Automated Data Extraction &amp; ETL Pipeline</text>',
        f'<text x="84" y="167" fill="{MUTED}" font-size="14">A controlled workflow from permitted public sources to audited, client-ready outputs</text>',
        '<path d="M84 204H1516" stroke="#2A3A51"/>',
    ]
    card_y, card_width, card_height = 250, 322, 224
    for index, card in enumerate(cards):
        x = int(card["x"])
        accent = str(card["accent"])
        parts.extend([
            f'<rect x="{x + 5}" y="256" width="{card_width}" height="{card_height}" rx="20" fill="#09111F" opacity=".62"/>',
            f'<rect x="{x}" y="{card_y}" width="{card_width}" height="{card_height}" rx="20" fill="{PANEL}" stroke="{PANEL_EDGE}" stroke-width="1.2"/>',
            f'<rect x="{x + 1}" y="{card_y}" width="{card_width - 2}" height="7" rx="4" fill="{accent}"/>',
            f'<text x="{x + 24}" y="284" fill="{accent}" font-size="12" font-weight="700">{escape(str(card["number"]))}</text>',
            f'<text x="{x + 72}" y="284" fill="{MUTED}" font-size="10" font-weight="700">{escape(str(card["label"]))}</text>',
        ])
        for line_index, title_line in enumerate(str(card["title"]).split("\n")):
            parts.append(f'<text x="{x + 24}" y="{337 + line_index * 22}" fill="{TEXT}" font-size="17" font-weight="700">{escape(title_line)}</text>')
        for item_index, item in enumerate(card["items"]):
            y = 404 + item_index * 23
            parts.extend([
                f'<circle cx="{x + 29}" cy="{y - 4}" r="3" fill="{accent}"/>',
                f'<text x="{x + 44}" y="{y}" fill="{MUTED}" font-size="10.2">{escape(str(item))}</text>',
            ])
        parts.append(f'<text x="{x + 24}" y="465" fill="{accent}" font-size="8.1" font-weight="700" letter-spacing=".6">{escape(str(card["tag"]))}</text>')
        if index < len(cards) - 1:
            next_x = int(cards[index + 1]["x"])
            parts.append(f'<line x1="{x + card_width + 10}" y1="362" x2="{next_x - 13}" y2="362" stroke="#7390AC" stroke-width="1.8" marker-end="url(#arrow)"/>')
    parts.extend([
        f'<text x="84" y="538" fill="{BLUE}" font-size="9" font-weight="700" letter-spacing="1">CONTROL PLANE</text>',
        '<path d="M84 558H1516" stroke="#2A3A51"/>',
    ])
    for label, x, width in pills:
        parts.extend([
            f'<rect x="{x}" y="591" width="{width}" height="43" rx="12" fill="#111E31" stroke="#30435C"/>',
            f'<text x="{x + 16}" y="617" fill="{TEXT}" font-size="10">{escape(label)}</text>',
            f'<circle cx="{x + width - 17}" cy="612" r="4" fill="{GREEN}"/>',
        ])
    parts.extend([
        f'<text x="84" y="695" fill="{MUTED}" font-size="13">Designed to make each transformation visible, reproducible, and reviewable.</text>',
        f'<text x="84" y="792" fill="{GREEN}" font-size="9" font-weight="700" letter-spacing="1">SYNTHETIC SHOWCASE</text>',
        f'<text x="290" y="792" fill="{MUTED}" font-size="10.5">This diagram illustrates a workflow; the accompanying sample records and metrics are synthetic, not production results.</text>',
        '<text x="1516" y="846" text-anchor="end" fill="#73869D" font-size="8.2">WK DIGITAL OPERATIONS  /  COORDINATED BY JONATAN LUNA</text></g></svg>',
    ])
    SVG_OUTPUT.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXT, "axes.unicode_minus": False})
    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1600)
    ax.set_ylim(0, 900)
    ax.axis("off")
    ax.set_facecolor(BG)

    # Decorative, non-semantic grid to give the canvas a precise technical texture.
    for x in range(0, 1601, 64):
        ax.plot([x, x], [82, 802], color="#223148", linewidth=0.45, alpha=0.33, zorder=0)
    for y in range(82, 803, 64):
        ax.plot([0, 1600], [y, y], color="#223148", linewidth=0.45, alpha=0.33, zorder=0)

    ax.text(84, 828, "WK DIGITAL OPERATIONS", fontsize=11, fontweight="bold", color=GREEN, va="center")
    ax.text(84, 770, "Automated Data Extraction & ETL Pipeline", fontsize=29, fontweight="bold", color=TEXT, va="center")
    ax.text(84, 733, "A controlled workflow from permitted public sources to audited, client-ready outputs", fontsize=14, color=MUTED, va="center")
    ax.plot([84, 1516], [696, 696], color="#2A3A51", linewidth=1.0)

    cards = [
        {
            "x": 84, "accent": BLUE, "number": "01", "label": "EXTRACT",
            "title": "Multi-Source\nExtraction",
            "items": ["Permitted public sources", "Python · Playwright · APIs", "Source and access checks"],
            "tag": "INPUT CONTROL",
        },
        {
            "x": 454, "accent": GREEN, "number": "02", "label": "TRANSFORM",
            "title": "Automated Cleaning\n& Deduplication",
            "items": ["Pandas normalization", "Regex format validation", "Key-based deduplication"],
            "tag": "REPEATABLE ETL",
        },
        {
            "x": 824, "accent": BLUE, "number": "03", "label": "VALIDATE",
            "title": "Quality Assurance\n& Enrichment",
            "items": ["Schema and field checks", "Correction-count audit", "Exceptions surfaced"],
            "tag": "AUDIT TRAIL",
        },
        {
            "x": 1194, "accent": GREEN, "number": "04", "label": "DELIVER",
            "title": "Multi-Format\nClient Delivery",
            "items": ["Excel · CSV · JSON", "Interactive dashboard", "Clear handoff notes"],
            "tag": "READY TO REVIEW",
        },
    ]
    y, width, height = 426, 322, 224
    for idx, card in enumerate(cards):
        x = card["x"]
        shadow = FancyBboxPatch((x + 5, y - 6), width, height,
                                boxstyle="round,pad=0,rounding_size=20", linewidth=0,
                                facecolor="#09111F", alpha=0.62, zorder=1)
        body = FancyBboxPatch((x, y), width, height,
                              boxstyle="round,pad=0,rounding_size=20", linewidth=1.1,
                              edgecolor=PANEL_EDGE, facecolor=PANEL, zorder=2)
        accent = FancyBboxPatch((x + 1, y + height - 7), width - 2, 7,
                                boxstyle="round,pad=0,rounding_size=4", linewidth=0,
                                facecolor=card["accent"], zorder=3)
        ax.add_patch(shadow)
        ax.add_patch(body)
        ax.add_patch(accent)
        ax.text(x + 24, y + height - 34, card["number"], fontsize=12, fontweight="bold", color=card["accent"], va="center")
        ax.text(x + 72, y + height - 34, card["label"], fontsize=10, fontweight="bold", color=MUTED, va="center")
        ax.text(x + 24, y + height - 85, card["title"], fontsize=17, fontweight="bold", color=TEXT, va="center", linespacing=1.25)
        for j, item in enumerate(card["items"]):
            yy = y + 70 - j * 23
            ax.scatter([x + 29], [yy], s=18, color=card["accent"], zorder=5)
            ax.text(x + 44, yy, item, fontsize=10.2, color=MUTED, va="center")
        ax.text(x + 24, y + 9, card["tag"], fontsize=8.1, fontweight="bold", color=card["accent"], va="center")
        if idx < len(cards) - 1:
            arrow = FancyArrowPatch((x + width + 10, y + height / 2),
                                    (cards[idx + 1]["x"] - 13, y + height / 2),
                                    arrowstyle="-|>", mutation_scale=17, linewidth=1.8,
                                    color="#7390AC", zorder=4)
            ax.add_patch(arrow)

    # Bottom control plane and deliverable set.
    ax.text(84, 362, "CONTROL PLANE", fontsize=9, fontweight="bold", color=BLUE, va="center")
    ax.plot([84, 1516], [342, 342], color="#2A3A51", linewidth=1.0)
    pills = [
        ("Field-level audit", 84, 247),
        ("Deterministic reruns", 350, 242),
        ("Human review where needed", 612, 310),
        ("Export + dashboard delivery", 938, 332),
    ]
    for label, x, w in pills:
        patch = FancyBboxPatch((x, 266), w, 43, boxstyle="round,pad=0,rounding_size=12",
                               linewidth=1, edgecolor="#30435C", facecolor="#111E31", zorder=2)
        ax.add_patch(patch)
        ax.text(x + 16, 287, label, fontsize=10, color=TEXT, va="center")
        ax.scatter([x + w - 17], [287], s=25, color=GREEN, zorder=4)
    ax.text(84, 205, "Designed to make each transformation visible, reproducible, and reviewable.", fontsize=13, color=MUTED, va="center")
    ax.text(84, 108, "SYNTHETIC SHOWCASE", fontsize=9, fontweight="bold", color=GREEN, va="center")
    ax.text(290, 108, "This diagram illustrates a workflow; the accompanying sample records and metrics are synthetic, not production results.", fontsize=10.5, color=MUTED, va="center")
    ax.text(1516, 54, "WK DIGITAL OPERATIONS  /  COORDINATED BY JONATAN LUNA", fontsize=8.2, color="#73869D", ha="right", va="center")

    fig.savefig(OUTPUT, dpi=100, facecolor=BG)
    write_compact_svg(cards, pills)
    plt.close(fig)
    print(f"Wrote {OUTPUT} (1600x900) and compact {SVG_OUTPUT} (1600x900 viewBox)")


if __name__ == "__main__":
    main()
