#!/usr/bin/env python3
"""
Generate a chord diagram showing the number of people per Harvard school / research org
and research-interest keyword overlap as chord connections.

Usage:
    py scripts/visualize_school_connections.py
    py scripts/visualize_school_connections.py --output data/my_chart.png
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw"
DEFAULT_OUTPUT = ROOT / "data" / "school_connections.png"

# (short label, hex color)
SCHOOL_META: dict[str, tuple[str, str]] = {
    "boston_childrens_hospital_people":             ("BCH",       "#E74C3C"),
    "harvard_business_school_people":               ("HBS",       "#A51C30"),
    "harvard_college_dso_staff_people":             ("College",   "#C0392B"),
    "harvard_data_science_initiative_people":       ("HDSI",      "#8E44AD"),
    "harvard_divinity_school_people":               ("HDS",       "#9B59B6"),
    "harvard_education_school_people":              ("HGSE",      "#2980B9"),
    "harvard_extension_school_people":              ("Extension", "#5DADE2"),
    "harvard_graduate_school_of_design_people":     ("GSD",       "#E67E22"),
    "harvard_gsas_staff_people":                    ("GSAS",      "#F39C12"),
    "harvard_kennedy_school_people":                ("HKS",       "#27AE60"),
    "harvard_law_school_people":                    ("HLS",       "#7D6608"),
    "harvard_medical_school_people":                ("HMS",       "#1A5276"),
    "harvard_radcliffe_institute_people":           ("Radcliffe", "#CB4335"),
    "harvard_school_of_dental_medicine_people":     ("HSDM",      "#16A085"),
    "harvard_seas_people":                          ("SEAS",      "#2C3E50"),
    "harvard_t_h_chan_school_public_health_people": ("Chan",      "#3498DB"),
    "harvard_wyss_institute_people":                ("Wyss",      "#7FB3D3"),
}


def count_profiles(school_dir: Path) -> int:
    return sum(
        1 for d in school_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "profile.jsonl").exists()
    )


def get_keywords(school_dir: Path) -> set[str]:
    keywords: set[str] = set()
    for person_dir in school_dir.iterdir():
        if not person_dir.is_dir() or person_dir.name.startswith("_"):
            continue
        profile_file = person_dir / "profile.jsonl"
        if not profile_file.exists():
            continue
        with profile_file.open(encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    for kw in data.get("research_interests") or []:
                        keywords.add(kw.lower().strip())
                except (json.JSONDecodeError, AttributeError):
                    pass
    return keywords


def draw_arc_segment(ax, theta1: float, theta2: float, r_inner: float, r_outer: float, color: str) -> None:
    n = 120
    thetas = np.linspace(theta1, theta2, n)
    x_out = r_outer * np.cos(thetas)
    y_out = r_outer * np.sin(thetas)
    x_in = r_inner * np.cos(thetas[::-1])
    y_in = r_inner * np.sin(thetas[::-1])
    xs = np.concatenate([x_out, x_in, [x_out[0]]])
    ys = np.concatenate([y_out, y_in, [y_out[0]]])
    ax.fill(xs, ys, color=color, zorder=3, linewidth=0)


def draw_chord(ax, theta_a: float, theta_b: float, color: str, alpha: float, r: float = 0.78) -> None:
    p1 = np.array([r * math.cos(theta_a), r * math.sin(theta_a)])
    p2 = np.array([r * math.cos(theta_b), r * math.sin(theta_b)])
    ctrl = np.array([0.0, 0.0])
    verts = [tuple(p1), tuple(ctrl), tuple(p2), tuple(ctrl), tuple(p1), tuple(p1)]
    codes = [MPath.MOVETO, MPath.CURVE3, MPath.CURVE3, MPath.CURVE3, MPath.CURVE3, MPath.CLOSEPOLY]
    path = MPath(verts, codes)
    patch = PathPatch(path, facecolor=color, edgecolor="none", alpha=alpha, zorder=1)
    ax.add_patch(patch)


def main(output_path: Path = DEFAULT_OUTPUT) -> None:
    # --- Collect data ---
    schools = []
    for folder_name, (label, color) in SCHOOL_META.items():
        school_dir = DATA_DIR / folder_name
        if not school_dir.is_dir():
            continue
        count = count_profiles(school_dir)
        if count == 0:
            continue
        keywords = get_keywords(school_dir)
        schools.append({"key": folder_name, "label": label, "color": color,
                         "count": count, "keywords": keywords})

    n = len(schools)
    total = sum(s["count"] for s in schools)
    print(f"Found {n} schools, {total:,} total people")

    # --- Compute pairwise keyword overlap ---
    connections = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            overlap = len(schools[i]["keywords"] & schools[j]["keywords"])
            connections[i, j] = overlap
            connections[j, i] = overlap

    # --- Assign angles (proportional to count, starting from top, clockwise) ---
    GAP_DEG = 2.5
    gap_rad = math.radians(GAP_DEG)
    total_gap_rad = gap_rad * n
    usable_rad = 2 * math.pi - total_gap_rad

    # Start at top (pi/2) and go clockwise (subtract angles)
    angles: list[tuple[float, float, float]] = []
    cursor = math.pi / 2
    for s in schools:
        span = usable_rad * s["count"] / total
        start = cursor
        end = cursor - span
        mid = (start + end) / 2
        angles.append((start, end, mid))
        cursor = end - gap_rad

    # --- Draw ---
    fig, ax = plt.subplots(figsize=(16, 16), facecolor="#F8F8F8")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.9, 1.9)
    ax.set_ylim(-1.9, 1.9)

    R_INNER = 0.82
    R_OUTER = 0.95
    R_LABEL = 1.08
    MIN_OVERLAP = 3

    max_conn = connections.max() if connections.max() > 0 else 1

    # Draw chords first (behind arcs)
    for i in range(n):
        for j in range(i + 1, n):
            strength = connections[i, j]
            if strength < MIN_OVERLAP:
                continue
            alpha = 0.05 + 0.30 * (strength / max_conn)
            draw_chord(ax, angles[i][2], angles[j][2], schools[i]["color"], alpha)

    # Draw arc segments
    for i, s in enumerate(schools):
        start, end, mid = angles[i]
        draw_arc_segment(ax, end, start, R_INNER, R_OUTER, s["color"])

        # Position label radially
        lx = R_LABEL * math.cos(mid)
        ly = R_LABEL * math.sin(mid)
        ha = "left" if lx > 0.15 else ("right" if lx < -0.15 else "center")
        va = "bottom" if ly > 0.15 else ("top" if ly < -0.15 else "center")

        ax.text(lx, ly, f"{s['label']}\n{s['count']:,}",
                ha=ha, va=va, fontsize=9.5, fontweight="bold",
                color=s["color"], multialignment="center",
                linespacing=1.4)

    # Center label
    ax.text(0, 0.06, "Total", ha="center", va="center",
            fontsize=11, color="#888888")
    ax.text(0, -0.06, f"{total:,}", ha="center", va="center",
            fontsize=14, fontweight="bold", color="#444444")

    ax.set_title("Harvard Schools & Research Orgs\nPeople Count & Research Interest Overlap",
                 fontsize=14, pad=24, color="#333333", fontweight="bold")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate school chord diagram.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Output PNG path (default: data/school_connections.png)")
    args = parser.parse_args()
    main(args.output)
