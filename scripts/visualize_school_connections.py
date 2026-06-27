#!/usr/bin/env python3
"""
Chord diagram: Harvard schools/orgs connected by researcher similarity.

Algorithm:
  1. Build one text per person from bio + title + research_interests.
  2. Fit TF-IDF across all people (unigrams + bigrams, English stop words).
  3. For every org pair, compute cosine-similarity between all their people.
  4. Connection strength = number of cross-org person pairs with sim >= threshold,
     normalised by sqrt(|A| * |B|) so large orgs don't dominate.
  5. Draw a chord diagram: arc size = people count, chord width = connection strength.

Usage:
    py scripts/visualize_school_connections.py
    py scripts/visualize_school_connections.py --threshold 0.3 --output data/chart.png
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw"
DEFAULT_OUTPUT = ROOT / "data" / "school_connections.png"
DEFAULT_THRESHOLD = 0.3

# (short label, hex color) — order determines clockwise position in the diagram
SCHOOL_META: dict[str, tuple[str, str]] = {
    "harvard_t_h_chan_school_public_health_people": ("Chan",      "#3498DB"),
    "harvard_radcliffe_institute_people":           ("Radcliffe", "#CB4335"),
    "boston_childrens_hospital_people":             ("BCH",       "#E74C3C"),
    "harvard_business_school_people":               ("HBS",       "#A51C30"),
    "harvard_kennedy_school_people":                ("HKS",       "#27AE60"),
    "harvard_law_school_people":                    ("HLS",       "#7D6608"),
    "harvard_education_school_people":              ("HGSE",      "#2980B9"),
    "harvard_graduate_school_of_design_people":     ("GSD",       "#E67E22"),
    "harvard_school_of_dental_medicine_people":     ("HSDM",      "#16A085"),
    "harvard_seas_people":                          ("SEAS",      "#2C3E50"),
    "harvard_medical_school_people":                ("HMS",       "#1A5276"),
    "harvard_wyss_institute_people":                ("Wyss",      "#7FB3D3"),
    "harvard_data_science_initiative_people":       ("HDSI",      "#8E44AD"),
    "harvard_gsas_staff_people":                    ("GSAS",      "#F39C12"),
    "harvard_extension_school_people":              ("Extension", "#5DADE2"),
    "harvard_college_dso_staff_people":             ("College",   "#C0392B"),
    "harvard_divinity_school_people":               ("HDS",       "#9B59B6"),
}


# ── data loading ──────────────────────────────────────────────────────────────

def load_school(school_dir: Path) -> tuple[int, list[str]]:
    """Return (person_count, list_of_texts) for one school directory."""
    texts: list[str] = []
    for person_dir in school_dir.iterdir():
        if not person_dir.is_dir() or person_dir.name.startswith("_"):
            continue
        pf = person_dir / "profile.jsonl"
        if not pf.exists():
            continue
        try:
            data = json.loads(pf.read_text(encoding="utf-8").splitlines()[0])
        except (json.JSONDecodeError, IndexError):
            continue
        parts = []
        # research_interests carries the clearest signal — weight it 3×
        for ri in data.get("research_interests") or []:
            parts.extend([ri] * 3)
        if data.get("title"):
            parts.append(data["title"])
        if data.get("bio"):
            parts.append(data["bio"])
        text = " ".join(parts).strip()
        if text:
            texts.append(text)
    return len(texts), texts


# ── similarity ────────────────────────────────────────────────────────────────

def build_tfidf(all_texts: list[str]) -> np.ndarray:
    print(f"  Fitting TF-IDF on {len(all_texts):,} person texts …")
    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
        min_df=3,
        max_df=0.80,
        max_features=8000,
        sublinear_tf=True,
    )
    return vec.fit_transform(all_texts)


def compute_connections(
    school_matrices: list[np.ndarray],
    threshold: float,
) -> np.ndarray:
    n = len(school_matrices)
    connections = np.zeros((n, n))
    total_pairs = sum(
        school_matrices[i].shape[0] * school_matrices[j].shape[0]
        for i in range(n) for j in range(i + 1, n)
    )
    print(f"  Computing similarities for {total_pairs:,} cross-org person pairs …")
    done = 0
    for i in range(n):
        for j in range(i + 1, n):
            Xi = school_matrices[i]
            Xj = school_matrices[j]
            if Xi.shape[0] == 0 or Xj.shape[0] == 0:
                continue
            sim = cosine_similarity(Xi, Xj)          # (|A| × |B|)
            count = float(np.sum(sim >= threshold))
            # normalise so large orgs don't dominate
            norm = math.sqrt(Xi.shape[0] * Xj.shape[0])
            connections[i, j] = connections[j, i] = count / norm
            done += Xi.shape[0] * Xj.shape[0]
    return connections


# ── drawing ───────────────────────────────────────────────────────────────────

def draw_arc(ax, theta1: float, theta2: float, r_in: float, r_out: float, color: str) -> None:
    n = 120
    t = np.linspace(theta1, theta2, n)
    xo, yo = r_out * np.cos(t), r_out * np.sin(t)
    xi, yi = r_in  * np.cos(t[::-1]), r_in * np.sin(t[::-1])
    ax.fill(
        np.concatenate([xo, xi, [xo[0]]]),
        np.concatenate([yo, yi, [yo[0]]]),
        color=color, zorder=3, linewidth=0,
    )


def draw_chord(ax, theta_a: float, theta_b: float, color: str, alpha: float, linewidth: float, r: float = 0.82) -> None:
    """Quadratic bezier curved line connecting two arc midpoints through the centre."""
    x1, y1 = r * math.cos(theta_a), r * math.sin(theta_a)
    x2, y2 = r * math.cos(theta_b), r * math.sin(theta_b)
    t = np.linspace(0, 1, 120)
    # quadratic bezier: control point pulled 60 % toward centre from the midpoint
    mx, my = (x1 + x2) / 2 * 0.40, (y1 + y2) / 2 * 0.40
    x = (1 - t)**2 * x1 + 2 * (1 - t) * t * mx + t**2 * x2
    y = (1 - t)**2 * y1 + 2 * (1 - t) * t * my + t**2 * y2
    ax.plot(x, y, color=color, alpha=alpha, linewidth=linewidth,
            solid_capstyle="round", zorder=2)


# ── main ──────────────────────────────────────────────────────────────────────

def main(output_path: Path = DEFAULT_OUTPUT, threshold: float = DEFAULT_THRESHOLD) -> None:
    # 1. Load all schools
    schools = []
    for folder, (label, color) in SCHOOL_META.items():
        d = DATA_DIR / folder
        if not d.is_dir():
            continue
        count, texts = load_school(d)
        if count == 0:
            continue
        schools.append({"label": label, "color": color, "count": count, "texts": texts})
        print(f"  {label:12s}  {count:5d} people  {len(texts):5d} texts")

    n = len(schools)
    total = sum(s["count"] for s in schools)
    print(f"\nTotal: {n} orgs, {total:,} people\n")

    # 2. TF-IDF
    all_texts: list[str] = []
    slices: list[tuple[int, int]] = []
    for s in schools:
        start = len(all_texts)
        all_texts.extend(s["texts"])
        slices.append((start, len(all_texts)))

    X = build_tfidf(all_texts)
    school_matrices = [X[a:b] for a, b in slices]

    # 3. Compute connections
    connections = compute_connections(school_matrices, threshold)

    # 4. Report top connections
    print(f"\nTop connections (threshold={threshold}):")
    pairs = [
        (connections[i, j], schools[i]["label"], schools[j]["label"])
        for i in range(n) for j in range(i + 1, n)
        if connections[i, j] > 0
    ]
    for strength, a, b in sorted(pairs, reverse=True)[:10]:
        print(f"  {a:12s} <-> {b:12s}  {strength:.3f}")

    # 5. Draw chord diagram
    GAP_DEG = 2.5
    gap_rad = math.radians(GAP_DEG)
    usable_rad = 2 * math.pi - gap_rad * n

    angles: list[tuple[float, float, float]] = []
    cursor = math.pi / 2
    for s in schools:
        span = usable_rad * s["count"] / total
        start, end = cursor, cursor - span
        angles.append((start, end, (start + end) / 2))
        cursor = end - gap_rad

    fig, ax = plt.subplots(figsize=(16, 16), facecolor="#F8F8F8")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.9, 1.9)
    ax.set_ylim(-1.9, 1.9)

    R_IN, R_OUT, R_LABEL = 0.82, 0.95, 1.08

    # chords
    max_c = connections.max() if connections.max() > 0 else 1
    for i in range(n):
        for j in range(i + 1, n):
            c = connections[i, j]
            if c <= 0:
                continue
            linewidth = 1.0 + 14.0 * (c / max_c)   # 1px – 15px
            alpha     = 0.25 + 0.55 * (c / max_c)   # 0.25 – 0.80
            draw_chord(ax, angles[i][2], angles[j][2],
                       schools[i]["color"], alpha, linewidth)

    # arcs + labels
    for i, s in enumerate(schools):
        start, end, mid = angles[i]
        draw_arc(ax, end, start, R_IN, R_OUT, s["color"])

        lx = R_LABEL * math.cos(mid)
        ly = R_LABEL * math.sin(mid)
        ha = "left" if lx > 0.15 else ("right" if lx < -0.15 else "center")
        va = "bottom" if ly > 0.15 else ("top" if ly < -0.15 else "center")
        ax.text(lx, ly, f"{s['label']}\n{s['count']:,}",
                ha=ha, va=va, fontsize=9.5, fontweight="bold",
                color=s["color"], multialignment="center", linespacing=1.4)

    # centre
    ax.text(0, 0.07, "Total",    ha="center", va="center", fontsize=11, color="#888888")
    ax.text(0, -0.07, f"{total:,}", ha="center", va="center",
            fontsize=14, fontweight="bold", color="#444444")

    ax.set_title(
        f"Harvard Schools & Research Orgs\n"
        f"People Count & Research Similarity Connections  (threshold={threshold})",
        fontsize=13, pad=24, color="#333333", fontweight="bold",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate school chord diagram.")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help="Cosine-similarity threshold (default 0.3)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Output PNG path")
    args = parser.parse_args()
    main(args.output, args.threshold)
