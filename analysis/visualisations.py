"""
visualisations.py  -  Matplotlib charts made by Python
=======================================================
These PNG pictures are created from the same CSV data as the website charts.
They are saved in static/images/charts/ and shown on the Data Visualisation page.
"""
import os
import matplotlib
matplotlib.use("Agg")  # no pop-up window needed; we only save pictures
import matplotlib.pyplot as plt
import numpy as np

from analysis.data_analysis import BASE_DIR, load_students, module_comparison

OUT_DIR = os.path.join(BASE_DIR, "static", "images", "charts")

# Project colour palette
CREAM, FOREST, SAGE, BUTTER, CORAL = "#FFF9F0", "#243B32", "#A8B5A0", "#F4D875", "#DD8978"


def _style(ax, title, xlabel, ylabel):
    """Same clean look for every chart."""
    ax.set_title(title, fontsize=13, color=FOREST, loc="left", pad=12, fontweight="bold")
    ax.set_xlabel(xlabel, color=FOREST)
    ax.set_ylabel(ylabel, color=FOREST)
    ax.tick_params(colors=FOREST)
    ax.set_facecolor("#FFFFFF")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(SAGE)
    ax.grid(axis="y", color="#E9E4D8", linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, name):
    fig.patch.set_facecolor(CREAM)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def chart_attendance_vs_assignment(df):
    fig, ax = plt.subplots(figsize=(7, 4.4))
    x = np.arange(len(df))
    w = 0.38
    ax.bar(x - w / 2, df["attendance"], w, label="Attendance (%)", color=FOREST)
    ax.bar(x + w / 2, df["assignment_completion"], w, label="Assignment completion (%)", color=SAGE)
    ax.set_xticks(x)
    ax.set_xticklabels(df["student_id"])
    ax.set_ylim(0, 105)
    _style(ax, "Attendance vs Assignment Completion", "Simulated student", "Percentage (%)")
    ax.legend(frameon=False)
    return _save(fig, "attendance_vs_assignment.png")


def chart_quiz_comparison(df):
    fig, ax = plt.subplots(figsize=(7, 4.4))
    colours = [CORAL if q < 5 else FOREST for q in df["quiz_score"]]
    bars = ax.bar(df["student_id"], df["quiz_score"], color=colours)
    for b, q in zip(bars, df["quiz_score"]):
        ax.text(b.get_x() + b.get_width() / 2, q + 0.2, f"{q:g}/10", ha="center", color=FOREST, fontsize=9)
    ax.set_ylim(0, 10.8)
    _style(ax, "Quiz Performance Comparison", "Simulated student", "Quiz score (out of 10)")
    return _save(fig, "quiz_comparison.png")


def chart_revision_vs_quiz(df):
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.scatter(df["revision_sessions"], df["quiz_score"], s=140, color=FOREST, zorder=3)
    for _, r in df.iterrows():
        ax.annotate(r["student_id"], (r["revision_sessions"], r["quiz_score"]),
                    textcoords="offset points", xytext=(8, 6), color=FOREST)
    ax.set_xlim(4, 10.6)
    ax.set_ylim(0, 10)
    _style(ax, "Revision Activity vs Quiz Scores", "Revision sessions (out of 10)", "Quiz score (out of 10)")
    return _save(fig, "revision_vs_quiz.png")


def chart_combined_scores(df):
    fig, ax = plt.subplots(figsize=(7, 4.4))
    best = df["combined_score"].idxmax()
    colours = [BUTTER if i == best else SAGE for i in df.index]
    bars = ax.bar(df["student_id"], df["combined_score"], color=colours, edgecolor=FOREST, linewidth=0.8)
    for b, v in zip(bars, df["combined_score"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.2f}", ha="center", color=FOREST, fontsize=9)
    ax.set_ylim(0, 100)
    _style(ax, "Combined Learning-Progress Score (illustrative)", "Simulated student", "Score (0-100)")
    return _save(fig, "combined_scores.png")


def chart_module_comparison():
    rows = module_comparison()
    names = [r["module_name"].replace(" ", "\n", 1) for r in rows]
    x = np.arange(len(rows))
    w = 0.2
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(x - 1.5 * w, [r["avg_attendance"] for r in rows], w, label="Attendance", color=FOREST)
    ax.bar(x - 0.5 * w, [r["avg_assignment"] for r in rows], w, label="Assignments", color=SAGE)
    ax.bar(x + 0.5 * w, [r["avg_revision_pct"] for r in rows], w, label="Revision", color=BUTTER)
    ax.bar(x + 1.5 * w, [r["avg_quiz_pct"] for r in rows], w, label="Quiz", color=CORAL)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8)
    ax.set_ylim(0, 105)
    _style(ax, "Module Comparison (synthetic data)", "Module", "Average (%)")
    ax.legend(frameon=False, ncol=4, fontsize=8)
    return _save(fig, "module_comparison.png")


def generate_all_charts():
    """Create every chart. Returns the list of file names created."""
    os.makedirs(OUT_DIR, exist_ok=True)
    df = load_students()
    paths = [
        chart_attendance_vs_assignment(df),
        chart_quiz_comparison(df),
        chart_revision_vs_quiz(df),
        chart_combined_scores(df),
        chart_module_comparison(),
    ]
    return [os.path.basename(p) for p in paths]


if __name__ == "__main__":
    print("Created:", generate_all_charts())
