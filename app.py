"""
app.py  -  Flask backend for LearnSense AI (Project DA-015, Group BCA_AI_15)
=============================================================================
Run with:   python app.py      then open  http://127.0.0.1:5000

Pages (HTML):  /  /analytics  /students  /charts  /learnsense  /responsible  /about
JSON routes:   /api/summary  /api/students  /api/modules  /api/chart-data
               /api/scenarios  /api/analyse (POST)  /api/reassess (POST)
"""
import os
from flask import Flask, render_template, jsonify, request

from analysis import data_analysis as da
from analysis.visualisations import generate_all_charts
from logic import friction_engine as fe

app = Flask(__name__)

PROJECT = {
    "title": "Online Learning Engagement Analysis",
    "project_id": "DA-015",
    "group_id": "BCA_AI_15",
    "domain": "EdTech Analytics",
    "solution": "LearnSense AI",
    "full_solution": "LearnSense AI \u2014 Intelligent Learning Friction Detection and Recovery System",
    "tagline": "Understand Learning. Detect Friction. Support Progress.",
}


@app.context_processor
def inject_project():
    """Makes `project` available in every template."""
    return {"project": PROJECT}


def safe_load(func, *args):
    """Run a data function; if the CSV is broken, return (None, error message)."""
    try:
        return func(*args), None
    except Exception as exc:  # beginner friendly: show the message instead of crashing
        return None, str(exc)


# ------------------------------ HTML PAGES ---------------------------------
@app.route("/")
def home():
    df, err = safe_load(da.load_students)
    if err:
        return render_template("error.html", message=err), 500
    return render_template(
        "index.html", active="home", stats=da.summary_stats(df),
        insights=da.generate_insights(df), students=da.students_as_records(df),
        distribution=da.distribution(df))


@app.route("/analytics")
def analytics():
    df, err = safe_load(da.load_students)
    mdf, err2 = safe_load(da.load_modules)
    if err or err2:
        return render_template("error.html", message=err or err2), 500
    modules = da.module_comparison(mdf)
    return render_template(
        "analytics.html", active="analytics", indicators=da.indicator_comparison(df),
        students=da.students_as_records(df), modules=modules,
        module_notes=da.module_explanations(modules), groups=da.group_comparison(mdf),
        weights=da.SCORE_WEIGHTS)


@app.route("/students")
def students():
    df, err = safe_load(da.load_students)
    if err:
        return render_template("error.html", message=err), 500
    return render_template("students.html", active="students",
                           students=da.students_as_records(df), weights=da.SCORE_WEIGHTS)


@app.route("/charts")
def charts():
    return render_template("charts.html", active="charts",
                           images=sorted(os.listdir(os.path.join(app.static_folder, "images", "charts")))
                           if os.path.isdir(os.path.join(app.static_folder, "images", "charts")) else [])


@app.route("/learnsense")
def learnsense():
    return render_template("learnsense.html", active="learnsense", scenarios=fe.SCENARIOS,
                           weights=fe.WEIGHTS)


@app.route("/responsible")
def responsible():
    return render_template("responsible.html", active="responsible")


@app.route("/about")
def about():
    return render_template("about.html", active="about")


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", message="That page does not exist."), 404


# ------------------------------ JSON ROUTES --------------------------------
@app.route("/api/summary")
def api_summary():
    df, err = safe_load(da.load_students)
    if err:
        return jsonify({"error": err}), 500
    return jsonify(da.summary_stats(df))


@app.route("/api/students")
def api_students():
    df, err = safe_load(da.load_students)
    if err:
        return jsonify({"error": err}), 500
    return jsonify(da.students_as_records(df))


@app.route("/api/modules")
def api_modules():
    mdf, err = safe_load(da.load_modules)
    if err:
        return jsonify({"error": err}), 500
    return jsonify({"modules": da.module_comparison(mdf), "groups": da.group_comparison(mdf)})


@app.route("/api/chart-data")
def api_chart_data():
    """Everything Chart.js needs, straight from the dataset."""
    df, err = safe_load(da.load_students)
    mdf, err2 = safe_load(da.load_modules)
    if err or err2:
        return jsonify({"error": err or err2}), 500
    return jsonify({
        "ids": df["student_id"].tolist(),
        "attendance": df["attendance"].tolist(),
        "assignment": df["assignment_completion"].tolist(),
        "quiz_score": df["quiz_score"].tolist(),
        "quiz_pct": df["quiz_pct"].tolist(),
        "revision_sessions": df["revision_sessions"].tolist(),
        "revision_pct": df["revision_pct"].tolist(),
        "combined": df["combined_score"].tolist(),
        # lists keep the band order (Flask sorts dictionary keys alphabetically)
        "distribution_labels": list(da.distribution(df).keys()),
        "distribution_values": list(da.distribution(df).values()),
        "modules": da.module_comparison(mdf),
    })


@app.route("/api/scenarios")
def api_scenarios():
    return jsonify(fe.SCENARIOS)


@app.route("/api/analyse", methods=["POST"])
def api_analyse():
    data = request.get_json(silent=True)
    try:
        return jsonify(fe.analyse_session(data))
    except fe.InputError as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/reassess", methods=["POST"])
def api_reassess():
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(fe.compare_before_after(
            data.get("before"), data.get("after"), data.get("quiz_before"), data.get("quiz_after")))
    except fe.InputError as exc:
        return jsonify({"error": str(exc)}), 400


# Make the Matplotlib pictures when the app starts (also works under gunicorn).
try:
    generate_all_charts()
except Exception as exc:
    print("Warning: could not create Matplotlib charts:", exc)

if __name__ == "__main__":
    app.run(debug=True)
