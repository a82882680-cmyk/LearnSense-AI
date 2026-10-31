"""
data_analysis.py  -  Pandas + NumPy calculations for DA-015
============================================================
All numbers shown on the website come from the CSV files in /data.
Nothing is typed in by hand.

IMPORTANT: the data is SIMULATED SAMPLE DATA - NOT REAL STUDENT RECORDS.
"""
import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDENTS_CSV = os.path.join(BASE_DIR, "data", "students.csv")
MODULES_CSV = os.path.join(BASE_DIR, "data", "modules.csv")

# Weights for the illustrative Combined Learning-Progress Score
SCORE_WEIGHTS = {"attendance": 0.25, "quiz": 0.30, "revision": 0.20, "assignment": 0.25}

STUDENT_COLUMNS = ["student_id", "attendance", "assignment_completion", "quiz_score", "revision_sessions"]
MODULE_COLUMNS = ["module_id", "module_name", "learner_group", "learners", "attendance",
                  "assignment_completion", "quiz_score", "revision_sessions"]


def _read_csv(path, required_columns):
    """Read a CSV and make sure the needed columns exist. Gives a clear error if not."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    df = pd.read_csv(path)
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"{os.path.basename(path)} is missing columns: {missing}")
    return df


def load_students():
    """Load the five simulated students and add percentage columns + combined score."""
    df = _read_csv(STUDENTS_CSV, STUDENT_COLUMNS)

    # Quiz is out of 10 and revision is out of 10 -> convert both to percentages
    df["quiz_pct"] = df["quiz_score"] * 10
    df["revision_pct"] = df["revision_sessions"] * 10

    # Combined Score = Attendance x0.25 + Quiz% x0.30 + Revision% x0.20 + Assignment x0.25
    df["combined_score"] = (
        df["attendance"] * SCORE_WEIGHTS["attendance"]
        + df["quiz_pct"] * SCORE_WEIGHTS["quiz"]
        + df["revision_pct"] * SCORE_WEIGHTS["revision"]
        + df["assignment_completion"] * SCORE_WEIGHTS["assignment"]
    ).round(2)

    # Average of the three ACTIVITY indicators (attendance, assignment, revision)
    df["activity_avg"] = (
        (df["attendance"] + df["assignment_completion"] + df["revision_pct"]) / 3
    ).round(1)
    # Gap = activity minus quiz performance. A big positive gap means
    # "lots of activity but a low quiz score".
    df["activity_quiz_gap"] = (df["activity_avg"] - df["quiz_pct"]).round(1)
    return df


def load_modules():
    """Load the synthetic module-level dataset (kept separate from the 5 students)."""
    df = _read_csv(MODULES_CSV, MODULE_COLUMNS)
    df["quiz_pct"] = df["quiz_score"] * 10
    df["revision_pct"] = df["revision_sessions"] * 10
    return df


def score_band(score):
    """Neutral band for a combined score (describes a number, not a person)."""
    if score >= 75:
        return "75 and above"
    if score >= 55:
        return "55 to 74"
    return "Below 55"


def summary_stats(df=None):
    """Averages for the Home dashboard cards."""
    df = load_students() if df is None else df
    return {
        "total_learners": int(len(df)),
        "avg_attendance": round(float(df["attendance"].mean()), 1),
        "avg_assignment": round(float(df["assignment_completion"].mean()), 1),
        "avg_quiz_score": round(float(df["quiz_score"].mean()), 1),
        "avg_quiz_pct": round(float(df["quiz_pct"].mean()), 1),
        "avg_revision_pct": round(float(df["revision_pct"].mean()), 1),
        "avg_revision_sessions": round(float(df["revision_sessions"].mean()), 1),
        "avg_combined": round(float(df["combined_score"].mean()), 2),
    }


def indicator_comparison(df=None):
    """Average, highest and lowest value for every indicator (all as percentages)."""
    df = load_students() if df is None else df
    cols = {
        "Attendance": "attendance",
        "Assignment completion": "assignment_completion",
        "Revision activity": "revision_pct",
        "Quiz performance": "quiz_pct",
    }
    rows = []
    for label, col in cols.items():
        top = df.loc[df[col].idxmax()]
        low = df.loc[df[col].idxmin()]
        rows.append({
            "indicator": label,
            "type": "Performance" if col == "quiz_pct" else "Activity",
            "average": round(float(df[col].mean()), 1),
            "highest": float(df[col].max()), "highest_id": top["student_id"],
            "lowest": float(df[col].min()), "lowest_id": low["student_id"],
            "spread": round(float(np.ptp(df[col].to_numpy())), 1),
        })
    return rows


def generate_insights(df=None):
    """
    Build plain-language insights from the data using simple rules.
    Every sentence is created from calculated values.
    """
    df = load_students() if df is None else df
    insights = []

    best = df.loc[df["combined_score"].idxmax()]
    low = df.loc[df["combined_score"].idxmin()]
    insights.append({
        "title": "Spread of combined scores",
        "text": f"Combined scores range from {low['combined_score']:.2f} ({low['student_id']}) "
                f"to {best['combined_score']:.2f} ({best['student_id']}). "
                f"The class average is {df['combined_score'].mean():.2f}.",
    })

    # Activity high but quiz low (activity average 75+ and quiz below 50%)
    gap_rows = df[(df["activity_avg"] >= 75) & (df["quiz_pct"] < 50)]
    for _, r in gap_rows.iterrows():
        insights.append({
            "title": f"{r['student_id']}: high activity, low quiz result",
            "text": f"{r['student_id']} has attendance of {r['attendance']:g}% and revision of "
                    f"{r['revision_pct']:g}%, but a quiz score of {r['quiz_score']:g}/10 and assignment "
                    f"completion of {r['assignment_completion']:g}%. High activity does not always mean "
                    f"high understanding, so this may be a case for a friendly check-in.",
            "flag": True,
        })

    # Lowest activity indicators
    lowest_all = df[(df["attendance"] < 65) & (df["assignment_completion"] < 50)]
    for _, r in lowest_all.iterrows():
        insights.append({
            "title": f"{r['student_id']}: lower across all indicators",
            "text": f"{r['student_id']} is lower on attendance ({r['attendance']:g}%), assignments "
                    f"({r['assignment_completion']:g}%), revision ({r['revision_pct']:g}%) and quiz "
                    f"({r['quiz_score']:g}/10). Support planning could start with finding what is "
                    f"making participation difficult.",
            "flag": True,
        })

    # Lower attendance but good quiz score
    odd = df[(df["attendance"] < 75) & (df["quiz_pct"] >= 70)]
    for _, r in odd.iterrows():
        insights.append({
            "title": f"{r['student_id']}: lower attendance, stronger quiz result",
            "text": f"{r['student_id']} attended {r['attendance']:g}% of sessions but scored "
                    f"{r['quiz_score']:g}/10 with {r['assignment_completion']:g}% assignment completion. "
                    f"Attendance alone does not tell the whole story.",
        })
    return insights


def module_comparison(mdf=None):
    """
    Average of each indicator per module.
    Groups with more learners count more (weighted average using np.average).
    """
    mdf = load_modules() if mdf is None else mdf
    rows = []
    for (mid, name), g in mdf.groupby(["module_id", "module_name"], sort=True):
        w = g["learners"].to_numpy()
        rows.append({
            "module_id": mid,
            "module_name": name,
            "learners": int(w.sum()),
            "avg_attendance": round(float(np.average(g["attendance"], weights=w)), 1),
            "avg_assignment": round(float(np.average(g["assignment_completion"], weights=w)), 1),
            "avg_quiz_score": round(float(np.average(g["quiz_score"], weights=w)), 2),
            "avg_quiz_pct": round(float(np.average(g["quiz_pct"], weights=w)), 1),
            "avg_revision_sessions": round(float(np.average(g["revision_sessions"], weights=w)), 2),
            "avg_revision_pct": round(float(np.average(g["revision_pct"], weights=w)), 1),
        })
    return rows


def module_explanations(rows=None):
    """Explain differences between modules using the calculated averages."""
    rows = module_comparison() if rows is None else rows
    out = []
    top_quiz = max(rows, key=lambda r: r["avg_quiz_pct"])
    low_quiz = min(rows, key=lambda r: r["avg_quiz_pct"])
    top_assign = max(rows, key=lambda r: r["avg_assignment"])
    low_assign = min(rows, key=lambda r: r["avg_assignment"])
    out.append(f"{top_quiz['module_name']} has the highest average quiz score "
               f"({top_quiz['avg_quiz_score']}/10) and {low_quiz['module_name']} has the lowest "
               f"({low_quiz['avg_quiz_score']}/10) in this illustrative data.")
    out.append(f"Assignment completion is highest in {top_assign['module_name']} "
               f"({top_assign['avg_assignment']}%) and lowest in {low_assign['module_name']} "
               f"({low_assign['avg_assignment']}%).")
    for r in rows:
        if r["avg_attendance"] - r["avg_assignment"] >= 12:
            out.append(f"In {r['module_name']}, attendance ({r['avg_attendance']}%) is noticeably higher than "
                       f"assignment completion ({r['avg_assignment']}%). This gap is worth looking into, "
                       f"but the data alone cannot tell us why.")
    out.append("These are made-up numbers for demonstration. They are not institutional results and "
               "should not be used to judge any real module or teacher.")
    return out


def group_comparison(mdf=None):
    """Average per learner group across all modules (another way to compare learner groups)."""
    mdf = load_modules() if mdf is None else mdf
    rows = []
    for name, g in mdf.groupby("learner_group", sort=True):
        w = g["learners"].to_numpy()
        rows.append({
            "learner_group": name,
            "avg_attendance": round(float(np.average(g["attendance"], weights=w)), 1),
            "avg_assignment": round(float(np.average(g["assignment_completion"], weights=w)), 1),
            "avg_quiz_pct": round(float(np.average(g["quiz_pct"], weights=w)), 1),
            "avg_revision_pct": round(float(np.average(g["revision_pct"], weights=w)), 1),
        })
    return rows


def distribution(df=None):
    """Count of students in each combined-score band."""
    df = load_students() if df is None else df
    bands = df["combined_score"].apply(score_band)
    order = ["Below 55", "55 to 74", "75 and above"]
    return {b: int((bands == b).sum()) for b in order}


def students_as_records(df=None):
    """Students as a list of dictionaries (easy to send as JSON)."""
    df = load_students() if df is None else df
    df = df.copy()
    df["band"] = df["combined_score"].apply(score_band)
    df["gap_flag"] = (df["activity_avg"] >= 75) & (df["quiz_pct"] < 50)
    return df.to_dict(orient="records")
